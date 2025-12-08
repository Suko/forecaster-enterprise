# Minibambini Data - Validation Results

**Date:** 2025-12-06  
**Sample Size:** 50,000 rows (full dataset: 340,290 rows)

---

## Executive Summary

**Status:** ⚠️ **DATA IS MESSY BUT FIXABLE**

The data has quality issues but they're manageable. ETL can clean it, but forecasting will be challenging due to extreme sparsity (98.7% zero sales).

---

## Key Findings

### ✅ What's Good

| Metric | Value | Status |
|--------|-------|--------|
| **Structure** | 7 columns, all present | ✅ Good |
| **Date Range** | 2023-10-01 to 2024-04-30 (212 days) | ✅ Good |
| **Data Types** | Correct | ✅ Good |
| **Unique Products** | 184 products | ✅ Good |
| **Unique Vendors** | 13 vendors | ✅ Good |

### ⚠️ What Needs Fixing

| Issue | Count | % | Impact | Fix |
|-------|-------|---|--------|-----|
| **Missing SKUs** | 38,676 | 77.4% | High | Generate standardized SKUs |
| **Zero Sales** | 49,360 | 98.7% | High | Normal (sparse data) |
| **Negative Sales** | 43 | 0.09% | Low | Clip to 0 |
| **Negative Inventory** | 51 | 0.10% | Low | Clip to 0 |
| **Empty Rows** | ~175 | 0.35% | Low | Remove |
| **Missing Vendor** | 175 | 0.35% | Low | Fill with "Unknown" |
| **Missing Title** | 175 | 0.35% | Low | Fill with "Unknown Product" |

### 📊 Data Characteristics

**Sales Distribution:**
- Total sales: 628 units (in 50,000 rows)
- Average: 0.01 units per row
- **98.7% zero sales** ← Very sparse!
- Max sales per day: Need to check

**Inventory Distribution:**
- Average inventory: 1.76 units
- **34.4% stockouts** (inventory = 0)
- Negative inventory: 51 rows (data error)

**Time Series:**
- Date range: 212 days (7 months)
- Daily data: Yes
- Gaps: Need to check (ETL will fill)

---

## Assessment

### Can We Use This Data? ⚠️ **YES, BUT...**

**✅ Usable After ETL:**
- Structure is good
- Dates are valid
- Products are identifiable
- Issues are fixable

**⚠️ Challenges:**
1. **Extreme Sparsity (98.7% zeros)**
   - Most days have zero sales
   - Forecasting will be difficult
   - May need to filter to items with regular sales

2. **Missing SKUs (77.4%)**
   - Need to generate standardized SKUs
   - ETL script handles this

3. **Data Quality Issues**
   - Negative values (easy fix: clip to 0)
   - Empty rows (easy fix: remove)
   - Missing fields (easy fix: fill defaults)

### Recommendation

**✅ Proceed with ETL, but:**
1. **Filter items** - Only use items with regular sales (>10 sales total)
2. **Test accuracy** - Validate forecasts before production use
3. **Monitor closely** - This is sparse data, accuracy may be lower

---

## Next Steps

### 1. Run ETL ✅
```bash
python etl_to_ts_demand_daily.py
```
- Will clean all issues
- Generate SKUs
- Create full daily series

### 2. Filter Items
**Only use items with:**
- Total sales > 50 units
- Sales on > 10% of days
- At least 30 days of history

### 3. Test Accuracy
```bash
python test_forecast_accuracy.py
```
- Run forecasts on historical data
- Calculate MAPE/MAE/RMSE
- Accept only if MAPE < 50% (sparse data = lower accuracy expected)

---

## Expected Outcomes

### After ETL:
- ✅ Clean data (no negatives, no empty rows)
- ✅ Standardized SKUs (all items have SKU)
- ✅ Full daily series (no gaps)
- ✅ Ready for forecasting

### After Testing:
- ⚠️ Some items may have poor accuracy (due to sparsity)
- ✅ Filter to best items (regular sales patterns)
- ✅ Use only items with acceptable accuracy

---

## Summary

**Data Quality:** ⚠️ Messy but fixable  
**ETL Required:** ✅ Yes (will clean all issues)  
**Forecasting Viability:** ⚠️ **VERY LIMITED** (only 4 items suitable)  
**Recommendation:** ✅ Proceed with ETL, but focus on the 4 items with regular sales

**Bottom Line:** 
- ✅ Data can be cleaned and used
- ⚠️ Only 4 items have regular sales patterns (suitable for forecasting)
- ⚠️ 98.7% zero sales = very sparse data
- ✅ Use these 4 items for testing forecast accuracy
- ⚠️ Don't expect high accuracy due to extreme sparsity

### Items Suitable for Testing (4 items):
1. **Snugi - Merino čizme Snugi - braon** (34 sales, 6% frequency)
2. **BeSafe - Ogledalo BeSafe** (22 sales, 6% frequency)
3. **Snugi - Merino čizme Snugi - braon** (variant, 22 sales, 5.1% frequency)
4. **Carriwell - Steznik poslije porođaja** (21 sales, 5.9% frequency)

