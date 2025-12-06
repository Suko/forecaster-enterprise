# Forecasting API Design - Multi-Model Architecture

**Status:** Design Phase  
**Goal:** Flexible API supporting multiple forecasting models with pure forecast and inventory calculation endpoints

---

## Architecture Overview

### Core Design Principles

1. **Model Abstraction**: Support multiple forecasting models (Chronos-2, TimesFM, Moirai, etc.) via strategy pattern
2. **Two Endpoint Types**: 
   - **Pure Forecast**: Time series forecasting only
   - **Inventory Calculation**: Forecast + inventory metrics + fallback equations
3. **Fallback Strategy**: When ML models fail or insufficient data, use standard inventory equations
4. **Model Selection**: Configurable via query parameter or request body

---

## API Endpoints Design

### 1. Pure Forecast Endpoint

**Endpoint:** `POST /api/v1/forecast`

**Purpose:** Generate time series forecasts using specified model

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string (enum) | No | Model identifier (default: `chronos-2`) |

**Supported Models:**
- `chronos-2` - Amazon Chronos-2 (default, best accuracy)
- `chronos-bolt-base` - Chronos-Bolt (faster, good accuracy)
- `chronos-bolt-small` - Chronos-Bolt (lightweight)
- `timesfm` - Google TimesFM (future)
- `moirai` - Salesforce Moirai (future)
- `statistical` - Statistical fallback (moving average, exponential smoothing)

#### Request Body
```json
{
  "item_ids": ["SKU001", "SKU002"],
  "prediction_length": 30,
  "quantile_levels": [0.1, 0.5, 0.9],
  "use_covariates": true,
  "start_date": "2024-01-01T00:00:00Z",
  "model_config": {
    "model": "chronos-2",
    "device": "cpu",
    "batch_size": 256
  }
}
```

#### Response
```json
{
  "forecast_id": "uuid",
  "primary_model": "chronos-2",
  "recommended_model": "chronos-2",
  "all_methods_run": true,
  "forecasts": [
    {
      "item_id": "SKU001",
      "results": {
        "chronos-2": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 125.5,
              "quantiles": {
                "0.1": 98.2,
                "0.5": 125.5,
                "0.9": 152.8
              }
            }
          ],
          "status": "success",
          "metadata": {
            "historical_data_points": 90,
            "covariates_used": ["promo_flag", "holiday_flag"],
            "confidence": "high"
          }
        },
        "statistical_ma7": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 118.3
            }
          ],
          "status": "success",
          "method": "moving_average_7d"
        },
        "statistical_ma30": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 122.1
            }
          ],
          "status": "success",
          "method": "moving_average_30d"
        },
        "statistical_exponential": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 120.8
            }
          ],
          "status": "success",
          "method": "exponential_smoothing"
        },
        "naive": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 127.0
            }
          ],
          "status": "success",
          "method": "naive_forecast"
        }
      },
      "recommended_method": "chronos-2",
      "recommendation_reason": "Highest historical accuracy (MAPE: 8.2%)"
    }
  ]
}
```

---

### 2. Inventory Calculation Endpoint

**Endpoint:** `POST /api/v1/inventory/calculate`

**Purpose:** Generate forecast + inventory metrics + recommendations with fallback to standard equations

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string (enum) | No | Model identifier (default: `chronos-2`) |
| `fallback_strategy` | string (enum) | No | Fallback method (default: `statistical`) |

**Fallback Strategies:**
- `statistical` - Moving average, exponential smoothing
- `simple_average` - Simple average of historical data
- `seasonal_average` - Seasonal patterns (weekly/monthly)
- `zero` - Return zero forecast (last resort)

#### Request Body
```json
{
  "item_ids": ["SKU001", "SKU002"],
  "prediction_length": 30,
  "inventory_params": {
    "current_stock": 500,
    "lead_time_days": 14,
    "safety_stock_days": 7,
    "reorder_point": 200,
    "moq": 100,
    "service_level": 0.95
  },
  "forecast_params": {
    "quantile_levels": [0.1, 0.5, 0.9],
    "use_covariates": true
  },
  "model_config": {
    "model": "chronos-2",
    "fallback_enabled": true,
    "fallback_strategy": "statistical"
  }
}
```

