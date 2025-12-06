# Forecasting Function Plan

**Status:** Planning Phase  
**Target:** Implement Chronos-2 forecasting following best practices  
**Reference:** [Chronos-2 GitHub](https://github.com/amazon-science/chronos-forecasting)

---

## Current State

### Backend Architecture
- **FastAPI** with async/await throughout
- **Layered architecture**: API → Services → Models
- **Auth system** in place (JWT, user management)
- **PostgreSQL** database with async SQLAlchemy
- **No forecasting functionality yet**

### Existing Chronos Implementation (pluto)
- `chronos_integration.py` - ChronosService class
- Uses `Chronos2Pipeline.from_pretrained()`
- Supports covariates (promo, holiday, weekend, marketing)
- Uses `predict_df()` method with pandas DataFrames

---

## Design Principles

### 1. Follow Backend Architecture Patterns
- **API Layer** (`api/forecast.py`): Thin route handlers
- **Schemas** (`schemas/forecast.py`): Pydantic request/response models
- **Services** (`services/forecast_service.py`): Business logic
- **Models** (`models/forecast.py`): Database models (forecast runs, results)

### 2. Chronos-2 Best Practices
Based on [official documentation](https://github.com/amazon-science/chronos-forecasting):

- Use `Chronos2Pipeline.from_pretrained()` for model loading
- Use `predict_df()` method (not `predict()`) for DataFrame-based predictions
- Support both univariate and multivariate forecasting
- Support past and future covariates
- Return quantile forecasts (default: [0.1, 0.5, 0.9])
- Handle device mapping (cpu/cuda) via environment variables

### 3. Multi-Tenancy Considerations
- All forecasts scoped by `client_id` (from auth context)
- Data isolation per tenant
- Rate limiting per client
- Forecast storage per client

### 4. Data Format (from CHRONOS2_PAYLOAD_FORMAT.md)
- **Target**: Historical time series values (min 5, recommended 30+)
- **Past covariates**: Optional, must match target length
- **Future covariates**: Optional, must match prediction_length
- **Covariates are optional** - only include what you have
- Use numeric flags (0/1) instead of strings when possible

---

## Implementation Plan

### Phase 1: Core Forecasting Service

#### 1.1 Service Layer (`services/forecast_service.py`)

```python
class ForecastService:
    """Forecasting service using Chronos-2"""
    
    async def initialize_model(self):
        """Lazy load Chronos-2 model (singleton pattern)"""
        
    async def generate_forecast(
        self,
        client_id: UUID,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_df: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = [0.1, 0.5, 0.9],
        id_column: str = "id",
        timestamp_column: str = "timestamp",
        target: str = "target"
    ) -> pd.DataFrame:
        """Generate forecast using Chronos-2"""
        
    async def validate_input_data(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_df: Optional[pd.DataFrame] = None
    ) -> None:
        """Validate input data format"""
```

**Key Features:**
- Lazy model initialization (load on first use)
- Input validation (min length, data types, covariate alignment)
- Error handling with fallbacks
- Logging for debugging

#### 1.2 Data Preparation Utilities

```python
async def prepare_context_data(
    sales_data: List[Dict],
    item_id: str,
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """Prepare historical context data for Chronos-2"""
    # - Aggregate to daily level
    # - Fill missing dates with 0
    # - Add covariates if available
    # - Format: id, timestamp, target, [covariates]
    
async def prepare_future_covariates(
    prediction_length: int,
    start_date: datetime,
    covariates: Optional[Dict] = None
) -> Optional[pd.DataFrame]:
    """Prepare future covariates DataFrame"""
    # - Create date range for forecast period
    # - Add known future covariates (holidays, planned promos)
    # - Format: id, timestamp, [covariates] (NO target column)
```

### Phase 2: API Endpoints

#### 2.1 Schemas (`schemas/forecast.py`)

```python
class ForecastRequest(BaseModel):
    """Request schema for forecast endpoint"""
    item_ids: List[str]  # Items to forecast
    prediction_length: int = Field(ge=1, le=365)  # Days ahead
    quantile_levels: List[float] = [0.1, 0.5, 0.9]
    use_covariates: bool = True
    start_date: Optional[datetime] = None  # Cutoff date (default: today)
    
class ForecastResponse(BaseModel):
    """Response schema for forecast endpoint"""
    forecast_id: UUID
    item_id: str
    predictions: List[Dict]  # [{date, value, quantiles}]
    metadata: Dict
```

#### 2.2 API Routes (`api/forecast.py`)

```python
@router.post("/forecast", response_model=List[ForecastResponse])
async def create_forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate forecast for specified items"""
    # 1. Get client_id from current_user
    # 2. Fetch historical data from database
    # 3. Prepare context_df and future_df
    # 4. Call forecast_service.generate_forecast()
    # 5. Store results in database
    # 6. Return formatted response
```

**Endpoints:**
- `POST /api/v1/forecast` - Generate forecast (synchronous)
- `POST /api/v1/forecast-jobs` - Submit async forecast job
- `GET /api/v1/forecast-jobs/{job_id}` - Get job status/result
- `GET /api/v1/forecasts` - List historical forecasts
- `GET /api/v1/forecasts/{forecast_id}` - Get specific forecast

### Phase 3: Database Models

#### 3.1 Forecast Run Model (`models/forecast.py`)

```python
class ForecastRun(Base):
    """Forecast execution metadata"""
    __tablename__ = "forecast_runs"
    
    forecast_run_id: UUID = Column(UUID, primary_key=True)
    client_id: UUID = Column(UUID, ForeignKey("clients.client_id"), nullable=False)
    user_id: UUID = Column(UUID, ForeignKey("users.id"), nullable=False)
    model_name: str = Column(String, default="chronos-2")
    model_version: str = Column(String)
    prediction_length: int = Column(Integer)
    quantile_levels: List[float] = Column(JSON)
    status: str = Column(String)  # pending, completed, failed
    created_at: datetime = Column(DateTime(timezone=True))
    
class ForecastResult(Base):
    """Per-day forecast outputs"""
    __tablename__ = "forecast_results"
    
    result_id: UUID = Column(UUID, primary_key=True)
    forecast_run_id: UUID = Column(UUID, ForeignKey("forecast_runs.forecast_run_id"))
    item_id: str = Column(String)
    date: date = Column(Date)
    horizon_day: int = Column(Integer)  # 1, 2, 3, ...
    point_forecast: float = Column(Numeric)
    p10: Optional[float] = Column(Numeric)
    p50: Optional[float] = Column(Numeric)
    p90: Optional[float] = Column(Numeric)
```

**Note:** Database schema inspired by `DATA_MODELS_AUDIT.md` but simplified for MVP.

### Phase 4: Data Integration

#### 4.1 Historical Data Fetching

```python
async def fetch_historical_sales(
    db: AsyncSession,
    client_id: UUID,
    item_ids: List[str],
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """Fetch historical sales data from database"""
    # Query: SELECT date, item_id, units_sold, promo_flag, ...
    # FROM ts_demand_daily
    # WHERE client_id = ? AND item_id IN (?) AND date BETWEEN ? AND ?
    # Returns: DataFrame with columns needed for Chronos
```

**Data Source:**
- For MVP: Query from `ts_demand_daily` table (from DATA_MODELS_AUDIT.md)
- If table doesn't exist yet: Use placeholder/mock data
- Future: Integrate with ETL pipeline

#### 4.2 Covariate Preparation

```python
async def fetch_covariates(
    db: AsyncSession,
    client_id: UUID,
    start_date: datetime,
    end_date: datetime,
    future: bool = False
) -> pd.DataFrame:
    """Fetch covariates (promo, holiday, marketing)"""
    # Past covariates: historical data
    # Future covariates: planned events (promo calendar, holidays)
```

**Covariates to Support:**
- `promo_flag` (binary): From promo_calendar table
- `holiday_flag` (binary): From date_dimension or holiday API
- `is_weekend` (binary): Derived from date
- `marketing_spend_daily` (numeric): Optional, from marketing_metrics
- `price` (numeric): Optional, from pricing data

---

## Implementation Steps

### Step 1: Add Dependencies
```toml
# pyproject.toml
dependencies = [
    # ... existing dependencies
    "chronos-forecasting>=2.1.0",
    "pandas>=2.0.0",
    "numpy>=1.24.0",
]
```

### Step 2: Create Service Layer
- `services/forecast_service.py` - Core forecasting logic
- Model initialization (singleton pattern)
- Input validation
- Error handling

### Step 3: Create Schemas
- `schemas/forecast.py` - Request/response models
- Validation rules (prediction_length limits, quantile ranges)

### Step 4: Create API Routes
- `api/forecast.py` - Endpoint handlers
- Authentication required (get_current_user)
- Rate limiting per client

### Step 5: Database Models
- `models/forecast.py` - SQLAlchemy models
- Alembic migration for forecast tables

### Step 6: Data Integration
- Historical data fetching from database
- Covariate preparation
- Mock data for testing (if tables don't exist)

### Step 7: Testing
- Unit tests for service layer
- Integration tests for API endpoints
- Test with real Chronos-2 model

---

## Key Differences from pluto Implementation

### 1. Architecture
- **pluto**: Monolithic service class
- **forecaster_enterprise**: Layered architecture (API → Services → Models)

### 2. Data Source
- **pluto**: Direct database queries in service
- **forecaster_enterprise**: Service layer fetches data, API layer handles HTTP

### 3. Multi-Tenancy
- **pluto**: Single tenant (implicit)
- **forecaster_enterprise**: Explicit client_id from auth context

### 4. Error Handling
- **pluto**: Print statements and fallbacks
- **forecaster_enterprise**: Proper logging, structured errors, database tracking

### 5. Response Format
- **pluto**: Custom DataFrame format
- **forecaster_enterprise**: Standardized Pydantic models, stored in database

---

## Configuration

### Environment Variables
```bash
# Chronos Model Configuration
CHRONOS_MODEL_ID=amazon/chronos-2  # or chronos-bolt-* variants
CHRONOS_DEVICE=cpu  # or cuda
CHRONOS_BATCH_SIZE=256  # Optional

# Forecasting Limits
MAX_PREDICTION_LENGTH=365  # Max days to forecast
MIN_HISTORICAL_DATA=7  # Minimum days of history required
```

### Model Selection
- **Default**: `amazon/chronos-2` (120M parameters, best accuracy)
- **Fast**: `amazon/chronos-bolt-base` (205M, 250x faster)
- **Lightweight**: `amazon/chronos-bolt-tiny` (9M, fastest)

---

## Testing Strategy

### Unit Tests
- Service layer: Data preparation, validation
- Model initialization: Singleton pattern, error handling

### Integration Tests
- API endpoints: Authentication, rate limiting
- Database: Forecast storage and retrieval

### End-to-End Tests
- Full forecast workflow: Request → Data fetch → Forecast → Storage → Response

---

## Future Enhancements

1. **Async Job Processing**: Background tasks for long-running forecasts
2. **Forecast Evaluation**: Compare predictions vs actuals
3. **Model Comparison**: Support multiple models (Chronos, TimesFM, etc.)
4. **Covariate Engineering**: Automatic feature generation
5. **Forecast Overrides**: Manual adjustments to predictions
6. **Batch Forecasting**: Forecast multiple items efficiently

---

## References

- [Chronos-2 GitHub](https://github.com/amazon-science/chronos-forecasting)
- [Chronos-2 Payload Format](../ecommerce-agent/CHRONOS2_PAYLOAD_FORMAT.md)
- [Data Models Audit](../../forecaster/DATA_MODELS_AUDIT.md)
- [Forecasting API Requirements](../../planning/forecasting-api-requirements.md)
- [Existing Implementation](../ecommerce-agent/api/pluto/chronos_integration.py)

---

**Next Steps:**
1. Review and approve this plan
2. Define multi-tenancy level (per client_id from auth)
3. Start with Step 1: Add dependencies and create service layer

