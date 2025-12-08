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
from .data_access import DataAccess


class ForecastService:
    """Orchestrates forecasting execution"""
    
    def __init__(self, db: AsyncSession, use_test_data: bool = False):
        """
        Initialize forecast service.
        
        Args:
            db: Database session
            use_test_data: If True, use CSV test data instead of database
        """
        self.db = db
        self.model_factory = ModelFactory()
        self._models: Dict[str, BaseForecastModel] = {}
        self.data_access = DataAccess(db, use_test_data=use_test_data)
    
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
                    
                    # Fetch historical data
                    context_df = await self.data_access.fetch_historical_data(
                        client_id=client_id,
                        item_ids=item_ids,
                    )
                    
                    if context_df.empty:
                        raise ValueError(f"No historical data found for items: {item_ids}")
                    
                    # Generate forecast for each item separately
                    # (Models may return single-item results)
                    item_results = {}
                    for item_id in item_ids:
                        # Filter context for this item
                        item_context = context_df[context_df["id"] == item_id].copy()
                        
                        if item_context.empty:
                            continue
                        
                        # Generate forecast for this item
                        predictions_df = await model.predict(
                            context_df=item_context,
                            prediction_length=prediction_length,
                            quantile_levels=quantile_levels,
                        )
                        
                        # Ensure id column is set
                        if "id" not in predictions_df.columns:
                            predictions_df["id"] = item_id
                        
                        item_results[item_id] = predictions_df
                    
                    results_by_method[method_id] = item_results
                    
                except Exception as e:
                    # Log error but continue with other methods
                    if method_id == primary_model:
                        # If primary fails, use baseline
                        recommended_method = "statistical_ma7"
                    # Store error in forecast_run
                    forecast_run.error_message = f"{method_id} failed: {str(e)}"
            
            # Store results in database (only if we have results)
            if results_by_method:
                await self._store_results(
                    forecast_run, results_by_method, item_ids, prediction_length
                )
                # Flush to ensure results are in the session before commit
                await self.db.flush()
            else:
                # No results generated - mark as failed
                forecast_run.status = ForecastStatus.FAILED.value
                forecast_run.error_message = "No forecast results generated for any method"
            
            # Update forecast run
            forecast_run.recommended_method = recommended_method
            forecast_run.status = ForecastStatus.COMPLETED.value
        
        except Exception as e:
            forecast_run.status = ForecastStatus.FAILED.value
            forecast_run.error_message = str(e)
            raise
        
        await self.db.commit()
        return forecast_run
    
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
                
                # Skip if DataFrame is empty
                if predictions_df.empty:
                    continue
                
                # Reset index to ensure sequential numbering
                predictions_df = predictions_df.reset_index(drop=True)
                
                # Iterate and store each prediction
                for horizon_day, (idx, row) in enumerate(predictions_df.iterrows(), start=1):
                    # Ensure timestamp column exists
                    if "timestamp" not in row:
                        continue
                    
                    result = ForecastResult(
                        forecast_run_id=forecast_run.forecast_run_id,
                        client_id=forecast_run.client_id,
                        item_id=item_id,
                        method=method_id,
                        date=pd.to_datetime(row["timestamp"]).date(),
                        horizon_day=horizon_day,
                        point_forecast=float(row["point_forecast"]),
                        p10=float(row.get("p10")) if "p10" in row and pd.notna(row.get("p10")) else None,
                        p50=float(row.get("p50")) if "p50" in row and pd.notna(row.get("p50")) else None,
                        p90=float(row.get("p90")) if "p90" in row and pd.notna(row.get("p90")) else None,
                    )
                    self.db.add(result)
    
    async def get_forecast_run(self, forecast_run_id: str) -> Optional[ForecastRun]:
        """Get forecast run by ID"""
        # Convert string to UUID if needed (GUID type returns UUID objects)
        import uuid
        if isinstance(forecast_run_id, str):
            forecast_run_id = uuid.UUID(forecast_run_id)
        
        result = await self.db.execute(
            select(ForecastRun).where(ForecastRun.forecast_run_id == forecast_run_id)
        )
        return result.scalar_one_or_none()
    
    async def get_forecast_results(
        self,
        forecast_run_id,
        method: Optional[str] = None,
    ) -> Dict[str, List[Dict]]:
        """
        Fetch forecast results from database and format for API response.
        
        Args:
            forecast_run_id: Forecast run ID (string or UUID)
            method: Optional method filter (if None, uses recommended_method from run)
        
        Returns:
            Dictionary mapping item_id to list of predictions
        """
        # Convert string to UUID if needed (GUID type returns UUID objects)
        import uuid
        if isinstance(forecast_run_id, str):
            forecast_run_id_uuid = uuid.UUID(forecast_run_id)
        elif isinstance(forecast_run_id, uuid.UUID):
            forecast_run_id_uuid = forecast_run_id
        else:
            forecast_run_id_uuid = forecast_run_id
        
        # Get forecast run to determine method (pass original to preserve type)
        forecast_run = await self.get_forecast_run(forecast_run_id)
        if not forecast_run:
            return {}
        
        # Use recommended method if not specified
        if method is None:
            method = forecast_run.recommended_method or forecast_run.primary_model
        
        # Ensure we have the latest data (refresh from DB)
        await self.db.refresh(forecast_run)
        
        # Query results - try without method filter first to see what exists
        query_all = select(ForecastResult).where(
            ForecastResult.forecast_run_id == forecast_run_id_uuid,
        ).order_by(ForecastResult.item_id, ForecastResult.date)
        
        result_all = await self.db.execute(query_all)
        all_results = result_all.scalars().all()
        
        # If no results at all, return empty
        if not all_results:
            return {}
        
        # Filter by method if specified
        if method:
            results = [r for r in all_results if r.method == method]
        else:
            results = all_results
        
        # Group by item_id
        results_by_item: Dict[str, List[Dict]] = {}
        
        for row in results:
            item_id = row.item_id
            if item_id not in results_by_item:
                results_by_item[item_id] = []
            
            # Format prediction
            prediction = {
                "date": row.date,
                "point_forecast": float(row.point_forecast),
            }
            
            # Add quantiles if available
            quantiles = {}
            if row.p10 is not None:
                quantiles["p10"] = float(row.p10)
            if row.p50 is not None:
                quantiles["p50"] = float(row.p50)
            if row.p90 is not None:
                quantiles["p90"] = float(row.p90)
            
            if quantiles:
                prediction["quantiles"] = quantiles
            
            results_by_item[item_id].append(prediction)
        
        return results_by_item

