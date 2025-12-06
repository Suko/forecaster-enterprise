"""
Chronos-2 Model Implementation

Wrapper around Amazon's Chronos-2 pretrained forecasting model.
"""
import os
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ...core.models.base import BaseForecastModel

try:
    from chronos import Chronos2Pipeline
    CHRONOS_AVAILABLE = True
except ImportError:
    CHRONOS_AVAILABLE = False
    Chronos2Pipeline = None


class Chronos2Model(BaseForecastModel):
    """Chronos-2 ML model implementation"""
    
    def __init__(
        self,
        model_id: str = None,
        device_map: str = None,
    ):
        super().__init__(model_name="chronos-2")
        
        if not CHRONOS_AVAILABLE:
            raise ImportError(
                "chronos package not installed. "
                "Install with: pip install chronos-forecasting"
            )
        
        self.model_id = model_id or os.environ.get("CHRONOS_MODEL_ID", "amazon/chronos-2")
        self.device_map = device_map or os.environ.get("CHRONOS_DEVICE", "cpu")
        self.pipeline: Optional[Chronos2Pipeline] = None
    
    async def initialize(self) -> None:
        """Initialize Chronos-2 pipeline (lazy loading)"""
        if self._initialized:
            return
        
        try:
            self.pipeline = Chronos2Pipeline.from_pretrained(
                self.model_id,
                device_map=self.device_map
            )
            self._initialized = True
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Chronos-2 model: {e}") from e
    
    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_covariates: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = None,
    ) -> pd.DataFrame:
        """
        Generate forecast using Chronos-2.
        
        Args:
            context_df: Historical data with columns: id, timestamp, target, [past_covariates]
            prediction_length: Number of days to forecast
            future_covariates: Optional future covariates DataFrame
            quantile_levels: Quantiles to return (default: [0.1, 0.5, 0.9])
        
        Returns:
            DataFrame with columns: id, timestamp, point_forecast, p10, p50, p90
        """
        if not self._initialized:
            await self.initialize()
        
        # Validate input
        self.validate_input(context_df, prediction_length, min_history=5)
        
        if quantile_levels is None:
            quantile_levels = [0.1, 0.5, 0.9]
        
        try:
            # Prepare data for Chronos-2
            # Chronos-2 expects specific format via predict_df()
            predictions_df = self.pipeline.predict_df(
                context_df,
                prediction_length=prediction_length,
                future_df=future_covariates,
                quantile_levels=quantile_levels,
            )
            
            # Ensure consistent column names
            result_df = pd.DataFrame()
            result_df["id"] = predictions_df.get("id", context_df["id"].iloc[0] if not context_df.empty else "item_1")
            result_df["timestamp"] = predictions_df.get("timestamp", pd.date_range(
                start=context_df["timestamp"].max() + timedelta(days=1),
                periods=prediction_length,
                freq="D"
            ))
            
            # Extract point forecast (median/p50)
            if "0.5" in predictions_df.columns or "median" in predictions_df.columns:
                result_df["point_forecast"] = predictions_df.get("0.5", predictions_df.get("median", predictions_df.iloc[:, 0]))
            else:
                result_df["point_forecast"] = predictions_df.iloc[:, 0]  # First column as fallback
            
            # Extract quantiles
            for q in quantile_levels:
                q_str = str(q)
                if q_str in predictions_df.columns:
                    result_df[f"p{int(q*100)}"] = predictions_df[q_str]
            
            return result_df
            
        except Exception as e:
            raise RuntimeError(f"Chronos-2 prediction failed: {e}") from e
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model metadata"""
        return {
            "model_name": self.model_name,
            "model_id": self.model_id,
            "device": self.device_map,
            "initialized": self._initialized,
            "version": "chronos-2",
        }

