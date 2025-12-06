"""
Quality Calculator

Calculates forecast accuracy metrics using industry-standard formulas.
"""
from typing import List, Optional, Dict
import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import date

from models.forecast import ForecastResult


class QualityCalculator:
    """Calculate forecast accuracy metrics"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    @staticmethod
    def calculate_mape(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """
        Calculate Mean Absolute Percentage Error (MAPE).
        
        Formula: MAPE = (100/n) × Σ|Actual - Forecast|/Actual
        
        Industry Standard: APICS
        """
        if len(actuals) != len(forecasts):
            return None
        
        errors = []
        for actual, forecast in zip(actuals, forecasts):
            if actual > 0:
                errors.append(abs(actual - forecast) / actual)
        
        if not errors:
            return None
        
        return (100.0 / len(errors)) * sum(errors)
    
    @staticmethod
    def calculate_mae(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """
        Calculate Mean Absolute Error (MAE).
        
        Formula: MAE = (1/n) × Σ|Actual - Forecast|
        
        Industry Standard: Statistical Standard
        """
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        errors = [abs(a - f) for a, f in zip(actuals, forecasts)]
        return sum(errors) / len(errors)
    
    @staticmethod
    def calculate_rmse(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """
        Calculate Root Mean Squared Error (RMSE).
        
        Formula: RMSE = √[(1/n) × Σ(Actual - Forecast)²]
        
        Industry Standard: Statistical Standard
        """
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        squared_errors = [(a - f) ** 2 for a, f in zip(actuals, forecasts)]
        mse = sum(squared_errors) / len(squared_errors)
        return math.sqrt(mse)
    
    @staticmethod
    def calculate_bias(actuals: List[float], forecasts: List[float]) -> Optional[float]:
        """
        Calculate Forecast Bias.
        
        Formula: Bias = (1/n) × Σ(Forecast - Actual)
        
        Positive = over-forecasting, Negative = under-forecasting
        
        Industry Standard: APICS
        """
        if len(actuals) != len(forecasts) or len(actuals) == 0:
            return None
        
        errors = [f - a for a, f in zip(actuals, forecasts)]
        return sum(errors) / len(errors)
    
    async def calculate_quality_metrics(
        self,
        item_id: str,
        method: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Optional[float]]:
        """
        Calculate quality metrics for a specific item and method.
        
        Args:
            item_id: Item identifier
            method: Forecasting method ("chronos-2", "statistical_ma7")
            start_date: Start date for analysis
            end_date: End date for analysis
        
        Returns:
            Dictionary with MAPE, MAE, RMSE, Bias, and sample_size
        """
        # Build query
        query = select(ForecastResult).where(
            and_(
                ForecastResult.item_id == item_id,
                ForecastResult.method == method,
                ForecastResult.actual_value.isnot(None),
            )
        )
        
        if start_date:
            query = query.where(ForecastResult.date >= start_date)
        if end_date:
            query = query.where(ForecastResult.date <= end_date)
        
        query = query.order_by(ForecastResult.date)
        
        result = await self.db.execute(query)
        results = result.scalars().all()
        
        if not results:
            return {
                "mape": None,
                "mae": None,
                "rmse": None,
                "bias": None,
                "sample_size": 0,
            }
        
        actuals = [float(r.actual_value) for r in results]
        forecasts = [float(r.point_forecast) for r in results]
        
        return {
            "mape": self.calculate_mape(actuals, forecasts),
            "mae": self.calculate_mae(actuals, forecasts),
            "rmse": self.calculate_rmse(actuals, forecasts),
            "bias": self.calculate_bias(actuals, forecasts),
            "sample_size": len(results),
        }

