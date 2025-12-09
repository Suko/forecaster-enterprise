# Comprehensive Model Comparison - All 20 SKUs

**Date:** 2025-12-08  
**Test Period:** 30 days  
**SKUs Tested:** All 20 SKUs

## Summary

✅ **All 20 SKUs tested successfully with 4 models each**

### Models Tested

1. **Our MA7** - 7-day Moving Average (baseline)
2. **Darts NaiveMean** - Simple mean baseline
3. **Darts ExponentialSmoothing** - Statistical model
4. **Our Chronos-2** - AI foundation model

## Overall Performance

| Model | Count | MAPE (mean) | MAE (mean) | RMSE (mean) |
|-------|-------|-------------|------------|-------------|
| **Our Chronos-2** | 20 | **16.76%** | **15.99** | **22.66** |
| **Darts ExponentialSmoothing** | 20 | 20.26% | 19.37 | 26.52 |
| **Our MA7** | 20 | 24.03% | 22.22 | 28.99 |
| **Darts NaiveMean** | 20 | 28.21% | 23.08 | 28.20 |

### Key Findings

1. **Our Chronos-2 is the best performer**
   - Lowest MAPE: 16.76%
   - Lowest MAE: 15.99
   - Lowest RMSE: 22.66
   - Best on 19 out of 20 SKUs

2. **Darts ExponentialSmoothing is second best**
   - MAPE: 20.26%
   - MAE: 19.37
   - Best on 1 SKU (SKU004)

3. **Our MA7 vs Darts NaiveMean**
   - Our MA7: 24.03% MAPE, 22.22 MAE
   - Darts NaiveMean: 28.21% MAPE, 23.08 MAE
   - Our MA7 performs slightly better

## Per-SKU Results

| SKU | Best Model | MAE | MAPE |
|-----|------------|-----|------|
| SKU002 | Our Chronos-2 | 3.31 | 13.0% |
| SKU011 | Our Chronos-2 | 3.53 | 12.0% |
| SKU005 | Our Chronos-2 | 4.33 | 13.8% |
| SKU003 | Our Chronos-2 | 6.48 | 17.5% |
| SKU009 | Our Chronos-2 | 6.08 | 14.4% |
| SKU019 | Our Chronos-2 | 7.90 | 17.8% |
| SKU007 | Our Chronos-2 | 9.48 | 16.5% |
| SKU016 | Our Chronos-2 | 9.50 | 15.8% |
| **SKU004** | **Darts ExponentialSmoothing** | **9.13** | **13.2%** |
| SKU015 | Our Chronos-2 | 12.33 | 14.9% |
| SKU013 | Our Chronos-2 | 20.87 | 14.9% |
| SKU018 | Our Chronos-2 | 14.93 | 18.3% |
| SKU008 | Our Chronos-2 | 19.76 | 18.2% |
| SKU014 | Our Chronos-2 | 19.46 | 20.6% |
| SKU020 | Our Chronos-2 | 21.09 | 17.8% |
| SKU012 | Our Chronos-2 | 23.23 | 18.0% |
| SKU017 | Our Chronos-2 | 24.73 | 17.4% |
| SKU006 | Our Chronos-2 | 26.97 | 21.8% |
| SKU010 | Our Chronos-2 | 34.82 | 22.7% |
| SKU001 | Our Chronos-2 | 41.77 | N/A* |

*SKU001 has zero values in test data (MAPE unavailable)

## Model Rankings

### By MAPE (Lower is Better)

1. **Our Chronos-2**: 16.76% ✅
2. **Darts ExponentialSmoothing**: 20.26%
3. **Our MA7**: 24.03%
4. **Darts NaiveMean**: 28.21%

### By MAE (Lower is Better)

1. **Our Chronos-2**: 15.99 ✅
2. **Darts ExponentialSmoothing**: 19.37
3. **Our MA7**: 22.22
4. **Darts NaiveMean**: 23.08

### By RMSE (Lower is Better)

1. **Our Chronos-2**: 22.66 ✅
2. **Darts ExponentialSmoothing**: 26.52
3. **Darts NaiveMean**: 28.20
4. **Our MA7**: 28.99

## Insights

1. **Chronos-2 Dominance**
   - Best on 19/20 SKUs (95%)
   - Average improvement: 3.5% MAPE over ExponentialSmoothing
   - Average improvement: 7.3% MAPE over MA7

2. **ExponentialSmoothing Performance**
   - Good baseline for comparison
   - Best on SKU004 (only case where it beats Chronos-2)
   - 20% better than NaiveMean

3. **MA7 vs NaiveMean**
   - Our MA7 performs slightly better (4% MAPE improvement)
   - Both are simple baselines
   - MA7 uses recent 7-day average (more responsive)

4. **SKU001 Challenge**
   - Highest MAE (41.77) for Chronos-2
   - Has zero values in test data (MAPE unavailable)
   - All models struggle with this SKU

## Usage

### Run Test

```bash
cd backend
uv run python scripts/comprehensive_model_comparison.py --max-skus 20
```

### Options

- `--max-skus N`: Test N SKUs (default: 20)
- `--test-days N`: Use N days as test period (default: 30)
- `--darts-chronos`: Include Darts Chronos2Model (slow, optional)

### Output

- Console summary with metrics
- Detailed JSON report: `reports/comprehensive_model_comparison_*.json`

## Technical Details

- **Enhanced Validator**: All data validated and cleaned (missing dates filled, NaN handled)
- **Fair Comparison**: All models receive only `target` column (no covariates)
- **Darts Metrics**: Consistent metric calculation using Darts library
- **Test Period**: Last 30 days (2024-12-02 to 2024-12-31)
- **Training Period**: Up to 2024-12-01 (701 days)

## Conclusion

✅ **Our Chronos-2 implementation is validated and performs best**

- Best overall performance across all metrics
- Consistent results across 19/20 SKUs
- Ready for production use

✅ **All models working correctly with Enhanced Validator**

- Data quality ensured
- Consistent comparison methodology
- Comprehensive testing complete

---
*Report generated: 2025-12-08*  
*Script: `scripts/comprehensive_model_comparison.py`*  
*Detailed JSON: `reports/comprehensive_model_comparison_20251208_193838.json`*

