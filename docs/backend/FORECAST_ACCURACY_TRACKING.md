# Forecast Accuracy Tracking

**Last Updated:** 2025-12-17  
**Status:** ✅ **IMPLEMENTED** - Accuracy tracking infrastructure complete

---

## Overview

Forecast accuracy tracking allows you to measure how well your forecasts perform over time. This enables:
- **Quality monitoring**: Track forecast performance per SKU, method, and time period
- **Model selection**: Compare different forecasting methods (Chronos-2 vs MA7)
- **Business insights**: Understand which products are easier/harder to forecast
- **Continuous improvement**: Identify areas where forecasting can be improved

---

## How Accuracy Tracking Works

### **1. Forecast Generation**
When a forecast is generated:
- Predictions stored in `forecast_results` table
- `actual_value` column is **NULL** (not yet known)
- Forecast run metadata stored in `forecast_runs` table

```python
# Forecast generated
forecast_run = await forecast_service.generate_forecast(...)

# Results stored with actual_value = NULL
# forecast_results: {date, point_forecast, actual_value: NULL}
```

### **2. Wait for Actual Sales**
After forecast is generated, wait for actual sales data to arrive:
- Sales data comes from ETL sync (`ts_demand_daily`)
- Typically 1-7 days after forecast date
- Actual values are the real sales that occurred

### **3. Backfill Actual Values**
Once actual sales data is available, backfill into forecast results:

**API Endpoint:** `POST /api/v1/forecast/forecasts/actuals`

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

### **4. Calculate Accuracy Metrics**
Once actuals are backfilled, calculate accuracy:

**API Endpoint:** `GET /api/v1/forecast/forecasts/quality/{item_id}`

**Metrics Calculated:**
- **MAPE** (Mean Absolute Percentage Error): `|actual - forecast| / actual * 100`
- **MAE** (Mean Absolute Error): `|actual - forecast|`
- **RMSE** (Root Mean Squared Error): `sqrt(mean((actual - forecast)^2))`
- **Bias**: `mean(forecast - actual)` (positive = over-forecast, negative = under-forecast)

---

## Accuracy Tracking Workflow

### **Daily Workflow (Production)**

```
Day 1 (2025-12-17):
  ├─ 3 AM: Generate forecast for next 30 days
  ├─ Store predictions (actual_value = NULL)
  └─ Use forecast for inventory metrics ✅

Day 2 (2025-12-18):
  ├─ ETL sync: Load yesterday's sales (2025-12-17)
  ├─ Backfill: Update forecast_results.actual_value for 2025-12-17
  └─ Calculate accuracy: Compare forecast vs actual for 2025-12-17

Day 3 (2025-12-19):
  ├─ ETL sync: Load yesterday's sales (2025-12-18)
  ├─ Backfill: Update forecast_results.actual_value for 2025-12-18
  └─ Calculate accuracy: Compare forecast vs actual for 2025-12-18

... repeat daily ...
```

### **Automated Backfill (Future)**

**Current:** Manual backfill via API  
**Future:** Automated backfill after ETL sync

```python
# After ETL sync completes
async def auto_backfill_actuals(client_id, sync_date):
    # Get forecasts that need actuals
    forecasts = await get_forecasts_needing_actuals(client_id, sync_date)
    
    # Get actual sales from ts_demand_daily
    actuals = await get_actual_sales(client_id, sync_date)
    
    # Backfill
    await backfill_forecast_actuals(forecasts, actuals)
    
    # Calculate accuracy metrics
    await calculate_accuracy_metrics(client_id, sync_date)
```

---

## Accuracy Metrics Explained

### **MAPE (Mean Absolute Percentage Error)**
**Formula:** `mean(|actual - forecast| / actual) * 100`

**Interpretation:**
- **0-10%**: Excellent forecast accuracy
- **10-20%**: Good forecast accuracy
- **20-50%**: Acceptable forecast accuracy
- **>50%**: Poor forecast accuracy (consider different method)

**Example:**
```
Forecast: 100 units
Actual: 110 units
MAPE: |110 - 100| / 110 * 100 = 9.1% ✅ Excellent
```

### **MAE (Mean Absolute Error)**
**Formula:** `mean(|actual - forecast|)`

**Interpretation:**
- Lower is better
- Units: Same as demand (e.g., units per day)
- Useful for understanding absolute error magnitude

**Example:**
```
Forecast: 100 units/day
Actual: 110 units/day
MAE: |110 - 100| = 10 units/day
```

### **RMSE (Root Mean Squared Error)**
**Formula:** `sqrt(mean((actual - forecast)^2))`

**Interpretation:**
- Penalizes large errors more than MAE
- Units: Same as demand
- Useful for understanding worst-case errors

**Example:**
```
Forecasts: [100, 100, 100]
Actuals: [110, 90, 120]
RMSE: sqrt(((110-100)^2 + (90-100)^2 + (120-100)^2) / 3) = 12.9 units
```

### **Bias**
**Formula:** `mean(forecast - actual)`

**Interpretation:**
- **Positive**: Systematically over-forecasting (forecast > actual)
- **Negative**: Systematically under-forecasting (forecast < actual)
- **Zero**: No systematic bias (good!)

