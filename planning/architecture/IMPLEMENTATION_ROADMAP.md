# Implementation Roadmap

**Status:** Planning Phase  
**Goal:** Step-by-step implementation plan for forecasting module

---

## Phase 1: Core Layer (Foundation)

### Goal
Establish pure forecasting foundation with no business logic.

### Tasks

#### 1.1 Core Models
- [ ] Create `forecasting/core/models/base.py`
- [ ] Implement `BaseForecastModel` abstract class
- [ ] Define interface methods:
  - `initialize()`
  - `predict()`
  - `get_model_info()`
- [ ] Add type hints and docstrings

#### 1.2 Core Pipeline
- [ ] Create `forecasting/core/pipelines/forecast_pipeline.py`
- [ ] Implement basic forecasting pipeline
- [ ] Add data validation
- [ ] Add error handling

#### 1.3 Core Utils
- [ ] Create `forecasting/core/utils/validation.py`
  - Input data validation
  - Type checking
  - Range validation
- [ ] Create `forecasting/core/utils/date_utils.py`
  - Date range generation
  - Timezone handling
  - Date formatting
- [ ] Create `forecasting/core/utils/data_conversion.py`
  - DataFrame conversions
  - Format transformations

#### 1.4 Testing
- [ ] Unit tests for `BaseForecastModel` interface
- [ ] Unit tests for validation utils
- [ ] Unit tests for date utils
- [ ] Integration tests for pipeline

**Deliverable:** Core layer with abstract model interface and utilities

---

## Phase 2: Features Layer

### Goal
Add feature engineering and covariate preparation.

### Tasks

#### 2.1 Covariates
- [ ] Create `forecasting/features/covariates/holiday.py`
  - Holiday calendar integration
  - Past/future holiday flags
- [ ] Create `forecasting/features/covariates/promo.py`
  - Promotion flag preparation
  - Promo calendar integration
- [ ] Create `forecasting/features/covariates/marketing.py`
  - Marketing spend preparation
  - Marketing index calculation
- [ ] Create `forecasting/features/covariates/calendar.py`
  - Weekend flags
  - Day of week features
  - Month features

#### 2.2 Covariate Service
- [ ] Create `forecasting/features/covariates/__init__.py`
- [ ] Implement `CovariateService` to orchestrate all covariates
- [ ] Add covariate combination logic

#### 2.3 Transformers
- [ ] Create `forecasting/features/transformers/scaling.py`
  - Data scaling/normalization
- [ ] Create `forecasting/features/transformers/aggregation.py`
  - Data aggregation utilities

#### 2.4 Validators
- [ ] Create `forecasting/features/validators/feature_validator.py`
  - Covariate validation
  - Feature completeness checks

#### 2.5 Testing
- [ ] Unit tests for each covariate type
- [ ] Integration tests for covariate combination
- [ ] Validation tests

**Deliverable:** Feature engineering layer with all covariates

---

## Phase 3: Modes Layer

### Goal
Implement forecasting methods (ML and statistical).

### Tasks

#### 3.1 ML Models
- [ ] Create `forecasting/modes/ml/chronos2.py`
  - Implement `Chronos2Model(BaseForecastModel)`
  - Model initialization
  - Prediction logic
  - Error handling
- [ ] Create `forecasting/modes/ml/chronos_bolt.py`
  - Implement `ChronosBoltModel(BaseForecastModel)`
  - Similar structure to Chronos-2

#### 3.2 Statistical Methods
- [ ] Create `forecasting/modes/statistical/moving_average.py`
  - Implement `MovingAverageModel(BaseForecastModel)`
  - MA7, MA30 variants
- [ ] Create `forecasting/modes/statistical/exponential.py`
  - Implement `ExponentialSmoothingModel(BaseForecastModel)`
- [ ] Create `forecasting/modes/statistical/naive.py`
  - Implement `NaiveModel(BaseForecastModel)`

#### 3.3 Model Factory
- [ ] Create `forecasting/modes/factory.py`
  - Implement `ModelFactory`
  - Model registration
  - Model creation logic

#### 3.4 Testing
- [ ] Unit tests (mocked models)
- [ ] Integration tests (real models)
- [ ] Factory tests

**Deliverable:** Multiple forecasting methods (Chronos-2 + statistical)

---

## Phase 4: Applications Layer

### Goal
Add business applications (inventory, profitability).

### Tasks

#### 4.1 Inventory Application
- [ ] Create `forecasting/applications/inventory/calculator.py`
  - Implement `InventoryCalculator`
  - Industry standard formulas
- [ ] Create `forecasting/applications/inventory/metrics.py`
  - Safety stock calculation (APICS standard)
  - Reorder point calculation (APICS standard)
  - DIR calculation
  - Stockout risk calculation
- [ ] Create `forecasting/applications/inventory/recommendations.py`
  - Recommendation logic
  - Action prioritization
- [ ] Create `forecasting/applications/inventory/schemas.py`
  - Inventory-specific schemas

