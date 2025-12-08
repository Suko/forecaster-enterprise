# Forecasting Module Architecture

**Status:** ✅ Complete  
**Scope:** Full Architecture (MVP + Future Phases)  
**Quick Start:** See [MVP_UNIFIED.md](MVP_UNIFIED.md) for simplified MVP view

---

**Goal:** Scalable, maintainable, testable forecasting architecture

---

## ⚠️ Important: MVP vs Future Phases

**Current MVP Implementation:**
- ✅ `core/models/base.py` - BaseForecastModel interface
- ✅ `modes/ml/chronos2.py` - Chronos-2 model
- ✅ `modes/statistical/moving_average.py` - MA7 model
- ✅ `modes/factory.py` - ModelFactory
- ✅ `applications/inventory/calculator.py` - InventoryCalculator
- ✅ `services/forecast_service.py` - ForecastService
- ✅ `services/data_access.py` - DataAccess (database/test data)
- ✅ `services/quality_calculator.py` - QualityCalculator

**Future Phases (Not Yet Implemented):**
- ⏳ `features/` directory - Covariate preparation (Phase 2+)
- ⏳ `ForecastPipeline` - Core pipeline orchestration (Phase 2+)
- ⏳ `CovariateService` - Covariate service (Phase 2+)
- ⏳ Additional ML models (TimesFM, Moirai, etc.) (Phase 2+)

**Note:** This document describes the full architecture including future phases. For MVP implementation details, see [MVP_UNIFIED.md](MVP_UNIFIED.md).

---

## Architecture Overview

### Design Principles

1. **Layered Architecture**: Clear separation of concerns
2. **Dependency Inversion**: Higher layers depend on abstractions
3. **Single Responsibility**: Each module has one clear purpose
4. **Open/Closed**: Open for extension, closed for modification
5. **Testability**: Each layer can be tested independently

---

## Data Flow Diagram

### Overview

The forecasting system operates in two cycles:
1. **Automatic Cycle**: Scheduled every 7 days
2. **Manual Cycle**: User-requested via API

Both cycles follow the same data flow but are triggered differently.

### Complete Data Flow (ASCII Diagram)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES (ETL Layer)                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│   Shopify     │          │   CSV Upload  │          │  Other APIs   │
│   APIs        │          │   (Manual)    │          │  (Future)     │
│               │          │               │          │               │
│ - Orders      │          │ - Sales Data  │          │ - Marketing   │
│ - Products    │          │ - Inventory  │          │ - Weather     │
│ - Inventory   │          │ - Promotions │          │ - Holidays    │
│ - Promotions  │          │               │          │               │
└───────┬───────┘          └───────┬───────┘          └───────┬───────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │      ETL Pipeline            │
                    │  (dbt / Airbyte / Custom)    │
                    │                              │
                    │  - Transform & Normalize     │
                    │  - Generate Full Daily Series│
                    │  - Calculate Covariates      │
                    │  - Populate Dimensions       │
                    │                              │
                    │  Sync: Daily OR On-Demand    │
                    │  (Triggered by forecast req)  │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   ts_demand_daily            │
                    │   (PostgreSQL Table)         │
                    │                              │
                    │  Grain: (client_id,          │
                    │         item_id,             │
                    │         location_id,         │
                    │         date_local)          │
                    │                              │
                    │  Columns:                    │
                    │  - units_sold                │
                    │  - revenue                   │
                    │  - promotion_flag            │
                    │  - holiday_flag              │
                    │  - marketing_spend           │
                    │  - stock_on_hand_end         │
                    │  - ... (covariates)          │
                    └──────────────┬───────────────┘
                                   │
                                   │ Historical Data
                                   │ (Read Only)
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  CYCLE 1:         │    │  CYCLE 2:         │    │  Both Cycles      │
│  AUTOMATIC        │    │  MANUAL           │    │  Continue...      │
│  (Every 7 Days)   │    │  (User Request)   │    │                   │
└───────────────────┘    └───────────────────┘    └───────────────────┘
        │                          │                          │
        │                          │                          │
        │ Scheduled Job            │ API Request              │
        │ (Cron / Celery)          │ POST /api/v1/forecast   │
        │                          │                          │
        ▼                          ▼                          │
