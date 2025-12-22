"""
Simulation API Schemas

Pydantic models for simulation request/response validation.
"""
from typing import List, Optional, Dict
from datetime import date as date_type
from pydantic import BaseModel, Field
from uuid import UUID
from decimal import Decimal


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class SimulationConfig(BaseModel):
    """Configuration for simulation behavior"""
    
    auto_place_orders: bool = Field(True, description="Automatically place orders when reorder point is triggered")
    lead_time_buffer_days: int = Field(0, ge=0, description="Additional buffer days for lead time")
    min_order_quantity: int = Field(1, ge=1, description="Minimum order quantity")
    service_level: float = Field(0.95, ge=0.0, le=1.0, description="Target service level")


class SimulationRequest(BaseModel):
    """Request schema for simulation endpoint"""
    
    client_id: UUID = Field(..., description="Client ID")
    start_date: date_type = Field(..., description="Simulation start date (e.g., 12 months ago)")
    end_date: date_type = Field(..., description="Simulation end date (e.g., today)")
    item_ids: Optional[List[str]] = Field(None, description="Optional: specific items to simulate. If None, simulates all items.")
    simulation_config: Optional[SimulationConfig] = Field(None, description="Simulation configuration. Uses defaults if not provided.")
    
    class Config:
        json_schema_extra = {
            "example": {
                "client_id": "123e4567-e89b-12d3-a456-426614174000",
                "start_date": "2024-01-01",
                "end_date": "2024-12-22",
                "item_ids": ["SKU001", "SKU002"],
                "simulation_config": {
                    "auto_place_orders": True,
                    "lead_time_buffer_days": 0,
                    "min_order_quantity": 1,
                    "service_level": 0.95
                }
            }
        }


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class DailyComparison(BaseModel):
    """Daily comparison of simulated vs real outcomes"""
    
    date: date_type
    item_id: str
    simulated_stock: float
    real_stock: float
    actual_sales: Optional[float] = Field(None, description="Actual sales for this day")
    simulated_stockout: bool
    real_stockout: bool
    order_placed: Optional[bool] = None
    order_quantity: Optional[float] = None


class ItemLevelResult(BaseModel):
    """Item-level simulation results"""
    
    item_id: str
    stockout_rate: Dict[str, float] = Field(..., description="Keys: 'simulated', 'real'")
    inventory_value: Dict[str, Decimal] = Field(..., description="Keys: 'simulated', 'real'")
    service_level: Dict[str, float] = Field(..., description="Keys: 'simulated', 'real'")
    total_orders_placed: int
    improvement: Dict[str, float] = Field(..., description="Keys: 'stockout_reduction', 'inventory_reduction'")


class SimulationMetrics(BaseModel):
    """Overall simulation metrics"""
    
    stockout_rate: Dict[str, float] = Field(..., description="Keys: 'simulated', 'real'")
    inventory_value: Dict[str, Decimal] = Field(..., description="Keys: 'simulated', 'real'")
    service_level: Dict[str, float] = Field(..., description="Keys: 'simulated', 'real'")
    total_cost: Dict[str, Decimal] = Field(..., description="Keys: 'simulated', 'real'")


class SimulationImprovements(BaseModel):
    """Improvement metrics vs baseline"""
    
    stockout_reduction: float = Field(..., description="Percentage reduction in stockout rate")
    inventory_reduction: float = Field(..., description="Percentage reduction in inventory value")
    cost_savings: Decimal = Field(..., description="Absolute cost savings")
    service_level_improvement: float = Field(..., description="Percentage improvement in service level")


class SimulationResponse(BaseModel):
    """Response schema for simulation endpoint"""
    
    simulation_id: UUID
    status: str = Field(..., description="Status: 'completed', 'failed', 'in_progress'")
    start_date: date_type
    end_date: date_type
    total_days: int
    results: Optional[SimulationMetrics] = None
    improvements: Optional[SimulationImprovements] = None
    daily_comparison: Optional[List[DailyComparison]] = None
    item_level_results: Optional[List[ItemLevelResult]] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "simulation_id": "123e4567-e89b-12d3-a456-426614174000",
                "status": "completed",
                "start_date": "2024-01-01",
                "end_date": "2024-12-22",
                "total_days": 356,
                "results": {
                    "stockout_rate": {"simulated": 0.012, "real": 0.048},
                    "inventory_value": {"simulated": 2400000, "real": 3100000},
                    "service_level": {"simulated": 0.988, "real": 0.952},
                    "total_cost": {"simulated": 2800000, "real": 3500000}
                },
                "improvements": {
                    "stockout_reduction": 0.75,
                    "inventory_reduction": 0.23,
                    "cost_savings": 700000,
                    "service_level_improvement": 0.036
                }
            }
        }