#### Response
```json
{
  "calculation_id": "uuid",
  "primary_model": "chronos-2",
  "recommended_model": "chronos-2",
  "all_methods_run": true,
  "results": [
    {
      "item_id": "SKU001",
      "forecast_results": {
        "chronos-2": {
          "predictions": [
            {
              "date": "2024-01-02",
              "point_forecast": 125.5,
              "quantiles": {
                "0.1": 98.2,
                "0.5": 125.5,
                "0.9": 152.8
              }
            }
          ],
          "total_forecast_30d": 3765.0,
          "avg_daily_demand": 125.5,
          "status": "success"
        },
        "statistical_ma7": {
          "predictions": [...],
          "total_forecast_30d": 3549.0,
          "avg_daily_demand": 118.3,
          "status": "success"
        },
        "statistical_ma30": {
          "predictions": [...],
          "total_forecast_30d": 3663.0,
          "avg_daily_demand": 122.1,
          "status": "success"
        }
      },
      "inventory_metrics": {
        "current_stock": 500,
        "days_of_inventory_remaining": 3.98,
        "safety_stock": 878.5,
        "reorder_point": 2546.0,
        "recommended_order_quantity": 3044.5,
        "stockout_risk": "high",
        "stockout_date": "2024-01-05",
        "days_until_reorder": -10.2,
        "calculated_from": "chronos-2"
      },
      "inventory_metrics_all_methods": {
        "chronos-2": {
          "days_of_inventory_remaining": 3.98,
          "recommended_order_quantity": 3044.5,
          "stockout_date": "2024-01-05"
        },
        "statistical_ma7": {
          "days_of_inventory_remaining": 4.23,
          "recommended_order_quantity": 2927.0,
          "stockout_date": "2024-01-06"
        },
        "statistical_ma30": {
          "days_of_inventory_remaining": 4.09,
          "recommended_order_quantity": 3041.0,
          "stockout_date": "2024-01-05"
        }
      },
      "recommendations": {
        "action": "URGENT_REORDER",
        "priority": "critical",
        "message": "Stockout expected in 4 days. Reorder immediately.",
        "suggested_order_date": "2024-01-01",
        "suggested_order_quantity": 3044,
        "based_on_method": "chronos-2"
      },
      "calculation_method": {
        "forecast_method": "chronos-2",
        "inventory_method": "standard_equations",
        "recommended_method": "chronos-2",
        "all_methods_available": true
      }
    }
  ]
}
```

---

## Model Abstraction Layer

### Strategy Pattern Implementation

```python
# services/models/base_forecast_model.py
class BaseForecastModel(ABC):
    """Base interface for all forecasting models"""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize model (lazy loading)"""
        
    @abstractmethod
    async def predict(
        self,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_df: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = [0.1, 0.5, 0.9]
    ) -> pd.DataFrame:
        """Generate forecast"""
        
    @abstractmethod
    def get_model_info(self) -> Dict:
        """Get model metadata"""

# services/models/chronos_model.py
class Chronos2Model(BaseForecastModel):
    """Chronos-2 implementation"""
    
# services/models/statistical_model.py
class StatisticalModel(BaseForecastModel):
    """Statistical fallback (moving average, exponential smoothing)"""
    
# services/models/model_factory.py
class ModelFactory:
    """Factory for creating model instances"""
    
    @staticmethod
    def create_model(model_id: str) -> BaseForecastModel:
        """Create model instance based on model_id"""
        models = {
            "chronos-2": Chronos2Model,
            "chronos-bolt-base": ChronosBoltModel,
            "statistical": StatisticalModel,
            # ... more models
        }
        return models[model_id]()
```

---

## Inventory Calculation Service

### Standard Inventory Equations

#### 1. Days of Inventory Remaining (DIR)
```
DIR = Current Stock / Average Daily Demand
```