#### 4.2 Testing
- [ ] Unit tests for calculations
- [ ] Integration tests with forecast service
- [ ] Formula validation tests

**Deliverable:** Inventory calculation application

---

## Phase 5: Service Orchestration & API Integration

### Goal
Add service orchestration and integrate with existing backend API structure.

### Tasks

#### 5.1 Service Orchestration
- [ ] Create `forecasting/services/forecast_service.py`
  - Implement `ForecastService`
  - Orchestrate: features → modes → core
  - Error handling
  - Result formatting
- [ ] Create `forecasting/services/inventory_service.py`
  - Implement `InventoryService`
  - Orchestrate: forecast → inventory calculator
  - Recommendations

#### 5.2 Backend Integration - Schemas
- [ ] Create `backend/schemas/forecast.py` (follows existing pattern)
  - `ForecastRequest`
  - `ForecastResponse`
  - `ItemForecast`
- [ ] Create `backend/schemas/inventory.py` (follows existing pattern)
  - `InventoryCalculationRequest`
  - `InventoryCalculationResponse`
  - `InventoryMetrics`

#### 5.3 Backend Integration - API Routes
- [ ] Create `backend/api/forecast.py` (follows existing pattern)
  - `POST /api/v1/forecast` endpoint
  - Authentication (uses existing `get_current_user`)
  - Rate limiting (uses existing rate limiting)
- [ ] Create `backend/api/inventory.py` (follows existing pattern)
  - `POST /api/v1/inventory/calculate` endpoint
  - Authentication
  - Rate limiting

#### 5.4 Dependency Injection
- [ ] Create service registration (in `backend/api/forecast.py` or `backend/core/dependencies.py`)
- [ ] Integrate with FastAPI dependency injection
- [ ] Add routes to `main.py`

#### 5.5 Testing
- [ ] API endpoint tests (in `tests/test_api_forecast.py`)
- [ ] Service orchestration tests
- [ ] End-to-end tests

**Deliverable:** Complete API with endpoints integrated into existing backend structure

---

## Phase 6: Database Integration

### Goal
Store forecasts and results in database.

### Tasks

#### 6.1 Database Models
- [ ] Create `models/forecast.py`
  - `ForecastRun` model
  - `ForecastResult` model
  - `ForecastMethodPerformance` model

#### 6.2 Database Service
- [ ] Create `forecasting/interfaces/services/db_service.py`
  - Store forecast runs
  - Store forecast results
  - Query historical forecasts

#### 6.3 Integration
- [ ] Integrate with forecast service
- [ ] Store all method results
- [ ] Store actuals when available

#### 6.4 Testing
- [ ] Database model tests
- [ ] Storage/retrieval tests

**Deliverable:** Database-backed forecast storage

---

## Implementation Checklist

### Phase 1: Core ✅
- [ ] Core models
- [ ] Core pipeline
- [ ] Core utils
- [ ] Tests

### Phase 2: Features
- [ ] Covariates
- [ ] Transformers
- [ ] Validators
- [ ] Tests

### Phase 3: Modes
- [ ] ML models
- [ ] Statistical methods
- [ ] Factory
- [ ] Tests

### Phase 4: Applications
- [ ] Inventory calculator
- [ ] Inventory metrics
- [ ] Recommendations
- [ ] Tests

### Phase 5: Interfaces
- [ ] Schemas
- [ ] Services
- [ ] Routes
- [ ] Tests

### Phase 6: Database
- [ ] Models
- [ ] Database service
- [ ] Integration
- [ ] Tests

---

## Success Criteria

### Phase 1 Complete
- ✅ Core layer implemented
- ✅ Abstract model interface defined
- ✅ Utilities available
- ✅ Tests passing

### Phase 2 Complete
- ✅ All covariates implemented
- ✅ Feature service working
- ✅ Tests passing

### Phase 3 Complete
- ✅ Chronos-2 model working
- ✅ Statistical methods working
- ✅ Factory working
- ✅ Tests passing

### Phase 4 Complete
- ✅ Inventory calculations working
- ✅ Industry standard formulas implemented
- ✅ Tests passing

### Phase 5 Complete
- ✅ Service orchestration working
- ✅ API endpoints integrated into existing backend
- ✅ Schemas follow existing backend pattern
- ✅ End-to-end tests passing

### Phase 6 Complete
- ✅ Database storage working
- ✅ Historical data queryable
- ✅ Tests passing

---

## Timeline Estimate

- **Phase 1 (Core):** 1-2 weeks
- **Phase 2 (Features):** 1 week
- **Phase 3 (Modes):** 2-3 weeks
- **Phase 4 (Applications):** 1-2 weeks
- **Phase 5 (Interfaces):** 1-2 weeks
- **Phase 6 (Database):** 1 week

**Total MVP:** 7-11 weeks

---

## Next Steps

1. ✅ Review architecture
2. ✅ Create directory structure
3. ⏳ Start Phase 1: Core layer implementation

