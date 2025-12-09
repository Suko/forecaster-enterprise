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
        db=db,
    )
    
    # Get user_id if available (for user calls)
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        # No JWT token - this is a system call
        user_id = "system"
    
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
        )
        
        # Fetch results for response
        results_by_item = await service.get_forecast_results(
            forecast_run_id=forecast_run.forecast_run_id,
            method=forecast_run.recommended_method or forecast_run.primary_model,
        )
        
        # Format response
        from schemas.forecast import ItemForecast, Prediction, PredictionQuantiles, SKUClassificationInfo
        
        # Get classifications if available
        sku_classifications = getattr(forecast_run, '_sku_classifications', {})
        
        item_forecasts = []
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
            
            item_forecasts.append(
                ItemForecast(
                    item_id=item_id,
                    method_used=forecast_run.recommended_method or forecast_run.primary_model,
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
        db=db,
    )
    
    # Get user_id if available
    try:
        current_user = await get_current_user(request_obj, db)
        user_id = current_user.id
    except HTTPException:
        user_id = "system"
    
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
        db=db,
    )
    updated_count = 0
    
    try:
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
            
            # Update all methods for this date
            for forecast_result in results:
                forecast_result.actual_value = actual.actual_value
                updated_count += 1
        
        await db.commit()
        
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
        db=db,
    )
    
    quality_calc = QualityCalculator(db)
    
    # Calculate metrics for both methods
    methods = ["chronos-2", "statistical_ma7"]
    method_qualities = []
    
    for method in methods:
        metrics = await quality_calc.calculate_quality_metrics(
            client_id=client_id,  # Multi-tenant filter
            item_id=item_id,
            method=method,
            start_date=start_date,
            end_date=end_date,
        )
        
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

