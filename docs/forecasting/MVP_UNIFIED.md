# Forecasting System - MVP Unified Documentation

**Version:** 1.0  
**Date:** 2025-01-XX  
**Status:** ✅ Implementation In Progress

## Implementation Status

**Last Updated:** 2025-12-06

### ✅ Completed
- Database migration (`forecast_runs`, `forecast_results` tables)
- SQLAlchemy models (`ForecastRun`, `ForecastResult`)
- BaseForecastModel abstract interface
- Chronos2Model wrapper
- MovingAverageModel (7-day)
- ForecastService orchestration
- InventoryCalculator (industry standard formulas)
- QualityCalculator (MAPE/MAE/RMSE)
- Pydantic schemas (all request/response models)
- API endpoints (4 endpoints implemented)
- Authentication integration

### ⚠️ In Progress / TODO
- Data access layer (`_fetch_historical_data()` - placeholder)
- Result fetching for API responses (basic structure, needs DB queries)
- Unit tests
- Integration tests
- ETL integration (ts_demand_daily table population)

---

## Table of Contents

1. [MVP System Overview](#1-mvp-system-overview)
2. [Minimal Data Models](#2-minimal-data-models-for-mvp)
3. [Unified Documentation Summary](#3-unified-documentation-summary)
4. [Executive Overview (Non-Technical)](#4-executive-overview-non-technical)

---

# 1. MVP System Overview

## 1.1 What We're Building

A forecasting API that predicts future demand for inventory items using:
- **Primary**: Chronos-2 (Amazon's pretrained ML model)
- **Baseline**: 7-day Moving Average (for comparison and fallback)

## 1.2 Minimal Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer                               │
│  POST /api/v1/forecast      POST /api/v1/inventory/calculate │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Service Layer                             │
│  ForecastService          InventoryService                   │
│  - Run Chronos-2          - Calculate metrics                │
│  - Run MA7 baseline       - Generate recommendations         │
│  - Select best method     - Use industry formulas            │
└─────────────────────────────┬───────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Chronos-2      │  │  Statistical    │  │   Database      │
│  Model          │  │  Methods        │  │   (PostgreSQL)  │
│  (Pretrained)   │  │  (MA7)          │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 1.3 Two Execution Cycles

| Cycle | Trigger | Frequency | Items |
|-------|---------|-----------|-------|
| **Automatic** | Scheduler (Cron) | Every 7 days | All active items |
| **Manual** | API request | On-demand | User-specified |

## 1.4 Required Components (MVP)

### Must Have Now

| Component | Purpose | Location |
|-----------|---------|----------|
| `ForecastService` | Orchestrate forecasting | `forecasting/services/` |
| `Chronos2Model` | ML predictions | `forecasting/modes/ml/` |
| `MovingAverageModel` | Baseline predictions | `forecasting/modes/statistical/` |
| `InventoryCalculator` | DIR, ROP, Safety Stock | `forecasting/applications/inventory/` |
| `QualityCalculator` | Calculate MAPE/MAE/RMSE | `forecasting/services/` |
| `ForecastRun` (DB) | Track forecast executions | `models/forecast.py` |
| `ForecastResult` (DB) | Store predictions + actuals | `models/forecast.py` |
| Request/Response Schemas | API contracts | `schemas/forecast.py` |
| API Endpoints | HTTP interface | `api/forecast.py` |
| **Actuals Backfill Endpoint** | Update actual values | `api/forecast.py` |
| **Quality View Endpoint** | View MAPE/MAE/RMSE | `api/forecast.py` |

### Can Add Later (Phase 2+)

| Component | Purpose | Phase |
|-----------|---------|-------|
| Additional statistical methods (MA30, Exponential) | More baselines | Phase 2 |
| Performance tracking service | Automated accuracy tracking | Phase 2 |
| `forecast_method_performance` table | Store aggregated metrics | Phase 2 |
| Model versioning | Track model changes | Phase 2 |
| **Data quality monitoring** | Alerts, anomaly detection | Phase 2 |
| **Data quality events table** | Store quality issues | Phase 2 |
| Drift detection | Monitor data quality trends | Phase 3 |
| Additional ML models (TimesFM, Moirai) | Model options | Phase 3 |

## 1.5 Why This Design is Appropriate for MVP

1. **Simplicity**: Only 2 forecasting methods (Chronos-2 + MA7)
2. **Speed**: Can implement in 2-3 weeks
3. **Testability**: Each component can be tested independently
4. **Extensibility**: Adding new models requires no architecture changes
5. **Production Ready**: Uses proven Chronos-2 model
6. **Fallback Safety**: If ML fails, statistical method works

---

# 2. Minimal Data Models for MVP

## 2.1 Database Tables (Essential Only)

### Table 1: `forecast_runs` (Required)

**Purpose**: Track each forecast execution

```sql
CREATE TABLE forecast_runs (
    -- Identity
    forecast_run_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL,              -- Multi-tenancy
    user_id VARCHAR NOT NULL,             -- Who triggered
    
    -- Configuration
    primary_model VARCHAR(50) DEFAULT 'chronos-2',
    prediction_length INT NOT NULL,        -- Days ahead (e.g., 30)
    item_ids JSONB,                        -- Items forecasted
    
    -- Results
    recommended_method VARCHAR(50),        -- Best method used
    status VARCHAR(20) DEFAULT 'pending',  -- pending/completed/failed
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Indexes
    INDEX idx_runs_client (client_id),
    INDEX idx_runs_status (status)
);
```

**Fields**: 11 (minimal set)

### Table 2: `forecast_results` (Required)

**Purpose**: Store daily predictions from each method

**Key Design**: We store predictions from BOTH methods (chronos-2 AND statistical_ma7) even though we only return one in the API response. This enables:
- Future accuracy tracking (compare predictions vs actuals)
- Method performance analysis (which method works better per item)
- Historical comparison (Phase 2 feature)

```sql
CREATE TABLE forecast_results (
    -- Identity
    result_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    forecast_run_id UUID REFERENCES forecast_runs(forecast_run_id),
    client_id UUID NOT NULL,
    
    -- What
    item_id VARCHAR(255) NOT NULL,
    method VARCHAR(50) NOT NULL,           -- 'chronos-2' or 'statistical_ma7'
    
    -- When
    date DATE NOT NULL,
    horizon_day INT NOT NULL,              -- 1, 2, 3... days ahead
    
    -- Predictions
    point_forecast NUMERIC(18,2) NOT NULL, -- Main prediction
    p10 NUMERIC(18,2),                     -- 10th percentile (lower)
    p50 NUMERIC(18,2),                     -- 50th percentile (median)
    p90 NUMERIC(18,2),                     -- 90th percentile (upper)
    
    -- Actuals (filled later)
    actual_value NUMERIC(18,2),            -- Real sales (backfilled)
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE (forecast_run_id, item_id, method, date),
    
    -- Indexes
    INDEX idx_results_item (item_id, method, date)
);
```

**Fields**: 14 (minimal set)

## 2.2 Pydantic Schemas (Essential Only)

### Request Schemas

```python
# Forecast Request (Minimal)
class ForecastRequest(BaseModel):
    item_ids: List[str]                    # Required: what to forecast
    prediction_length: int = 30            # Optional: default 30 days
    model: str = "chronos-2"               # Optional: primary model

# Inventory Request (Minimal)
class InventoryCalculationRequest(BaseModel):
    item_ids: List[str]
    prediction_length: int = 30
    inventory_params: Dict[str, InventoryParams]

class InventoryParams(BaseModel):
    current_stock: float                   # Required
    lead_time_days: int                    # Required
    safety_stock_days: int = 7             # Optional
    service_level: float = 0.95            # Optional
```

### Response Schemas

```python
# Forecast Response (Minimal)
class ForecastResponse(BaseModel):
    forecast_id: UUID
    forecasts: List[ItemForecast]

class ItemForecast(BaseModel):
    item_id: str
    method_used: str                       # Which method produced this
    predictions: List[Prediction]

class Prediction(BaseModel):
    date: date
    point_forecast: float
    quantiles: Optional[Dict[str, float]]  # {"0.1": 98, "0.5": 125, "0.9": 152}

# Inventory Response (Minimal)
class InventoryCalculationResponse(BaseModel):
    calculation_id: UUID
    results: List[InventoryResult]

class InventoryResult(BaseModel):
    item_id: str
    days_of_inventory_remaining: float
    safety_stock: float
    reorder_point: float
    stockout_risk: str                     # "low"/"medium"/"high"
    recommended_action: str                # "OK"/"MONITOR"/"REORDER"/"URGENT"
```

## 2.3 Data Model Relationships

```
                 ┌─────────────────┐
                 │  forecast_runs  │
                 │                 │
                 │ forecast_run_id │◄──────────┐
                 │ client_id       │           │
                 │ user_id         │           │
                 │ primary_model   │           │
                 │ status          │           │
                 └────────┬────────┘           │
                          │                    │
                          │ 1:N                │
                          ▼                    │
                 ┌─────────────────┐           │
                 │forecast_results │           │
                 │                 │           │
                 │ result_id       │           │
                 │ forecast_run_id ├───────────┘
                 │ item_id         │
                 │ method          │  ⭐ Stores BOTH:
                 │ date            │     - chronos-2 predictions
                 │ point_forecast  │     - statistical_ma7 predictions
                 │ actual_value    │  (filled later for accuracy calc)
                 │                 │  ⭐ Enables future accuracy tracking
                 └─────────────────┘
```

## 2.4 What's NOT Needed for MVP

**Note**: We store BOTH method predictions in `forecast_results` (MVP), but the performance analysis table comes later (Phase 2).

| Excluded | Reason | Add In |
|----------|--------|--------|
| `forecast_method_performance` | Need history first (we're storing it now!) | Phase 2 |
| `inventory_calculations` | Calculate on-the-fly | Phase 2 |
| `data_quality_events` | Basic validation in MVP, monitoring in Phase 2 | Phase 2 |
| `forecast_feedback` | Need UI first | Phase 3 |
| `model_versions` | Single model initially | Phase 3 |
| `location_id` column | Single location MVP | Phase 2 |

---

# 3. Unified Documentation Summary

## 3.1 Terminology (Standardized)

| Term | Definition | Used In |
|------|------------|---------|
| **Forecast Run** | Single execution producing predictions | API, DB |
| **Method** | Algorithm used (chronos-2, statistical_ma7) | All |
| **Prediction Length** | Days ahead to forecast (default: 30) | API |
| **Point Forecast** | Main prediction value (p50/median) | Response |
| **Quantiles** | Prediction intervals (p10, p50, p90) | Response |
| **DIR** | Days of Inventory Remaining | Inventory |
| **ROP** | Reorder Point | Inventory |
| **MAPE** | Mean Absolute Percentage Error | Accuracy |

## 3.2 Industry Standard Formulas

All calculations use published standards:

### Forecast Accuracy (APICS/Statistical)
```
MAPE = (100/n) × Σ|Actual - Forecast| / Actual
MAE  = (1/n) × Σ|Actual - Forecast|
RMSE = √[(1/n) × Σ(Actual - Forecast)²]
Bias = (1/n) × Σ(Forecast - Actual)
```

### Inventory Calculations (APICS)
```
DIR = Current Stock / Avg Daily Demand
Safety Stock = Z × σ × √(Lead Time)    [Z = 1.65 for 95% service]
ROP = (Avg Daily Demand × Lead Time) + Safety Stock
Order Qty = Forecast Demand + Safety Stock - Current Stock
```

## 3.3 API Contracts (Unified)

### Endpoint 1: Pure Forecast

```
POST /api/v1/forecast

Request:
{
  "item_ids": ["SKU001", "SKU002"],
  "prediction_length": 30
}

Response:
{
  "forecast_id": "uuid",
  "forecasts": [{
    "item_id": "SKU001",
    "method_used": "chronos-2",
    "predictions": [
      {"date": "2024-01-02", "point_forecast": 125.5, "quantiles": {"0.1": 98, "0.5": 125, "0.9": 152}}
    ]
  }]
}
```

### Endpoint 2: Inventory Calculation

```
POST /api/v1/inventory/calculate

Request:
{
  "item_ids": ["SKU001"],
  "prediction_length": 30,
  "inventory_params": {
    "SKU001": {
      "current_stock": 500,
      "lead_time_days": 14,
      "safety_stock_days": 7
    }
  }
}

Response:
{
  "calculation_id": "uuid",
  "results": [{
    "item_id": "SKU001",
    "days_of_inventory_remaining": 4.0,
    "safety_stock": 878,
    "reorder_point": 2546,
    "stockout_risk": "high",
    "recommended_action": "URGENT_REORDER"
  }]
}
```

### Endpoint 3: Backfill Actuals (MVP - For Quality Testing)

```
POST /api/v1/forecasts/actuals

Request:
{
  "item_id": "SKU001",
  "actuals": [
    {"date": "2024-01-02", "actual_value": 130.0},
    {"date": "2024-01-03", "actual_value": 125.0}
  ]
}

Response:
{
  "updated_count": 2,
  "message": "Actuals backfilled successfully"
}
```

**Purpose:** Update `forecast_results.actual_value` so we can calculate quality metrics.

### Endpoint 4: View Quality Metrics (MVP - Simple Query)

```
GET /api/v1/forecasts/quality/{item_id}?start_date=2024-01-01&end_date=2024-01-31

Response:
{
  "item_id": "SKU001",
  "period": {"start": "2024-01-01", "end": "2024-01-31"},
  "methods": [
    {
      "method": "chronos-2",
      "predictions_count": 30,
      "actuals_count": 30,
      "mape": 8.2,
      "mae": 10.5,
      "rmse": 14.3
    },
    {
      "method": "statistical_ma7",
      "predictions_count": 30,
      "actuals_count": 30,
      "mape": 12.5,
      "mae": 15.2,
      "rmse": 19.8
    }
  ]
}
```

**Purpose:** Calculate and view MAPE/MAE/RMSE for both methods (MVP: simple calculation, Phase 2: automated tracking)

## 3.4 Data Flow (Single Diagram)

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           DATA FLOW OVERVIEW                              │
└──────────────────────────────────────────────────────────────────────────┘

    ┌────────────┐                              ┌────────────┐
    │   Shopify  │──────┐                ┌──────│    User    │
    │    API     │      │                │      │   (API)    │
    └────────────┘      │                │      └────────────┘
                        ▼                ▼
                 ┌─────────────────────────────┐
                 │       ETL Pipeline          │
                 │   (Airbyte/dbt/Custom)      │
                 └─────────────┬───────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         ts_demand_daily                                   │
│                    (Historical Sales Data)                                │
│                                                                          │
│    client_id | item_id | date | units_sold | promo_flag | holiday_flag   │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
              ┌───────────────────┴───────────────────┐
              │                                       │
              ▼                                       ▼
    ┌──────────────────┐                   ┌──────────────────┐
    │  AUTOMATIC CYCLE │                   │   MANUAL CYCLE   │
    │  (Every 7 Days)  │                   │  (API Request)   │
    │                  │                   │                  │
    │  Scheduler       │                   │  POST /forecast  │
    │  triggers all    │                   │  triggers        │
    │  active items    │                   │  specific items  │
    └────────┬─────────┘                   └────────┬─────────┘
             │                                      │
             └──────────────────┬───────────────────┘
                                │
                                ▼
                 ┌─────────────────────────────┐
                 │      ForecastService        │
                 │                             │
                 │  1. Fetch historical data  │
                 │  2. Run Chronos-2          │
                 │  3. Run MA7 baseline       │
                 │  4. Select best method     │
                 └─────────────┬───────────────┘
                 
                 Note: API input validation happens
                 automatically via Pydantic schemas
                               │
                               ▼
                 ┌─────────────────────────────┐
                 │       forecast_runs         │
                 │       forecast_results      │
                 │                             │
                 │  ⭐ Store BOTH methods:     │
                 │     - chronos-2 predictions │
                 │     - statistical_ma7       │
                 │                             │
                 │  Why? For future accuracy   │
                 │  tracking & comparison      │
                 └─────────────┬───────────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
    ┌──────────────────┐              ┌──────────────────┐
    │  API Response    │              │  Inventory Calc  │
    │  (Pure Forecast) │              │  (DIR, ROP, etc) │
    └──────────────────┘              └──────────────────┘
```

## 3.5 Implementation Checklist (Unified)

### Phase 1: MVP (Weeks 1-3)

- [x] Create database migration for `forecast_runs`, `forecast_results`
- [x] Implement `BaseForecastModel` interface
- [x] Implement `Chronos2Model` wrapper
- [x] Implement `MovingAverageModel` (7-day)
- [x] Implement `ForecastService` (orchestration)
- [x] Implement `InventoryCalculator` (formulas)
- [x] Implement `QualityCalculator` (MAPE/MAE/RMSE)
- [x] Create Pydantic schemas (request/response) - includes automatic validation
- [x] Create API endpoints (forecast, inventory, actuals, quality)
- [x] Add actuals backfill endpoint (for quality testing)
- [x] Add basic quality calculation (MAPE/MAE/RMSE)
- [x] Add authentication integration
- [ ] **Implement data access layer** (`_fetch_historical_data()` from ts_demand_daily)
- [ ] **Complete API response building** (fetch results from DB)
- [ ] Write unit tests
- [ ] Write integration tests

#### Data Validation (MVP)

**Automatic (via Pydantic):**
- ✅ API input validation (required fields, types, ranges) - happens automatically
- ✅ Request schema validation (item_ids not empty, prediction_length 1-365)

**Manual Checks Needed:**
- ✅ Missing data handling: If insufficient history (< 7 days), use statistical_ma7 fallback
- ✅ Error handling: If no data, return clear error message
- ✅ Error logging: Log forecast failures

**What We Defer (Phase 2+):**
- ❌ Data quality monitoring/alerts (Phase 2)
- ❌ Anomaly detection (Phase 2)
- ❌ Data drift detection (Phase 3)
- ❌ Automated data quality scoring (Phase 2)
- ❌ `data_quality_events` table (Phase 2)

### Phase 2: Enhancement (Weeks 4-6)

- [ ] Add performance tracking table (`forecast_method_performance`)
- [ ] **Enhance** accuracy calculation (automated, scheduled)
- [ ] **Enhance** MAPE/MAE/RMSE (full performance service)
- [ ] Add performance API endpoint (view metrics)
- [ ] Add additional statistical methods
- [ ] Add location_id support
- [ ] Add scheduler for automatic cycle

**Note:** MVP includes basic actuals backfill and manual quality calculation. Phase 2 adds automated tracking and performance service.

---

# 4. Executive Overview (Non-Technical)

## 4.1 What Does This System Do?

**In Simple Terms**: The forecasting system predicts how many units of each product will sell in the next 30 days, and tells you when to reorder inventory.

```
            TODAY                    30 DAYS FROM NOW
              │                            │
              ▼                            ▼
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Historical Sales ──────► PREDICTION ──────► Forecast   │
│     (Past)                   ↓                (Future)  │
│                              │                          │
│                              ▼                          │
│                    Inventory Decision                   │
│                    "Reorder 3000 units"                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## 4.2 How It Works (Simple Explanation)

1. **Collect**: System gathers your sales history from Shopify (stores)
2. **Learn**: AI model (Chronos-2) learns your sales patterns
3. **Predict**: System forecasts future demand for each product
4. **Calculate**: Using predictions, calculates when you'll run out of stock
5. **Recommend**: Tells you what to order and when

## 4.3 Key Features

| Feature | What It Does | Business Value |
|---------|--------------|----------------|
| **Demand Forecast** | Predicts daily sales | Plan inventory better |
| **Confidence Range** | Shows prediction uncertainty | Make informed decisions |
| **Stockout Alert** | Warns when you'll run out | Avoid lost sales |
| **Reorder Recommendation** | Suggests order quantities | Optimize purchasing |

## 4.4 Main Data Flows

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│   YOUR SHOPIFY STORE                                            │
│         │                                                       │
│         │  (Sales data flows in daily)                          │
│         ▼                                                       │
│   ┌─────────────┐                                               │
│   │   DATABASE  │ ◄──── Stores your sales history               │
│   └─────────────┘                                               │
│         │                                                       │
│         │  (Every 7 days, OR when you request)                  │
│         ▼                                                       │
│   ┌─────────────┐                                               │
│   │  AI MODEL   │ ◄──── Amazon Chronos-2 (proven technology)    │
│   └─────────────┘                                               │
│         │                                                       │
│         │  (Predictions generated)                              │
│         ▼                                                       │
│   ┌─────────────┐                                               │
│   │   RESULTS   │ ◄──── "SKU001: expect 125 units/day"          │
│   └─────────────┘       "SKU002: reorder in 5 days"             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 4.5 Business Goals Alignment

| Business Goal | How System Achieves It |
|---------------|------------------------|
| **Reduce Stockouts** | Predicts demand, alerts before you run out |
| **Reduce Overstock** | Right-sized order quantities, not guessing |
| **Save Time** | Automatic forecasts every 7 days |
| **Better Decisions** | Data-driven recommendations, not gut feelings |
| **Scalability** | Works for 10 items or 10,000 items |

## 4.6 Why Industry Standards Matter

**All our calculations use formulas from APICS** (Association for Supply Chain Management):

- **Safety Stock Formula**: Same as Fortune 500 companies use
- **Reorder Point**: Industry standard calculation
- **Accuracy Metrics**: MAPE, MAE, RMSE (universally recognized)

**Why this matters**: 
- We can explain every calculation to auditors
- Consistent with industry best practices
- Proven formulas, not experimental

## 4.7 MVP vs Future Evolution

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│   MVP (NOW)                    FUTURE                          │
│   ─────────                    ──────                          │
│                                                                │
│   • 1 AI Model                 • Multiple AI models            │
│   • 1 Baseline method          • 5+ comparison methods         │
│   • Basic accuracy             • Advanced performance tracking │
│   • Manual + Auto trigger      • Real-time forecasting         │
│   • Simple alerts              • Predictive analytics          │
│                                                                │
│   ────────────────────────►                                    │
│       GROW INCREMENTALLY                                       │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## 4.8 Feedback Loops

The system improves over time through:

### Automatic Feedback
```
1. We store all predictions
2. When actual sales come in, we compare
3. We calculate accuracy (MAPE)
4. System learns which method works best per product
```

### User Feedback (Future)
```
1. Users can correct forecasts
2. Users provide actual inventory counts
3. System adjusts recommendations
4. Continuous improvement
```

### Monitoring Signals
- **MAPE Tracking**: If accuracy drops below 30%, alert triggered
- **Data Quality**: If data is missing, system uses fallback method
- **Model Drift**: If patterns change, system adapts

---

## Summary

### What We Built (MVP)
- Simple, working forecasting system
- 2 methods: Chronos-2 (primary) + MA7 (baseline)
- 2 database tables: `forecast_runs` + `forecast_results`
- 2 API endpoints: `/forecast` + `/inventory/calculate`

### Why It Works
- Uses proven Amazon Chronos-2 model
- Industry-standard formulas (APICS)
- Stores everything for future analysis
- Easy to extend with more models

### Business Value
- Automated demand prediction
- Reduced stockouts
- Optimized inventory levels
- Data-driven decisions

### Evolution Path
- Phase 1: MVP (current)
- Phase 2: Performance tracking, more methods
- Phase 3: Advanced analytics, drift detection

---

## Quality Testing After MVP

**✅ What's Ready for Testing:**

1. **Storage**: Both method predictions stored in `forecast_results`
2. **Actuals Backfill**: API endpoint to update `actual_value` column
3. **Quality Calculation**: Simple function to calculate MAPE/MAE/RMSE
4. **Quality View**: API endpoint to view metrics for both methods
5. **Comparison**: Can compare chronos-2 vs statistical_ma7 accuracy

**Workflow After MVP:**
```
1. Generate forecasts (both methods stored)
2. Wait for actual sales data
3. Backfill actuals via API: POST /api/v1/forecasts/actuals
4. View quality metrics: GET /api/v1/forecasts/quality/{item_id}
5. Compare which method performed better
```

**What's Enhanced in Phase 2:**
- Automated actuals backfill (from ETL)
- Performance tracking table (aggregated metrics)
- Scheduled quality reports
- Historical trend analysis

---

**Document Status**: ✅ Ready for Implementation

**References**:
- Industry Standards: APICS SCOR Model
- Forecasting Model: Amazon Chronos-2
- Accuracy Metrics: MAPE, MAE, RMSE (Statistical Standards)


