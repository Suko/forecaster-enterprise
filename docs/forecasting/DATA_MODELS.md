# Forecasting Module - Data Models

**Status:** ✅ Complete  
**Scope:** Full Data Models (MVP + Future Phases)  
**Quick Start:** See [MVP_UNIFIED.md](MVP_UNIFIED.md) for minimal MVP models

---

**Last Updated:** 2025-01-XX

---

## Overview

This document defines all data models required for the forecasting module, organized by layer:

1. **Database Models (SQLAlchemy)** - Persistent storage
2. **Request Schemas (Pydantic)** - API input validation
3. **Response Schemas (Pydantic)** - API output structure
4. **Input Data Models** - Source data access patterns
5. **Internal Data Models** - Service layer data structures

---

## Multi-Tenant Architecture

**Status:** ✅ Implemented - Unified architecture for SaaS and on-premise

**Implementation:**
- ✅ `Client` model created (`clients` table)
- ✅ `User` model includes `client_id` foreign key
- ✅ JWT token includes `client_id` claim
- ✅ All queries filter by `client_id` (unified)
- ✅ Same codebase works for both SaaS and on-premise deployments

**Key Design:**
- **Unified Schema**: Both SaaS and on-premise use same schema (includes `client_id` column)
- **Unified Queries**: Both deployments filter by `client_id` (same code)
- **Unified Authentication**: Both deployments get `client_id` from JWT token
- **No Configuration Needed**: System is agnostic to deployment model

**See:** [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md) for complete design details.

---

## 1. Database Models (SQLAlchemy)

**Location:** `backend/models/forecast.py`

**✅ Implementation Note:** The actual implementation uses **dialect-aware types**:
- `GUID()` - Uses PostgreSQL `UUID` in production, `CHAR(36)` in SQLite tests
- `JSONBType()` - Uses PostgreSQL `JSONB` in production, `JSON` in SQLite tests

This provides:
- ✅ **Production:** Full PostgreSQL benefits (UUID indexing, JSONB performance)
- ✅ **Tests:** SQLite compatibility (works with in-memory database)
- ✅ **Automatic:** SQLAlchemy handles the conversion based on database dialect

### 1.1 ForecastRun

**Purpose:** Tracks forecast execution metadata and configuration.

```python
class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    
    # Primary Key (UUID in PostgreSQL, CHAR(36) in SQLite)
    forecast_run_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy (UUID in PostgreSQL, CHAR(36) in SQLite)
    client_id = Column(GUID(), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # Keep String for FK compatibility
    
    # Model Configuration
    primary_model = Column(String(50), nullable=False, default="chronos-2")
    prediction_length = Column(Integer, nullable=False)  # Days ahead (e.g., 30)
    item_ids = Column(JSON)  # List of items forecasted (JSON for SQLite, JSONB in PostgreSQL)
    
    # Results
    recommended_method = Column(String(50))  # Method used for response
    status = Column(String(20), nullable=False, default="pending")  # pending, completed, failed
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Note:** Actual implementation is simplified for MVP. Future fields (model_version, methods_run, quantile_levels, training dates, runtime_ms, updated_at) can be added in Phase 2.

**Relationships:**
- `user_id` → `users.id`
- One-to-many with `ForecastResult`

---

### 1.2 ForecastResult

**Purpose:** Stores per-day forecast outputs for each method executed.

**Key Design Decision:** One row per `(forecast_run_id, item_id, method, date)` to support multi-method storage.

```python
class ForecastResult(Base):
    __tablename__ = "forecast_results"
    
    # Primary Key (UUID in PostgreSQL, CHAR(36) in SQLite)
    result_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys (UUID in PostgreSQL, CHAR(36) in SQLite)
    forecast_run_id = Column(GUID(), ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    client_id = Column(GUID(), nullable=False, index=True)
    
    # Item & Method
    item_id = Column(String(255), nullable=False, index=True)
    method = Column(String(50), nullable=False)  # "chronos-2", "statistical_ma7"
    
    # Forecast Date
    date = Column(Date, nullable=False)
    horizon_day = Column(Integer, nullable=False)  # Days ahead: 1, 2, 3, ...
    
    # Forecast Values (Industry Standard Quantiles)
    point_forecast = Column(Numeric(18, 2), nullable=False)  # Main prediction
    p10 = Column(Numeric(18, 2))  # 10th percentile (lower bound)
    p50 = Column(Numeric(18, 2))  # 50th percentile (median)
    p90 = Column(Numeric(18, 2))  # 90th percentile (upper bound)
    
    # Actual Values (Backfilled Later)
    actual_value = Column(Numeric(18, 2))  # Real sales (backfilled via API)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Note:** Actual implementation is simplified for MVP. Future fields (location_id, error, updated_at) can be added in Phase 2.
    
    # Indexes for Performance
    __table_args__ = (
        Index('idx_forecast_results_run_item', 'forecast_run_id', 'item_id'),
        Index('idx_forecast_results_item_method_date', 'item_id', 'method', 'date'),
        Index('idx_forecast_results_method', 'method'),
        Index('idx_forecast_results_actuals', 'actual_value'),
        UniqueConstraint('forecast_run_id', 'item_id', 'method', 'date', name='uq_forecast_result'),
    )
```

**Relationships:**
- `forecast_run_id` → `forecast_runs.forecast_run_id`
- Many-to-one with `ForecastRun`

---

### 1.3 ForecastMethodPerformance (Future - Phase 2)

**Purpose:** Tracks historical performance metrics per method for method selection.

```python
class ForecastMethodPerformance(Base):
    __tablename__ = "forecast_method_performance"
    
    # Primary Key
    performance_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Multi-tenancy
    client_id = Column(UUID, nullable=False, index=True)
    
    # Method & Item
    method = Column(String(50), nullable=False)
    item_id = Column(String(255), nullable=False, index=True)
    location_id = Column(UUID, nullable=True)
    
    # Evaluation Period
    evaluation_start_date = Column(Date, nullable=False)
    evaluation_end_date = Column(Date, nullable=False)
    sample_size = Column(Integer)  # Number of forecasts evaluated
    
    # Industry Standard Accuracy Metrics
    mape = Column(Numeric(9, 4))  # Mean Absolute Percentage Error
    mae = Column(Numeric(18, 4))  # Mean Absolute Error
    rmse = Column(Numeric(18, 4))  # Root Mean Squared Error
    bias = Column(Numeric(18, 4))  # Forecast Bias
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_method_perf_item_method', 'item_id', 'method'),
        Index('idx_method_perf_client_method', 'client_id', 'method'),
    )