#### 2. Safety Stock
```
Safety Stock = (Z-score × Standard Deviation of Demand × √Lead Time) 
             + (Average Daily Demand × Safety Stock Days)
```
Where:
- Z-score based on service level (95% = 1.65)
- Safety Stock Days = buffer days (default: 7)

#### 3. Reorder Point (ROP)
```
ROP = (Average Daily Demand × Lead Time) + Safety Stock
```

#### 4. Recommended Order Quantity
```
Recommended Qty = (Forecasted Demand × Prediction Length) 
                + Safety Stock 
                - Current Stock
                
# Apply MOQ constraint
If Recommended Qty < MOQ:
    Recommended Qty = MOQ
```

#### 5. Stockout Risk Calculation
```
Stockout Risk = (Forecasted Demand / Current Stock) × 100

Risk Levels:
- Low: < 50%
- Medium: 50-70%
- High: 70-90%
- Critical: > 90%
```

#### 6. Stockout Date Prediction
```
Stockout Date = Today + (Current Stock / Average Daily Demand)
```

---

## Multi-Model Strategy (Always Return All Methods)

### Design Philosophy

Instead of using fallback only when primary model fails, **always run all available methods** and return all results. This enables:

1. **Historical Performance Tracking**: Compare which methods performed better over time
2. **Model Selection**: Data-driven decision on which model to use
3. **Confidence Building**: Multiple predictions provide confidence intervals
4. **A/B Testing**: Test different models on same data
5. **Risk Mitigation**: If one model fails, others are available

### Always-Run Methods

#### 1. Primary Model (User Selected)
- `chronos-2` (default)
- `chronos-bolt-base`
- `timesfm`
- `moirai`
- etc.

#### 2. Statistical Methods (Always Run)
```python
# Moving Average (7-day window)
avg_daily_demand_ma7 = sum(last_7_days) / 7

# Moving Average (30-day window)
avg_daily_demand_ma30 = sum(last_30_days) / 30

# Exponential Smoothing
forecast_es = alpha * last_value + (1 - alpha) * previous_forecast

# Simple Average
avg_daily_demand_simple = sum(all_historical) / len(all_historical)
```

#### 3. Seasonal Methods (If Data Available)
```python
# Weekly Seasonal Average
if day_of_week == "Monday":
    forecast_seasonal = historical_monday_average
# ... etc

# Monthly Seasonal Average
if month == "December":
    forecast_seasonal = historical_december_average
```

#### 4. Baseline Methods (Always Run)
```python
# Naive Forecast (last value)
forecast_naive = last_historical_value

# Zero Forecast (for new items)
forecast_zero = 0
```

### Response Structure (All Methods)

All endpoints return results from **all methods**, not just the primary model:

```json
{
  "forecast_id": "uuid",
  "primary_model": "chronos-2",
  "results": {
    "chronos-2": {
      "predictions": [...],
      "status": "success",
      "confidence": "high",
      "metadata": {...}
    },
    "statistical_ma7": {
      "predictions": [...],
      "status": "success",
      "method": "moving_average_7d"
    },
    "statistical_ma30": {
      "predictions": [...],
      "status": "success",
      "method": "moving_average_30d"
    },
    "statistical_exponential": {
      "predictions": [...],
      "status": "success",
      "method": "exponential_smoothing"
    },
    "statistical_simple": {
      "predictions": [...],
      "status": "success",
      "method": "simple_average"
    },
    "naive": {
      "predictions": [...],
      "status": "success",
      "method": "naive_forecast"
    }
  },
  "recommended_model": "chronos-2",
  "recommendation_reason": "Highest historical accuracy for this item type"
}
```

### Performance Tracking

All forecast results are stored in the database with method identification:

