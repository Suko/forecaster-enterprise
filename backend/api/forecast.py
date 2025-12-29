"""
Forecast API Endpoints

Endpoints for forecasting and inventory calculations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
import logging

from models import get_db, User
from auth import get_current_user
from auth.service_auth import get_client_id_from_request_or_token, get_optional_client_id
from schemas.forecast import (
    ForecastRequest,
    ForecastResponse,
    InventoryCalculationRequest,
    InventoryCalculationTaskResponse,
    InventoryCalculationTaskStatus,
    BackfillActualsRequest,
    BackfillActualsResponse,
    QualityResponse,
    SKUClassificationInfo,
    ForecastRefreshRequest,
    ForecastRefreshResponse,
)
from forecasting.services.forecast_service import ForecastService
from forecasting.services.quality_calculator import QualityCalculator
from forecasting.applications.inventory.calculator import InventoryCalculator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    request: ForecastRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate forecast for specified items.

    **IMPORTANT**: 
    - Regular user calls (without skip_persistence): Rejected - forecasts run automatically in background
    - Testbed/experiments (with skip_persistence=true): Allowed - for testing/comparison purposes only
    - System/automated calls: Allowed - use service API key
    
    Authentication:
    - Service API key (system calls): X-API-Key header + client_id in request body
    - User calls with skip_persistence=true (testbed): Allowed for experiments
    - User calls without skip_persistence: Rejected - forecasts run automatically in background

    Returns predictions from recommended method (primary if successful, baseline if not).
    Both methods are stored in database for future quality analysis (unless skip_persistence=true).
    """
    # Check if this is a user call (has JWT token)
    is_user_call = False
    try:
        current_user = await get_current_user(request_obj, db)
        is_user_call = True
        user_id = current_user.id
    except HTTPException:
        # No JWT token - this is a system call
        user_id = None
    
    # Reject synchronous forecasts for user calls UNLESS it's testbed mode (skip_persistence=true)
    # Testbed is a special experiments page where users explicitly want to generate forecasts
    if is_user_call and not request.skip_persistence:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Synchronous forecast generation is not available for user calls. "
                "Forecasts are automatically generated in the background when forecast data is older than 7 days. "
                "Use service API key for system/automated forecast generation, or use the Testbed page for experiments."
            ),
        )
    
    # Get client_id from service API key + request body (system calls only)
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=request.client_id,  # Required for system calls
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # All data is stored in ts_demand_daily table, filtered by client_id
    # Test users have test data in the table, real users have real data
    service = ForecastService(db)

    try:
        forecast_run = await service.generate_forecast(
            client_id=client_id,
            user_id=user_id,
            item_ids=request.item_ids,
            prediction_length=request.prediction_length,
            primary_model=request.model or "chronos-2",
            include_baseline=request.include_baseline,
            run_all_methods=request.run_all_methods,
            skip_persistence=request.skip_persistence,
            training_end_date=request.training_end_date,
        )

        # Fetch results for response
        # If skip_persistence=True and run_all_methods=True, return all methods
        # Otherwise, return primary method only
        from schemas.forecast import ItemForecast, Prediction, PredictionQuantiles, SKUClassificationInfo
        import pandas as pd

        # Get classifications if available
        sku_classifications = getattr(forecast_run, '_sku_classifications', {})

        item_forecasts = []
        
        if request.skip_persistence and hasattr(forecast_run, '_results_by_method'):
            # Test Bed mode: Convert in-memory results to API format
            results_by_method = forecast_run._results_by_method
            
            # If run_all_methods=True, return forecasts for all methods
            # Otherwise, return only primary method
            methods_to_return = list(results_by_method.keys()) if request.run_all_methods else [forecast_run.primary_model or forecast_run.recommended_method]
            
            for method_id in methods_to_return:
                if method_id not in results_by_method:
                    continue
                    
                item_results = results_by_method[method_id]
                
                for item_id in request.item_ids:
                    if item_id not in item_results:
                        continue
                    
                    predictions_df = item_results[item_id]
                    if predictions_df.empty:
                        continue
                    
                    # Convert DataFrame to predictions list
                    predictions = []
                    for _, row in predictions_df.iterrows():
                        quantiles = None
                        if "p10" in row and pd.notna(row.get("p10")):
                            quantiles = PredictionQuantiles(
                                p10=float(row.get("p10")) if pd.notna(row.get("p10")) else None,
                                p50=float(row.get("p50")) if pd.notna(row.get("p50")) else None,
                                p90=float(row.get("p90")) if pd.notna(row.get("p90")) else None,
                            )
                        
                        date_value = pd.to_datetime(row["timestamp"]).date() if "timestamp" in row else None
                        if not date_value:
                            continue
                            
                        predictions.append(
                            Prediction(
                                date=date_value,
                                point_forecast=float(row["point_forecast"]),
                                quantiles=quantiles,
                            )
                        )
                    
                    if not predictions:
                        continue
                    
                    # Get classification for this item
                    classification_info = None
                    if item_id in sku_classifications:
                        classification = sku_classifications[item_id]
                        classification_info = SKUClassificationInfo(
                            abc_class=classification.abc_class,
                            xyz_class=classification.xyz_class,
                            demand_pattern=classification.demand_pattern,
                            forecastability_score=classification.forecastability_score,
                            recommended_method=classification.recommended_method,
                            expected_mape_range=classification.expected_mape_range,
                            warnings=classification.warnings,
                        )
                    
                    item_forecasts.append(
                        ItemForecast(
                            item_id=item_id,
                            method_used=method_id,
                            predictions=predictions,
                            classification=classification_info,
                        )
                    )
        else:
            # Normal mode: Fetch from database
            method_to_fetch = forecast_run.primary_model or forecast_run.recommended_method
            results_by_item = await service.get_forecast_results(
                forecast_run_id=forecast_run.forecast_run_id,
                method=method_to_fetch,
            )
            
            # If no results for primary_model, try recommended_method as fallback
            if not results_by_item and forecast_run.recommended_method and forecast_run.recommended_method != forecast_run.primary_model:
                method_to_fetch = forecast_run.recommended_method
                results_by_item = await service.get_forecast_results(
                    forecast_run_id=forecast_run.forecast_run_id,
                    method=method_to_fetch,
                )

            for item_id in request.item_ids:
                if item_id not in results_by_item:
                    continue

                predictions = []
                for pred_data in results_by_item[item_id]:
                    quantiles = None
                    if "quantiles" in pred_data:
                        quantiles = PredictionQuantiles(**pred_data["quantiles"])

                    predictions.append(
                        Prediction(
                            date=pred_data["date"],
                            point_forecast=pred_data["point_forecast"],
                            quantiles=quantiles,
                        )
                    )

                # Get classification for this item
                classification_info = None
                if item_id in sku_classifications:
                    classification = sku_classifications[item_id]
                    classification_info = SKUClassificationInfo(
                        abc_class=classification.abc_class,
                        xyz_class=classification.xyz_class,
                        demand_pattern=classification.demand_pattern,
                        forecastability_score=classification.forecastability_score,
                        recommended_method=classification.recommended_method,
                        expected_mape_range=classification.expected_mape_range,
                        warnings=classification.warnings,
                    )

                # Use the method that actually has results
                actual_method_used = method_to_fetch or forecast_run.primary_model or forecast_run.recommended_method
                
                item_forecasts.append(
                    ItemForecast(
                        item_id=item_id,
                        method_used=actual_method_used,
                        predictions=predictions,
                        classification=classification_info,
                    )
                )

        return ForecastResponse(
            forecast_id=str(forecast_run.forecast_run_id),
            primary_model=forecast_run.primary_model,
            forecasts=item_forecasts,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Forecast generation failed: {str(e)}",
        )


