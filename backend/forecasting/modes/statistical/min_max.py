"""
Min/Max Rules Statistical Model

For low-value, high-variability SKUs (C-Z classification).
Uses simple rules: min = safety stock, max = reorder point.

This is a cost-effective approach for SKUs where:
- Low value (C-class)
- High variability (Z-class)
- Complex forecasting not worth the cost
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from datetime import timedelta

from ...core.models.base import BaseForecastModel


class MinMaxModel(BaseForecastModel):
    """
    Min/Max Rules for low-value, high-variability SKUs.
    
    Best for:
    - C-Z SKUs (low value, high variability)
    - Cost-effective forecasting
    - Simple inventory management
    """
    
    def __init__(self):
        super().__init__(model_name="min_max")
    
    async def initialize(self) -> None:
        """No initialization needed for statistical methods"""
        self._initialized = True
    
    def get_model_info(self) -> dict:
        """Get model metadata"""
        return {
            "name": "Min/Max Rules",
            "type": "statistical",
            "description": "Simple rules for low-value, high-variability SKUs",
            "version": "1.0.0"
        }
    
    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_covariates: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = None,
    ) -> pd.DataFrame:
        """
        Generate forecast using Min/Max rules.
        
        Strategy:
        - Min (safety stock) = 0 (or small buffer)
        - Max (reorder point) = average demand
        - Forecast = average demand (constant)
        
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
        
        # Calculate simple statistics
        avg_demand = float(target_series.mean())
        std_demand = float(target_series.std()) if len(target_series) > 1 else 0.0
        
        # Min/Max strategy: Use average demand as forecast
        # This is simple and cost-effective for low-value items
        forecast_value = max(0.0, avg_demand)
        
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

