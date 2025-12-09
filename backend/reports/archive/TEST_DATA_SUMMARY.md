# Test Data Summary - Which SKUs Were Tested?

## Database Status

✅ **Total SKUs in database: 20**
✅ **All 20 SKUs have 731 days of data** (2023-01-01 to 2024-12-31)

## Tests Run

### 1. **Comprehensive Test (All 20 SKUs)** ✅

**Script:** `tests/test_forecast_accuracy.py`

**Report:** `reports/forecast_accuracy_report_20251208_175335.json`

**SKUs Tested:** All 20 SKUs
- SKU001, SKU002, SKU003, SKU004, SKU005
- SKU006, SKU007, SKU008, SKU009, SKU010
- SKU011, SKU012, SKU013, SKU014, SKU015
- SKU016, SKU017, SKU018, SKU019, SKU020

**Results:**
- ✅ All 20 SKUs tested successfully
- ✅ Both Chronos-2 and MA7 models tested
- ✅ Comprehensive accuracy metrics generated
- ✅ Full report saved to JSON

**Usage:**
```bash
cd backend
uv run python tests/test_forecast_accuracy.py
```

---

### 2. **Quick Validation Tests (5 SKUs)** ⚡

**Scripts:**
- `scripts/compare_darts_vs_ours.py` - Darts vs Our Chronos-2
- `scripts/test_ma7_with_enhanced_validator.py` - MA7 validation

**SKUs Tested:** First 5 SKUs (LIMIT 5)
- SKU010, SKU001, SKU008, SKU016, SKU019

**Purpose:**
- Quick validation of implementation
- Comparison with Darts reference
- Testing enhanced validator

**Why only 5?**
- Faster execution for quick validation
- Representative sample
- Full 20 SKU test takes longer

---

## Summary

| Test Type | SKUs Tested | Purpose | Status |
|-----------|-------------|---------|--------|
| **Comprehensive** | All 20 | Full accuracy report | ✅ Complete |
| **Darts Comparison** | 5 | Implementation validation | ✅ Complete |
| **MA7 Validation** | 5 | Enhanced validator test | ✅ Complete |

## All 20 SKUs Available

All 20 SKUs have complete data (731 days each):

1. SKU001 - SKU020 (all with 731 days)

## Run Full Test on All 20 SKUs

If you want to test all 20 SKUs with the enhanced validator:

```bash
cd backend
uv run python tests/test_forecast_accuracy.py
```

This will:
- Test all 20 SKUs
- Use enhanced validator (with missing dates filled, NaN handled)
- Generate comprehensive report
- Compare Chronos-2 vs MA7 for all SKUs

## Recent Test Results

### Comprehensive Test (20 SKUs)
- ✅ All 20 SKUs successful
- ✅ Chronos-2 average MAPE: ~20%
- ✅ MA7 average MAPE: ~20%
- ✅ Report: `forecast_accuracy_report_20251208_175335.json`

### Quick Validation (5 SKUs)
- ✅ Darts comparison: 1.2% average difference
- ✅ MA7 validation: Working correctly
- ✅ Enhanced validator: Working correctly

---
*Last updated: 2025-12-08*

