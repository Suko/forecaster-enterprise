"""
Forecast API Schemas

Pydantic models for request/response validation.
"""
from typing import List, Optional, Dict, Tuple
from datetime import date as date_type
from pydantic import BaseModel, Field
from uuid import UUID


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ForecastRequest(BaseModel):
    """Request schema for pure forecast endpoint"""

    item_ids: List[str] = Field(..., min_length=1, description="List of item IDs to forecast")
    prediction_length: int = Field(30, ge=1, le=365, description="Forecast horizon in days")
    model: Optional[str] = Field("chronos-2", description="Primary model to use")
    include_baseline: bool = Field(True, description="Include statistical_ma7 baseline")
    client_id: Optional[str] = Field(None, description="Client ID (required for service API key calls, optional for JWT)")

    class Config:
        json_schema_extra = {
            "example": {
                "item_ids": ["SKU001", "SKU002"],
                "prediction_length": 30,
                "model": "chronos-2",
                "include_baseline": True,
            }
        }


class InventoryParams(BaseModel):
    """Inventory parameters per item"""

    current_stock: float = Field(..., gt=0, description="Current inventory level")
    lead_time_days: int = Field(..., ge=0, description="Lead time in days")
    safety_stock_days: Optional[int] = Field(7, ge=0, description="Safety stock in days")
    moq: Optional[int] = Field(None, ge=0, description="Minimum Order Quantity")
    service_level: float = Field(0.95, ge=0.0, le=1.0, description="Service level (e.g., 0.95 for 95%)")


class InventoryCalculationRequest(BaseModel):
    """Request schema for inventory calculation endpoint"""

    item_ids: List[str] = Field(..., min_length=1, description="List of item IDs")
    prediction_length: int = Field(30, ge=1, le=365, description="Forecast horizon in days")
    inventory_params: Dict[str, InventoryParams] = Field(
        ...,
        description="Inventory parameters per item_id"
    )
    model: Optional[str] = Field("chronos-2", description="Primary model to use")
    client_id: Optional[str] = Field(None, description="Client ID (required for service API key calls, optional for JWT)")

    class Config:
        json_schema_extra = {
            "example": {
                "item_ids": ["SKU001"],
                "prediction_length": 30,
                "inventory_params": {
                    "SKU001": {
                        "current_stock": 500,
                        "lead_time_days": 14,
                        "safety_stock_days": 7,
                        "moq": 100,
                        "service_level": 0.95,
                    }
                },
                "model": "chronos-2",
            }
        }


class ActualValue(BaseModel):
    """Single actual value for backfilling"""

    date: date_type = Field(..., description="Date of actual sales")
    actual_value: float = Field(..., ge=0, description="Actual units sold")


class BackfillActualsRequest(BaseModel):
    """Request schema for backfilling actual values"""

    item_id: str = Field(..., description="Item identifier")
    actuals: List[ActualValue] = Field(..., min_length=1, description="List of actual values")

    class Config:
        json_schema_extra = {
            "example": {
                "item_id": "SKU001",
                "actuals": [
                    {"date": "2024-01-02", "actual_value": 130.0},
                    {"date": "2024-01-03", "actual_value": 125.0},
                ],
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class PredictionQuantiles(BaseModel):
    """Industry standard quantile predictions"""

    p10: Optional[float] = Field(None, description="10th percentile (lower bound)")
    p50: Optional[float] = Field(None, description="50th percentile (median)")
    p90: Optional[float] = Field(None, description="90th percentile (upper bound)")


class Prediction(BaseModel):
    """Single day prediction"""

    date: date_type = Field(..., description="Forecast date")
    point_forecast: float = Field(..., description="Point forecast (median/mean)")
    quantiles: Optional[PredictionQuantiles] = Field(None, description="Quantile predictions")


class SKUClassificationInfo(BaseModel):
    """SKU classification (ABC-XYZ) information"""

    abc_class: str = Field(..., description="ABC class: A (high volume), B (medium), C (low)")
    xyz_class: str = Field(..., description="XYZ class: X (low variability), Y (medium), Z (high)")
    demand_pattern: str = Field(..., description="Demand pattern: regular, intermittent, lumpy")
    forecastability_score: float = Field(..., description="Forecastability score (0.0 to 1.0)")
    recommended_method: str = Field(..., description="Recommended forecasting method")
    expected_mape_range: Tuple[float, float] = Field(..., description="Expected MAPE range (min, max)")
    warnings: List[str] = Field(default_factory=list, description="Classification warnings")


class ItemForecast(BaseModel):
    """Forecast results for a single item"""

    item_id: str = Field(..., description="Item identifier")
    method_used: str = Field(..., description="Method used for predictions")
    predictions: List[Prediction] = Field(..., description="Daily predictions")
    classification: Optional[SKUClassificationInfo] = Field(None, description="SKU classification (ABC-XYZ)")


class ForecastResponse(BaseModel):
    """Response schema for pure forecast endpoint"""

    forecast_id: str = Field(..., description="Unique forecast run ID")
    primary_model: str = Field(..., description="Model that was requested")
    forecasts: List[ItemForecast] = Field(..., description="Forecast results per item")


class InventoryMetrics(BaseModel):
    """Industry standard inventory metrics"""

    current_stock: float = Field(..., description="Current inventory level")
    days_of_inventory_remaining: float = Field(..., description="Days of Inventory Remaining (DIR)")
    safety_stock: float = Field(..., description="Calculated safety stock")
    reorder_point: float = Field(..., description="Reorder Point (ROP)")
    recommended_order_quantity: float = Field(..., description="Recommended order quantity")
    stockout_risk: str = Field(..., description="Stockout risk level: low, medium, high, critical")
    stockout_date: Optional[date_type] = Field(None, description="Predicted stockout date")


class Recommendations(BaseModel):
    """Actionable recommendations"""

    action: str = Field(..., description="Recommended action: URGENT_REORDER, REORDER, MONITOR, OK")
    priority: str = Field(..., description="Priority level: critical, high, medium, low")
    message: str = Field(..., description="Human-readable recommendation message")


class InventoryResult(BaseModel):
    """Inventory calculation result for a single item"""

    item_id: str = Field(..., description="Item identifier")
    inventory_metrics: InventoryMetrics = Field(..., description="Calculated inventory metrics")
    recommendations: Recommendations = Field(..., description="Actionable recommendations")


class InventoryCalculationResponse(BaseModel):
    """Response schema for inventory calculation endpoint"""

    calculation_id: str = Field(..., description="Unique calculation ID")
    results: List[InventoryResult] = Field(..., description="Inventory results per item")


class BackfillActualsResponse(BaseModel):
    """Response schema for backfilling actuals"""

    updated_count: int = Field(..., description="Number of records updated")
    message: str = Field(..., description="Status message")


class MethodQuality(BaseModel):
    """Quality metrics for a single method"""

    method: str = Field(..., description="Method identifier")
    predictions_count: int = Field(..., description="Number of predictions")
    actuals_count: int = Field(..., description="Number of actuals available")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%)")
    mae: Optional[float] = Field(None, description="Mean Absolute Error (units)")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error")
    bias: Optional[float] = Field(None, description="Forecast Bias")


class QualityResponse(BaseModel):
    """Response schema for quality metrics endpoint"""

    item_id: str = Field(..., description="Item identifier")
    period: Dict[str, Optional[date_type]] = Field(..., description="Analysis period")
    methods: List[MethodQuality] = Field(..., description="Quality metrics per method")