┌───────────────────┐    ┌───────────────────┐              │
│  Scheduler        │    │  FastAPI          │              │
│  Service          │    │  Endpoint         │              │
│                   │    │                   │              │
│  - Check last     │    │  - Authenticate   │              │
│    forecast date  │    │  - Validate       │              │
│  - Determine      │    │  - Extract        │              │
│    items to       │    │    item_ids       │              │
│    forecast       │    │  - Extract         │              │
│  - Trigger        │    │    params          │              │
│    forecast       │    │                   │              │
└─────────┬─────────┘    └─────────┬─────────┘              │
          │                        │                          │
          └────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   ForecastService            │
                    │   (Service Layer)            │
                    │                              │
                    │  - Fetch historical data     │
                    │  - Prepare covariates        │
                    │  - Select methods            │
                    │  - Orchestrate execution     │
                    └──────────────┬───────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Data Access Layer          │
                    │                              │
                    │  fetch_historical_sales()    │
                    │  - Query ts_demand_daily     │
                    │  - Filter by client_id       │
                    │  - Filter by item_ids        │
                    │  - Filter by date range      │
                    │  - Return DataFrame          │
                    └──────────────┬───────────────┘
                                   │
                                   │ Historical DataFrame
                                   │ (units_sold, covariates)
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Features Layer             │
                    │                              │
                    │  - Prepare covariates        │
                    │  - Transform data            │
                    │  - Validate features         │
                    │  - Format for models         │
                    └──────────────┬───────────────┘
                                   │
                                   │ Prepared Data
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Modes Layer                │
                    │   (Multiple Methods)         │
                    │                              │
                    │  ┌──────────┐  ┌──────────┐ │
                    │  │ Chronos-2│  │Statistical│ │
                    │  │ Model   │  │ MA7 Model │ │
                    │  └────┬─────┘  └────┬─────┘ │
                    │       │             │       │
                    │       └──────┬──────┘       │
                    │              │              │
                    │         Run All Methods     │
                    │         (Parallel)          │
                    └──────────────┬───────────────┘
                                   │
                                   │ Forecast Results
                                   │ (per method)
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Method Selection           │
                    │                              │
                    │  - Primary: chronos-2        │
                    │  - Fallback: statistical_ma7 │
                    │  - Select recommended        │
                    └──────────────┬───────────────┘
                                   │
                                   │ Selected Results
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Database Storage            │
                    │   (PostgreSQL)                │
                    │                              │
                    │  ┌──────────────────────┐   │
                    │  │ forecast_runs         │   │
                    │  │ - forecast_run_id    │   │
                    │  │ - client_id          │   │
                    │  │ - primary_model      │   │
                    │  │ - methods_run        │   │
                    │  │ - recommended_method │   │
                    │  │ - status             │   │
                    │  └──────────┬───────────┘   │
                    │             │                │
                    │             │ FK             │
                    │             ▼                │
                    │  ┌──────────────────────┐   │
                    │  │ forecast_results     │   │
                    │  │ - forecast_run_id    │   │
                    │  │ - item_id            │   │
                    │  │ - method             │   │
                    │  │ - date               │   │
                    │  │ - point_forecast     │   │
                    │  │ - p10, p50, p90      │   │
                    │  │ - (all methods)       │   │
                    │  └──────────────────────┘   │
                    └──────────────┬───────────────┘
                                   │
                                   │ Stored Results
                                   │
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
        ▼                          ▼                          ▼
┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐
│  Response         │    │  Inventory         │    │  Future:           │
│  (Pure Forecast)  │    │  Calculation       │    │  - Performance    │
│                   │    │  (Optional)        │    │    Analysis       │
│  - Return only    │    │                    │    │  - Method          │
│    recommended    │    │  - Calculate DIR   │    │    Comparison      │
│    method         │    │  - Calculate ROP   │    │  - Backfill        │
│  - Include        │    │  - Calculate       │    │    Actuals        │
│    baseline       │    │    Safety Stock    │    │                    │
│    summary        │    │  - Stockout Risk   │    │                    │
│                   │    │  - Recommendations│    │                    │
└───────────────────┘    └───────────────────┘    └───────────────────┘
        │                          │                          │
        └──────────────────────────┼──────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   API Response               │
                    │   (JSON)                     │
                    │                              │
                    │  - forecast_id               │
                    │  - forecasts[]               │
                    │    - item_id                │
                    │    - predictions[]           │
                    │    - accuracy_indicators     │
                    │    - inventory_metrics       │
                    │      (if requested)          │
                    └──────────────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────────┐
                    │   Frontend / Client         │
                    │   - Display forecasts      │
                    │   - Show inventory alerts   │
                    │   - Generate reports       │
                    └──────────────────────────────┘
