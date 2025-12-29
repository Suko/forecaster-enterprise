# Forecasting: Testing, Frequency, and Accuracy Tracking

> **🛑 DEPRECATED**: This document has been consolidated into [forecasting/README.md](../forecasting/README.md)
>
> **Date Archived**: 2025-12-29
>
> This content is no longer maintained. Please refer to the consolidated documentation for current information.

## Forecast History & Accuracy Tracking

### ✅ **Current Implementation**

**Forecast Storage:**
- `forecast_runs` table: Stores each forecast execution (run_id, created_at, status)
- `forecast_results` table: Stores daily predictions (point_forecast, p10, p50, p90)
- `forecast_results.actual_value`: Stores actual sales (backfilled later for accuracy)

**Accuracy Tracking:**
- ✅ `actual_value` column in `forecast_results` (backfilled from `ts_demand_daily`)
- ✅ `POST /api/v1/forecast/forecasts/actuals` - Backfill actuals endpoint
- ✅ `QualityCalculator` service - Calculates MAPE, MAE, RMSE
- ✅ `GET /api/v1/forecast/forecasts/quality/{item_id}` - Get accuracy metrics

**How It Works:**
1. Generate forecast → Store predictions in `forecast_results` (actual_value = NULL)
2. Wait for actual sales data → Backfill `actual_value` from `ts_demand_daily`
3. Calculate accuracy → Compare predictions vs actuals (MAPE, MAE, RMSE)

---

## Testing Before Cron Jobs

### **Option 1: Manual API Calls** (Recommended for Testing)

**Step 1: Generate Forecast**
```bash
# Generate forecast for test items
curl -X POST "http://localhost:8000/api/v1/forecast/generate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001", "SKU002", "SKU003"],
    "prediction_length": 30,
    "primary_model": "chronos-2"
  }'
```

**Response:**
```json
{
  "forecast_run_id": "uuid-here",
  "status": "completed",
  "created_at": "2025-12-16T10:00:00Z"
}
```

**Step 2: Check Forecast Results**
```bash
# Get forecast results
curl -X GET "http://localhost:8000/api/v1/forecast/results/{forecast_run_id}" \
  -H "Authorization: Bearer <token>"
```

**Step 3: Test Integration (Use Forecast in Dashboard)**
```bash
# Get products with metrics (should use forecast if available)
curl -X GET "http://localhost:8000/api/v1/inventory/products" \
  -H "Authorization: Bearer <token>"
```

**Step 4: Backfill Actuals (After Sales Data Available)**
```bash
# Backfill actual values for accuracy tracking
curl -X POST "http://localhost:8000/api/v1/forecast/forecasts/actuals" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_id": "SKU001",
    "actuals": [
      {"date": "2025-12-17", "actual_value": 45.5},
      {"date": "2025-12-18", "actual_value": 52.3}
    ]
  }'
```

**Step 5: Check Accuracy**
```bash
# Get accuracy metrics
curl -X GET "http://localhost:8000/api/v1/forecast/forecasts/quality/SKU001" \
  -H "Authorization: Bearer <token>"
```

---

### **Option 2: Manual Forecast Test Script** (Recommended for Quick Testing)

**Use `scripts/manual_forecast_test.py`:**

This script runs a complete forecast test and shows how forecasts affect inventory metrics:

```bash
cd backend
uv run python scripts/manual_forecast_test.py
```

**What it does:**
1. Finds items with sales data (≥30 days history)
2. Gets metrics BEFORE forecast (using historical data)
3. Generates forecast for those items
4. Gets metrics AFTER forecast (using forecast data)
5. Compares DIR, stockout risk, and status changes

**Output example:**
```
📊 COMPARISON: M5_HOUSEHOLD_1_409
DIR (days): 64.1 → 70.0 (+5.9 days, +9.2%)
Stockout Risk: N/A → N/A
Status: normal → normal ✅ Same
```

**Validate Forecast Results:**

After generating a forecast, validate it:

```bash
# Validate specific forecast run
uv run python scripts/validate_forecast_results.py <forecast_run_id>

# Or validate latest forecast
uv run python scripts/validate_forecast_results.py
```

**What validation checks:**
- ✅ Forecast run exists and is completed
- ✅ Forecast results are stored correctly
- ✅ Data quality (no nulls, no negatives)
- ✅ Metrics calculations are correct
- ✅ Structure is valid

---

