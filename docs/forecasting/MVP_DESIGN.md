# Forecasting API - MVP Design

**Status:** MVP Phase  
**Goal:** Simple, working forecasting API with extensible architecture

---

## MVP Scope

### What We Build (Phase 1)

1. **One Primary Model**: `chronos-2` only
2. **One Baseline Method**: `statistical_ma7` (for comparison)
3. **Two Endpoints**: Pure forecast + Inventory calculation
4. **Storage**: Store results in database (for future analysis)
5. **Simple Response**: Return only recommended method results

### What We Defer (Phase 2+)

- Multiple statistical methods (MA30, exponential, etc.)
- Performance analysis service
- Performance API endpoints
- Multiple ML models (TimesFM, Moirai)
- Inventory metrics per method

---

## API Endpoints (MVP)

### 1. Pure Forecast Endpoint

**Endpoint:** `POST /api/v1/forecast`

#### Request
```json
{
  "item_ids": ["SKU001", "SKU002"],
  "prediction_length": 30,
  "model": "chronos-2",  // Optional, default: "chronos-2"
  "include_baseline": true  // Optional, default: true (runs statistical_ma7)
}
```

#### Response - What You Get Back

```json
{
  "forecast_id": "550e8400-e29b-41d4-a716-446655440000",
  "primary_model": "chronos-2",
  "forecasts": [
    {
      "item_id": "SKU001",
      "recommended_method": "chronos-2",  // Best method (primary if successful)
      "predictions": [  // ⭐ ONLY recommended method predictions
        {
          "date": "2024-01-02",
          "point_forecast": 125.5,  // ⭐ Median/mean prediction
          "quantiles": {  // ⭐ Uncertainty intervals (confidence bands)
            "0.1": 98.2,   // 10th percentile (lower bound)
            "0.5": 125.5,  // 50th percentile (median)
            "0.9": 152.8   // 90th percentile (upper bound)
          },
          "uncertainty_range": 54.6,  // ⭐ 90th - 10th percentile (spread)
          "coefficient_of_variation": 0.22  // ⭐ CV = std/mean (relative uncertainty)
        },
        {
          "date": "2024-01-03",
          "point_forecast": 128.3,
          "quantiles": {
            "0.1": 100.1,
            "0.5": 128.3,
            "0.9": 156.5
          }
        }
        // ... 30 days total
      ],
      "metadata": {
        "method_used": "chronos-2",
        "historical_data_points": 90,  // ⭐ Number of historical data points used
        "covariates_used": ["promo_flag", "holiday_flag"]
      },
      "accuracy_indicators": {  // ⭐ Historical accuracy (if available) - Industry Standard Metrics
        "mape": 8.2,  // Mean Absolute Percentage Error (%) - Industry Standard
        "mae": 10.5,   // Mean Absolute Error (units) - Industry Standard
        "rmse": 14.3,  // Root Mean Squared Error - Industry Standard
        "bias": -2.1,  // Forecast Bias (positive = over-forecast, negative = under-forecast) - Industry Standard
        "sample_size": 45,       // Number of past forecasts used
        "last_updated": "2024-01-01"  // When accuracy was last calculated
      },
      "baseline_comparison": {  // ⭐ Only if include_baseline=true
        "method": "statistical_ma7",
        "avg_daily_demand": 118.3,  // For comparison only
        "total_forecast_30d": 3549.0
      }
    }
  ]
}
```

**Key Points:**
- ✅ **Returns**: Only recommended method predictions (not all methods)
- ✅ **Includes**: Baseline comparison summary (avg, total) for reference
- ✅ **Stores**: All methods in database (for future analysis)
- ✅ **Simple**: One prediction array per item

---

### 2. Inventory Calculation Endpoint

**Endpoint:** `POST /api/v1/inventory/calculate`

#### Request
```json
{
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
  "model": "chronos-2"  // Optional
}
```

#### Response - What You Get Back

```json
{
  "calculation_id": "660e8400-e29b-41d4-a716-446655440001",
  "results": [
    {
      "item_id": "SKU001",
      "forecast": {  // ⭐ Forecast summary (from recommended method)
        "method_used": "chronos-2",
        "total_forecast_30d": 3765.0,
        "avg_daily_demand": 125.5
      },
      "inventory_metrics": {  // ⭐ Calculated from recommended forecast
        "current_stock": 500,
        "days_of_inventory_remaining": 3.98,
        "safety_stock": 878.5,
        "reorder_point": 2546.0,
        "recommended_order_quantity": 3044,
        "stockout_risk": "high",
        "stockout_date": "2024-01-05",
        "days_until_reorder": -10
      },
      "recommendations": {  // ⭐ Actionable recommendations
        "action": "URGENT_REORDER",
        "priority": "critical",
        "message": "Stockout expected in 4 days. Reorder immediately.",
        "suggested_order_date": "2024-01-01",
        "suggested_order_quantity": 3044
      }
    }
  ]
}
```