```

### Data Source Details

#### Input Data: `ts_demand_daily`

**Source:** Populated by ETL pipeline from:
- **Shopify APIs**: Orders, products, inventory, promotions
- **CSV Uploads**: Manual data imports
- **Other Sources**: Marketing APIs, weather APIs, holiday calendars (future)

**ETL Process:**
1. **Ingestion**: Raw data → `raw.shopify_*` tables
2. **Staging**: Transform → `stg_*` tables
3. **Dimensions**: SCD2 dimensions (`item_dimension`, `location_dimension`)
4. **Fact Table**: Build `ts_demand_daily` with full daily series

**Key Requirements:**
- **Full Daily Series**: Must include zero-demand days for each `(client_id, item_id, location_id)`
- **Covariates**: Include promotion flags, holiday flags, marketing spend, etc.
- **Historical Range**: Typically 1-2 years of history for training

#### Output Data: Forecast Tables

**`forecast_runs`**: Execution metadata
- Tracks when forecast was run
- Which methods were executed
- Which method was recommended
- Status and error messages

**`forecast_results`**: Daily predictions
- One row per `(forecast_run_id, item_id, method, date)`
- Stores all methods (for future analysis)
- Includes quantiles (p10, p50, p90)
- Can be backfilled with actuals later

### Cycle Comparison

| Aspect | Automatic Cycle | Manual Cycle |
|--------|----------------|--------------|
| **Trigger** | Scheduled (every 7 days) | User API request |
| **Items** | All active items | User-specified items |
| **Parameters** | Default (30 days) | User-specified |
| **Storage** | Always stored | Always stored |
| **Response** | Optional (webhook/notification) | Immediate API response |
| **Use Case** | Regular updates | Ad-hoc analysis, what-if scenarios |

### Data Flow Summary

1. **Data Ingestion** (ETL Layer)
   - Sources → ETL Pipeline → `ts_demand_daily`

2. **Forecast Trigger** (Two Paths)
   - Automatic: Scheduler → ForecastService
   - Manual: API Request → ForecastService

3. **Data Preparation** (Service Layer)
   - Read from `ts_demand_daily`
   - Prepare covariates
   - Format for models

4. **Forecast Execution** (Modes Layer)
   - Run multiple methods (Chronos-2, Statistical)
   - Generate predictions

5. **Storage** (Database)
   - Store in `forecast_runs`
   - Store all methods in `forecast_results`

6. **Response** (API Layer)
   - Return recommended method
   - Include accuracy indicators
   - Optional: Inventory calculations

---

## Layer Structure

```
forecasting/
├── core/                    # Pure forecasting (no business logic)
│   └── models/              # Model abstractions (BaseForecastModel)
│       └── base.py          # BaseForecastModel interface
│
├── modes/                   # Forecasting methods/modes
│   ├── ml/                  # ML models
│   │   └── chronos2.py      # Chronos-2 model wrapper
│   ├── statistical/         # Statistical methods
│   │   └── moving_average.py  # MA7 model
│   └── factory.py           # ModelFactory
│
├── applications/            # Business applications
│   └── inventory/           # Inventory calculations
│       └── calculator.py    # InventoryCalculator (APICS formulas)
│
└── services/                # Service orchestration (NOT API routes)
    ├── forecast_service.py  # ForecastService (orchestration)
    ├── data_access.py       # DataAccess (database/test data)
    └── quality_calculator.py # QualityCalculator (MAPE/MAE/RMSE)
```

---

## Layer Details

### 1. Core Layer (`forecasting/core/`)

**Purpose:** Pure forecasting logic - no business rules, no features, no applications

**Responsibilities:**
- Model abstraction (`BaseForecastModel`)
- Forecasting pipeline orchestration
- Data validation (format, types, ranges)
- Core utilities (date handling, data conversion)

**Dependencies:** None (lowest layer)

**Structure:**
```
core/
├── __init__.py
├── models/
│   ├── __init__.py
│   └── base.py              # BaseForecastModel abstract class
├── pipelines/
│   ├── __init__.py
│   └── forecast_pipeline.py # Core forecasting pipeline
└── utils/
    ├── __init__.py
    ├── validation.py        # Data validation
    ├── date_utils.py        # Date handling
    └── data_conversion.py   # Data format conversion