**Example:**
```
Forecast: 100 units/day
Actual: 90 units/day
Bias: 100 - 90 = +10 (over-forecasting by 10 units/day)
```

---

## Using Accuracy Metrics

### **1. Compare Forecasting Methods**

```python
# Get accuracy for Chronos-2
chronos_metrics = await get_quality_metrics(
    item_id="SKU001",
    method="chronos-2",
    start_date=date(2025, 12, 1),
    end_date=date(2025, 12, 30)
)

# Get accuracy for MA7 baseline
ma7_metrics = await get_quality_metrics(
    item_id="SKU001",
    method="statistical_ma7",
    start_date=date(2025, 12, 1),
    end_date=date(2025, 12, 30)
)

# Compare
if chronos_metrics["mape"] < ma7_metrics["mape"]:
    print("Chronos-2 is more accurate ✅")
else:
    print("MA7 is more accurate (or similar)")
```

### **2. Identify Problem Products**

```python
# Get accuracy for all products
all_metrics = await get_all_products_accuracy(client_id)

# Find products with poor accuracy
poor_accuracy = [
    item for item in all_metrics 
    if item["mape"] > 50  # >50% error
]

print(f"Products needing attention: {len(poor_accuracy)}")
```

### **3. Track Accuracy Over Time**

```python
# Get accuracy trends
weekly_accuracy = await get_accuracy_trends(
    item_id="SKU001",
    period="weekly"
)

# Plot: MAPE over time
# Identify if accuracy is improving or degrading
```

---

## API Endpoints

### **Backfill Actuals**
```http
POST /api/v1/forecast/forecasts/actuals
Authorization: Bearer <token>
Content-Type: application/json

{
  "item_id": "SKU001",
  "actuals": [
    {"date": "2025-12-17", "actual_value": 45.5},
    {"date": "2025-12-18", "actual_value": 52.3}
  ]
}
```

### **Get Accuracy Metrics**
```http
GET /api/v1/forecast/forecasts/quality/{item_id}?start_date=2025-12-01&end_date=2025-12-30
Authorization: Bearer <token>

Response:
{
  "item_id": "SKU001",
  "period": {"start": "2025-12-01", "end": "2025-12-30"},
  "methods": [
    {
      "method": "chronos-2",
      "mape": 12.5,
      "mae": 8.3,
      "rmse": 10.2,
      "bias": -1.5
    },
    {
      "method": "statistical_ma7",
      "mape": 18.7,
      "mae": 12.1,
      "rmse": 15.3,
      "bias": 2.1
    }
  ]
}
```

---

## Data Validation Integration

Forecast accuracy is validated in `DataValidationService`:

**Checks:**
- ✅ Forecast results can store actual values
- ✅ Accuracy metrics can be calculated
- ✅ Actual values are backfilled correctly
- ✅ Quality endpoint returns valid metrics

**Validation Report:**
```json
{
  "forecast_validation": {
    "info": [
      "Forecast accuracy tracking: 150 actual values backfilled",
      "Use /api/v1/forecast/forecasts/quality/{item_id} to view accuracy metrics"
    ]
  }
}
```

---

## Best Practices

### **1. Backfill Regularly**
- Backfill actuals daily after ETL sync
- Don't wait too long (actuals should be available within 1-7 days)

### **2. Track Accuracy Per SKU Classification**
- A-X items (high value, fast): Expect lower MAPE (<15%)
- C-Z items (low value, slow): Higher MAPE acceptable (<30%)

### **3. Monitor Accuracy Trends**
- Track MAPE over time (weekly/monthly)
- Alert if accuracy degrades significantly
- Compare methods to choose best for each SKU

### **4. Use Accuracy for Model Selection**
- System automatically selects best method per SKU
- Accuracy metrics inform `recommended_method` in `forecast_runs`

---

## Future Enhancements

### **Automated Backfill**
- Auto-backfill after ETL sync completes
- No manual API calls needed

### **Accuracy Dashboard**
- Visual dashboard showing accuracy trends
- Per-SKU accuracy charts
- Method comparison graphs

### **Accuracy Alerts**
- Alert when accuracy drops below threshold
- Alert when bias becomes significant
- Alert when method should be changed

### **Accuracy-Based Recommendations**
- Recommend different methods based on accuracy
- Suggest when to retrain models
- Identify products needing manual review

---

## Summary

**Current State:**
- ✅ Forecast results can store actual values
- ✅ Backfill API endpoint exists
- ✅ Accuracy metrics calculation works
- ✅ Quality endpoint returns metrics
- ✅ Validation includes accuracy checks

**Workflow:**
1. Generate forecast → Store predictions
2. Wait for actual sales → ETL sync
3. Backfill actuals → Update `forecast_results.actual_value`
4. Calculate accuracy → Use quality endpoint
5. Monitor & improve → Track trends over time

**Next Steps:**
- ⏳ Automated backfill after ETL sync
- ⏳ Accuracy dashboard (frontend)
- ⏳ Accuracy-based alerts

---

**Related Documentation:**
- [Forecasting Integration](./FORECASTING_INTEGRATION.md)
- [Forecasting Testing & Frequency](./FORECASTING_TESTING_AND_FREQUENCY.md)
- [Data Validation API](./DATA_VALIDATION_API.md)

