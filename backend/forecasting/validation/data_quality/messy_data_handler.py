"""
Messy Data Handler

Handles real-world data quality issues:
- Missing values (gaps, NULLs)
- Inconsistent formats
- Duplicate records
- Out-of-order dates
- Mixed data types
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MessyDataHandler:
    """
    Handles messy real-world data before classification/forecasting.
    
    Detects and fixes common data quality issues.
    """
    
    def detect_issues(self, df: pd.DataFrame, date_col: str = "date_local") -> Dict[str, List]:
        """
        Detect all data quality issues in the DataFrame.
        
        Returns:
            Dictionary with issue types and their locations
        """
        issues = {
            "missing_values": [],
            "duplicate_dates": [],
            "out_of_order": [],
            "negative_values": [],
            "inconsistent_types": [],
            "date_gaps": [],
        }
        
        if df.empty:
            return issues
        
        # Check for missing values
        for col in df.columns:
            missing = df[col].isna().sum()
            if missing > 0:
                issues["missing_values"].append({
                    "column": col,
                    "count": int(missing),
                    "percentage": float(missing / len(df) * 100)
                })
        
        # Check for duplicate dates (if date column exists)
        if date_col in df.columns:
            duplicates = df[df.duplicated(subset=[date_col], keep=False)]
            if not duplicates.empty:
                issues["duplicate_dates"].append({
                    "count": len(duplicates),
                    "dates": duplicates[date_col].tolist()[:10]  # First 10
                })
            
            # Check for out-of-order dates
            if len(df) > 1:
                sorted_df = df.sort_values(date_col)
                if not df[date_col].equals(sorted_df[date_col]):
                    issues["out_of_order"].append({
                        "count": len(df) - len(sorted_df.drop_duplicates(subset=[date_col])),
                        "message": "Dates are not in chronological order"
                    })
            
            # Check for date gaps
            if len(df) > 1:
                df_sorted = df.sort_values(date_col).copy()
                df_sorted[date_col] = pd.to_datetime(df_sorted[date_col])
                date_diff = df_sorted[date_col].diff()
                expected_diff = pd.Timedelta(days=1)
                gaps = date_diff[date_diff > expected_diff * 1.5]  # More than 1.5 days
                if not gaps.empty:
                    issues["date_gaps"].append({
                        "count": len(gaps),
                        "gaps": [
                            {
                                "from": str(gaps.index[i-1]),
                                "to": str(gaps.index[i]),
                                "days": int(gaps.iloc[i].days)
                            }
                            for i in range(len(gaps))
                        ][:10]  # First 10 gaps
                    })
        
        # Check for negative values in sales/units
        numeric_cols = ["units_sold", "sales_qty", "target"]
        for col in numeric_cols:
            if col in df.columns:
                negative = (df[col] < 0).sum()
                if negative > 0:
                    issues["negative_values"].append({
                        "column": col,
                        "count": int(negative)
                    })
        
        # Check for inconsistent types
        for col in df.columns:
            if df[col].dtype == "object":
                # Try to convert to numeric
                try:
                    pd.to_numeric(df[col], errors="raise")
                except (ValueError, TypeError):
                    issues["inconsistent_types"].append({
                        "column": col,
                        "type": str(df[col].dtype),
                        "sample": df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                    })
        
        return issues
    
    def clean_data(
        self, 
        df: pd.DataFrame, 
        strategy: str = "moderate",
        date_col: str = "date_local",
        target_col: str = "units_sold"
    ) -> Tuple[pd.DataFrame, Dict[str, any]]:
        """
        Clean data with specified strategy.
        
        Strategies:
        - "conservative": Minimal changes, only critical fixes
        - "moderate": Standard cleaning (default)
        - "aggressive": Maximum cleaning, may lose some data
        
        Returns:
            (cleaned_df, cleaning_report)
        """
        if df.empty:
            return df, {"message": "Empty DataFrame"}
        
        original_count = len(df)
        report = {
            "original_rows": original_count,
            "actions_taken": [],
            "rows_removed": 0,
            "rows_added": 0,
        }
        
        df_clean = df.copy()
        
        # 1. Handle date column
        if date_col in df_clean.columns:
            # Convert to datetime
            df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors="coerce")
            
            # Remove rows with invalid dates
            invalid_dates = df_clean[date_col].isna()
            if invalid_dates.sum() > 0:
                if strategy in ["moderate", "aggressive"]:
                    df_clean = df_clean[~invalid_dates]
                    report["actions_taken"].append(f"Removed {invalid_dates.sum()} rows with invalid dates")
                    report["rows_removed"] += int(invalid_dates.sum())
            
            # Sort by date
            df_clean = df_clean.sort_values(date_col).reset_index(drop=True)
            report["actions_taken"].append("Sorted by date")
            
            # Remove duplicate dates (keep first)
            duplicates = df_clean.duplicated(subset=[date_col], keep="first")
            if duplicates.sum() > 0:
                df_clean = df_clean[~duplicates]
                report["actions_taken"].append(f"Removed {duplicates.sum()} duplicate date rows")
                report["rows_removed"] += int(duplicates.sum())
        
        # 2. Handle target column (units_sold, sales_qty, target)
        target_cols = [target_col, "sales_qty", "target"]
        target_col_found = None
        for col in target_cols:
            if col in df_clean.columns:
                target_col_found = col
                break
        
        if target_col_found:
            # Convert to numeric
            df_clean[target_col_found] = pd.to_numeric(
                df_clean[target_col_found], 
                errors="coerce"
            )
            
            # Handle negative values
            negative = (df_clean[target_col_found] < 0).sum()
            if negative > 0:
                if strategy == "aggressive":
                    # Set to 0
                    df_clean.loc[df_clean[target_col_found] < 0, target_col_found] = 0
                    report["actions_taken"].append(f"Set {negative} negative values to 0")
                elif strategy == "moderate":
                    # Set to 0 for small negatives, remove large negatives
                    small_neg = (df_clean[target_col_found] < 0) & (df_clean[target_col_found] > -10)
                    large_neg = df_clean[target_col_found] < -10
                    df_clean.loc[small_neg, target_col_found] = 0
                    df_clean = df_clean[~large_neg]
                    report["actions_taken"].append(f"Fixed {small_neg.sum()} small negatives, removed {large_neg.sum()} large negatives")
                    report["rows_removed"] += int(large_neg.sum())
            
            # Handle NaN values
            nan_count = df_clean[target_col_found].isna().sum()
            if nan_count > 0:
                if strategy in ["moderate", "aggressive"]:
                    # Fill with 0 (zero demand)
                    df_clean[target_col_found] = df_clean[target_col_found].fillna(0)
                    report["actions_taken"].append(f"Filled {nan_count} NaN values with 0")
        
        # 3. Fill missing dates (if strategy is aggressive)
        if strategy == "aggressive" and date_col in df_clean.columns:
            if len(df_clean) > 1:
                # Create full date range
                min_date = df_clean[date_col].min()
                max_date = df_clean[date_col].max()
                full_range = pd.date_range(min_date, max_date, freq="D")
                
                # Reindex with full range
                df_clean = df_clean.set_index(date_col)
                df_clean = df_clean.reindex(full_range)
                df_clean = df_clean.reset_index()
                df_clean = df_clean.rename(columns={"index": date_col})
                
                # Fill missing values
                if target_col_found:
                    df_clean[target_col_found] = df_clean[target_col_found].fillna(0)
                
                report["rows_added"] = len(df_clean) - original_count
                report["actions_taken"].append(f"Filled missing dates (added {report['rows_added']} rows)")
        
        report["final_rows"] = len(df_clean)
        report["rows_changed"] = abs(len(df_clean) - original_count)
        
        return df_clean, report
    
    def assess_cleanliness(self, df: pd.DataFrame, date_col: str = "date_local") -> Dict[str, float]:
        """
        Score data quality (0-1 scale).
        
        Returns:
            Dictionary with quality scores
        """
        if df.empty:
            return {
                "overall": 0.0,
                "completeness": 0.0,
                "consistency": 0.0,
                "accuracy": 0.0
            }
        
        scores = {}
        
        # Completeness: How much data is present?
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isna().sum().sum()
        scores["completeness"] = 1.0 - (missing_cells / total_cells) if total_cells > 0 else 0.0
        
        # Consistency: Are dates in order? No duplicates?
        consistency_score = 1.0
        if date_col in df.columns:
            # Check for duplicates
            duplicates = df.duplicated(subset=[date_col]).sum()
            consistency_score *= (1.0 - (duplicates / len(df))) if len(df) > 0 else 1.0
            
            # Check for order
            if len(df) > 1:
                sorted_df = df.sort_values(date_col)
                if not df[date_col].equals(sorted_df[date_col]):
                    consistency_score *= 0.8  # Penalty for out-of-order
        
        scores["consistency"] = consistency_score
        
        # Accuracy: No negative values, reasonable ranges
        accuracy_score = 1.0
        numeric_cols = ["units_sold", "sales_qty", "target"]
        for col in numeric_cols:
            if col in df.columns:
                # Check for negatives
                negative = (df[col] < 0).sum()
                if negative > 0:
                    accuracy_score *= (1.0 - (negative / len(df))) if len(df) > 0 else 1.0
        
        scores["accuracy"] = accuracy_score
        
        # Overall: Weighted average
        scores["overall"] = (
            scores["completeness"] * 0.4 +
            scores["consistency"] * 0.3 +
            scores["accuracy"] * 0.3
        )
        
        return scores