```

**Key Classes:**
```python
# core/models/base.py
class BaseForecastModel(ABC):
    """Abstract base class for all forecasting models"""
    @abstractmethod
    async def predict(self, context_df, prediction_length, ...) -> pd.DataFrame:
        """Pure forecasting - no business logic"""
```

**Testing:**
- Unit tests for validation
- Unit tests for data conversion
- Integration tests for pipeline

---

### 2. Features Layer (`forecasting/features/`)

**Purpose:** Feature engineering, covariates, data transformations

**Responsibilities:**
- Covariate preparation (promo, holiday, marketing)
- Data transformations (scaling, normalization)
- Feature validation
- Feature selection

**Dependencies:** `core/` (uses core utilities)

**Structure:**
```
features/
├── __init__.py
├── covariates/
│   ├── __init__.py
│   ├── holiday.py           # Holiday calendar features
│   ├── promo.py             # Promotion features
│   ├── marketing.py         # Marketing spend features
│   └── calendar.py          # Calendar features (weekend, etc.)
├── transformers/
│   ├── __init__.py
│   ├── scaling.py           # Data scaling/normalization
│   └── aggregation.py       # Data aggregation
└── validators/
    ├── __init__.py
    └── feature_validator.py # Feature validation
```

**Key Classes:**
```python
# features/covariates/holiday.py
class HolidayCovariate:
    """Prepare holiday covariates"""
    def prepare_past_covariates(self, start_date, end_date) -> pd.DataFrame:
        """Prepare historical holiday flags"""
    
    def prepare_future_covariates(self, start_date, end_date) -> pd.DataFrame:
        """Prepare future holiday flags"""

# features/covariates/promo.py
class PromoCovariate:
    """Prepare promotion covariates"""
    # Similar structure
```

**Testing:**
- Unit tests for each covariate type
- Integration tests for covariate combination
- Validation tests

---

### 3. Modes Layer (`forecasting/modes/`)

**Purpose:** Different forecasting methods (ML models, statistical methods)

**Responsibilities:**
- Implement specific forecasting models
- Model initialization and management
- Model-specific configurations

**Dependencies:** `core/` (implements `BaseForecastModel`), `features/` (uses covariates)

**Structure:**
```
modes/
├── __init__.py
├── ml/
│   ├── __init__.py
│   ├── chronos2.py          # Chronos-2 implementation
│   ├── chronos_bolt.py      # Chronos-Bolt implementation
│   ├── timesfm.py           # TimesFM implementation (future)
│   └── moirai.py            # Moirai implementation (future)
├── statistical/
│   ├── __init__.py
│   ├── moving_average.py    # Moving average methods
│   ├── exponential.py       # Exponential smoothing
│   ├── naive.py             # Naive forecast
│   └── seasonal.py          # Seasonal methods (future)
└── factory.py               # Model factory
```

**Key Classes:**
```python
# modes/ml/chronos2.py
class Chronos2Model(BaseForecastModel):
    """Chronos-2 ML model implementation"""
    async def initialize(self):
        """Initialize Chronos-2 pipeline"""
    
    async def predict(self, context_df, prediction_length, ...):
        """Generate forecast using Chronos-2"""

# modes/statistical/moving_average.py
class MovingAverageModel(BaseForecastModel):
    """Moving average statistical method"""
    async def predict(self, context_df, prediction_length, ...):
        """Generate forecast using moving average"""
```

**Testing:**
- Unit tests for each model
- Mock tests (don't load actual models in unit tests)
- Integration tests with real models

---

### 4. Applications Layer (`forecasting/applications/`)

**Purpose:** Business applications that use forecasting

**Responsibilities:**
- Business logic (inventory calculations, profitability analysis)
- Domain-specific rules
- Application-specific metrics

**Dependencies:** `core/`, `modes/`, `features/` (uses all lower layers)

**Structure:**
```
applications/
├── __init__.py
├── inventory/
│   ├── __init__.py
│   ├── calculator.py        # Inventory calculations
│   ├── metrics.py           # Inventory metrics (DIR, ROP, etc.)
│   ├── recommendations.py  # Inventory recommendations
│   └── schemas.py          # Inventory-specific schemas
├── profitability/
│   ├── __init__.py
│   ├── calculator.py        # Profitability calculations (future)
│   └── metrics.py           # Profitability metrics (future)
└── demand/
    ├── __init__.py
    ├── planner.py           # Demand planning (future)
    └── optimizer.py         # Demand optimization (future)
