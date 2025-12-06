"""
Moving Average Statistical Model

7-day moving average baseline forecasting method.
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import timedelta

from ...core.models.base import BaseForecastModel


class MovingAverageModel(BaseForecastModel):
    """7-day Moving Average statistical forecasting method"""
    
    def __init__(self, window: int = 7):
        super().__init__(model_name="statistical_ma7")
        self.window = window
    
    async def initialize(self) -> None:
        """No initialization needed for statistical methods"""
        self._initialized = True
    
    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_covariates: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = None,
    ) -> pd.DataFrame:
        """
        Generate forecast using 7-day moving average.
        
        Args:
            context_df: Historical data with columns: id, timestamp, target
            prediction_length: Number of days to forecast
            future_covariates: Ignored for statistical methods
            quantile_levels: Quantiles to return (default: [0.1, 0.5, 0.9])
        
        Returns:
            DataFrame with columns: id, timestamp, point_forecast, p10, p50, p90
        """
        # Validate input
        self.validate_input(context_df, prediction_length, min_history=self.window)
        
        if quantile_levels is None:
            quantile_levels = [0.1, 0.5, 0.9]
        
        # Calculate moving average from last N days
        target_values = context_df["target"].values
        last_window = target_values[-self.window:]
        avg_demand = np.mean(last_window)
        std_demand = np.std(last_window) if len(last_window) > 1 else 0.0
        
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
        result_df["point_forecast"] = avg_demand
        
        # Calculate quantiles (simple approximation using normal distribution)
        # For statistical methods, we use a simple approximation
        for q in quantile_levels:
            # Simple quantile approximation: mean ± z_score * std
            # For 0.1, 0.5, 0.9: z-scores are approximately -1.28, 0, 1.28
            if q == 0.5:
                result_df[f"p{int(q*100)}"] = avg_demand
            elif q < 0.5:
                z_score = -1.28  # Approximation for 10th percentile
                result_df[f"p{int(q*100)}"] = max(0, avg_demand + z_score * std_demand)
            else:  # q > 0.5
                z_score = 1.28  # Approximation for 90th percentile
                result_df[f"p{int(q*100)}"] = avg_demand + z_score * std_demand
        
        return result_df
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata"""
        return {
            "model_name": self.model_name,
            "window": self.window,
            "initialized": self._initialized,
            "type": "statistical",
        }