```sql
-- forecast_results table
CREATE TABLE forecast_results (
    result_id UUID PRIMARY KEY,
    forecast_run_id UUID,
    item_id VARCHAR,
    date DATE,
    method VARCHAR,  -- 'chronos-2', 'statistical_ma7', etc.
    prediction_value NUMERIC,
    actual_value NUMERIC,  -- Filled later when actuals are available
    error NUMERIC,  -- |prediction - actual|
    created_at TIMESTAMP
);

-- forecast_method_performance table
CREATE TABLE forecast_method_performance (
    performance_id UUID PRIMARY KEY,
    item_id VARCHAR,
    method VARCHAR,
    period_start DATE,
    period_end DATE,
    mape NUMERIC,  -- Mean Absolute Percentage Error
    mae NUMERIC,  -- Mean Absolute Error
    rmse NUMERIC,  -- Root Mean Squared Error
    total_predictions INTEGER,
    successful_predictions INTEGER,
    updated_at TIMESTAMP
);
```

### Historical Performance Analysis

Service to analyze which methods performed better:

```python
# services/forecast_performance_service.py
class ForecastPerformanceService:
    """Analyze historical performance of different forecasting methods"""
    
    async def get_method_performance(
        self,
        item_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Dict]:
        """Get performance metrics for all methods"""
        # Query forecast_results with actuals
        # Calculate MAPE, MAE, RMSE per method
        # Return ranked list
        
    async def get_recommended_method(
        self,
        item_id: str
    ) -> str:
        """Get recommended method based on historical performance"""
        # Analyze last 30-90 days
        # Return method with lowest MAPE/MAE
        # Consider: data availability, item characteristics
```

### Fallback Strategy (When Primary Fails)

Even though we always run all methods, we still need fallback logic:

1. **Primary Model Fails**: Use statistical methods as primary recommendation
2. **All Methods Fail**: Return error with diagnostic information
3. **Insufficient Data**: Only statistical methods run (skip ML models)

---

## Service Layer Architecture

### Forecast Service

```python
# services/forecast_service.py
class ForecastService:
    """Main forecasting service with model abstraction"""
    
    def __init__(self):
        self.model_factory = ModelFactory()
        self.models: Dict[str, BaseForecastModel] = {}
    
    async def get_model(self, model_id: str) -> BaseForecastModel:
        """Get or initialize model instance"""
        if model_id not in self.models:
            model = self.model_factory.create_model(model_id)
            await model.initialize()
            self.models[model_id] = model
        return self.models[model_id]
    
    async def generate_forecast_all_methods(
        self,
        primary_model_id: str,
        context_df: pd.DataFrame,
        prediction_length: int,
        future_df: Optional[pd.DataFrame] = None,
        quantile_levels: List[float] = [0.1, 0.5, 0.9],
        include_statistical: bool = True
    ) -> Dict:
        """Generate forecast using ALL methods (primary + statistical)"""
        results = {}
        
        # 1. Run primary model
        try:
            primary_model = await self.get_model(primary_model_id)
            primary_result = await primary_model.predict(
                context_df, prediction_length, future_df, quantile_levels
            )
            results[primary_model_id] = {
                "predictions": primary_result,
                "status": "success",
                "is_primary": True
            }
        except Exception as e:
            results[primary_model_id] = {
                "predictions": None,
                "status": "failed",
                "error": str(e),
                "is_primary": True
            }
        
        # 2. Always run statistical methods
        if include_statistical:
            statistical_methods = [
                "statistical_ma7",
                "statistical_ma30",
                "statistical_exponential",
                "statistical_simple",
                "naive"
            ]
            
            for method_id in statistical_methods:
                try:
                    method_model = await self.get_model(method_id)
                    method_result = await method_model.predict(
                        context_df, prediction_length, None, quantile_levels
                    )
                    results[method_id] = {
                        "predictions": method_result,
                        "status": "success",
                        "is_primary": False
                    }
                except Exception as e:
                    results[method_id] = {
                        "predictions": None,
                        "status": "failed",
                        "error": str(e),
                        "is_primary": False
                    }
        
        # 3. Get recommended method (based on historical performance)
        recommended_method = await self._get_recommended_method(
            context_df.get("item_id", "unknown"),
            results
        )
        
        return {
            "primary_model": primary_model_id,
            "results": results,
            "recommended_model": recommended_method,
            "all_methods_run": True
        }
    
    async def _get_recommended_method(
        self,
        item_id: str,
        results: Dict
    ) -> str:
        """Get recommended method based on historical performance"""
        # Check historical performance for this item
        performance_service = ForecastPerformanceService()
        historical_performance = await performance_service.get_method_performance(
            item_id, 
            start_date=datetime.now() - timedelta(days=90),
            end_date=datetime.now()
        )
        
        # If we have historical data, use best performing method
        if historical_performance:
            best_method = min(
                historical_performance.items(),
                key=lambda x: x[1].get("mape", float("inf"))
            )[0]
            # Only recommend if it's available in current results
            if best_method in results and results[best_method]["status"] == "success":
                return best_method
        
        # Otherwise, use primary model if successful
        for method_id, result in results.items():
            if result.get("is_primary") and result["status"] == "success":
                return method_id
        
        # Fallback to first successful method
        for method_id, result in results.items():
            if result["status"] == "success":
                return method_id
        
        return "none"
```

