"""
Forecast API Endpoints

Endpoints for forecasting and inventory calculations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from models import get_db, User
from auth import get_current_user
from auth.service_auth import get_client_id_from_request_or_token, get_optional_client_id
from schemas.forecast import (
    ForecastRequest,
    ForecastResponse,
    InventoryCalculationRequest,
    InventoryCalculationResponse,
    BackfillActualsRequest,
    BackfillActualsResponse,
    QualityResponse,
    SKUClassificationInfo,
)
from forecasting.services.forecast_service import ForecastService
from forecasting.services.quality_calculator import QualityCalculator
from forecasting.applications.inventory.calculator import InventoryCalculator

router = APIRouter(prefix="/api/v1", tags=["forecast"])


@router.post("/forecast", response_model=ForecastResponse, status_code=status.HTTP_201_CREATED)
async def create_forecast(
    request: ForecastRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate forecast for specified items.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token (request.client_id ignored)
    - Service API key (system calls): X-API-Key header + client_id in request body

    Returns predictions from recommended method (primary if successful, baseline if not).
    Both methods are stored in database for future quality analysis.
    """
    # Get client_id from JWT token OR service API key + request body
    # Supports both user calls (JWT) and system calls (API key)
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=request.client_id,  # Optional: for system calls
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Get user_id if available (for user calls)
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        # No JWT token - this is a system call
        # Use None instead of "system" since user_id is nullable
        user_id = None

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


@router.post("/inventory/calculate", response_model=InventoryCalculationResponse, status_code=status.HTTP_201_CREATED)
async def calculate_inventory(
    request: InventoryCalculationRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Calculate inventory metrics from forecasts.

    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header + client_id in request body

    Generates forecast first, then calculates inventory metrics using industry-standard formulas.
    """
    # Get client_id from JWT token OR service API key + request body
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=request.client_id,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Get user_id if available
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        user_id = None

    # All data is stored in ts_demand_daily table, filtered by client_id
    forecast_service = ForecastService(db)
    inventory_calc = InventoryCalculator()

    try:
        # Generate forecast
        forecast_run = await forecast_service.generate_forecast(
            client_id=client_id,
            user_id=user_id,
            item_ids=request.item_ids,
            prediction_length=request.prediction_length,
            primary_model=request.model or "chronos-2",
            include_baseline=False,  # Only need one method for inventory
        )

        # Fetch forecast results
        results_by_item = await forecast_service.get_forecast_results(
            forecast_run_id=forecast_run.forecast_run_id,
        )

        results = []
        for item_id in request.item_ids:
            if item_id not in request.inventory_params:
                continue

            params = request.inventory_params[item_id]

            # Calculate average daily demand from forecast
            if item_id in results_by_item and results_by_item[item_id]:
                predictions = results_by_item[item_id]
                total_forecast = sum(p["point_forecast"] for p in predictions)
                avg_daily_demand = total_forecast / len(predictions) if predictions else 0.0
            else:
                # Fallback if no predictions
                avg_daily_demand = 0.0
                total_forecast = 0.0

            if avg_daily_demand <= 0:
                # Skip items with no forecast
                continue

            # Calculate inventory metrics
            dir_value = inventory_calc.calculate_days_of_inventory_remaining(
                params.current_stock,
                avg_daily_demand,
            )

            safety_stock = inventory_calc.calculate_safety_stock(
                avg_daily_demand,
                params.lead_time_days,
                params.safety_stock_days,
                params.service_level,
            )

            reorder_point = inventory_calc.calculate_reorder_point(
                avg_daily_demand,
                params.lead_time_days,
                safety_stock,
            )

            recommended_qty = inventory_calc.calculate_recommended_order_quantity(
                total_forecast,
                safety_stock,
                params.current_stock,
                params.moq,
            )

            stockout_risk = inventory_calc.calculate_stockout_risk(
                total_forecast,
                params.current_stock,
            )

            stockout_date = inventory_calc.calculate_stockout_date(
                params.current_stock,
                avg_daily_demand,
            )

            recommendations = inventory_calc.get_recommended_action(
                dir_value,
                stockout_risk,
            )

            from schemas.forecast import InventoryMetrics, Recommendations, InventoryResult

            results.append(
                InventoryResult(
                    item_id=item_id,
                    inventory_metrics=InventoryMetrics(
                        current_stock=params.current_stock,
                        days_of_inventory_remaining=dir_value,
                        safety_stock=safety_stock,
                        reorder_point=reorder_point,
                        recommended_order_quantity=recommended_qty,
                        stockout_risk=stockout_risk,
                        stockout_date=stockout_date,
                    ),
                    recommendations=Recommendations(**recommendations),
                )
            )

        return InventoryCalculationResponse(
            calculation_id=str(forecast_run.forecast_run_id),
            results=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Inventory calculation failed: {str(e)}",
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
    import logging
    logger = logging.getLogger(__name__)

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
