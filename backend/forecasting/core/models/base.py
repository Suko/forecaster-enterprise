"""
BaseForecastModel - Abstract interface for all forecasting models

All forecasting models must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
import pandas as pd
from datetime import date


class BaseForecastModel(ABC):
    """Abstract base class for all forecasting models"""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self._initialized = False

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the model (lazy loading).
        Should be called before first use.
        """
        pass

    @abstractmethod
    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_covariates: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = None,
    ) -> pd.DataFrame:
        """
        Generate forecast predictions.

        Args:
            context_df: Historical data with columns:
                - id: Item identifier
                - timestamp: Date column
                - target: Target variable (units_sold)
                - Optional: past covariates (promo_flag, holiday_flag, etc.)
            prediction_length: Number of days to forecast
            future_covariates: Optional future covariates DataFrame
            quantile_levels: List of quantiles to return (default: [0.1, 0.5, 0.9])

        Returns:
            DataFrame with columns:
                - id: Item identifier
                - timestamp: Forecast date
                - point_forecast: Main prediction (median/mean)
                - p10, p50, p90: Quantile predictions (if quantile_levels provided)
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get model metadata.

        Returns:
            Dictionary with model information (name, version, etc.)
        """
        pass

    def is_initialized(self) -> bool:
        """Check if model is initialized"""
        return self._initialized

    def validate_input(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        min_history: int = 7,
    ) -> None:
        """
        Validate input data before forecasting.

        Args:
            context_df: Historical data
            prediction_length: Forecast horizon
            min_history: Minimum required history (default: 7 days)

        Raises:
            ValueError: If validation fails
        """
        if context_df.empty:
            raise ValueError("Context DataFrame is empty")

        required_columns = ["id", "timestamp", "target"]
        missing = [col for col in required_columns if col not in context_df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        if len(context_df) < min_history:
            raise ValueError(
                f"Insufficient history: {len(context_df)} days, "
                f"minimum required: {min_history} days"
            )

        if prediction_length < 1:
            raise ValueError("prediction_length must be >= 1")

        if prediction_length > 365:
            raise ValueError("prediction_length must be <= 365")