```

**Key Classes:**
```python
# applications/inventory/calculator.py
class InventoryCalculator:
    """Calculate inventory metrics from forecasts"""
    def __init__(self, forecast_service: ForecastService):
        self.forecast_service = forecast_service
    
    async def calculate_metrics(
        self,
        item_id: str,
        forecast: ForecastResult,
        inventory_params: InventoryParams
    ) -> InventoryMetrics:
        """Calculate inventory metrics using industry standard formulas"""
        # Uses forecast from modes layer
        # Applies inventory formulas (industry standard)
        # Returns inventory metrics

# applications/inventory/metrics.py
class InventoryMetrics:
    """Industry standard inventory metrics"""
    def calculate_safety_stock(self, ...) -> float:
        """APICS standard formula"""
    
    def calculate_reorder_point(self, ...) -> float:
        """APICS standard formula"""
```

**Testing:**
- Unit tests for calculations
- Integration tests with forecast service
- Business logic tests

---

### 5. Service Orchestration (`forecasting/services/`)

**Purpose:** Service layer that orchestrates forecasting across all layers

**Responsibilities:**
- Service orchestration (combines all layers)
- Business logic coordination
- Error handling and logging

**Dependencies:** All layers (orchestrates everything)

**Note:** API routes and schemas are in the existing backend structure (`backend/api/` and `backend/schemas/`), not in the forecasting module.

**Structure:**
```
forecasting/
└── services/
    ├── __init__.py
    ├── forecast_service.py   # Forecast orchestration service
    └── inventory_service.py  # Inventory orchestration service
```

**Key Classes:**
```python
# forecasting/services/forecast_service.py
class ForecastService:
    """Orchestrates forecasting across all layers"""
    def __init__(
        self,
        model_factory: ModelFactory,      # modes layer
        covariate_service: CovariateService,  # features layer
        pipeline: ForecastPipeline        # core layer
    ):
        self.model_factory = model_factory
        self.covariate_service = covariate_service
        self.pipeline = pipeline
    
    async def generate_forecast(self, request: ForecastRequest):
        """Orchestrate forecast generation"""
        # 1. Validate request (core)
        # 2. Prepare covariates (features)
        # 3. Get model (modes)
        # 4. Generate forecast (core pipeline)
        # 5. Return result
```

**Integration with Backend:**
- API routes: `backend/api/forecast.py` (uses this service)
- Schemas: `backend/schemas/forecast.py` (Pydantic models)
- Service: `forecasting/services/forecast_service.py` (orchestration)

**Testing:**
- Service orchestration tests
- Integration tests (end-to-end)

---

## Dependency Flow

```
backend/api/forecast.py (API Routes - existing backend structure)
    ↓ depends on
forecasting/services/forecast_service.py (Service Orchestration)
    ↓ depends on
applications/ (Business Logic)
    ↓ depends on
modes/ (Forecasting Methods)
    ↓ depends on
features/ (Features & Covariates)
    ↓ depends on
