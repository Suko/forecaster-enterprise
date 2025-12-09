# Data Flow Documentation Standard

**Purpose:** Document the complete data flow for AI/model investigation and debugging.

**Standard:** ML Observability Best Practices (MLOps)

**Status:** **Phase 1 MVP - Required for Testing/Development**

> ⚠️ **Important:** This validation and audit system is **critical for testing and development** before moving to Phase 2. It ensures we fully control and understand the data flow before adding more features. In production, audit logging can be disabled via `ENABLE_AUDIT_LOGGING=false` to reduce overhead, but validation always runs.

---

## Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW PIPELINE                           │
└─────────────────────────────────────────────────────────────────┘

1. INPUT (Raw Data)
   ↓
   [DataAccess.fetch_historical_data()]
   - Source: ts_demand_daily table
   - Filter: client_id, item_ids, date_range
   - Output: DataFrame with columns [id, timestamp, target, covariates]
   ↓
   
2. VALIDATION
   ↓
   [DataValidator.validate_context_data()]
   - Check: required columns, date range, data quality
   - Report: statistics, missing values, gaps
   - Log: validation report to audit trail
   ↓
   
3. MODEL INPUT (Validated Data)
   ↓
   [Model.predict(context_df)]
   - Input: Validated DataFrame
   - Model: Chronos-2 or MA7
   - Output: Predictions DataFrame
   ↓
   
4. VALIDATION
   ↓
   [DataValidator.validate_predictions()]
   - Check: prediction count, required columns, nulls
   - Report: forecast statistics
   - Log: output validation to audit trail
   ↓
   
5. OUTPUT (Predictions)
   ↓
   [ForecastService._store_results()]
   - Store: forecast_results table
   - Fields: date, point_forecast, quantiles
   ↓
   
6. COMPARISON (Actuals vs Forecasts)
   ↓
   [QualityCalculator.calculate_quality_metrics()]
   - Input: Forecasts + Actuals (backfilled)
   - Calculate: MAPE, MAE, RMSE, Bias
   - Output: Quality metrics
```

---

## Audit Trail Format

Every forecast run should log:

### 1. INPUT Stage
```json
{
  "stage": "INPUT",
  "item_id": "SKU019",
  "method": "chronos-2",
  "timestamp": "2024-12-08T15:00:00Z",
  "data_summary": {
    "row_count": 701,
    "date_range": {"start": "2023-01-01", "end": "2024-12-01"},
    "target_stats": {
      "mean": 50.06,
      "std": 18.54,
      "min": 0.0,
      "max": 150.0
    },
    "columns": ["id", "timestamp", "target", "promo_flag", ...]
  },
  "validation": {
    "is_valid": true,
    "warnings": ["2 date gaps detected"],
    "data_quality_issues": []
  }
}
```

### 2. OUTPUT Stage
```json
{
  "stage": "OUTPUT",
  "item_id": "SKU019",
  "method": "chronos-2",
  "timestamp": "2024-12-08T15:00:05Z",
  "predictions_summary": {
    "count": 30,
    "date_range": {"start": "2024-12-02", "end": "2024-12-31"},
    "forecast_stats": {
      "mean": 45.25,
      "min": 37.26,
      "max": 65.90
    }
  },
  "validation": {
    "is_valid": true,
    "issues": []
  }
}
```

### 3. COMPARISON Stage
```json
{
  "stage": "COMPARISON",
  "item_id": "SKU019",
  "timestamp": "2024-12-08T15:00:10Z",
  "comparison_summary": {
    "sample_size": 30,
    "date_range": {"start": "2024-12-02", "end": "2024-12-31"},
    "metrics": {
      "mape": 18.14,
      "mae": 8.06,
      "rmse": 10.53,
      "bias": -2.55
    }
  }
}
```

---

## Validation Checks

### Input Validation (Before Model)
- ✅ Required columns present (id, timestamp, target)
- ✅ Minimum history (7+ days)
- ✅ No null timestamps
- ✅ Date range valid
- ✅ Target values numeric
- ⚠️ Warnings: date gaps, null values, negative values

### Output Validation (After Model)
- ✅ Prediction count matches request
- ✅ Required columns (timestamp, point_forecast)
- ✅ No null predictions
- ⚠️ Warnings: negative predictions (unusual for sales)

---

## Storage

**Audit trails stored in:**
- `ForecastRun` model (future: add `audit_metadata` JSONB column)
- Log files (optional, for debugging)
- Database: `forecast_runs` table (metadata)

**Query audit trail:**
```sql
SELECT forecast_run_id, created_at, primary_model, item_ids, error_message
FROM forecast_runs
WHERE client_id = '...'
ORDER BY created_at DESC;
```

---

## Configuration

**Audit Logging** is enabled by default in development/testing environments.

To control audit logging:
```bash
# Enable (default in dev/test)
ENABLE_AUDIT_LOGGING=true

# Disable (production - reduces overhead)
ENABLE_AUDIT_LOGGING=false
```

**Note:** Data validation always runs regardless of audit logging setting. Audit logging only controls whether detailed audit trails are stored.

## Best Practices

1. **Always validate** before sending to model (validation always runs)
2. **Enable audit logging** in testing/development (default)
3. **Log data summaries** (not full data - too large)
4. **Track transformations** at each stage
5. **Store metadata** in database for querying
6. **Make it queryable** for AI/investigation tools
7. **Disable in production** if performance is critical (validation still runs)

---

## For AI/Investigation

**Query pattern:**
```
"Show me all forecasts for SKU019 where input data had issues"
→ Check validation reports in audit trail

"What data was sent to Chronos-2 for forecast run X?"
→ Check INPUT stage in audit trail

"Why did accuracy drop for this item?"
→ Compare validation reports across runs
```