### Inventory Calculation Service

```python
# services/inventory_calculation_service.py
class InventoryCalculationService:
    """Service for inventory calculations with forecast integration"""
    
    def __init__(self, forecast_service: ForecastService):
        self.forecast_service = forecast_service
    
    async def calculate_inventory_metrics(
        self,
        item_id: str,
        forecast_result: Dict,
        inventory_params: Dict
    ) -> Dict:
        """Calculate inventory metrics from forecast"""
        
        # Extract forecast data
        avg_daily_demand = forecast_result["avg_daily_demand"]
        total_forecast = forecast_result["total_forecast"]
        
        # Calculate metrics using standard equations
        dir_value = inventory_params["current_stock"] / avg_daily_demand
        safety_stock = self._calculate_safety_stock(
            avg_daily_demand,
            inventory_params["safety_stock_days"],
            inventory_params.get("service_level", 0.95)
        )
        reorder_point = self._calculate_reorder_point(
            avg_daily_demand,
            inventory_params["lead_time_days"],
            safety_stock
        )
        recommended_qty = self._calculate_recommended_order(
            total_forecast,
            safety_stock,
            inventory_params["current_stock"],
            inventory_params.get("moq", 0)
        )
        stockout_risk = self._calculate_stockout_risk(
            total_forecast,
            inventory_params["current_stock"]
        )
        stockout_date = self._calculate_stockout_date(
            inventory_params["current_stock"],
            avg_daily_demand
        )
        
        return {
            "days_of_inventory_remaining": dir_value,
            "safety_stock": safety_stock,
            "reorder_point": reorder_point,
            "recommended_order_quantity": recommended_qty,
            "stockout_risk": stockout_risk,
            "stockout_date": stockout_date
        }
    
    def _calculate_safety_stock(
        self,
        avg_daily_demand: float,
        safety_stock_days: int,
        service_level: float
    ) -> float:
        """Calculate safety stock using standard formula"""
        z_score = self._get_z_score(service_level)
        # Simplified: use average demand * safety days
        # Full version would use demand variance
        return avg_daily_demand * safety_stock_days * (1 + z_score * 0.2)
    
    def _calculate_reorder_point(
        self,
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: float
    ) -> float:
        """Calculate reorder point"""
        return (avg_daily_demand * lead_time_days) + safety_stock
    
    def _calculate_recommended_order(
        self,
        forecasted_demand: float,
        safety_stock: float,
        current_stock: float,
        moq: int
    ) -> float:
        """Calculate recommended order quantity"""
        recommended = forecasted_demand + safety_stock - current_stock
        return max(recommended, moq) if moq > 0 else max(recommended, 0)
    
    def _calculate_stockout_risk(
        self,
        forecasted_demand: float,
        current_stock: float
    ) -> str:
        """Calculate stockout risk level"""
        if current_stock <= 0:
            return "critical"
        risk_pct = (forecasted_demand / current_stock) * 100
        if risk_pct > 90:
            return "critical"
        elif risk_pct > 70:
            return "high"
        elif risk_pct > 50:
            return "medium"
        return "low"
    
    def _calculate_stockout_date(
        self,
        current_stock: float,
        avg_daily_demand: float
    ) -> Optional[str]:
        """Calculate predicted stockout date"""
        if avg_daily_demand <= 0:
            return None
        days_until_stockout = current_stock / avg_daily_demand
        stockout_date = datetime.now() + timedelta(days=int(days_until_stockout))
        return stockout_date.isoformat()
    
    def _get_z_score(self, service_level: float) -> float:
        """Get Z-score for service level"""
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33
        }
        return z_scores.get(service_level, 1.65)
```