**Key Points:**
- ✅ **Returns**: Forecast summary (not full predictions array)
- ✅ **Returns**: Inventory metrics (calculated from forecast)
- ✅ **Returns**: Actionable recommendations
- ✅ **Simple**: One result object per item

---

## Data Flow

### What Happens Behind the Scenes

1. **Forecast Generation**
   ```
   Request → Forecast Service
              ├─ Run chronos-2 (primary)
              ├─ Run statistical_ma7 (baseline)
              └─ Store both in database
   ```

2. **Method Selection**
   ```
   If chronos-2 succeeds:
     → Use chronos-2 (recommended)
   Else:
     → Use statistical_ma7 (fallback)
   ```

3. **Response Building**
   ```
   Only return recommended method results
   Include baseline summary for comparison
   ```

4. **Database Storage**
   ```
   forecast_results table:
   - One row per method per date
   - All methods stored (for future analysis)
   - Can calculate performance later
   ```

---

## Response Data Types

### Pure Forecast Response

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `forecast_id` | UUID | Unique forecast run ID | `"550e8400-..."` |
| `primary_model` | string | Model that was requested | `"chronos-2"` |
| `forecasts` | array | One per item | `[{...}]` |
| `forecasts[].item_id` | string | Item identifier | `"SKU001"` |
| `forecasts[].recommended_method` | string | Method used for predictions | `"chronos-2"` |
| `forecasts[].predictions` | array | Daily predictions | `[{date, point_forecast, quantiles}]` |
| `forecasts[].predictions[].date` | date | Forecast date | `"2024-01-02"` |
| `forecasts[].predictions[].point_forecast` | float | Median/mean prediction | `125.5` |
| `forecasts[].predictions[].quantiles` | object | Quantile predictions (uncertainty intervals) | `{"0.1": 98.2, "0.5": 125.5, "0.9": 152.8}` |
| `forecasts[].predictions[].uncertainty_range` | float | Prediction spread (90th - 10th percentile) | `54.6` |
| `forecasts[].predictions[].coefficient_of_variation` | float | Relative uncertainty (CV = std/mean) | `0.22` |
| `forecasts[].metadata` | object | Forecast metadata | `{method_used, historical_data_points, ...}` |
| `forecasts[].accuracy_indicators` | object | Historical accuracy metrics (if available) - Industry Standard | `{mape, mae, rmse, bias, ...}` |
| `forecasts[].accuracy_indicators.mape` | float | Mean Absolute Percentage Error (%) - Industry Standard | `8.2` |
| `forecasts[].accuracy_indicators.mae` | float | Mean Absolute Error (units) - Industry Standard | `10.5` |
| `forecasts[].accuracy_indicators.rmse` | float | Root Mean Squared Error - Industry Standard | `14.3` |
| `forecasts[].accuracy_indicators.bias` | float | Forecast Bias (positive=over, negative=under) - Industry Standard | `-2.1` |
| `forecasts[].accuracy_indicators.sample_size` | int | Number of past forecasts used | `45` |
| `forecasts[].baseline_comparison` | object | Baseline summary (optional) | `{method, avg_daily_demand, total_forecast_30d}` |

### Inventory Calculation Response

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `calculation_id` | UUID | Unique calculation ID | `"660e8400-..."` |
| `results` | array | One per item | `[{...}]` |
| `results[].item_id` | string | Item identifier | `"SKU001"` |
| `results[].forecast` | object | Forecast summary | `{method_used, total_forecast_30d, avg_daily_demand}` |
| `results[].inventory_metrics` | object | Calculated metrics | `{current_stock, days_remaining, ...}` |
| `results[].inventory_metrics.current_stock` | float | Current inventory | `500` |
| `results[].inventory_metrics.days_of_inventory_remaining` | float | DIR value | `3.98` |
| `results[].inventory_metrics.safety_stock` | float | Calculated safety stock | `878.5` |
| `results[].inventory_metrics.reorder_point` | float | Calculated ROP | `2546.0` |
| `results[].inventory_metrics.recommended_order_quantity` | float | Recommended order | `3044` |
| `results[].inventory_metrics.stockout_risk` | string | Risk level | `"high"` |
| `results[].inventory_metrics.stockout_date` | date | Predicted stockout | `"2024-01-05"` |
| `results[].recommendations` | object | Actionable recommendations | `{action, priority, message, ...}` |

---

## Why This Approach?

### ✅ Benefits

