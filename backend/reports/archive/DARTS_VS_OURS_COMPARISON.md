# Darts Chronos2Model vs Our Custom Implementation

**Purpose:** Validate our custom Chronos-2 implementation against Darts' reference implementation.

**Reference:** [Darts Chronos2Model Documentation](https://unit8co.github.io/darts/generated_api/darts.models.forecasting.chronos2_model.html)

## How to Run

```bash
cd backend
uv run python scripts/compare_darts_vs_ours.py
```

## What It Tests

1. **Same Data**: Both models use identical training and test data from database
2. **Same Input**: Both receive only `target` column (covariates removed for fair comparison)
3. **Same Model**: Both use Chronos-2 (same underlying model)
4. **Compare Results**: Metrics (MAPE, MAE, RMSE) and prediction values

## Latest Results (Without Covariates)

**✅ Validation PASSED** - Our implementation matches Darts almost perfectly!

| Metric | Average Difference |
|--------|-------------------|
| **MAE** | **1.2%** (min: 0.3%, max: 1.9%) |
| **RMSE** | **0.8%** (min: 0.3%, max: 1.2%) |

### Per-SKU Results

| SKU | Darts MAE | Our MAE | Difference |
|-----|-----------|---------|------------|
| SKU019 | 7.88 | 7.90 | **0.3%** ✅ |
| SKU008 | 19.60 | 19.76 | **0.8%** ✅ |
| SKU010 | 35.22 | 34.82 | **1.1%** ✅ |
| SKU016 | 9.65 | 9.50 | **1.6%** ✅ |
| SKU001 | 42.60 | 41.77 | **1.9%** ✅ |

## Interpretation

- **✅ < 2% difference**: Excellent - implementations are equivalent
- **✅ 2-5% difference**: Good - acceptable variation
- **⚠️ 5-10% difference**: May indicate minor implementation differences
- **❌ > 10% difference**: May indicate implementation or data handling issues

## Notes

- **Covariates removed**: For fair comparison, both models receive only `target` column
- **Covariates in Phase 2**: Covariate handling will be validated separately in Phase 2
- **Darts Chronos2Model**: Requires `fit()` even though it's a foundation model
- **Mac (MPS)**: Use `to_cpu()` to avoid float64 issues
- **Validation**: Results confirm our Chronos-2 implementation is correct ✅

## Previous Results (With Covariates)

When covariates were included, SKU001 showed 34.6% difference. Investigation revealed:
- Our model received covariates (`promo_flag`, `holiday_flag`, `is_weekend`, `marketing_spend`)
- Darts model received only `target` column
- This caused unfair comparison - see `SKU001_INVESTIGATION.md` for details

---
*Last updated: 2025-12-08*