```

**Note:** This table is for Phase 2 (method selection based on history). MVP uses simple fallback logic.

---

### 1.4 InventoryCalculation (Optional - If Storing Inventory Results Separately)

**Purpose:** Stores inventory calculation results if we want to persist them separately from forecasts.

```python
class InventoryCalculation(Base):
    __tablename__ = "inventory_calculations"
    
    # Primary Key
    calculation_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    
    # Foreign Keys
    forecast_run_id = Column(UUID, ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    
    # Multi-tenancy
    client_id = Column(UUID, nullable=False, index=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False)
    
    # Item
    item_id = Column(String(255), nullable=False, index=True)
    location_id = Column(UUID, nullable=True)
    
    # Input Parameters
    current_stock = Column(Numeric(18, 2), nullable=False)
    lead_time_days = Column(Integer, nullable=False)
    safety_stock_days = Column(Integer)
    moq = Column(Integer)  # Minimum Order Quantity
    service_level = Column(Numeric(5, 4))  # e.g., 0.95 for 95%
    
    # Calculated Metrics (Industry Standard)
    days_of_inventory_remaining = Column(Numeric(9, 2))
    safety_stock = Column(Numeric(18, 2))
    reorder_point = Column(Numeric(18, 2))
    recommended_order_quantity = Column(Numeric(18, 2))
    stockout_risk = Column(String(20))  # "low", "medium", "high"
    stockout_date = Column(Date)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_inv_calc_item', 'item_id'),
        Index('idx_inv_calc_run', 'forecast_run_id'),
    )
```

**Note:** For MVP, inventory calculations can be computed on-the-fly from forecasts. This table is optional if we want to persist historical inventory recommendations.

---

## 2. Request Schemas (Pydantic)

**Location:** `backend/schemas/forecast.py`

### 2.1 Pure Forecast Request

```python
class ForecastRequest(BaseModel):
    """Request schema for pure forecast endpoint"""
    
    item_ids: List[str] = Field(..., min_items=1, description="List of item IDs to forecast")
    prediction_length: int = Field(30, ge=1, le=365, description="Forecast horizon in days")
    model: Optional[str] = Field("chronos-2", description="Model to use (optional, defaults to chronos-2)")
    location_id: Optional[UUID] = Field(None, description="Location ID (optional for MVP)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "item_ids": ["SKU001", "SKU002"],
                "prediction_length": 30,
                "model": "chronos-2"
            }
        }