### **Option 3: Python Script** (For Automated Testing)

**Use `scripts/test_forecast_integration.py`:**

```python
"""Test forecast integration before cron jobs"""
import asyncio
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from models.database import get_db
from forecasting.services.forecast_service import ForecastService
from services.inventory_service import InventoryService

async def test_forecast_integration():
    """Test full forecast integration flow"""
    async for db in get_db():
        client_id = UUID("your-test-client-id")
        user_id = "test-user"
        
        # 1. Generate forecast
        forecast_service = ForecastService(db)
        forecast_run = await forecast_service.generate_forecast(
            client_id=str(client_id),
            user_id=user_id,
            item_ids=["SKU001", "SKU002"],
            prediction_length=30,
            primary_model="chronos-2"
        )
        
        print(f"✅ Forecast generated: {forecast_run.forecast_run_id}")
        
        # 2. Test inventory service uses forecast
        inventory_service = InventoryService(db)
        products = await inventory_service.get_products_with_metrics(
            client_id=client_id,
            page=1,
            page_size=10
        )
        
        print(f"✅ Products fetched: {len(products['items'])}")
        for product in products['items']:
            if product.item_id in ["SKU001", "SKU002"]:
                print(f"   {product.item_id}: DIR={product.dir}, using_forecast={product.using_forecast}")
        
        # 3. Wait for actual sales (simulate)
        # In real scenario, wait for sales data to arrive
        
        # 4. Backfill actuals
        from api.forecast import backfill_actuals
        # ... backfill logic
        
        print("✅ Integration test complete")

if __name__ == "__main__":
    asyncio.run(test_forecast_integration())
```

---

### **Option 3: Test Endpoint** (Quick Testing)

**Add test endpoint for development:**

```python
@router.post("/forecast/test-integration")
async def test_forecast_integration(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """Test endpoint: Generate forecast and verify integration"""
    # Generate forecast
    # Check if dashboard uses it
    # Return test results
    pass
```

---

## Forecast Frequency Recommendations

### **Daily Forecasts** (Recommended for Most Cases)

**When to use:**
- ✅ Fast-moving inventory (high turnover)
- ✅ Seasonal products
- ✅ Products with promotions
- ✅ High-value items (stockout cost is high)

**Benefits:**
- ✅ Fresh forecasts every day
- ✅ Reacts quickly to demand changes
- ✅ Better for short-term planning

**Drawbacks:**
- ⚠️ More compute resources
- ⚠️ More database storage

**Schedule:**
- **Time:** 2-4 AM (off-peak hours)
- **Frequency:** Daily
- **Cron:** `0 3 * * *` (3 AM daily)

---

### **Weekly Forecasts** (For Stable Products)

**When to use:**
- ✅ Slow-moving inventory
- ✅ Stable demand patterns
- ✅ Low-value items
- ✅ Products with long lead times

**Benefits:**
- ✅ Less compute resources
- ✅ Sufficient for weekly planning
- ✅ Lower database growth

**Drawbacks:**
- ⚠️ Less reactive to changes
- ⚠️ May miss short-term trends

**Schedule:**
- **Time:** Sunday 2-4 AM
- **Frequency:** Weekly
- **Cron:** `0 3 * * 0` (3 AM every Sunday)

---

### **Hybrid Approach** (Recommended)

**Different frequencies by product classification:**

| Classification | Frequency | Reason |
|----------------|-----------|--------|
| A-X (High value, fast) | Daily | Critical items, need accuracy |
| A-Y (High value, medium) | Daily | High stockout cost |
| A-Z (High value, slow) | Weekly | Stable demand |
| B-X, B-Y | Weekly | Medium priority |
| B-Z, C-X, C-Y, C-Z | Weekly | Low priority, stable |

**Implementation:**
```python
# In forecast scheduler
async def schedule_forecasts_by_classification():
    # Daily: A-X, A-Y
    daily_items = await get_items_by_classification(["A-X", "A-Y"])
    await generate_forecast(daily_items)
    
    # Weekly: All others (on Sunday)
    if date.today().weekday() == 6:  # Sunday
        weekly_items = await get_items_by_classification(["A-Z", "B-*", "C-*"])
        await generate_forecast(weekly_items)
```

---

## Recommended Frequency by Business Context

### **E-commerce (Fast-Moving)**
- **Frequency:** Daily
- **Time:** 3 AM
- **Reason:** High turnover, promotions, seasonal changes