---

## Database Models for Multi-Method Storage

### Forecast Run Model

```python
# models/forecast.py
class ForecastRun(Base):
    """Forecast execution metadata"""
    __tablename__ = "forecast_runs"
    
    forecast_run_id: UUID = Column(UUID, primary_key=True)
    client_id: UUID = Column(UUID, ForeignKey("clients.client_id"), nullable=False)
    user_id: UUID = Column(UUID, ForeignKey("users.id"), nullable=False)
    primary_model: str = Column(String, default="chronos-2")
    prediction_length: int = Column(Integer)
    quantile_levels: List[float] = Column(JSON)
    methods_run: List[str] = Column(JSON)  # All methods that were executed
    recommended_method: str = Column(String)  # Best method based on history
    status: str = Column(String)  # pending, completed, failed
    created_at: datetime = Column(DateTime(timezone=True))
```

### Forecast Result Model (Per Method)

```python
class ForecastResult(Base):
    """Per-day forecast outputs - ONE ROW PER METHOD"""
    __tablename__ = "forecast_results"
    
    result_id: UUID = Column(UUID, primary_key=True)
    forecast_run_id: UUID = Column(UUID, ForeignKey("forecast_runs.forecast_run_id"))
    item_id: str = Column(String)
    method: str = Column(String)  # 'chronos-2', 'statistical_ma7', etc.
    date: date = Column(Date)
    horizon_day: int = Column(Integer)  # 1, 2, 3, ...
    point_forecast: float = Column(Numeric)
    p10: Optional[float] = Column(Numeric)
    p50: Optional[float] = Column(Numeric)
    p90: Optional[float] = Column(Numeric)
    actual_value: Optional[float] = Column(Numeric)  # Filled later when actuals available
    error: Optional[float] = Column(Numeric)  # |prediction - actual|
    created_at: datetime = Column(DateTime(timezone=True))
    
    # Indexes for performance queries
    __table_args__ = (
        Index('idx_forecast_results_item_method_date', 'item_id', 'method', 'date'),
        Index('idx_forecast_results_method', 'method'),
        Index('idx_forecast_results_actuals', 'actual_value'),
    )
```

### Method Performance Model

```python
class ForecastMethodPerformance(Base):
    """Aggregated performance metrics per method"""
    __tablename__ = "forecast_method_performance"
    
    performance_id: UUID = Column(UUID, primary_key=True)
    client_id: UUID = Column(UUID, ForeignKey("clients.client_id"), nullable=False)
    item_id: str = Column(String)
    method: str = Column(String)
    period_start: date = Column(Date)
    period_end: date = Column(Date)
    total_predictions: int = Column(Integer)
    successful_predictions: int = Column(Integer)
    mape: Optional[float] = Column(Numeric)  # Mean Absolute Percentage Error
    mae: Optional[float] = Column(Numeric)  # Mean Absolute Error
    rmse: Optional[float] = Column(Numeric)  # Root Mean Squared Error
    updated_at: datetime = Column(DateTime(timezone=True))
    
    # Indexes for performance queries
    __table_args__ = (
        Index('idx_method_performance_item_method', 'item_id', 'method'),
        Index('idx_method_performance_period', 'period_start', 'period_end'),
    )
```