```

---

### 2.2 Inventory Calculation Request

```python
class InventoryParams(BaseModel):
    """Inventory parameters per item"""
    
    current_stock: float = Field(..., gt=0, description="Current inventory level")
    lead_time_days: int = Field(..., ge=0, description="Lead time in days")
    safety_stock_days: Optional[int] = Field(None, ge=0, description="Safety stock in days")
    moq: Optional[int] = Field(None, ge=0, description="Minimum Order Quantity")
    service_level: float = Field(0.95, ge=0.0, le=1.0, description="Service level (e.g., 0.95 for 95%)")


class InventoryCalculationRequest(BaseModel):
    """Request schema for inventory calculation endpoint"""
    
    item_ids: List[str] = Field(..., min_items=1, description="List of item IDs")
    prediction_length: int = Field(30, ge=1, le=365, description="Forecast horizon in days")
    inventory_params: Dict[str, InventoryParams] = Field(
        ...,
        description="Inventory parameters per item_id"
    )
    model: Optional[str] = Field("chronos-2", description="Model to use (optional)")
    location_id: Optional[UUID] = Field(None, description="Location ID (optional for MVP)")
    
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
                        "service_level": 0.95
                    }
                },
                "model": "chronos-2"
            }
        }
```

---

## 3. Response Schemas (Pydantic)

**Location:** `backend/schemas/forecast.py`

### 3.1 Pure Forecast Response

```python
class PredictionQuantiles(BaseModel):
    """Industry standard quantile predictions"""
    
    p10: Optional[float] = Field(None, description="10th percentile (lower bound)")
    p50: Optional[float] = Field(None, description="50th percentile (median)")
    p90: Optional[float] = Field(None, description="90th percentile (upper bound)")


class Prediction(BaseModel):
    """Single day prediction"""
    
    date: date = Field(..., description="Forecast date")
    point_forecast: float = Field(..., description="Point forecast (median/mean)")
    quantiles: Optional[PredictionQuantiles] = Field(None, description="Quantile predictions")
    uncertainty_range: Optional[float] = Field(None, description="Uncertainty range (p90 - p10)")
    coefficient_of_variation: Optional[float] = Field(None, description="Coefficient of Variation (CV)")


class AccuracyIndicators(BaseModel):
    """Industry standard accuracy metrics"""
    
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error (%)")
    mae: Optional[float] = Field(None, description="Mean Absolute Error (units)")
    rmse: Optional[float] = Field(None, description="Root Mean Squared Error")
    bias: Optional[float] = Field(None, description="Forecast Bias (positive=over, negative=under)")
    sample_size: Optional[int] = Field(None, description="Number of past forecasts used")


class BaselineComparison(BaseModel):
    """Baseline method summary for comparison"""
    
    method: str = Field(..., description="Baseline method name")
    avg_daily_demand: float = Field(..., description="Average daily demand")
    total_forecast_30d: float = Field(..., description="Total forecast for 30 days")


class ForecastMetadata(BaseModel):
    """Forecast metadata"""
    
    method_used: str = Field(..., description="Method used for predictions")
    historical_data_points: Optional[int] = Field(None, description="Number of historical data points")
    training_start_date: Optional[date] = Field(None, description="Training period start")
    training_end_date: Optional[date] = Field(None, description="Training period end")


class ItemForecast(BaseModel):
    """Forecast results for a single item"""
    
    item_id: str = Field(..., description="Item identifier")
    recommended_method: str = Field(..., description="Method used for predictions")
    predictions: List[Prediction] = Field(..., description="Daily predictions")
    metadata: ForecastMetadata = Field(..., description="Forecast metadata")
    accuracy_indicators: Optional[AccuracyIndicators] = Field(None, description="Historical accuracy (if available)")
    baseline_comparison: Optional[BaselineComparison] = Field(None, description="Baseline summary (optional)")


class ForecastResponse(BaseModel):
    """Response schema for pure forecast endpoint"""
    
    forecast_id: UUID = Field(..., description="Unique forecast run ID")
    primary_model: str = Field(..., description="Model that was requested")
    forecasts: List[ItemForecast] = Field(..., description="Forecast results per item")
```

---

### 3.2 Inventory Calculation Response

```python
class ForecastSummary(BaseModel):
    """Forecast summary for inventory calculation"""
    
    method_used: str = Field(..., description="Method used for predictions")
    total_forecast_30d: float = Field(..., description="Total forecast for prediction period")
    avg_daily_demand: float = Field(..., description="Average daily demand")