@router.post("/inventory/calculate", response_model=InventoryCalculationTaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def calculate_inventory(
    request: InventoryCalculationRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate inventory metrics from forecasts asynchronously.

    **IMPORTANT**: This endpoint now runs calculations in the background and returns immediately.
    Use the returned task_id to poll for completion status.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header + client_id in request body

    Returns a task ID immediately. Poll /inventory/calculate/{task_id} for results.
    """
    # Get client_id from JWT token OR service API key + request body
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=request.client_id,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Get user_id if authenticated
    user_id = None
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        pass  # System call without user context

    # Start background calculation task
    from services.inventory_service import InventoryService
    from uuid import UUID

    inventory_service = InventoryService(db)
    task_id = await inventory_service.start_inventory_calculation_task(
        client_id=UUID(client_id),
        user_id=user_id,
        item_ids=request.item_ids,
        prediction_length=request.prediction_length,
        inventory_params={k: v.dict() for k, v in request.inventory_params.items()},  # Convert to dict
        model=request.model or "chronos-2",
    )

    # Estimate completion time based on number of items
    estimated_seconds = max(10, len(request.item_ids) * 2)  # Rough estimate

    from schemas.forecast import InventoryCalculationTaskResponse

    return InventoryCalculationTaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Inventory calculation started for {len(request.item_ids)} items",
        estimated_completion_seconds=estimated_seconds,
    )


@router.get("/inventory/calculate/{task_id}", response_model=InventoryCalculationTaskStatus)
async def get_inventory_calculation_status(
    task_id: str,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get the status of an inventory calculation task.

    Poll this endpoint to check if the calculation is complete.
    When status is 'completed', results will be included.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header
    """
    # Get client_id to ensure user can only access their own tasks
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,  # Not in request body
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    from services.inventory_service import InventoryService
    inventory_service = InventoryService(db)
    task_data = inventory_service.get_inventory_calculation_task_status(task_id)

    if not task_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found or expired",
        )

    # Check if task belongs to this client (basic security)
    if task_data.get("client_id") != client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this task",
        )

    from schemas.forecast import InventoryCalculationTaskStatus
    from datetime import datetime

    return InventoryCalculationTaskStatus(
        task_id=task_data["task_id"],
        status=task_data["status"],
        progress_percentage=task_data.get("progress_percentage"),
        message=task_data.get("message", ""),
        created_at=task_data["created_at"],
        completed_at=task_data.get("completed_at"),
        results=task_data.get("results"),
        error_message=task_data.get("error_message"),
    )