1. **Simple Responses**: Only return what's needed (recommended method)
2. **Fast**: Don't return unnecessary data
3. **Extensible**: Database stores everything for future analysis
4. **User-Friendly**: Clear, focused results
5. **Future-Proof**: Can add "return_all_methods" flag later

### 📊 Database vs. API Response

| Data | Database | API Response |
|------|----------|--------------|
| All method predictions | ✅ Stored | ❌ Not returned |
| Recommended method predictions | ✅ Stored | ✅ Returned |
| Baseline summary | ✅ Stored | ✅ Returned (summary only) |
| Performance metrics | ✅ Stored | ❌ Not returned (Phase 2) |
| Full method details | ✅ Stored | ❌ Not returned |

**Rationale**: Store everything, return only what's needed.

---

## Model Development Plan

### Phase 1: MVP (Current)

**Models:**
- ✅ `chronos-2` (primary)
- ✅ `statistical_ma7` (baseline)

**Features:**
- Basic forecasting
- Inventory calculations
- Database storage
- Simple responses

### Phase 2: Enhanced Statistical Methods

**Models:**
- ✅ `chronos-2` (primary)
- ✅ `statistical_ma7` (baseline)
- ➕ `statistical_ma30` (new)
- ➕ `statistical_exponential` (new)
- ➕ `naive` (new)

**Features:**
- More baseline methods
- Better comparison
- Optional "return_all_methods" flag

### Phase 3: Additional ML Models

**Models:**
- ✅ `chronos-2`
- ➕ `chronos-bolt-base` (new)
- ➕ `timesfm` (new)
- ➕ `moirai` (new)

**Features:**
- Multiple ML model options
- Model comparison
- Performance analysis

### Phase 4: Performance Analysis

**Features:**
- Performance tracking service
- Historical analysis
- Method recommendation engine
- Performance API endpoints

---

## Implementation Checklist

### MVP (Phase 1)

- [ ] Model abstraction layer (`BaseForecastModel`)
- [ ] `Chronos2Model` implementation
- [ ] `StatisticalMA7Model` implementation
- [ ] `ModelFactory` for model creation
- [ ] `ForecastService` with method selection
- [ ] Database models (`ForecastRun`, `ForecastResult`)
- [ ] Pure forecast endpoint
- [ ] Inventory calculation endpoint
- [ ] Inventory calculation service
- [ ] Response schemas (simplified)

### Phase 2 (Future)

- [ ] Additional statistical methods
- [ ] "return_all_methods" option
- [ ] Performance analysis service
- [ ] Performance API endpoints

---

## Example: What Data You Get Back

### Scenario: Forecast 30 days for SKU001

**Request:**
```json
POST /api/v1/forecast
{
  "item_ids": ["SKU001"],
  "prediction_length": 30
}
```

**Response Data:**
```json
{
  "forecast_id": "abc-123",
  "primary_model": "chronos-2",
  "forecasts": [{
    "item_id": "SKU001",
    "recommended_method": "chronos-2",
    "predictions": [
      // ⭐ 30 prediction objects (one per day)
      {"date": "2024-01-02", "point_forecast": 125.5, "quantiles": {...}},
      {"date": "2024-01-03", "point_forecast": 128.3, "quantiles": {...}},
      // ... 28 more days
    ],
    "metadata": {
      "method_used": "chronos-2",
      "historical_data_points": 90
    },
    "accuracy_indicators": {  // ⭐ Only if historical data available - Industry Standard Metrics
      "mape": 8.2,  // Industry Standard
      "mae": 10.5,   // Industry Standard
      "rmse": 14.3,  // Industry Standard
      "bias": -2.1,  // Industry Standard
      "sample_size": 45
    },
    "baseline_comparison": {
      "method": "statistical_ma7",
      "avg_daily_demand": 118.3,
      "total_forecast_30d": 3549.0
    }
  }]
}
```

**What's Stored in Database (Not Returned):**
- Full predictions from `statistical_ma7` (all 30 days)
- Full predictions from `chronos-2` (all 30 days)
- Method metadata
- Performance data (for future analysis)

**What's Returned:**
- ✅ Only `chronos-2` predictions (30 days)
- ✅ Baseline summary (avg, total) for comparison
- ❌ Not: Full baseline predictions
- ❌ Not: Performance metrics
- ❌ Not: All method details

---

## Forecast Accuracy & Uncertainty Indicators

### Industry Standard Metrics (What We Return)

Based on industry best practices, we return **standard forecasting metrics** that are widely recognized and explainable to clients:

#### 1. **Prediction Intervals** (Standard - Industry Best Practice)

**Quantiles** - Standard confidence intervals used across forecasting industry:
- `0.1` percentile (10th) - Lower bound of 80% prediction interval
- `0.5` percentile (50th) - Median forecast
- `0.9` percentile (90th) - Upper bound of 80% prediction interval