class InventoryMetrics(BaseModel):
    """Industry standard inventory metrics"""
    
    current_stock: float = Field(..., description="Current inventory level")
    days_of_inventory_remaining: float = Field(..., description="Days of Inventory Remaining (DIR)")
    safety_stock: float = Field(..., description="Calculated safety stock")
    reorder_point: float = Field(..., description="Reorder Point (ROP)")
    recommended_order_quantity: float = Field(..., description="Recommended order quantity")
    stockout_risk: str = Field(..., description="Stockout risk level: low, medium, high")
    stockout_date: Optional[date] = Field(None, description="Predicted stockout date")
    days_until_reorder: Optional[int] = Field(None, description="Days until reorder point is reached")


class Recommendations(BaseModel):
    """Actionable recommendations"""
    
    action: str = Field(..., description="Recommended action: URGENT_REORDER, REORDER, MONITOR, OK")
    priority: str = Field(..., description="Priority level: critical, high, medium, low")
    message: str = Field(..., description="Human-readable recommendation message")
    suggested_order_date: Optional[date] = Field(None, description="Suggested order date")
    suggested_order_quantity: Optional[float] = Field(None, description="Suggested order quantity")


class InventoryResult(BaseModel):
    """Inventory calculation result for a single item"""
    
    item_id: str = Field(..., description="Item identifier")
    forecast: ForecastSummary = Field(..., description="Forecast summary")
    inventory_metrics: InventoryMetrics = Field(..., description="Calculated inventory metrics")
    recommendations: Recommendations = Field(..., description="Actionable recommendations")


class InventoryCalculationResponse(BaseModel):
    """Response schema for inventory calculation endpoint"""
    
    calculation_id: UUID = Field(..., description="Unique calculation ID")
    results: List[InventoryResult] = Field(..., description="Inventory results per item")
```

---

## 4. Input Data Models

**Purpose:** Define how to access and structure source data from `ts_demand_daily`.

**Location:** `backend/services/forecasting/data_access.py`

### 4.1 Historical Sales Data Structure

```python
class HistoricalSalesData(BaseModel):
    """Structure for historical sales data fetched from ts_demand_daily"""
    
    date: date
    item_id: str
    location_id: Optional[UUID]
    units_sold: float
    revenue: Optional[float]
    orders_count: Optional[int]
    
    # Covariates (if available)
    promotion_flag: Optional[bool]
    promotion_type: Optional[str]
    discount_pct: Optional[float]
    regular_price: Optional[float]
    actual_price: Optional[float]
    
    # Known future covariates (for Chronos-2)
    holiday_flag: Optional[bool]
    holiday_type: Optional[str]
    planned_promo_flag: Optional[bool]
    planned_promo_type: Optional[str]
    
    # Calendar features
    is_weekend: Optional[bool]
    month: Optional[int]  # 1-12
    peak_season_flag: Optional[bool]
```

### 4.2 Data Access Function Signature

```python
async def fetch_historical_sales(
    db: AsyncSession,
    client_id: UUID,
    item_ids: List[str],
    start_date: date,
    end_date: date,
    location_id: Optional[UUID] = None
) -> pd.DataFrame:
    """
    Fetch historical sales data from ts_demand_daily table.
    
    Returns:
        DataFrame with columns:
        - date, item_id, location_id, units_sold
        - Optional: revenue, orders_count, promotion_flag, etc.
        - Sorted by date, item_id
    """
    # Query: SELECT * FROM ts_demand_daily
    # WHERE client_id = ? AND item_id IN (?)
    #   AND date_local BETWEEN ? AND ?
    #   AND (location_id = ? OR location_id IS NULL)
    # ORDER BY date_local, item_id
    pass
```

**Note:** For MVP, if `ts_demand_daily` doesn't exist, use mock/placeholder data.

---

## 5. Internal Data Models (Service Layer)

**Purpose:** Data structures used internally by forecasting services.

**Location:** `backend/services/forecasting/types.py`

### 5.1 Forecast Method Result

```python
class ForecastMethodResult(BaseModel):
    """Result from a single forecasting method"""
    
    method: str  # "chronos-2", "statistical_ma7", etc.
    item_id: str
    predictions: List[Prediction]  # Daily predictions
    metadata: Dict[str, Any]  # Method-specific metadata
    success: bool
    error_message: Optional[str] = None
```

### 5.2 Method Selection Result

```python
class MethodSelectionResult(BaseModel):
    """Result of method selection logic"""
    
    recommended_method: str
    all_methods: List[str]  # All methods that were executed
    selection_reason: str  # Why this method was selected