**Key Design Points:**
- **One row per method per date**: Enables easy comparison and performance tracking
- **Actual values stored**: When actuals are available, calculate errors
- **Performance aggregation**: Pre-calculated metrics for fast queries
- **Indexes**: Optimized for common queries (item+method, method performance)

---

## Request/Response Schemas

### Pure Forecast Schemas

```python
# schemas/forecast.py

class ModelConfig(BaseModel):
    model: str = Field(default="chronos-2", description="Model identifier")
    device: str = Field(default="cpu", description="Device (cpu/cuda)")
    batch_size: int = Field(default=256, ge=1, le=1024)

class ForecastRequest(BaseModel):
    item_ids: List[str] = Field(..., min_items=1)
    prediction_length: int = Field(..., ge=1, le=365)
    quantile_levels: List[float] = Field(default=[0.1, 0.5, 0.9])
    use_covariates: bool = Field(default=True)
    start_date: Optional[datetime] = None
    model_config: ModelConfig = Field(default_factory=ModelConfig)

class ForecastResponse(BaseModel):
    forecast_id: UUID
    model_used: str
    fallback_used: bool
    forecasts: List[ItemForecast]

class ItemForecast(BaseModel):
    item_id: str
    predictions: List[PredictionPoint]
    metadata: ForecastMetadata
```

### Inventory Calculation Schemas

```python
# schemas/inventory.py

class InventoryParams(BaseModel):
    current_stock: float = Field(..., ge=0)
    lead_time_days: int = Field(..., ge=1, le=365)
    safety_stock_days: int = Field(default=7, ge=0, le=30)
    reorder_point: Optional[float] = Field(None, ge=0)
    moq: int = Field(default=0, ge=0)
    service_level: float = Field(default=0.95, ge=0.5, le=0.99)

class InventoryCalculationRequest(BaseModel):
    item_ids: List[str] = Field(..., min_items=1)
    prediction_length: int = Field(..., ge=1, le=365)
    inventory_params: Dict[str, InventoryParams]  # Per item
    forecast_params: Optional[ModelConfig] = None
    model_config: ModelConfig = Field(default_factory=ModelConfig)
    fallback_strategy: str = Field(default="statistical")

class InventoryCalculationResponse(BaseModel):
    calculation_id: UUID
    model_used: str
    fallback_used: bool
    results: List[InventoryResult]

class InventoryResult(BaseModel):
    item_id: str
    forecast: ForecastData
    inventory_metrics: InventoryMetrics
    recommendations: InventoryRecommendations
    calculation_method: CalculationMethod
```

---

## Implementation Phases

### Phase 1: Model Abstraction (MVP)
- [ ] Create `BaseForecastModel` interface
- [ ] Implement `Chronos2Model`
- [ ] Implement `StatisticalModel` (fallback)
- [ ] Create `ModelFactory`
- [ ] Update `ForecastService` to use factory

### Phase 2: Pure Forecast Endpoint
- [ ] Create forecast schemas
- [ ] Create forecast API routes
- [ ] Integrate with forecast service
- [ ] Add model selection via query param

### Phase 3: Inventory Calculation Endpoint
- [ ] Create inventory calculation service
- [ ] Implement standard inventory equations
- [ ] Create inventory schemas
- [ ] Create inventory API routes
- [ ] Integrate forecast + inventory calculation
- [ ] Calculate inventory metrics for all forecast methods

