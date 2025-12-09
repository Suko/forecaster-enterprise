# Evaluation Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for evaluating forecasting model performance and accuracy.

---

## 1. Primary Metrics

### MAPE (Mean Absolute Percentage Error)

**Formula:**
```
MAPE = (1/n) × Σ |actual - forecast| / actual × 100%
```

**Interpretation:**
| MAPE | Interpretation |
|------|----------------|
| < 10% | Excellent |
| 10-20% | Good |
| 20-50% | Acceptable |
| 50-100% | Challenging |
| > 100% | Poor |

**Notes:**
- Primary metric for forecast accuracy
- Undefined when actual = 0 (use WMAPE instead)
- Scale-independent (comparable across SKUs)

### MAE (Mean Absolute Error)

**Formula:**
```
MAE = (1/n) × Σ |actual - forecast|
```

**Use Case:**
- Compare models on same scale
- Understand absolute error magnitude
- More intuitive than MAPE

### RMSE (Root Mean Squared Error)

**Formula:**
```
RMSE = √[(1/n) × Σ (actual - forecast)²]
```

**Use Case:**
- Penalize large errors
- Sensitive to outliers
- Compare model stability

### Bias

**Formula:**
```
Bias = (1/n) × Σ (forecast - actual)
```

**Interpretation:**
| Bias | Meaning |
|------|---------|
| > 0 | Over-forecasting |
| < 0 | Under-forecasting |
| ≈ 0 | Unbiased |

---

## 2. Secondary Metrics

### WMAPE (Weighted Mean Absolute Percentage Error)

**Formula:**
```
WMAPE = Σ |actual - forecast| / Σ actual × 100%
```

**Use Case:**
- Aggregate accuracy across multiple SKUs
- Handles zero actuals better than MAPE
- Preferred for portfolio-level reporting

### Directional Accuracy

**Formula:**
```
DA = % of periods where sign(actual_change) = sign(forecast_change)
```

**Use Case:**
- Trend prediction accuracy
- Important for planning decisions

### Coverage (Prediction Intervals)

**Formula:**
```
Coverage = % of actuals within [P10, P90]
```

**Target:** 80% coverage expected for 10-90 interval

---

## 3. Evaluation by SKU Classification

### Expected Performance

| Classification | Target MAPE | Minimum MAPE | Maximum MAPE |
|----------------|-------------|--------------|--------------|
| A-X | 15% | 10% | 25% |
| A-Y | 30% | 20% | 40% |
| A-Z | 45% | 30% | 60% |
| B-X | 20% | 15% | 30% |
| B-Y | 35% | 25% | 50% |
| B-Z | 55% | 40% | 70% |
| C-* | 75% | 50% | 100% |
| Lumpy | 70% | 50% | 90% |
| Intermittent | 60% | 40% | 80% |

### Evaluation Criteria

| Result | Criteria |
|--------|----------|
| ✅ Pass | MAPE ≤ Maximum expected |
| ⚠️ Warning | MAPE > Maximum but < 2× Maximum |
| ❌ Fail | MAPE > 2× Maximum expected |

---

## 4. Model Comparison Standards

### Required Comparisons

1. **New model vs. baseline (MA7)**
2. **New model vs. current production**
3. **Model with/without covariates**

### Comparison Metrics

| Comparison | Primary Metric | Secondary |
|------------|----------------|-----------|
| Overall accuracy | WMAPE | MAE, RMSE |
| Per-SKU accuracy | MAPE | MAE |
| Consistency | Std(MAPE) | Range |
| Bias | Mean Bias | Bias % |

### Statistical Significance

- Minimum 20 SKUs for valid comparison
- Report confidence intervals
- Use paired tests when applicable

---

## 5. Forecast Horizon Evaluation

### Accuracy Degradation

| Horizon Day | Expected MAPE Increase |
|-------------|------------------------|
| Day 1 | Baseline |
| Day 3 | +10-20% |
| Day 7 | +20-40% |
| Day 14 | +40-60% |
| Day 30 | +60-100% |

### Horizon-Specific Targets

| Horizon | A-X Target | A-Y Target | A-Z Target |
|---------|------------|------------|------------|
| 1 day | 10% | 20% | 30% |
| 7 days | 15% | 30% | 45% |
| 30 days | 25% | 50% | 75% |

---

## 6. Reporting Standards

### Required Report Elements

1. **Summary statistics**
   - Mean MAPE across all SKUs
   - Median MAPE
   - % within expected range

2. **Per-classification breakdown**
   - MAPE by ABC class
   - MAPE by XYZ class
   - MAPE by demand pattern

3. **Outlier analysis**
   - SKUs with MAPE > 2× expected
   - Root cause analysis

4. **Recommendations**
   - Method improvements
   - Data quality issues
   - Expected range adjustments

### Report Format

```markdown
## Evaluation Summary

| Metric | Value |
|--------|-------|
| SKUs Tested | N |
| Mean MAPE | X% |
| Median MAPE | X% |
| Within Range | X% |

## By Classification

| Class | Mean MAPE | Within Range |
|-------|-----------|--------------|
| A-X | X% | X% |
| ... | ... | ... |
```

---

## 7. Continuous Evaluation

### Frequency

| Evaluation | Frequency |
|------------|-----------|
| Quick validation | After each change |
| Full evaluation | Weekly |
| Benchmark comparison | Monthly |

### Tracking

- Maintain historical MAPE trends
- Flag degradation > 10%
- Alert on systematic issues

---

## 8. Compliance

All evaluations must:

1. ✅ Use standard metrics (MAPE, MAE, RMSE, Bias)
2. ✅ Compare against expected ranges
3. ✅ Include per-classification breakdown
4. ✅ Document methodology
5. ✅ Provide actionable recommendations

---

*This standard is mandatory for all model evaluations.*

