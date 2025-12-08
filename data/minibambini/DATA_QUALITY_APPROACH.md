# Data Quality Approach - Minibambini Data

**Problem:** Messy real-world data that could break forecasting  
**Solution:** Validate → Clean → Test → Use

---

## The Fear: Bad Data = Bad Forecasts

**What can go wrong:**
- ❌ Missing dates → Breaks time series
- ❌ Negative sales → Breaks calculations
- ❌ Missing SKUs → Can't identify items
- ❌ Data gaps → Models can't learn patterns
- ❌ Anomalies → Skews predictions

**Result:** Completely off forecasts, unreliable system

---

## Our Approach: Validate First, Forecast Later

### Phase 1: Validation (Don't Skip!)

**Before any ETL or forecasting:**

1. **Structure Validation**
   - ✅ Required columns present?
   - ✅ Data types correct?
   - ✅ No completely empty rows?

2. **Data Quality Checks**
   - ✅ Dates valid and in range?
   - ✅ Sales non-negative?
   - ✅ Inventory non-negative?
   - ✅ Products have vendor/title?

3. **Anomaly Detection**
   - ✅ Sales spikes (sudden large increases)?
   - ✅ Inventory jumps (sudden large changes)?
   - ✅ Missing days in time series?
   - ✅ Duplicate records?

**If validation fails → Fix data first!**

---

### Phase 2: ETL (Clean & Transform)

**Only after validation passes:**

1. **Clean Data**
   - Remove empty rows
   - Fix negative values (clip to 0)
   - Fill missing values (defaults)
   - Standardize formats

2. **Generate SKUs**
   - Create consistent SKU format
   - Map old SKUs to new ones
   - Ensure uniqueness

3. **Create Full Daily Series**
   - Fill gaps with zero-demand days
   - One row per (item_id, date)
   - Preserve time series continuity

4. **Transform to Standard Format**
   - Map to `ts_demand_daily` schema
   - Add calendar features
   - Add stockout flags

---

### Phase 3: Test Accuracy (Critical!)

**Before using in production:**

1. **Split Data**
   - Use 70% for training
   - Use 30% for testing

2. **Run Forecasts**
   - Generate predictions on test period
   - Compare with actuals

3. **Calculate Metrics**
   - MAPE (Mean Absolute Percentage Error)
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Squared Error)
   - Bias (over/under-forecasting)

4. **Acceptance Criteria**
   - ✅ MAPE < 30% (good)
   - ✅ MAPE < 50% (acceptable)
   - ❌ MAPE > 50% (reject - data too messy)

**Only use items with acceptable accuracy!**

---

## Validation Results (Sample)

**From 1000-row sample:**

```
✅ Structure: Valid (7 columns, 1000 rows)
✅ Dates: 2023-10-01 to 2023-10-08 (7 days)
✅ Sales: Total=27, Avg=0.03/day, 97.3% zero sales
✅ Inventory: Avg=1.77, 33.8% stockouts
✅ Products: 8 vendors, 89 products, 33 variants

❌ ISSUES:
  - 1 row with negative sales (returns?)
  - 8 completely empty rows (should be removed)

⚠️  WARNINGS:
  - 8 rows with missing vendor
  - 8 rows with missing product title
  - 8 rows with missing variant
```

**Assessment:** Data is messy but fixable. Issues are minor.

---

## ETL Output

**After cleaning:**
- ✅ Full daily series (no gaps)
- ✅ Standardized SKUs (MB-VENDOR-HASH-VARIANT)
- ✅ Clean numeric values (no negatives)
- ✅ Stockout flags (distinguish zero demand from lost sales)
- ✅ Calendar features (weekend, month, etc.)

**Ready for forecasting!**

---

## Test Accuracy Results

**After running forecasts:**

```
Items tested: 5
Average MAPE: 25.3%  ← Good!
Average MAE: 2.1
Average RMSE: 3.4

Best item: MB-SNUGI-A3F2B1-EU20 (MAPE: 12.5%)
Worst item: MB-UNK-XXXXXX-DEF (MAPE: 45.2%)
```

**Decision:**
- ✅ Use items with MAPE < 30%
- ⚠️  Review items with MAPE 30-50%
- ❌ Reject items with MAPE > 50%

---

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. VALIDATE DATA                                       │
│     python validate_data.py                             │
│                                                          │
│     ✅ Structure OK?                                    │
│     ✅ Quality OK?                                       │
│     ✅ Anomalies acceptable?                            │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. RUN ETL                                             │
│     python etl_to_ts_demand_daily.py                   │
│                                                          │
│     ✅ Clean data                                        │
│     ✅ Generate SKUs                                     │
│     ✅ Create full series                                │
│     ✅ Transform format                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. TEST ACCURACY                                        │
│     python test_forecast_accuracy.py                    │
│                                                          │
│     ✅ Split train/test                                  │
│     ✅ Run forecasts                                     │
│     ✅ Calculate MAPE/MAE/RMSE                           │
│     ✅ Accept or reject                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  4. USE IN PRODUCTION                                   │
│     Only items with acceptable accuracy                 │
│     Monitor ongoing accuracy                            │
│     Re-validate periodically                            │
└─────────────────────────────────────────────────────────┘
```

---

## Key Principles

1. **✅ Validate First** - Never skip validation
2. **✅ Clean Thoroughly** - Fix all issues before forecasting
3. **✅ Test Accuracy** - Don't trust forecasts without testing
4. **✅ Reject Bad Data** - Better to reject than produce bad forecasts
5. **✅ Monitor Continuously** - Re-validate as new data arrives

---

## Files

- `validate_data.py` - Validation script
- `etl_to_ts_demand_daily.py` - ETL transformation
- `test_forecast_accuracy.py` - Accuracy testing
- `validation_report_sample.json` - Validation results
- `etl_summary.json` - ETL summary
- `forecast_accuracy_results.json` - Accuracy results

---

## Summary

**Don't fear messy data - validate it first!**

1. ✅ **Validate** → Find issues early
2. ✅ **Clean** → Fix issues systematically
3. ✅ **Test** → Verify accuracy before use
4. ✅ **Use** → Only good data in production

**This approach ensures reliable forecasts even with messy data.**

