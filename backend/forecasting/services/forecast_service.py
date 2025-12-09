"""
ForecastService - Orchestrates forecasting across all layers

Coordinates model execution, method selection, and result storage.
"""
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from models.forecast import ForecastRun, ForecastResult, ForecastStatus, SKUClassification as SKUClassificationModel
from ..modes.factory import ModelFactory
from ..core.models.base import BaseForecastModel
from .data_access import DataAccess
from .data_validator import DataValidator
from .data_audit import DataAuditLogger
from .sku_classifier import SKUClassifier, SKUClassification
from config import settings

logger = logging.getLogger(__name__)


class ForecastService:
    """Orchestrates forecasting execution"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize forecast service.
        
        All data is stored in ts_demand_daily table, filtered by client_id.
        Test users have test data in the table, real users have real data.
        
        Args:
            db: Database session
        """
        self.db = db
        self.model_factory = ModelFactory()
        self._models: Dict[str, BaseForecastModel] = {}
        self.data_access = DataAccess(db)
        self.validator = DataValidator()
        self.sku_classifier = SKUClassifier()
    
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
        training_end_date: Optional[date] = None,
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
            training_end_date: Optional cutoff date for training data (for backtesting)
        
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
        
        results_by_method: Dict[str, Dict[str, pd.DataFrame]] = {}
        
        # Classify SKUs FIRST (ABC-XYZ analysis) - needed for method routing
        sku_classifications: Dict[str, SKUClassification] = {}
        try:
            # Fetch historical data for classification (get revenue data)
            context_df_for_classification = await self.data_access.fetch_historical_data(
                client_id=client_id,
                item_ids=item_ids,
                end_date=None,  # Use all available data for classification
            )
            
            if not context_df_for_classification.empty:
                # Calculate revenue for each SKU (using units_sold as proxy)
                revenue_dict = {}
                for item_id in item_ids:
                    item_data = context_df_for_classification[context_df_for_classification["id"] == item_id]
                    if not item_data.empty:
                        # Get target column
                        target_col = None
                        for col in ["units_sold", "target", "sales_qty"]:
                            if col in item_data.columns:
                                target_col = col
                                break
                        if target_col:
                            revenue_dict[item_id] = float(item_data[target_col].sum())
                
                total_revenue = sum(revenue_dict.values()) if revenue_dict else 0
                
                # Classify each SKU
                for item_id in item_ids:
                    item_data = context_df_for_classification[context_df_for_classification["id"] == item_id]
                    if not item_data.empty and item_id in revenue_dict:
                        try:
                            classification = self.sku_classifier.classify_sku(
                                item_id=item_id,
                                history_df=item_data,
                                revenue=revenue_dict[item_id],
                                total_revenue=total_revenue,
                            )
                            sku_classifications[item_id] = classification
                            
                            # Store classification in database
                            await self._store_classification(client_id, classification)
                            
                            # Optionally use recommended method from classification
                            # (For now, we still use primary_model, but log the recommendation)
                            if classification.recommended_method != primary_model:
                                logger.info(
                                    f"SKU {item_id} ({classification.abc_class}-{classification.xyz_class}) "
                                    f"recommends {classification.recommended_method}, "
                                    f"but using {primary_model} as specified"
                                )
                        except Exception as e:
                            logger.warning(f"Failed to classify SKU {item_id}: {e}")
        
        except Exception as e:
            logger.warning(f"SKU classification failed (continuing with forecast): {e}")
        
        # Determine which methods to run based on classifications
        # Map classification recommendations to actual implemented methods
        method_mapping = {
            "chronos2": "chronos-2",
            "chronos-2": "chronos-2",
            "ma7": "statistical_ma7",
            "statistical_ma7": "statistical_ma7",
            "sba": "sba",  # ✅ SBA implemented
            "croston": "croston",  # ✅ Croston implemented
            "min_max": "min_max",  # ✅ Min/Max implemented
        }
        
        # Collect recommended methods from classifications
        recommended_methods = []
        for item_id in item_ids:
            if item_id in sku_classifications:
                classification = sku_classifications[item_id]
                rec_method = classification.recommended_method
                # Map to actual implemented method
                actual_method = method_mapping.get(rec_method, primary_model)
                recommended_methods.append(actual_method)
                logger.info(
                    f"SKU {item_id} ({classification.abc_class}-{classification.xyz_class}) "
                    f"recommends {rec_method} → using {actual_method}"
                )
        
        # Determine methods to run
        if recommended_methods:
            # Use the most common recommended method, or primary_model if no consensus
            from collections import Counter
            method_counts = Counter(recommended_methods)
            recommended_method = method_counts.most_common(1)[0][0]
            methods_to_run = [recommended_method]
            
            # Always include baseline for comparison
            if include_baseline and "statistical_ma7" not in methods_to_run:
                methods_to_run.append("statistical_ma7")
            
            logger.info(f"Using recommended method routing: {methods_to_run} (from classifications)")
        else:
            # No classifications available, use primary_model
            recommended_method = primary_model
            methods_to_run = [primary_model]
            if include_baseline:
                methods_to_run.append("statistical_ma7")
            logger.info(f"No classifications available, using primary_model: {primary_model}")
        
        try:
            # Run each method
            for method_id in methods_to_run:
                try:
                    model = await self._get_model(method_id)
                    
                    # Fetch historical data (limit to training_end_date if provided)
                    context_df = await self.data_access.fetch_historical_data(
                        client_id=client_id,
                        item_ids=item_ids,
                        end_date=training_end_date,
                    )
                    
                    if context_df.empty:
                        raise ValueError(f"No historical data found for items: {item_ids}")
                    
                    # Generate forecast for each item separately
                    # (Models may return single-item results)
                    item_results = {}
                    
                    # Initialize audit logger only if audit logging is enabled
                    audit_logger = None
                    if settings.enable_audit_logging:
                        audit_logger = DataAuditLogger(self.db, str(forecast_run.forecast_run_id))
                    
                    for item_id in item_ids:
                        # Filter context for this item
                        item_context = context_df[context_df["id"] == item_id].copy()
                        
                        if item_context.empty:
                            logger.warning(f"No data found for item {item_id}")
                            continue
                        
                        # VALIDATE INPUT DATA (IN) - Always validate, even if audit logging is off
                        # Enhanced validator: fills missing dates and NaN values (like Darts)
                        result = self.validator.validate_context_data(
                            item_context, item_id, min_history_days=7,
                            fill_missing_dates=True,  # Fill gaps (like Darts' fill_missing_dates=True)
                            fillna_strategy="zero",   # Fill NaN with 0 (like Darts' fillna_value=0)
                        )
                        
                        # Handle both old and new return signatures
                        if len(result) == 4:
                            is_valid, validation_report, error_msg, cleaned_df = result
                        else:
                            is_valid, validation_report, error_msg = result
                            cleaned_df = item_context  # Fallback to original
                        
                        if not is_valid:
                            logger.error(f"Data validation failed for {item_id}: {error_msg}")
                            if audit_logger:
                                audit_logger.log_data_input(item_id, item_context, method_id, validation_report)
                            continue
                        
                        # Use cleaned data (with missing dates filled, NaN handled)
                        # This ensures models receive clean, complete time series (like Darts)
                        item_context = cleaned_df if cleaned_df is not None else item_context
                        
                        # Log validated input data (if audit logging enabled)
                        if audit_logger:
                            audit_logger.log_data_input(item_id, item_context, method_id, validation_report)
                        
                        # Generate forecast for this item
                        try:
                            predictions_df = await model.predict(
                                context_df=item_context,
                                prediction_length=prediction_length,
                                quantile_levels=quantile_levels,
                            )
                        except Exception as e:
                            logger.error(f"Model prediction failed for {item_id} ({method_id}): {e}", exc_info=True)
                            continue
                        
                        # Check if predictions_df is empty
                        if predictions_df.empty:
                            logger.warning(f"Empty predictions DataFrame for {item_id} ({method_id})")
                            continue
                        
                        # VALIDATE OUTPUT DATA (OUT) - Always validate
                        is_valid_out, validation_report_out, error_msg_out = self.validator.validate_predictions(
                            predictions_df, item_id, prediction_length
                        )
                        
                        if not is_valid_out:
                            logger.error(f"Prediction validation failed for {item_id}: {error_msg_out}")
                            # Continue anyway - store invalid predictions for debugging
                        
                        # Log model output (if audit logging enabled)
                        if audit_logger:
                            audit_logger.log_model_output(item_id, predictions_df, method_id, validation_report_out)
                        
                        # Ensure id column is set
                        if "id" not in predictions_df.columns:
                            predictions_df["id"] = item_id
                        
                        item_results[item_id] = predictions_df
                    
                    # Only add to results_by_method if we have non-empty results
                    if item_results and any(not df.empty for df in item_results.values()):
                        results_by_method[method_id] = item_results
                        
                        # Store audit trail in forecast_run (if audit logging enabled)
                        if audit_logger and audit_logger.audit_trail:
                            if forecast_run.audit_metadata is None:
                                forecast_run.audit_metadata = {}
                            forecast_run.audit_metadata[method_id] = audit_logger.get_audit_trail()
                    else:
                        logger.warning(f"No results generated for method {method_id}")
                    
                except Exception as e:
                    # Log error but continue with other methods
                    logger.error(f"Method {method_id} failed: {e}", exc_info=True)
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
                
                # Update forecast run - only set to completed if we have results
                forecast_run.recommended_method = recommended_method
                forecast_run.status = ForecastStatus.COMPLETED.value
            else:
                # No results generated - mark as failed
                forecast_run.status = ForecastStatus.FAILED.value
                forecast_run.error_message = "No forecast results generated for any method"
                forecast_run.recommended_method = None
        
        except Exception as e:
            forecast_run.status = ForecastStatus.FAILED.value
            forecast_run.error_message = str(e)
            raise
        
        await self.db.commit()
        
        # Attach classifications to forecast_run for API response
        forecast_run._sku_classifications = sku_classifications  # type: ignore
        
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
    
    async def _store_classification(
        self,
        client_id: str,
        classification: SKUClassification
    ) -> None:
        """Store or update SKU classification in database"""
        from sqlalchemy import select
        
        # Check if classification already exists
        result = await self.db.execute(
            select(SKUClassificationModel).where(
                SKUClassificationModel.client_id == client_id,
                SKUClassificationModel.item_id == classification.item_id
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            # Update existing classification
            existing.abc_class = classification.abc_class
            existing.xyz_class = classification.xyz_class
            existing.demand_pattern = classification.demand_pattern
            existing.coefficient_of_variation = classification.coefficient_of_variation
            existing.average_demand_interval = classification.average_demand_interval
            existing.revenue_contribution = classification.revenue_contribution
            existing.forecastability_score = classification.forecastability_score
            existing.recommended_method = classification.recommended_method
            existing.expected_mape_min = classification.expected_mape_range[0]
            existing.expected_mape_max = classification.expected_mape_range[1]
            existing.history_days_used = classification.metadata.get("total_days")
            existing.classification_metadata = {
                "warnings": classification.warnings,
                **classification.metadata
            }
        else:
            # Create new classification
            new_classification = SKUClassificationModel(
                client_id=client_id,
                item_id=classification.item_id,
                abc_class=classification.abc_class,
                xyz_class=classification.xyz_class,
                demand_pattern=classification.demand_pattern,
                coefficient_of_variation=classification.coefficient_of_variation,
                average_demand_interval=classification.average_demand_interval,
                revenue_contribution=classification.revenue_contribution,
                forecastability_score=classification.forecastability_score,
                recommended_method=classification.recommended_method,
                expected_mape_min=classification.expected_mape_range[0],
                expected_mape_max=classification.expected_mape_range[1],
                history_days_used=classification.metadata.get("total_days"),
                classification_metadata={
                    "warnings": classification.warnings,
                    **classification.metadata
                }
            )
            self.db.add(new_classification)
    
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

