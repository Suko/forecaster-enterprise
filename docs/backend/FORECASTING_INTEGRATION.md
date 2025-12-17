# Forecasting Integration in Inventory Management

## Current State: Where Forecasting Comes Into Play

### ✅ **Currently Integrated**

#### 1. **Special Inventory Calculation Endpoint**
**Endpoint**: `POST /api/v1/forecast/inventory/calculate`

**What it does**:
- Generates forecast for requested items
- Uses forecasted demand (next 30 days) to calculate:
  - DIR (Days of Inventory Remaining)
  - Safety Stock
  - Reorder Point
  - Recommended Order Quantity
  - Stockout Risk
  - Stockout Date

**Code Location**: `backend/api/forecast.py:144-282`

**Flow**:
```python
1. Generate forecast → forecast_run
2. Fetch forecast results → results_by_item
3. Calculate avg_daily_demand from forecast
4. Use forecast-based demand for all metrics
```

**When to use**: When you want **forward-looking** inventory planning based on predicted demand.

#### 2. **MetricsService Support for Forecasts**
**Code Location**: `backend/services/metrics_service.py:45-77`

**What it does**:
- `calculate_dir()` accepts optional `forecasted_demand_30d` parameter
- If provided, uses forecast instead of historical average
- Falls back to historical data if forecast not provided

**Current Usage**:
```python
# With forecast (forward-looking)
dir = await metrics_service.calculate_dir(
    client_id, item_id, stock,
    forecasted_demand_30d=Decimal("900")  # 30 days forecast
)

# Without forecast (backward-looking)
dir = await metrics_service.calculate_dir(
    client_id, item_id, stock
    # Uses last 30 days from ts_demand_daily
)
```

### ⚠️ **Partially Integrated**

#### 3. **Regular Inventory Endpoints (Historical Data Only)**
**Endpoints**:
- `GET /api/v1/inventory/products` - Product list with metrics
- `GET /api/v1/inventory/products/{item_id}` - Product details
- `GET /api/v1/dashboard` - Dashboard summary

**Current Behavior**: 
- **All use historical data** (last 30 days from `ts_demand_daily`)
- **Do NOT use forecasts** even if available

**Code Locations**:
- `backend/services/inventory_service.py` - Uses `MetricsService` without forecast
- `backend/services/dashboard_service.py` - Uses historical average only

**Impact**: 
- Dashboard shows **backward-looking** metrics (based on past sales)
- Not using **forward-looking** forecasts for planning

### ❌ **Not Integrated Yet**

#### 4. **Forecast Results Validation**
**Missing**: Validation of forecast results quality

**What should be validated**:
- Forecast accuracy (MAPE, MAE, RMSE)
- Forecast completeness (all items have forecasts)
- Forecast freshness (forecasts not too old)
- Forecast vs actual comparison (backfill actuals)

**Where**: `backend/services/data_validation_service.py` - No forecast validation yet

#### 5. **Automatic Forecast-Based Metrics**
**Missing**: Automatic use of latest forecasts in regular endpoints

**What should happen**:
- When fetching products/dashboard, check if recent forecast exists
- If forecast exists and is fresh (< 7 days old), use it
- Otherwise, fall back to historical average

**Current**: Always uses historical, never checks for forecasts

#### 6. **Forecast Refresh Scheduling**
**Missing**: Automatic forecast generation

**What should happen**:
- Scheduled forecast runs (daily/weekly)
- Store results in `forecast_results` table
- Metrics automatically use latest forecasts

**Current**: Forecasts only generated on-demand via API

## Data Flow Comparison

### Current Flow (Historical Data)
```
ts_demand_daily (last 30 days)
    ↓
Average Daily Demand = AVG(units_sold)
    ↓
DIR = current_stock / avg_daily_demand
    ↓
Stockout Risk = f(DIR, lead_time, buffer)
    ↓
Dashboard/Products API
```

### Forecast-Based Flow (Only in /inventory/calculate)
```
ts_demand_daily (training data)
    ↓
ForecastService.generate_forecast()
    ↓
forecast_results (next 30 days predictions)
    ↓
Average Daily Demand = AVG(forecasted_demand) / 30
    ↓
DIR = current_stock / forecasted_avg_daily
    ↓
Stockout Risk = f(DIR, lead_time, buffer)
    ↓
/inventory/calculate API only
```

### Ideal Flow (Hybrid)
```
Check: Does recent forecast exist?
    ↓
YES → Use forecast_results (forward-looking)
    ↓
NO → Use ts_demand_daily (backward-looking)
    ↓
Calculate metrics with chosen demand source
    ↓
All endpoints (dashboard, products, etc.)
```

## Integration Gaps

### Gap 1: Regular Endpoints Don't Use Forecasts
**Problem**: Dashboard and product list use historical data only

