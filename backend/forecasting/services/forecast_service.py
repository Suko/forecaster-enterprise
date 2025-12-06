"""
ForecastService - Orchestrates forecasting across all layers

Coordinates model execution, method selection, and result storage.
"""
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.forecast import ForecastRun, ForecastResult, ForecastStatus
from ..modes.factory import ModelFactory
from ..core.models.base import BaseForecastModel


class ForecastService:
    """Orchestrates forecasting execution"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.model_factory = ModelFactory()
        self._models: Dict[str, BaseForecastModel] = {}
    
    async def _get_model(self, model_id: str) -> BaseForecastModel:
        """Get or initialize model instance"""
        if model_id not in self._models:
            model = self.model_factory.create_model(model_id)
            await model.initialize()
            self._models[model_id] = model
        return self._models[model_id]
    
    async def generate_forecast(
        self,
        client_id: str,
        user_id: str,
        item_ids: List[str],
        prediction_length: int,
        primary_model: str = "chronos-2",
        include_baseline: bool = True,
        quantile_levels: List[float] = None,
    ) -> ForecastRun:
        """
        Generate forecast for specified items.
        
        Args:
            client_id: Client identifier
            user_id: User who triggered the forecast
            item_ids: List of item IDs to forecast
            prediction_length: Days ahead to forecast
            primary_model: Primary model to use (default: "chronos-2")
            include_baseline: Whether to run statistical_ma7 baseline
            quantile_levels: Quantiles to return (default: [0.1, 0.5, 0.9])
        
        Returns:
            ForecastRun with stored results
        """
        if quantile_levels is None:
            quantile_levels = [0.1, 0.5, 0.9]
        
        # Create forecast run record
        forecast_run = ForecastRun(
            client_id=client_id,
            user_id=user_id,
            primary_model=primary_model,
            prediction_length=prediction_length,
            item_ids=item_ids,
            status=ForecastStatus.PENDING.value,
        )
        self.db.add(forecast_run)
        await self.db.flush()  # Get forecast_run_id
        
        methods_to_run = [primary_model]
        if include_baseline:
            methods_to_run.append("statistical_ma7")
        
        results_by_method: Dict[str, Dict[str, pd.DataFrame]] = {}
        recommended_method = primary_model
        
        try:
            # Run each method
            for method_id in methods_to_run:
                try:
                    model = await self._get_model(method_id)
                    
                    # TODO: Fetch historical data from ts_demand_daily
                    # For now, this is a placeholder - will need data access layer
                    context_df = await self._fetch_historical_data(
                        client_id, item_ids
                    )
                    
                    if context_df.empty:
                        raise ValueError(f"No historical data found for items: {item_ids}")
                    
                    # Generate forecast
                    predictions_df = await model.predict(
                        context_df=context_df,
                        prediction_length=prediction_length,
                        quantile_levels=quantile_levels,
                    )
                    
                    results_by_method[method_id] = {
                        item_id: predictions_df[predictions_df["id"] == item_id]
                        for item_id in item_ids
                    }
                    
                except Exception as e:
                    # Log error but continue with other methods
                    if method_id == primary_model:
                        # If primary fails, use baseline
                        recommended_method = "statistical_ma7"
                    # Store error in forecast_run
                    forecast_run.error_message = f"{method_id} failed: {str(e)}"
            
            # Store results in database
            await self._store_results(
                forecast_run, results_by_method, item_ids, prediction_length
            )
            
            # Update forecast run
            forecast_run.recommended_method = recommended_method
            forecast_run.status = ForecastStatus.COMPLETED.value
            
        except Exception as e:
            forecast_run.status = ForecastStatus.FAILED.value
            forecast_run.error_message = str(e)
            raise
        
        await self.db.commit()
        return forecast_run
    
    async def _fetch_historical_data(
        self,
        client_id: str,
        item_ids: List[str],
    ) -> pd.DataFrame:
        """
        Fetch historical sales data from database.
        
        TODO: Implement actual database query to ts_demand_daily table
        For MVP, this is a placeholder that returns empty DataFrame.
        """
        # Placeholder - will be implemented with actual data access
        # Expected columns: id, timestamp, target, [covariates]
        return pd.DataFrame()
    
    async def _store_results(
        self,
        forecast_run: ForecastRun,
        results_by_method: Dict[str, Dict[str, pd.DataFrame]],
        item_ids: List[str],
        prediction_length: int,
    ) -> None:
        """Store forecast results in database"""
        for method_id, item_results in results_by_method.items():
            for item_id in item_ids:
                if item_id not in item_results:
                    continue
                
                predictions_df = item_results[item_id]
                
                for idx, row in predictions_df.iterrows():
                    result = ForecastResult(
                        forecast_run_id=forecast_run.forecast_run_id,
                        client_id=forecast_run.client_id,
                        item_id=item_id,
                        method=method_id,
                        date=pd.to_datetime(row["timestamp"]).date(),
                        horizon_day=idx + 1,
                        point_forecast=float(row["point_forecast"]),
                        p10=float(row.get("p10", 0)) if "p10" in row else None,
                        p50=float(row.get("p50", 0)) if "p50" in row else None,
                        p90=float(row.get("p90", 0)) if "p90" in row else None,
                    )
                    self.db.add(result)
    
    async def get_forecast_run(self, forecast_run_id: str) -> Optional[ForecastRun]:
        """Get forecast run by ID"""
        result = await self.db.execute(
            select(ForecastRun).where(ForecastRun.forecast_run_id == forecast_run_id)
        )
        return result.scalar_one_or_none()

