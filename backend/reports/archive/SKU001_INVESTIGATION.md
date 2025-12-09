# SKU001 Investigation: Why 34.6% Difference?

## Problem
SKU001 showed a 34.6% difference between Darts Chronos2Model (MAE: 42.60) and our implementation (MAE: 57.34).

## Root Cause: **Covariates**

### The Issue
- **Our model** receives covariates: `promo_flag`, `holiday_flag`, `is_weekend`, `marketing_spend`
- **Darts Chronos2Model** in comparison script only receives `target` column
- **Chronos-2 pipeline** uses these covariates to make predictions, causing different (and in this case, worse) results

### Test Results

| Configuration | MAE | Difference from Darts |
|--------------|-----|---------------------|
| Darts (no covariates) | 42.60 | Baseline |
| Our model (WITH covariates) | 57.34 | **+34.6%** ❌ |
| Our model (WITHOUT covariates) | 41.77 | **-1.9%** ✅ |

## Findings

1. **Without covariates, our model matches Darts almost perfectly** (1.9% difference)
2. **With covariates, our model performs worse** (34.6% difference)
3. **Zero sales days are NOT the issue** - both models handle them similarly
4. **The problem is how covariates are being used** - they're making predictions worse for SKU001

## Data Analysis

- **Training data**: 701 days, mean sales: 161.07, CV: 39.8%
- **Test data**: 30 days, mean sales: 121.23, 4 zero-sales days (13.3%)
- **Zero sales days**: Both models predict non-zero values, but difference is small (8-21 units)

## Recommendations

### Option 1: Make Comparison Fair
- Give Darts the same covariates (if it supports them)
- Or remove covariates from our model for comparison

### Option 2: Investigate Covariate Usage
- Check if Chronos-2 is using covariates correctly
- Verify covariate data quality (especially `marketing_spend` which is object type)
- Consider if covariates should be used for this SKU

### Option 3: Conditional Covariate Usage
- Only use covariates when they improve accuracy
- Test each SKU to determine if covariates help or hurt

## Next Steps

1. ✅ **Identified root cause**: Covariates
2. ⏳ **Investigate**: Why do covariates make predictions worse for SKU001?
3. ⏳ **Test**: Do covariates help or hurt for other SKUs?
4. ⏳ **Decide**: Should we use covariates conditionally or always?

## Conclusion

The 34.6% difference is **NOT a bug** - it's because our model uses covariates while Darts doesn't. However, for SKU001, covariates are making predictions worse. This suggests we need to:

1. **Validate covariate quality** (especially `marketing_spend`)
2. **Test covariate impact** across all SKUs
3. **Consider conditional covariate usage** based on SKU characteristics

---
*Investigation date: 2025-12-08*
*Script: `backend/scripts/investigate_sku001.py`*

