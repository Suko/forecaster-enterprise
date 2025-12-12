"""
SBA (Syntetos-Boylan Approximation) Statistical Model

For lumpy/intermittent demand forecasting.
SBA is an improved version of Croston's method that corrects for bias.

Formula:
  Forecast = (1 - p/2) * (z / p)
  where:
    p = average demand interval (ADI)
    z = average demand size
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import timedelta

from ...core.models.base import BaseForecastModel


class SBAModel(BaseForecastModel):
    """
    Syntetos-Boylan Approximation for lumpy/intermittent demand.

    Best for:
    - Lumpy demand (sporadic, high-variability)
    - Intermittent demand (many zero-demand days)
    - ADI > 1.32 (average demand interval)
    """

    def __init__(self):
        super().__init__(model_name="sba")

    async def initialize(self) -> None:
        """No initialization needed for statistical methods"""
        self._initialized = True

    def get_model_info(self) -> dict:
        """Get model metadata"""
        return {
            "name": "SBA (Syntetos-Boylan Approximation)",
            "type": "statistical",
            "description": "For lumpy/intermittent demand forecasting",
            "version": "1.0.0"
        }

    def _calculate_adi(self, series: pd.Series) -> float:
        """
        Calculate Average Demand Interval (ADI).

        ADI = total_periods / number_of_non_zero_periods
        """
        non_zero_count = (series > 0).sum()
        if non_zero_count == 0:
            return float('inf')  # No demand at all

        total_periods = len(series)
        adi = total_periods / non_zero_count
        return float(adi)

    def _calculate_avg_demand_size(self, series: pd.Series) -> float:
        """
        Calculate average demand size (only for non-zero periods).
        """
        non_zero_values = series[series > 0]
        if len(non_zero_values) == 0:
            return 0.0

        return float(non_zero_values.mean())

    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_covariates: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = None,
    ) -> pd.DataFrame:
        """
        Generate forecast using SBA (Syntetos-Boylan Approximation).

        Args:
            context_df: Historical data with columns: id, timestamp, target
            prediction_length: Number of days to forecast
            future_covariates: Ignored for statistical methods
            quantile_levels: Quantiles to return (default: [0.1, 0.5, 0.9])

        Returns:
            DataFrame with columns: id, timestamp, point_forecast, p10, p50, p90
        """
        # Validate input
        self.validate_input(context_df, prediction_length, min_history=7)

        if quantile_levels is None:
            quantile_levels = [0.1, 0.5, 0.9]

        # Get target values
        target_values = pd.to_numeric(context_df["target"], errors='coerce')
        target_series = pd.Series(target_values.values)

        # Calculate SBA parameters
        adi = self._calculate_adi(target_series)
        avg_demand_size = self._calculate_avg_demand_size(target_series)

        # SBA Formula: Forecast = (1 - p/2) * (z / p)
        # where p = ADI, z = average demand size
        if adi == float('inf') or adi == 0:
            # No demand or invalid ADI, forecast zero
            forecast_value = 0.0
        else:
            # SBA formula
            p = adi
            z = avg_demand_size
            forecast_value = (1 - p / 2) * (z / p)
            # Ensure non-negative
            forecast_value = max(0.0, forecast_value)

        # Generate forecast dates
        last_date = pd.to_datetime(context_df["timestamp"].max())
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=prediction_length,
            freq="D"
        )

        # Create result DataFrame
        result_df = pd.DataFrame()
        result_df["id"] = context_df["id"].iloc[0] if "id" in context_df.columns else "item_1"
        result_df["timestamp"] = forecast_dates
        result_df["point_forecast"] = forecast_value

        # Calculate quantiles (simple approximation)
        # For SBA, we use a simple approximation based on historical variability
        non_zero_values = target_series[target_series > 0]
        if len(non_zero_values) > 1:
            std_demand = float(non_zero_values.std())
        else:
            std_demand = 0.0

        for q in quantile_levels:
            if q == 0.5:
                result_df[f"p{int(q*100)}"] = forecast_value
            elif q < 0.5:
                # Lower quantile: use forecast - some variability
                z_score = -1.28  # Approximation for 10th percentile
                result_df[f"p{int(q*100)}"] = max(0, forecast_value + z_score * std_demand)
            else:
                # Upper quantile: use forecast + some variability
                z_score = 1.28  # Approximation for 90th percentile
                result_df[f"p{int(q*100)}"] = forecast_value + z_score * std_demand

        return result_df