### **B2B Wholesale (Stable)**
- **Frequency:** Weekly
- **Time:** Sunday 3 AM
- **Reason:** Stable demand, longer planning cycles

### **Retail (Mixed)**
- **Frequency:** Hybrid (daily for A-X/Y, weekly for others)
- **Time:** 3 AM (daily), Sunday 3 AM (weekly)
- **Reason:** Mix of fast and slow movers

---

## Accuracy Tracking Workflow

### **1. Forecast Generation**
```python
# Generate forecast
forecast_run = await forecast_service.generate_forecast(...)

# Store predictions (actual_value = NULL)
# forecast_results: {date, point_forecast, actual_value: NULL}
```

### **2. Wait for Actual Sales**
```python
# Sales data arrives in ts_demand_daily
# Wait 1-7 days for actual sales to be recorded
```

### **3. Backfill Actuals**
```python
# Backfill actual values
await backfill_actuals(
    item_id="SKU001",
    actuals=[
        {"date": "2025-12-17", "actual_value": 45.5},
        {"date": "2025-12-18", "actual_value": 52.3}
    ]
)

# Updates forecast_results.actual_value
```

### **4. Calculate Accuracy**
```python
# Get accuracy metrics
quality = await get_quality_metrics(
    item_id="SKU001",
    start_date=date(2025, 12, 17),
    end_date=date(2025, 12, 30)
)

# Returns: MAPE, MAE, RMSE, Bias
```

### **5. Track Over Time**
```python
# Compare accuracy across forecast runs
# Track: MAPE trend, method performance, item-level accuracy
```

---

## Testing Checklist

### **Before Cron Jobs Setup:**

- [x] **Manual Forecast Generation** ✅
  - [x] Generate forecast via API
  - [x] Generate forecast via script (`manual_forecast_test.py`)
  - [x] Verify forecast stored in database
  - [x] Check forecast_results populated
  - [x] Validate forecast results (`validate_forecast_results.py`)

- [x] **Integration Testing** ✅
  - [x] Metrics calculated correctly with forecast data
  - [x] DIR calculation uses forecasted demand
  - [x] Stockout risk calculation uses forecasted demand
  - [x] Comparison script shows before/after metrics
  - [ ] Dashboard uses forecast (if available) - **TODO: Integration**
  - [ ] Product list uses forecast - **TODO: Integration**

- [ ] **Accuracy Tracking**
  - [ ] Backfill actuals after sales data
  - [ ] Calculate accuracy metrics
  - [ ] Verify MAPE/MAE/RMSE calculation

- [ ] **Cache Testing**
  - [ ] Forecast_run_id cached correctly
  - [ ] Cache invalidated on new forecast
  - [ ] Performance acceptable

- [x] **Edge Cases** ✅
  - [x] No forecast available (fallback to historical) - **Tested in manual_forecast_test.py**
  - [x] Forecast validation handles missing data - **Tested in validate_forecast_results.py**
  - [ ] Stale forecast (>7 days old) - **TODO: Test**
  - [ ] Multiple forecast runs (use latest) - **TODO: Test**

---

## Cron Job Setup (When Ready)

### **Daily Forecast (3 AM)**
```bash
# Crontab entry
0 3 * * * cd /path/to/backend && uv run python scripts/run_daily_forecast.py
```

### **Weekly Forecast (Sunday 3 AM)**
```bash
# Crontab entry
0 3 * * 0 cd /path/to/backend && uv run python scripts/run_weekly_forecast.py
```

### **Backfill Actuals (Daily 4 AM - After Forecast)**
```bash
# Backfill actuals from previous day
0 4 * * * cd /path/to/backend && uv run python scripts/backfill_actuals.py
```

---

## Summary

**Forecast History:**
- ✅ Stored in `forecast_runs` and `forecast_results`
- ✅ `actual_value` backfilled for accuracy tracking
- ✅ Accuracy metrics calculated (MAPE, MAE, RMSE)

**Testing Before Cron:**
- ✅ Manual API calls (recommended)
- ✅ Python scripts
- ✅ Test endpoints

**Forecast Frequency:**
- ✅ **Daily:** Fast-moving, high-value items
- ✅ **Weekly:** Stable, low-value items
- ✅ **Hybrid:** Best of both worlds

**Recommended:**
- Start with **daily forecasts** for all items
- Monitor accuracy and performance
- Optimize to hybrid (daily/weekly) based on results

