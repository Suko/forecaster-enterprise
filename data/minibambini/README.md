# Minibambini Data - Validation & ETL

**Purpose:** Validate messy data and create clean ETL pipeline for forecasting

---

## Quick Start

### 1. Validate Data Quality

```bash
cd /Users/mihapro/Development/ecommerce/forecaster_enterprise/data/minibambini
python validate_data.py
```

This will:
- ✅ Check data structure
- ✅ Validate dates, sales, inventory
- ✅ Detect anomalies
- ✅ Generate validation report

### 2. Run ETL

```bash
python etl_to_ts_demand_daily.py
```

This will:
- ✅ Clean messy data
- ✅ Generate standardized SKUs
- ✅ Create full daily series (fill gaps)
- ✅ Transform to `ts_demand_daily` format
- ✅ Save as `ts_demand_daily_clean.csv`

### 3. Test Forecast Accuracy

```bash
python test_forecast_accuracy.py
```

This will:
- ✅ Load cleaned data
- ✅ Run forecasts on historical data
- ✅ Compare predictions vs actuals
- ✅ Calculate MAPE/MAE/RMSE

---

## Data Files

| File | Rows | Purpose |
|------|------|---------|
| `minibambini.csv` | 340,290 | Raw messy data |
| `updated_vendors.csv` | 315,823 | Updated vendor data |
| `ts_demand_daily_clean.csv` | TBD | Clean ETL output |

---

## Validation Checklist

### ✅ Structure Validation
- [x] Required columns present
- [x] Data types correct
- [x] No completely empty rows

### ✅ Data Quality
- [x] Dates valid and in range
- [x] Sales non-negative
- [x] Inventory non-negative
- [x] Products have vendor/title

### ✅ Anomaly Detection
- [x] Sales spikes detected
- [x] Inventory jumps detected
- [x] Missing days in time series

---

## ETL Process

### Step 1: Load & Clean
- Remove empty rows
- Convert dates
- Convert sales/inventory to numeric
- Fill missing values

### Step 2: Generate SKUs
- Format: `MB-{VENDOR}-{PRODUCT_HASH}-{VARIANT_HASH}`
- Example: `MB-SNUGI-A3F2B1-EU20`

### Step 3: Create Full Daily Series
- Fill gaps with zero-demand days
- One row per (item_id, date)

### Step 4: Transform to ts_demand_daily
- Map to standard schema
- Add calendar features
- Add stockout flags

---

## Known Issues

### Data Quality Issues
1. **Missing SKUs:** 71% of rows have no SKU → Generated standardized SKUs
2. **Empty rows:** Some completely empty rows → Removed
3. **Date gaps:** Missing days in time series → Filled with zeros
4. **Negative values:** Some negative sales/inventory → Clipped to 0

### Anomalies Detected
- Sales spikes (sudden large increases)
- Inventory jumps (sudden large changes)
- Missing days (gaps in time series)

---

## Approach Summary

### Step 1: Validate First ✅
**Before doing anything, validate the data:**
- Check structure (columns, types)
- Validate dates, sales, inventory
- Detect anomalies (spikes, gaps, errors)
- **Don't proceed if validation fails!**

### Step 2: Clean & Transform ✅
**ETL process:**
- Remove empty/invalid rows
- Generate standardized SKUs
- Create full daily series (fill gaps)
- Transform to `ts_demand_daily` format

### Step 3: Test Accuracy ✅
**Validate forecasting works:**
- Split data into train/test
- Run forecasts on historical data
- Compare predictions vs actuals
- Calculate MAPE/MAE/RMSE
- **Only use if accuracy is acceptable!**

### Step 4: Identify Best Items
**Find items suitable for forecasting:**
- Stable sales patterns
- Sufficient history (30+ days)
- Not too many zeros
- Good accuracy in tests

---

## Next Steps

1. ✅ **Validate data** - Run `validate_data.py`
2. ✅ **Run ETL** - Run `etl_to_ts_demand_daily.py`
3. ✅ **Test accuracy** - Run `test_forecast_accuracy.py`
4. **Identify best items** - Use items with good accuracy
5. **Create production ETL** - Based on validated script

---

## Files

- `validate_data.py` - Data validation script
- `etl_to_ts_demand_daily.py` - ETL transformation script
- `test_forecast_accuracy_simple.py` - Forecast accuracy testing (standalone)
- `DATA_QUALITY_APPROACH.md` - **Read this first!** Complete approach
- `VALIDATION_RESULTS.md` - Validation findings
- `FORECAST_TEST_RESULTS.md` - **Test results summary**
- `validation_report_sample.json` - Validation results
- `etl_summary.json` - ETL summary
- `forecast_accuracy_results.json` - Accuracy test results
- `ts_demand_daily_clean.csv` - **Cleaned data ready for forecasting** (141 MB)


---

## Data Quality Approach

### Workflow: Validate → Clean → Test → Use

```
┌─────────────────────────────────────────────────────────┐
│  1. VALIDATE DATA                                       │
│     python validate_data.py                             │
│     ✅ Structure OK? ✅ Quality OK? ✅ Anomalies OK?    │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  2. RUN ETL                                             │
│     python etl_to_ts_demand_daily.py                   │
│     ✅ Clean ✅ Generate SKUs ✅ Fill gaps ✅ Transform │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  3. TEST ACCURACY                                       │
│     python test_forecast_accuracy_simple.py            │
│     ✅ Split data ✅ Forecast ✅ Calculate MAPE/MAE    │
└───────────────────────┬─────────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────────┐
│  4. USE IN PRODUCTION                                   │
│     Only items with acceptable accuracy                 │
└─────────────────────────────────────────────────────────┘
```

### Acceptance Criteria

| MAPE | Decision |
|------|----------|
| < 30% | ✅ Good - Use in production |
| 30-50% | ⚠️ Acceptable - Review before use |
| > 50% | ❌ Reject - Data too messy |

### Key Principles

1. **Validate First** - Never skip validation
2. **Clean Thoroughly** - Fix all issues before forecasting
3. **Test Accuracy** - Don't trust forecasts without testing
4. **Reject Bad Data** - Better to reject than produce bad forecasts
5. **Monitor Continuously** - Re-validate as new data arrives
