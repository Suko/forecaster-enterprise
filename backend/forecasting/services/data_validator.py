"""
Data Validator - Ensures data correctness before sending to models

Enhanced validator inspired by Darts' TimeSeries validation practices:
1. Consistent time frequency validation
2. Missing date detection and handling
3. Time index integrity checks
4. NaN value handling strategies

Validates and logs data transformations for audit trail.
Follows ML best practices for data validation.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Enhanced data validator inspired by Darts' TimeSeries validation.

    Darts practices we implement:
    - Time frequency consistency checks
    - Missing date detection (with fill options)
    - Time index integrity validation
    - Better NaN handling strategies
    """

    @staticmethod
    def validate_time_index(
        context_df: pd.DataFrame,
        expected_freq: str = "D",
        fill_missing_dates: bool = False,
    ) -> Tuple[bool, Dict[str, any], Optional[pd.DataFrame]]:
        """
        Validate time index consistency (inspired by Darts).

        Darts requires:
        - Consistent frequency (can be inferred or explicit)
        - No gaps (or fill_missing_dates=True)
        - Proper datetime index

        Args:
            context_df: DataFrame with timestamp column
            expected_freq: Expected frequency ('D' for daily, 'W' for weekly, etc.)
            fill_missing_dates: If True, fill missing dates with NaN/0

        Returns:
            (is_valid, report, cleaned_df)
        """
        report = {
            "has_timestamp": "timestamp" in context_df.columns,
            "timestamp_type": None,
            "date_range": None,
            "expected_days": None,
            "actual_days": None,
            "missing_dates": 0,
            "duplicate_dates": 0,
            "frequency_consistent": False,
            "issues": [],
            "warnings": [],
        }

        if "timestamp" not in context_df.columns:
            return False, report, None

        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(context_df["timestamp"]):
            context_df["timestamp"] = pd.to_datetime(context_df["timestamp"], errors='coerce')

        # Check for null timestamps
        null_timestamps = context_df["timestamp"].isna().sum()
        if null_timestamps > 0:
            report["issues"].append(f"{null_timestamps} null timestamps")
            return False, report, None

        # Sort by timestamp
        context_df = context_df.sort_values("timestamp").copy()

        # Check for duplicates (Darts may aggregate, we flag it)
        duplicates = context_df.duplicated(subset=["timestamp"]).sum()
        report["duplicate_dates"] = int(duplicates)
        if duplicates > 0:
            report["warnings"].append(f"{duplicates} duplicate timestamps detected")
            # Remove duplicates (keep first)
            context_df = context_df.drop_duplicates(subset=["timestamp"], keep='first')

        # Calculate date range
        min_date = context_df["timestamp"].min()
        max_date = context_df["timestamp"].max()
        report["date_range"] = {
            "start": str(min_date.date()),
            "end": str(max_date.date()),
        }

        # Check for missing dates (Darts' key validation)
        date_range = pd.date_range(start=min_date, end=max_date, freq=expected_freq)
        report["expected_days"] = len(date_range)
        report["actual_days"] = len(context_df)
        missing_dates = len(date_range) - len(context_df)
        report["missing_dates"] = missing_dates

        if missing_dates > 0:
            # Darts would require fill_missing_dates=True or explicit freq
            report["warnings"].append(
                f"{missing_dates} missing dates detected. "
                f"Time series should have consistent frequency."
            )

            if fill_missing_dates:
                # Fill missing dates (Darts' fill_missing_dates=True behavior)
                context_df = context_df.set_index("timestamp")
                context_df = context_df.reindex(date_range, fill_value=np.nan)
                context_df = context_df.reset_index()
                context_df = context_df.rename(columns={"index": "timestamp"})

                # Fill NaN values in target with 0 (zero-demand days)
                if "target" in context_df.columns:
                    context_df["target"] = context_df["target"].fillna(0)

                report["warnings"].append(f"Filled {missing_dates} missing dates with 0")
            else:
                # Check if frequency is consistent (Darts' requirement)
                date_diffs = context_df["timestamp"].diff().dt.days
                unique_diffs = date_diffs.dropna().unique()

                if len(unique_diffs) == 1:
                    report["frequency_consistent"] = True
                    report["detected_freq"] = f"{unique_diffs[0]}D"
                else:
                    report["frequency_consistent"] = False
                    report["issues"].append(
                        f"Inconsistent date frequency. "
                        f"Found gaps: {sorted(unique_diffs[unique_diffs > 1])}"
                    )

        # Check frequency consistency (Darts requires this)
        if missing_dates == 0:
            date_diffs = context_df["timestamp"].diff().dt.days
            unique_diffs = date_diffs.dropna().unique()

            if len(unique_diffs) == 1:
                report["frequency_consistent"] = True
                report["detected_freq"] = f"{unique_diffs[0]}D"
            elif len(unique_diffs) <= 2:
                # Allow small variation (e.g., 1-2 days)
                report["frequency_consistent"] = True
                report["warnings"].append(f"Minor frequency variation: {unique_diffs}")
            else:
                report["frequency_consistent"] = False
                report["issues"].append("Inconsistent date frequency detected")

        is_valid = len(report["issues"]) == 0
        return is_valid, report, context_df

    @staticmethod
    def validate_nan_values(
        context_df: pd.DataFrame,
        fillna_value: Optional[float] = 0,
        fillna_strategy: str = "zero",
    ) -> Tuple[bool, Dict[str, any], Optional[pd.DataFrame]]:
        """
        Validate and handle NaN values (inspired by Darts' fillna_value parameter).

        Darts allows fillna_value to replace NaN during TimeSeries creation.
        We implement similar strategies.

        Args:
            context_df: DataFrame to validate
            fillna_value: Value to fill NaN with (if strategy is 'value')
            fillna_strategy: Strategy ('zero', 'forward_fill', 'value', 'error')

        Returns:
            (is_valid, report, cleaned_df)
        """
        report = {
            "nan_counts": {},
            "nan_percentages": {},
            "filled_nans": {},
            "strategy": fillna_strategy,
            "issues": [],
            "warnings": [],
        }

        context_df = context_df.copy()

        # Check each column
        for col in context_df.columns:
            if col == "timestamp":
                continue

            nan_count = context_df[col].isna().sum()
            nan_pct = (nan_count / len(context_df)) * 100

            report["nan_counts"][col] = int(nan_count)
            report["nan_percentages"][col] = float(nan_pct)

            if nan_count > 0:
                if fillna_strategy == "error":
                    report["issues"].append(f"Column '{col}' has {nan_count} NaN values ({nan_pct:.1f}%)")
                elif fillna_strategy == "zero":
                    context_df[col] = context_df[col].fillna(0)
                    report["filled_nans"][col] = nan_count
                    report["warnings"].append(f"Filled {nan_count} NaN values in '{col}' with 0")
                elif fillna_strategy == "forward_fill":
                    context_df[col] = context_df[col].ffill().fillna(0)
                    report["filled_nans"][col] = nan_count
                    report["warnings"].append(f"Forward-filled {nan_count} NaN values in '{col}'")
                elif fillna_strategy == "value" and fillna_value is not None:
                    context_df[col] = context_df[col].fillna(fillna_value)
                    report["filled_nans"][col] = nan_count
                    report["warnings"].append(f"Filled {nan_count} NaN values in '{col}' with {fillna_value}")

        # Critical check: target column should not have too many NaNs
        if "target" in context_df.columns:
            target_nan_pct = report["nan_percentages"].get("target", 0)
            if target_nan_pct > 50:
                report["issues"].append(f"Target column has {target_nan_pct:.1f}% NaN values (too high)")

        is_valid = len(report["issues"]) == 0
        return is_valid, report, context_df

    @staticmethod
    def validate_complete(
        context_df: pd.DataFrame,
        item_id: str,
        min_history_days: int = 7,
        expected_freq: str = "D",
        fill_missing_dates: bool = True,
        fillna_strategy: str = "zero",
    ) -> Tuple[bool, Dict[str, any], Optional[pd.DataFrame], Optional[str]]:
        """
        Complete validation inspired by Darts' TimeSeries validation.

        Combines all checks:
        1. Time index consistency (Darts' key requirement)
        2. NaN value handling (Darts' fillna_value)
        3. Data type validation
        4. Business rule validation

        Returns:
            (is_valid, full_report, cleaned_df, error_message)
        """
        full_report = {
            "item_id": item_id,
            "validation_steps": [],
            "time_index_validation": None,
            "nan_validation": None,
            "data_quality_issues": [],
            "warnings": [],
        }

        # Make a copy to avoid modifying original
        context_df = context_df.copy()

        # Step 1: Validate time index (Darts' primary check)
        time_valid, time_report, context_df = DataValidator.validate_time_index(
            context_df, expected_freq=expected_freq, fill_missing_dates=fill_missing_dates
        )
        full_report["time_index_validation"] = time_report
        full_report["validation_steps"].append("time_index")

        if not time_valid and not fill_missing_dates:
            return False, full_report, None, f"Time index validation failed: {time_report['issues']}"

        # Step 2: Validate and handle NaN values (Darts' fillna_value)
        nan_valid, nan_report, context_df = DataValidator.validate_nan_values(
            context_df, fillna_strategy=fillna_strategy
        )
        full_report["nan_validation"] = nan_report
        full_report["validation_steps"].append("nan_values")

        if not nan_valid:
            full_report["data_quality_issues"].extend(nan_report["issues"])

        # Step 3: Check minimum history (our requirement)
        if len(context_df) < min_history_days:
            return False, full_report, None, f"Insufficient history: {len(context_df)} days (need {min_history_days}+)"

        # Step 4: Validate target column
        if "target" not in context_df.columns:
            return False, full_report, None, "Missing 'target' column"

        # Convert target to numeric (handles Decimal types)
        context_df["target"] = pd.to_numeric(context_df["target"], errors='coerce')

        # Check for negative values (business rule)
        negative_count = (context_df["target"] < 0).sum()
        if negative_count > 0:
            full_report["data_quality_issues"].append(f"{negative_count} negative target values")
            # Cap at 0
            context_df.loc[context_df["target"] < 0, "target"] = 0
            full_report["warnings"].append(f"Capped {negative_count} negative values to 0")

        # Collect all warnings
        if time_report.get("warnings"):
            full_report["warnings"].extend(time_report["warnings"])
        if nan_report.get("warnings"):
            full_report["warnings"].extend(nan_report["warnings"])

        # Final validation
        is_valid = len(full_report["data_quality_issues"]) == 0

        return is_valid, full_report, context_df, None if is_valid else "; ".join(full_report["data_quality_issues"])

    @staticmethod
    def validate_context_data(
        context_df: pd.DataFrame,
        item_id: str,
        min_history_days: int = 7,
        fill_missing_dates: bool = True,
        fillna_strategy: str = "zero",
    ) -> Tuple[bool, Dict[str, any], Optional[str], Optional[pd.DataFrame]]:
        """
        Validate context data before sending to model.

        Enhanced version that uses validate_complete() internally and returns cleaned DataFrame.
        Maintains backward compatibility but also returns cleaned data.

        Args:
            context_df: Historical data DataFrame
            item_id: Item identifier
            min_history_days: Minimum required history
            fill_missing_dates: Fill missing dates (default: True, like Darts)
            fillna_strategy: Strategy for handling NaN values

        Returns:
            (is_valid, validation_report, error_message, cleaned_df)
            Note: For backward compatibility, can also return (is_valid, report, error_message)
        """
        is_valid, full_report, cleaned_df, error_msg = DataValidator.validate_complete(
            context_df,
            item_id=item_id,
            min_history_days=min_history_days,
            expected_freq="D",
            fill_missing_dates=fill_missing_dates,
            fillna_strategy=fillna_strategy,
        )

        # Convert full_report to simplified format for backward compatibility
        simplified_report = {
            "item_id": item_id,
            "row_count": len(cleaned_df) if cleaned_df is not None else len(context_df),
            "date_range": full_report.get("time_index_validation", {}).get("date_range"),
            "target_stats": None,
            "missing_values": {},
            "data_quality_issues": full_report.get("data_quality_issues", []),
            "warnings": full_report.get("warnings", []),
        }

        # Add target stats if available
        if cleaned_df is not None and "target" in cleaned_df.columns:
            target_numeric = pd.to_numeric(cleaned_df["target"], errors='coerce')
            simplified_report["target_stats"] = {
                "mean": float(target_numeric.mean()),
                "std": float(target_numeric.std()),
                "min": float(target_numeric.min()),
                "max": float(target_numeric.max()),
                "zeros": int((target_numeric == 0).sum()),
                "nulls": int(target_numeric.isna().sum()),
            }

        # Return with cleaned_df for new usage
        # Note: For backward compatibility with old code expecting 3-tuple,
        # we return 4-tuple but old code can unpack first 3
        return is_valid, simplified_report, error_msg, cleaned_df

    @staticmethod
    def validate_predictions(
        predictions_df: pd.DataFrame,
        item_id: str,
        prediction_length: int,
    ) -> Tuple[bool, Dict[str, any], Optional[str]]:
        """
        Validate predictions returned from model.

        Returns:
            (is_valid, validation_report, error_message)
        """
        report = {
            "item_id": item_id,
            "expected_count": prediction_length,
            "actual_count": len(predictions_df),
            "has_timestamp": "timestamp" in predictions_df.columns,
            "has_point_forecast": "point_forecast" in predictions_df.columns,
            "forecast_stats": None,
            "issues": [],
        }

        # Check count
        if len(predictions_df) != prediction_length:
            report["issues"].append(f"Expected {prediction_length} predictions, got {len(predictions_df)}")

        # Check required columns
        if "point_forecast" not in predictions_df.columns:
            return False, report, "Missing 'point_forecast' column"

        if "timestamp" not in predictions_df.columns:
            report["issues"].append("Missing 'timestamp' column")

        # Check for null predictions
        null_forecasts = predictions_df["point_forecast"].isna().sum()
        if null_forecasts > 0:
            report["issues"].append(f"{null_forecasts} null predictions")

        # Check for negative predictions (shouldn't happen for sales)
        negative_count = (predictions_df["point_forecast"] < 0).sum()
        if negative_count > 0:
            report["warnings"] = [f"{negative_count} negative predictions (unusual for sales)"]

        # Calculate statistics
        if len(predictions_df) > 0:
            report["forecast_stats"] = {
                "mean": float(predictions_df["point_forecast"].mean()),
                "min": float(predictions_df["point_forecast"].min()),
                "max": float(predictions_df["point_forecast"].max()),
            }

        is_valid = len(report["issues"]) == 0
        return is_valid, report, None if is_valid else "; ".join(report["issues"])