### Phase 4: Multi-Method Execution
- [ ] Update forecast service to run all methods
- [ ] Implement statistical methods (MA7, MA30, exponential, simple, naive)
- [ ] Store all results in database with method identification
- [ ] Return all results in API response
- [ ] Error handling per method (don't fail entire request if one method fails)

### Phase 5: Performance Tracking
- [ ] Create forecast_results table with method column
- [ ] Create forecast_method_performance table
- [ ] Implement performance analysis service
- [ ] Calculate MAPE, MAE, RMSE per method
- [ ] Build recommendation engine based on historical performance
- [ ] API endpoint to view method performance metrics

### Phase 5: Additional Models
- [ ] TimesFM integration
- [ ] Moirai integration
- [ ] Chronos-Bolt variants

---

## Configuration

### Environment Variables
```bash
# Default Model
DEFAULT_FORECAST_MODEL=chronos-2

# Model Configuration
CHRONOS_MODEL_ID=amazon/chronos-2
CHRONOS_DEVICE=cpu
CHRONOS_BATCH_SIZE=256

# Fallback Configuration
FALLBACK_ENABLED=true
DEFAULT_FALLBACK_STRATEGY=statistical

# Inventory Configuration
DEFAULT_SERVICE_LEVEL=0.95
DEFAULT_SAFETY_STOCK_DAYS=7
```

---

## Error Handling

### Model Errors
- **Model not found**: Return 400 with available models list
- **Model initialization failed**: Fallback to statistical model
- **Prediction failed**: Fallback to statistical model
- **Insufficient data**: Fallback to statistical model

### Validation Errors
- **Invalid model_id**: Return 422 with enum values
- **Invalid prediction_length**: Return 422 with min/max
- **Missing required fields**: Return 422 with field list

---

## Performance Analysis Endpoints

### Get Method Performance

**Endpoint:** `GET /api/v1/forecasts/performance/{item_id}`

**Purpose:** View historical performance metrics for all methods

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_date` | date | No | Start date for analysis (default: 90 days ago) |
| `end_date` | date | No | End date for analysis (default: today) |
| `method` | string | No | Filter by specific method |

#### Response
```json
{
  "item_id": "SKU001",
  "period": {
    "start": "2024-01-01",
    "end": "2024-03-31"
  },
  "methods": [
    {
      "method": "chronos-2",
      "total_predictions": 90,
      "successful_predictions": 88,
      "success_rate": 0.978,
      "mape": 8.2,
      "mae": 10.5,
      "rmse": 14.3,
      "rank": 1,
      "recommended": true
    },
    {
      "method": "statistical_ma7",
      "total_predictions": 90,
      "successful_predictions": 90,
      "success_rate": 1.0,
      "mape": 12.5,
      "mae": 15.2,
      "rmse": 19.8,
      "rank": 2,
      "recommended": false
    },
    {
      "method": "statistical_ma30",
      "total_predictions": 90,
      "successful_predictions": 90,
      "success_rate": 1.0,
      "mape": 15.3,
      "mae": 18.7,
      "rmse": 23.1,
      "rank": 3,
      "recommended": false
    }
  ],
  "best_method": "chronos-2",
  "worst_method": "naive"
}
```

### Update Actuals

**Endpoint:** `POST /api/v1/forecasts/actuals`

**Purpose:** Update forecast results with actual values for performance tracking

#### Request Body
```json
{
  "item_id": "SKU001",
  "actuals": [
    {
      "date": "2024-01-02",
      "actual_value": 130.0
    },
    {
      "date": "2024-01-03",
      "actual_value": 125.0
    }
  ]
}
```

This will:
1. Find all forecast results for these dates
2. Calculate error = |prediction - actual|
3. Update `forecast_results` table
4. Recalculate performance metrics in `forecast_method_performance`

---

## Future Enhancements

1. **Ensemble Methods**: Combine predictions from multiple models (weighted average, voting)
2. **Auto Model Selection**: Automatically select best model based on data characteristics
3. **Confidence Intervals**: Calculate confidence based on method agreement
4. **Method Weighting**: Weight methods based on historical performance
5. **A/B Testing Framework**: Test different models on same data with controlled experiments
6. **Performance Dashboards**: Visualize method performance over time
7. **Alerting**: Alert when method performance degrades

---

## References

- [Chronos-2 GitHub](https://github.com/amazon-science/chronos-forecasting)
- [Forecasting API Requirements](../../planning/forecasting-api-requirements.md)
- [Chronos-2 Payload Format](../../ecommerce-agent/CHRONOS2_PAYLOAD_FORMAT.md)
- [Data Models Audit](../../forecaster/DATA_MODELS_AUDIT.md)