**Industry Standard:** Prediction intervals are the standard way to communicate forecast uncertainty. They show the range within which actual values are expected to fall with a given probability.

**Reference:** [Prediction Intervals - Wikipedia](https://en.wikipedia.org/wiki/Prediction_interval)

#### 2. **Coefficient of Variation** (Standard - Statistical Measure)

**CV = Standard Deviation / Mean**

Standard statistical measure of relative uncertainty. Higher CV indicates more relative uncertainty.

**Industry Standard:** Widely used in statistics and forecasting to measure relative variability.

#### 3. **Historical Accuracy Metrics** (Standard - Industry Best Practice)

**MAPE (Mean Absolute Percentage Error)** - Industry standard forecast accuracy metric:
- Formula: `MAPE = (100/n) × Σ|Actual - Forecast|/Actual`
- Lower is better (e.g., 8% = good, 20% = poor)
- Industry standard for comparing forecast accuracy

**MAE (Mean Absolute Error)** - Industry standard absolute error metric:
- Formula: `MAE = (1/n) × Σ|Actual - Forecast|`
- Absolute units (e.g., 10.5 units)
- Industry standard for measuring forecast error magnitude

**RMSE (Root Mean Squared Error)** - Industry standard for penalizing large errors:
- Formula: `RMSE = √[(1/n) × Σ(Actual - Forecast)²]`
- Industry standard for forecast evaluation

**Forecast Bias** - Industry standard for detecting systematic errors:
- Formula: `Bias = (1/n) × Σ(Forecast - Actual)`
- Positive = over-forecasting, Negative = under-forecasting
- Industry standard for detecting forecast bias

**Reference:** [Forecast Accuracy Metrics - Wikipedia](https://en.wikipedia.org/wiki/Forecast_bias)

#### 4. **Uncertainty Range** (Derived from Standard Quantiles)

**Uncertainty Range = 90th percentile - 10th percentile**

Simple measure of prediction spread, derived from standard quantiles. Larger range indicates more uncertainty.

**Note:** This is a simple calculation from standard quantiles, not a custom metric.


### When Accuracy Indicators Are Available

**Available:**
- If we have past forecasts for this item
- If actual values have been backfilled
- If we've calculated performance metrics

**Not Available (First Forecast):**
- New items (no history)
- First forecast run
- Before actuals are available

**Response:**
```json
{
  "accuracy_indicators": null  // or omitted if not available
}
```

### When Accuracy Indicators Are Available

**Available:**
- If we have past forecasts for this item
- If actual values have been backfilled
- If we've calculated performance metrics

**Not Available (First Forecast):**
- New items (no history)
- First forecast run
- Before actuals are available

**Response:**
```json
{
  "accuracy_indicators": null  // or omitted if not available
}
```

---

## Summary

### MVP Response Strategy

1. **Return Only Recommended Method**: Simple, focused results
2. **Include Industry Standard Metrics**: 
   - Prediction intervals (quantiles) - Industry standard
   - Coefficient of variation - Statistical standard
   - Historical accuracy (MAPE, MAE, RMSE, Bias) - Industry standard
3. **Include Uncertainty Intervals**: Quantiles show prediction ranges (industry standard)
4. **Include Historical Accuracy**: If available (past forecasts with actuals) - Industry standard metrics
5. **Include Baseline Summary**: For comparison (not full predictions)
6. **Store Everything**: All methods in database for future analysis
7. **No Custom Metrics**: Only industry-standard, explainable metrics

### Industry Standards Compliance

**All metrics returned are industry standard:**
- ✅ **Prediction Intervals (Quantiles)**: Standard forecasting practice
- ✅ **MAPE, MAE, RMSE**: Industry standard forecast accuracy metrics
- ✅ **Forecast Bias**: Industry standard for detecting systematic errors
- ✅ **Safety Stock Formula**: APICS standard formula
- ✅ **Reorder Point Formula**: Industry standard calculation
- ✅ **Days of Inventory Remaining**: Standard inventory metric

**No custom formulas or thresholds** - everything is based on established industry standards that can be explained to clients.

### Data You Get Back

**Pure Forecast:**
- Forecast ID
- Recommended method predictions (array of daily predictions)
- Baseline comparison summary (avg, total)
- Metadata

**Inventory Calculation:**
- Calculation ID
- Forecast summary (method, totals)
- Inventory metrics (DIR, safety stock, reorder point, etc.)
- Recommendations (action, priority, message)

**Not Returned (But Stored):**
- All method predictions (only recommended returned)
- Performance metrics (Phase 2)
- Historical analysis (Phase 2)

---

## Next Steps

1. ✅ Review and approve MVP design
2. ✅ Start implementation with simplified approach
3. ✅ Add complexity incrementally (Phase 2+)