core/ (Pure Forecasting)
```

**Key Rule:** Lower layers never depend on higher layers.

**Integration:** API routes and schemas are in existing `backend/api/` and `backend/schemas/`, not in forecasting module.

---

## Module Organization

### Directory Structure

```
backend/
├── forecasting/                    # Forecasting module
│   ├── __init__.py
│   │
│   ├── core/                       # Layer 1: Pure forecasting
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── base.py
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   └── forecast_pipeline.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validation.py
│   │       ├── date_utils.py
│   │       └── data_conversion.py
│   │
│   ├── features/                   # Layer 2: Features & covariates
│   │   ├── __init__.py
│   │   ├── covariates/
│   │   │   ├── __init__.py
│   │   │   ├── holiday.py
│   │   │   ├── promo.py
│   │   │   ├── marketing.py
│   │   │   └── calendar.py
│   │   ├── transformers/
│   │   │   ├── __init__.py
│   │   │   ├── scaling.py
│   │   │   └── aggregation.py
│   │   └── validators/
│   │       ├── __init__.py
│   │       └── feature_validator.py
│   │
│   ├── modes/                      # Layer 3: Forecasting methods
│   │   ├── __init__.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── chronos2.py
│   │   │   ├── chronos_bolt.py
│   │   │   └── timesfm.py
│   │   ├── statistical/
│   │   │   ├── __init__.py
│   │   │   ├── moving_average.py
│   │   │   ├── exponential.py
│   │   │   └── naive.py
│   │   └── factory.py
│   │
│   ├── applications/               # Layer 4: Business applications
│   │   ├── __init__.py
│   │   ├── inventory/
│   │   │   ├── __init__.py
│   │   │   ├── calculator.py
│   │   │   ├── metrics.py
│   │   │   ├── recommendations.py
│   │   │   └── schemas.py
│   │   └── profitability/
│   │       ├── __init__.py
│   │       └── calculator.py
│   │
│   └── services/                     # Service orchestration
│       ├── __init__.py
│       ├── forecast_service.py       # Forecast orchestration
│       └── inventory_service.py      # Inventory orchestration
│
└── ... (existing backend structure)
    ├── api/                          # API routes (existing)
    │   ├── auth.py                   # Existing auth routes
    │   └── forecast.py               # NEW: Forecast routes
    ├── schemas/                       # Schemas (existing)
    │   ├── auth.py                   # Existing auth schemas
    │   └── forecast.py               # NEW: Forecast schemas
    └── services/                      # Services (existing)
        ├── auth_service.py            # Existing auth service
        └── user_service.py            # Existing user service
│
└── ... (rest of backend)
```

---

## Implementation Strategy

### Phase 1: Core Layer (MVP)

**Goal:** Establish foundation

1. **Core Models**
   - [ ] `BaseForecastModel` abstract class
   - [ ] `ForecastPipeline` basic pipeline
   - [ ] Core utilities (validation, date utils)

2. **Testing**
   - [ ] Unit tests for core utilities
   - [ ] Integration tests for pipeline

### Phase 2: Features Layer

**Goal:** Add feature engineering

1. **Covariates**
   - [ ] Holiday covariate
   - [ ] Promo covariate
   - [ ] Calendar features (weekend, etc.)

2. **Testing**
   - [ ] Unit tests for each covariate
   - [ ] Integration tests for covariate combination

### Phase 3: Modes Layer

**Goal:** Add forecasting methods

1. **ML Models**
   - [ ] Chronos-2 implementation
   - [ ] Statistical MA7 implementation

2. **Testing**
   - [ ] Unit tests (mocked)
   - [ ] Integration tests (real models)

### Phase 4: Applications Layer

**Goal:** Add business applications

1. **Inventory Application**
   - [ ] Inventory calculator
   - [ ] Inventory metrics (industry standard formulas)
   - [ ] Recommendations

2. **Testing**
   - [ ] Unit tests for calculations
   - [ ] Integration tests with forecast service

### Phase 5: Interfaces Layer

**Goal:** Add API endpoints

1. **API Layer**
   - [ ] Forecast endpoint
   - [ ] Inventory calculation endpoint
   - [ ] Service orchestration

2. **Testing**
   - [ ] API endpoint tests
   - [ ] End-to-end tests

---

## Testing Strategy

### Test Structure

```
tests/
├── forecasting/
│   ├── core/
│   │   ├── test_models.py
│   │   ├── test_pipelines.py
│   │   └── test_utils.py
│   ├── features/
│   │   ├── test_covariates.py
│   │   └── test_transformers.py
│   ├── modes/
│   │   ├── test_ml_models.py
│   │   └── test_statistical.py
│   ├── applications/
│   │   └── test_inventory.py
│   └── interfaces/
│       ├── test_routes.py
│       └── test_services.py
```

### Testing Principles

1. **Unit Tests**: Test each module in isolation
2. **Integration Tests**: Test layer interactions
3. **Mock External Dependencies**: Don't load real ML models in unit tests
4. **Test Data**: Use fixtures for consistent test data

---

## Dependency Injection

### Service Registration

```python
# interfaces/services/__init__.py
def get_forecast_service() -> ForecastService:
    """Dependency injection for forecast service"""
    # Initialize all dependencies
    model_factory = ModelFactory()
    covariate_service = CovariateService()
    pipeline = ForecastPipeline()
    
    return ForecastService(
        model_factory=model_factory,
        covariate_service=covariate_service,
        pipeline=pipeline
    )