**Solution**: 
1. Check for recent forecast in `forecast_results`
2. If exists and fresh, use it
3. Otherwise, use historical average

**Code Change Needed**:
```python
# In inventory_service.py
async def get_products_with_metrics(...):
    # Check for recent forecast
    forecast_demand = await self._get_latest_forecast_demand(
        client_id, item_id
    )
    
    # Use forecast if available, else historical
    dir = await metrics_service.calculate_dir(
        client_id, item_id, stock,
        forecasted_demand_30d=forecast_demand  # None if no forecast
    )
```

### Gap 2: No Forecast Validation
**Problem**: No validation of forecast quality/accuracy

**Solution**: Add forecast validation to `DataValidationService`

**What to validate**:
- Forecast exists for all active products
- Forecast is recent (< 7 days old)
- Forecast accuracy metrics (if actuals available)
- Forecast completeness (all 30 days predicted)

**Code Location**: `backend/services/data_validation_service.py`

### Gap 3: No Automatic Forecast Generation
**Problem**: Forecasts only generated on-demand

**Solution**: Scheduled forecast jobs (Celery/cron)

**What to do**:
- Daily/weekly forecast runs for all active products
- Store in `forecast_results` table
- Metrics automatically pick up latest forecasts

## Where Forecasting Should Be Used

### ✅ **Should Use Forecasts** (Forward-Looking Planning)

1. **Dashboard Overview**
   - Stockout risk based on predicted demand
   - DIR based on forecasted demand
   - More accurate for planning

2. **Product List/Details**
   - Show forecast-based metrics
   - Indicate if using forecast vs historical
   - Better inventory planning

3. **Recommendations**
   - Reorder recommendations based on forecast
   - Stockout warnings based on predicted demand
   - More proactive than reactive

4. **Purchase Order Planning**
   - Order quantities based on forecast
   - Lead time + forecasted demand = better planning

### ⚠️ **Can Use Historical** (Backward-Looking Analysis)

1. **Historical Analysis**
   - Compare actual vs forecast
   - Forecast accuracy metrics
   - Trend analysis

2. **Fallback When No Forecast**
   - New products (no history yet)
   - Forecast generation failed
   - Historical is better than nothing

## Implementation Priority

### Priority 1: Use Forecasts in Regular Endpoints (HIGH)
**Why**: Dashboard/products should show forward-looking metrics

**Changes**:
1. Add `_get_latest_forecast_demand()` to `InventoryService`
2. Modify `get_products_with_metrics()` to use forecasts
3. Modify `DashboardService` to use forecasts
4. Add indicator: "Using forecast" vs "Using historical"

**Files**:
- `backend/services/inventory_service.py`
- `backend/services/dashboard_service.py`
- `backend/services/metrics_service.py` (already supports it)

### Priority 2: Forecast Validation (MEDIUM)
**Why**: Ensure forecast quality before using

**Changes**:
1. Add `_validate_forecasts()` to `DataValidationService`
2. Check forecast freshness, completeness, accuracy
3. Add to validation report

**Files**:
- `backend/services/data_validation_service.py`

### Priority 3: Automatic Forecast Generation (LOW)
**Why**: Keep forecasts fresh automatically

**Changes**:
1. Scheduled job to generate forecasts
2. Store in `forecast_results`
3. Metrics automatically use latest

**Files**:
- New: `backend/jobs/forecast_scheduler.py`
- Or: Celery task

## Current Code References

### Forecast Generation
- `backend/forecasting/services/forecast_service.py` - Main forecast service
- `backend/api/forecast.py` - Forecast API endpoints
- `backend/models/forecast.py` - Forecast data models

### Metrics Calculation
- `backend/services/metrics_service.py` - Supports forecast parameter
- `backend/services/inventory_service.py` - Currently doesn't use forecasts
- `backend/services/dashboard_service.py` - Currently doesn't use forecasts

### Forecast Storage
- `forecast_runs` table - Forecast execution records
- `forecast_results` table - Daily forecast predictions
- `forecast_results.item_id` matches `products.item_id` (critical!)

## Summary

**Current State**:
- ✅ Forecasting works and generates predictions
- ✅ Special endpoint uses forecasts for inventory calculation
- ⚠️ Regular endpoints (dashboard, products) use historical data only
- ❌ No forecast validation
- ❌ No automatic forecast generation

**Where Forecasting Comes Into Play**:
1. **Now**: Only in `/api/v1/forecast/inventory/calculate` endpoint
2. **Should be**: In all inventory metrics (dashboard, products, recommendations)
3. **Future**: Automatic scheduled forecasts + validation

**Next Steps**:
1. Integrate forecasts into regular endpoints (Priority 1)
2. Add forecast validation (Priority 2)
3. Set up automatic forecast generation (Priority 3)