```

---

## 6. Database Migration

**Location:** `backend/migrations/`

### 6.1 Migration File: `002_add_forecast_tables.py`

```python
"""Add forecast tables

Revision ID: 002
Revises: 001
Create Date: 2025-01-XX
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create forecast_runs table
    op.create_table(
        'forecast_runs',
        sa.Column('forecast_run_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('primary_model', sa.String(50), nullable=False),
        sa.Column('model_version', sa.String(50)),
        sa.Column('methods_run', postgresql.JSON),
        sa.Column('recommended_method', sa.String(50)),
        sa.Column('prediction_length', sa.Integer(), nullable=False),
        sa.Column('quantile_levels', postgresql.JSON),
        sa.Column('training_start_date', sa.Date()),
        sa.Column('training_end_date', sa.Date()),
        sa.Column('item_ids', postgresql.JSON),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.Text()),
        sa.Column('runtime_ms', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
    )
    op.create_index('idx_forecast_runs_client_status', 'forecast_runs', ['client_id', 'status'])
    op.create_index('idx_forecast_runs_created', 'forecast_runs', ['created_at'])
    
    # Create forecast_results table
    op.create_table(
        'forecast_results',
        sa.Column('result_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('forecast_run_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_id', sa.String(255), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True)),
        sa.Column('method', sa.String(50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('horizon_day', sa.Integer(), nullable=False),
        sa.Column('point_forecast', sa.Numeric(18, 2), nullable=False),
        sa.Column('p10', sa.Numeric(18, 2)),
        sa.Column('p50', sa.Numeric(18, 2)),
        sa.Column('p90', sa.Numeric(18, 2)),
        sa.Column('actual_value', sa.Numeric(18, 2)),
        sa.Column('error', sa.Numeric(18, 4)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['forecast_run_id'], ['forecast_runs.forecast_run_id']),
        sa.UniqueConstraint('forecast_run_id', 'item_id', 'method', 'date', name='uq_forecast_result'),
    )
    op.create_index('idx_forecast_results_run_item', 'forecast_results', ['forecast_run_id', 'item_id'])
    op.create_index('idx_forecast_results_item_method_date', 'forecast_results', ['item_id', 'method', 'date'])
    op.create_index('idx_forecast_results_method', 'forecast_results', ['method'])
    op.create_index('idx_forecast_results_actuals', 'forecast_results', ['actual_value'])


def downgrade():
    op.drop_table('forecast_results')
    op.drop_table('forecast_runs')
```

---

## 7. Data Model Relationships

```
ForecastRun (1) ──< (many) ForecastResult
ForecastRun.user_id ──> User.id
ForecastResult.forecast_run_id ──> ForecastRun.forecast_run_id

(Optional for Phase 2)
ForecastMethodPerformance (standalone, aggregated from ForecastResult)
InventoryCalculation (1) ──> ForecastRun (1)
```

---

## 8. Key Design Decisions

### 8.1 Multi-Method Storage

**Decision:** Store all method results in `forecast_results` with a `method` column.

**Rationale:**
- Enables historical performance analysis
- Allows method comparison over time
- Supports future method selection based on history

### 8.2 Quantile Storage

**Decision:** Store standard quantiles (p10, p50, p90) as separate columns.

**Rationale:**
- Industry standard for uncertainty intervals
- Easy to query and aggregate
- Supports calculation of uncertainty_range and CV

### 8.3 Optional Location Support

**Decision:** `location_id` is optional in MVP.

**Rationale:**
- Some clients may not have multi-location requirements
- Can be added later without breaking changes
- Simplifies MVP implementation

### 8.4 Separate Inventory Calculation Table

**Decision:** Inventory calculations can be computed on-the-fly (MVP) or stored separately (Phase 2).

**Rationale:**
- MVP: Simpler, no additional storage needed
- Phase 2: Enables historical inventory recommendation tracking

---

## 9. Next Steps

1. ✅ **Define Models** (This document)
2. ⏳ **Create SQLAlchemy Models** - Implement `backend/models/forecast.py`
3. ⏳ **Create Pydantic Schemas** - Implement `backend/schemas/forecast.py`
4. ⏳ **Create Migration** - Implement `backend/migrations/002_add_forecast_tables.py`
5. ⏳ **Create Data Access Layer** - Implement `backend/services/forecasting/data_access.py`
6. ⏳ **Update Database Init** - Add forecast models to `backend/models/database.py`

---

## 10. References

- **Industry Standards:** See `docs/forecasting/INDUSTRY_STANDARDS.md`
- **Data Warehouse Schema:** See `forecaster/DATA_MODELS_AUDIT.md`
- **MVP Design:** See `docs/forecasting/MVP_DESIGN.md`
- **Architecture:** See `docs/forecasting/ARCHITECTURE.md`