```

### FastAPI Integration

```python
# interfaces/routes/forecast.py
from forecasting.interfaces.services import get_forecast_service

@router.post("/api/v1/forecast")
async def create_forecast(
    request: ForecastRequest,
    service: ForecastService = Depends(get_forecast_service)
):
    """API endpoint"""
    return await service.generate_forecast(request)
```

---

## Data Flow Example

### Forecast Request Flow

```
1. API Request (backend/api/forecast.py) ← Existing backend structure
   ↓
2. Service Orchestration (forecasting/services/forecast_service.py)
   ↓
3. Feature Preparation (forecasting/features/covariates/)
   - Prepare holiday covariates
   - Prepare promo covariates
   ↓
4. Model Selection (forecasting/modes/factory.py)
   - Get Chronos-2 model
   ↓
5. Core Pipeline (forecasting/core/pipelines/forecast_pipeline.py)
   - Validate data
   - Run forecast
   ↓
6. Return Results
```

### Inventory Calculation Flow

```
1. API Request (backend/api/inventory.py) ← Existing backend structure
   ↓
2. Service Orchestration (forecasting/services/inventory_service.py)
   ↓
3. Generate Forecast (uses forecast_service)
   ↓
4. Inventory Calculator (forecasting/applications/inventory/calculator.py)
   - Calculate safety stock (industry standard)
   - Calculate reorder point (industry standard)
   - Calculate recommendations
   ↓
5. Return Results
```

---

## Extension Points

### Adding a New Model

1. Create model class in `modes/ml/` or `modes/statistical/`
2. Implement `BaseForecastModel` interface
3. Register in `modes/factory.py`
4. No changes needed in other layers

### Adding a New Covariate

1. Create covariate class in `features/covariates/`
2. Implement covariate interface
3. Register in covariate service
4. Use in feature preparation

### Adding a New Application

1. Create application directory in `applications/`
2. Implement application-specific logic
3. Create service in `forecasting/services/`
4. Create API routes in `backend/api/` (existing structure)
5. Create schemas in `backend/schemas/` (existing structure)
6. Register service in dependency injection

---

## Benefits of This Architecture

### ✅ Organization
- Clear separation of concerns
- Easy to find code
- Logical grouping

### ✅ Testability
- Each layer can be tested independently
- Mock dependencies easily
- Clear test boundaries

### ✅ Maintainability
- Changes isolated to specific layers
- Easy to understand dependencies
- Clear responsibilities

### ✅ Scalability
- Easy to add new models (modes layer)
- Easy to add new features (features layer)
- Easy to add new applications (applications layer)

### ✅ Reusability
- Core layer reusable across applications
- Features reusable across models
- Models reusable across applications

---

## Migration Path

### Integration with Existing Backend

**Existing Backend Structure:**
- `backend/api/` - API routes (auth.py)
- `backend/schemas/` - Pydantic schemas (auth.py)
- `backend/services/` - Business logic services (auth_service.py, user_service.py)

**Forecasting Module Integration:**
- `forecasting/` - Forecasting module (new)
- `backend/api/forecast.py` - Forecast API routes (new, follows existing pattern)
- `backend/schemas/forecast.py` - Forecast schemas (new, follows existing pattern)
- `forecasting/services/forecast_service.py` - Forecast orchestration (new)

**Integration Pattern:**
- API routes follow existing pattern in `backend/api/`
- Schemas follow existing pattern in `backend/schemas/`
- Forecasting services in `forecasting/services/` (module-specific)
- General services stay in `backend/services/`

---

## Next Steps

1. ✅ Review and approve architecture
2. ✅ Create directory structure
3. ✅ Start with Core layer (MVP)
4. ✅ Implement layer by layer
5. ✅ Add tests for each layer

---

## References

- **Layered Architecture Pattern**: https://en.wikipedia.org/wiki/Multitier_architecture
- **Dependency Inversion Principle**: SOLID principles
- **Clean Architecture**: Robert C. Martin's principles

