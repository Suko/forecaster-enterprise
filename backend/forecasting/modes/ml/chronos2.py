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
            # Chronos-2 expects 'item_id' column, but we use 'id'
            # Create a copy and rename if needed
            chronos_df = context_df.copy()
            if "id" in chronos_df.columns and "item_id" not in chronos_df.columns:
                chronos_df = chronos_df.rename(columns={"id": "item_id"})
            
            # Ensure numeric columns are numeric (Chronos-2 requires this)
            if "target" in chronos_df.columns:
                chronos_df["target"] = pd.to_numeric(chronos_df["target"], errors='coerce')
            # Ensure covariate columns are numeric if they exist
            for col in chronos_df.columns:
                if col not in ["item_id", "timestamp"] and chronos_df[col].dtype == 'object':
                    chronos_df[col] = pd.to_numeric(chronos_df[col], errors='coerce')
            
            # Chronos-2 expects specific format via predict_df()
            predictions_df = self.pipeline.predict_df(
                chronos_df,
                prediction_length=prediction_length,
                future_df=future_covariates,
                quantile_levels=quantile_levels,
            )
            
            # Ensure consistent column names
            # Get item_id from context (preserve original id)
            if not context_df.empty:
                if "id" in context_df.columns:
                    item_id = str(context_df["id"].iloc[0])
                elif "item_id" in context_df.columns:
                    item_id = str(context_df["item_id"].iloc[0])
                else:
                    item_id = "item_1"
            else:
                item_id = "item_1"
            
            # Generate timestamps if not in predictions_df
            if "timestamp" in predictions_df.columns:
                timestamps = predictions_df["timestamp"].values
            else:
                # Generate future timestamps starting from day after last context date
                last_date = pd.to_datetime(context_df["timestamp"]).max()
                timestamps = pd.date_range(
                    start=last_date + timedelta(days=1),
                    periods=prediction_length,
                    freq="D"
                )
            
            # Create result DataFrame with proper id column
            result_df = pd.DataFrame({
                "id": [item_id] * prediction_length,
                "timestamp": timestamps,
            })
            
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