@router.post("/forecasts/actuals", response_model=BackfillActualsResponse)
async def backfill_actuals(
    request: BackfillActualsRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Backfill actual values for quality testing.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header (client_id from JWT/request)

    Updates forecast_results.actual_value for specified item and dates.
    Enables calculation of accuracy metrics (MAPE, MAE, RMSE).
    """
    from sqlalchemy import select, and_, update
    from models.forecast import ForecastResult

    # Get client_id from JWT token OR service API key
    # Note: client_id not in BackfillActualsRequest, so we get it from auth
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,  # Not in request body for this endpoint
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )
    updated_count = 0

    try:
        logger.info(f"Backfilling actuals for item_id={request.item_id}, client_id={client_id}, count={len(request.actuals)}")
        
        for actual in request.actuals:
            # Find matching forecast results
            query = select(ForecastResult).where(
                and_(
                    ForecastResult.client_id == client_id,
                    ForecastResult.item_id == request.item_id,
                    ForecastResult.date == actual.date,
                    ForecastResult.actual_value.is_(None),  # Only update if not already set
                )
            )

            result = await db.execute(query)
            results = result.scalars().all()
            
            if not results:
                # Try to find results without the actual_value filter to see if they exist
                query_all = select(ForecastResult).where(
                    and_(
                        ForecastResult.client_id == client_id,
                        ForecastResult.item_id == request.item_id,
                        ForecastResult.date == actual.date,
                    )
                )
                result_all = await db.execute(query_all)
                all_results = result_all.scalars().all()
                if all_results:
                    logger.warning(f"Found {len(all_results)} results for date {actual.date} but actual_value already set")
                else:
                    logger.warning(f"No forecast results found for item_id={request.item_id}, date={actual.date}")

            # Update all methods for this date
            for forecast_result in results:
                forecast_result.actual_value = actual.actual_value
                updated_count += 1
                logger.debug(f"Updated forecast_result for method={forecast_result.method}, date={actual.date}")

        await db.commit()
        logger.info(f"Backfilled {updated_count} actual values")

        return BackfillActualsResponse(
            updated_count=updated_count,
            message=f"Updated {updated_count} forecast results with actual values",
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backfill actuals: {str(e)}",
        )


@router.get("/forecasts/quality/{item_id}", response_model=QualityResponse)
async def get_quality_metrics(
    item_id: str,
    request_obj: Request,
    start_date: Optional[date] = Query(None, description="Start date for analysis"),
    end_date: Optional[date] = Query(None, description="End date for analysis"),
    forecast_run_id: Optional[str] = Query(None, description="Filter by specific forecast run ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get quality metrics (MAPE, MAE, RMSE, Bias) for an item.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header (client_id from JWT/request)

    Compares accuracy of different forecasting methods.
    Requires actual values to be backfilled first.
    """
    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,  # Not in query params for this endpoint
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    quality_calc = QualityCalculator(db)
    import logging
    logger = logging.getLogger(__name__)

    # Get all unique methods that have forecast results for this item (with actuals)
    from sqlalchemy import select, distinct, and_, func
    from models.forecast import ForecastResult
    import uuid
    
    # Build base filter conditions
    # Note: We don't filter by forecast_run_id for finding methods, because we want to show
    # all methods that have results with actuals, even if they're from different runs.
    # The forecast_run_id filter is only applied when calculating metrics per method.
    base_conditions = [
        ForecastResult.client_id == client_id,
        ForecastResult.item_id == item_id,
        ForecastResult.actual_value.isnot(None),
    ]
    
    # If forecast_run_id is provided, we'll use it when calculating metrics, but not for finding methods
    # This allows us to show all available methods while still filtering metrics by run if needed
    forecast_run_id_uuid = None
    if forecast_run_id:
        try:
            forecast_run_id_uuid = uuid.UUID(forecast_run_id)
            logger.info(f"Will filter quality metrics by forecast_run_id: {forecast_run_id}")
        except ValueError:
            logger.warning(f"Invalid forecast_run_id format: {forecast_run_id}, ignoring filter")
    
    # First, check if we have any results with actuals
    count_query = select(func.count(ForecastResult.result_id)).where(
        and_(*base_conditions)
    )
    if start_date:
        count_query = count_query.where(ForecastResult.date >= start_date)
    if end_date:
        count_query = count_query.where(ForecastResult.date <= end_date)
    
    count_result = await db.execute(count_query)
    actuals_count = count_result.scalar() or 0
    logger.info(f"Quality metrics for item_id={item_id}: Found {actuals_count} results with actuals")
    
    methods_query = select(distinct(ForecastResult.method)).where(
        and_(*base_conditions)
    )
    if start_date:
        methods_query = methods_query.where(ForecastResult.date >= start_date)
    if end_date:
        methods_query = methods_query.where(ForecastResult.date <= end_date)
    
    methods_result = await db.execute(methods_query)
    methods = [row[0] for row in methods_result.all()]
    logger.info(f"Quality metrics: Methods with actuals: {methods}")
    
    # If no methods found with actuals, try to get all methods that have forecasts (even without actuals)
    # Still don't filter by forecast_run_id here - we want to see all available methods
    if not methods:
        base_conditions_no_actuals = [
            ForecastResult.client_id == client_id,
            ForecastResult.item_id == item_id,
        ]
        
        methods_query_all = select(distinct(ForecastResult.method)).where(
            and_(*base_conditions_no_actuals)
        )
        if start_date:
            methods_query_all = methods_query_all.where(ForecastResult.date >= start_date)
        if end_date:
            methods_query_all = methods_query_all.where(ForecastResult.date <= end_date)
        
        methods_result_all = await db.execute(methods_query_all)
        methods = [row[0] for row in methods_result_all.all()]
        logger.info(f"Quality metrics: All methods (without actuals filter): {methods}")
    
    # Fallback to default methods if still no methods found
    if not methods:
        methods = ["chronos-2", "statistical_ma7"]
        logger.warning(f"Quality metrics: No methods found, using defaults: {methods}")
    
    method_qualities = []

    for method in methods:
        # If forecast_run_id is provided, use it to filter metrics to only that run
        # Otherwise, show metrics across all runs (for comparison)
        metrics = await quality_calc.calculate_quality_metrics(
            client_id=client_id,  # Multi-tenant filter
            item_id=item_id,
            method=method,
            start_date=start_date,
            end_date=end_date,
            forecast_run_id=forecast_run_id,  # Filter by run if provided, otherwise show all
        )
        
        logger.info(f"Quality metrics for method={method}: sample_size={metrics['sample_size']}, mape={metrics['mape']}, mae={metrics['mae']}, rmse={metrics['rmse']}")

        from schemas.forecast import MethodQuality

        method_qualities.append(
            MethodQuality(
                method=method,
                predictions_count=metrics["sample_size"],
                actuals_count=metrics["sample_size"],
                mape=metrics["mape"],
                mae=metrics["mae"],
                rmse=metrics["rmse"],
                bias=metrics["bias"],
            )
        )

    return QualityResponse(
        item_id=item_id,
        period={"start": start_date, "end": end_date},
        methods=method_qualities,
    )


@router.get("/skus/{item_id}/classification", response_model=SKUClassificationInfo)
async def get_sku_classification(
    item_id: str,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get SKU classification (ABC-XYZ) for a specific item.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header

    Returns the latest classification for the item.
    """
    from sqlalchemy import select

    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Get classification from database
    from models.forecast import SKUClassification as SKUClassificationModel

    result = await db.execute(
        select(SKUClassificationModel).where(
            SKUClassificationModel.client_id == client_id,
            SKUClassificationModel.item_id == item_id
        ).order_by(SKUClassificationModel.classification_date.desc())
    )
    classification = result.scalar_one_or_none()

    if not classification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Classification not found for item {item_id}. Generate a forecast first to classify the SKU.",
        )

    # Extract warnings from metadata
    warnings = []
    if classification.classification_metadata and isinstance(classification.classification_metadata, dict):
        warnings = classification.classification_metadata.get("warnings", [])

    return SKUClassificationInfo(
        abc_class=classification.abc_class,
        xyz_class=classification.xyz_class,
        demand_pattern=classification.demand_pattern,
        forecastability_score=float(classification.forecastability_score),
        recommended_method=classification.recommended_method,
        expected_mape_range=(
            float(classification.expected_mape_min) if classification.expected_mape_min else 0.0,
            float(classification.expected_mape_max) if classification.expected_mape_max else 100.0
        ),
        warnings=warnings,
    )


@router.get("/forecast/models")
async def list_available_models():
    """
    List all available forecasting models.

    Returns list of model IDs with metadata.
    No authentication required - public endpoint.
    """
    from forecasting.modes.factory import ModelFactory

    models = ModelFactory.list_models()

    # Model metadata
    model_info = {
        "chronos-2": {
            "name": "Chronos-2",
            "description": "Amazon's foundation model for time series forecasting",
            "is_ml": True,
        },
        "statistical_ma7": {
            "name": "Moving Average (7-day)",
            "description": "Simple 7-day moving average baseline",
            "is_ml": False,
        },
        "sba": {
            "name": "SBA (Syntetos-Boylan)",
            "description": "Intermittent demand forecasting method",
            "is_ml": False,
        },
        "croston": {
            "name": "Croston's Method",
            "description": "Classic intermittent demand method",
            "is_ml": False,
        },
        "min_max": {
            "name": "Min-Max",
            "description": "Simple min-max range forecasting",
            "is_ml": False,
        },
    }

    return [
        {
            "id": model_id,
            "name": model_info.get(model_id, {}).get("name", model_id),
            "description": model_info.get(model_id, {}).get("description", ""),
            "is_ml": model_info.get(model_id, {}).get("is_ml", False),
        }
        for model_id in models
    ]


@router.get("/forecast/date-range")
async def get_date_range(
    request_obj: Request,
    item_id: Optional[str] = Query(None, description="Optional item ID to get date range for"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the date range of available historical data.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header

    Returns min/max dates and total days of data.
    """
    from sqlalchemy import text

    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Build query using raw SQL (ts_demand_daily has no SQLAlchemy model)
    if item_id:
        query = text("""
            SELECT
                MIN(date_local) as min_date,
                MAX(date_local) as max_date,
                COUNT(DISTINCT date_local) as total_days
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
        """)
        params = {"client_id": client_id, "item_id": item_id}
    else:
        query = text("""
            SELECT
                MIN(date_local) as min_date,
                MAX(date_local) as max_date,
                COUNT(DISTINCT date_local) as total_days
            FROM ts_demand_daily
            WHERE client_id = :client_id
        """)
        params = {"client_id": client_id}

    result = await db.execute(query, params)
    row = result.one()

    return {
        "min_date": row.min_date.isoformat() if row.min_date else None,
        "max_date": row.max_date.isoformat() if row.max_date else None,
        "total_days": row.total_days or 0,
    }


@router.get("/forecast/historical")
async def get_historical_data(
    request_obj: Request,
    item_id: str = Query(..., description="Item ID to get historical data for"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get historical sales data for an item.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header

    Returns daily units sold.
    """
    from sqlalchemy import text

    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Build query using raw SQL (ts_demand_daily has no SQLAlchemy model)
    params = {"client_id": client_id, "item_id": item_id}
    filters = []

    if start_date:
        filters.append("date_local >= :start_date")
        params["start_date"] = start_date
    if end_date:
        filters.append("date_local <= :end_date")
        params["end_date"] = end_date

    where_clause = " AND ".join(filters) if filters else ""
    if where_clause:
        where_clause = " AND " + where_clause

    query = text(f"""
        SELECT
            date_local,
            units_sold
        FROM ts_demand_daily
        WHERE client_id = :client_id
          AND item_id = :item_id
          {where_clause}
        ORDER BY date_local
    """)

    result = await db.execute(query, params)
    rows = result.all()

    return [
        {
            "date": row.date_local.isoformat(),
            "units_sold": float(row.units_sold),
        }
        for row in rows
    ]


@router.get("/forecast/{forecast_id}/results")
async def get_forecast_results_by_method(
    forecast_id: str,
    method: str,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get forecast results for a specific method from a forecast run.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header

    Args:
        forecast_id: Forecast run ID
        method: Forecast method to retrieve (e.g., "chronos-2", "statistical_ma7")

    Returns forecast results for the specified method.
    """
    from forecasting.services.forecast_service import ForecastService
    from schemas.forecast import ItemForecast, Prediction

    # Get client_id
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    service = ForecastService(db)

    # Fetch results for the specified method
    results_by_item = await service.get_forecast_results(
        forecast_run_id=forecast_id,
        method=method,
    )

    # Format response
    item_forecasts = []
    for item_id, predictions in results_by_item.items():
        item_forecasts.append(
            ItemForecast(
                item_id=item_id,
                method_used=method,
                predictions=[
                    Prediction(
                        date=p["date"],
                        point_forecast=p["point_forecast"],
                        quantiles=p.get("quantiles"),
                    )
                    for p in predictions
                ],
            )
        )

    return {
        "forecast_id": forecast_id,
        "method": method,
        "forecasts": item_forecasts,
    }


@router.get("/products/categories")
async def get_product_categories(
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of distinct product categories.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header

    Returns list of category names.
    """
    from sqlalchemy import select, func
    from models.product import Product

    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    query = select(func.distinct(Product.category)).where(
        Product.client_id == client_id,
        Product.category.isnot(None),
    ).order_by(Product.category)

    result = await db.execute(query)
    categories = [row[0] for row in result.all() if row[0]]

    return {"categories": categories}


@router.post("/refresh", response_model=ForecastRefreshResponse, status_code=status.HTTP_202_ACCEPTED)
async def refresh_forecasts(
    request: ForecastRefreshRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger forecast refresh for specified items.
    
    **Use Cases:**
    - User clicks "Refresh Forecasts" button in UI
    - Manual refresh when user wants updated forecasts immediately
    
    **Behavior:**
    - Runs in background (non-blocking) - returns immediately
    - If item_ids not provided, refreshes all active products for the client
    - Uses existing forecast service with proper client isolation
    
    **Authentication:** Requires JWT token (user calls only)
    
    **Note:** Automatic refresh should be handled by scheduled system jobs (every 7 days).
    This endpoint is for manual user-initiated refreshes only.
    """
    # Get client_id from JWT token (user calls only)
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,  # Not in request body for user calls
        x_api_key=None,  # User calls only - no service API key
        db=db,
    )
    
    # Get user_id
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for manual forecast refresh",
        )
    
    # If no item_ids provided, get all active products for the client
    if not request.item_ids:
        from sqlalchemy import select
        from models.product import Product
        
        products_result = await db.execute(
            select(Product.item_id).where(Product.client_id == client_id)
        )
        item_ids = [row[0] for row in products_result.all()]
        
        if not item_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No products found for this client",
            )
    else:
        item_ids = request.item_ids
    
    # Trigger background refresh (non-blocking)
    from services.inventory_service import InventoryService
    inventory_service = InventoryService(db)
    inventory_service._trigger_forecast_refresh(
        client_id=client_id,
        item_ids=item_ids,
        user_id=user_id
    )
    
    return ForecastRefreshResponse(
        message=f"Forecast refresh started in background for {len(item_ids)} item(s)",
        forecast_id=None,  # Not available immediately (background task)
        item_count=len(item_ids),
        status="started"
    )
