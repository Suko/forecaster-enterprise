# Forecast Accuracy Metrics - Best Practices

## Current Implementation ✅

### MAPE (Mean Absolute Percentage Error)
**Formula:** `MAPE = (100/n) × Σ|Actual - Forecast|/Actual`

**Industry Standard:** APICS (Association for Supply Chain Management)

**Our Implementation:**
- ✅ Calculated **per day** (not on totals)
- ✅ Skips days where `actual = 0` (prevents division by zero)
- ✅ Returns percentage (0-100%)
- ✅ Uses only days with actuals > 0

**Why Per-Day Calculation:**
- Measures **daily accuracy** (critical for inventory planning)
- More granular than total-based metrics
- Industry standard for demand forecasting
- Better reflects operational impact

**Example:**
```
Day 1: Actual=1.0, Forecast=1.2 → Error = 20%
Day 2: Actual=0.9, Forecast=0.8 → Error = 11%
Day 3: Actual=1.1, Forecast=1.0 → Error = 9%
MAPE = (20% + 11% + 9%) / 3 = 13.3%
```

### MAE (Mean Absolute Error)
**Formula:** `MAE = (1/n) × Σ|Actual - Forecast|`

**Purpose:** Absolute error in units (not percentage)

**Use Case:** When you need to know "how many units off" regardless of scale

### RMSE (Root Mean Squared Error)
**Formula:** `RMSE = √[(1/n) × Σ(Actual - Forecast)²]`

**Purpose:** Penalizes large errors more than small ones

**Use Case:** When large errors are particularly costly

### Bias
**Formula:** `Bias = (1/n) × Σ(Forecast - Actual)`

**Purpose:** 
- Positive = over-forecasting (too much inventory)
- Negative = under-forecasting (stockouts)

**Use Case:** Detecting systematic over/under-forecasting

## Why MAPE Can Be Lower Despite Higher Total Error

**Scenario:**
- **Chronos-2:** Total Forecast = 40, Actual = 45, MAPE = 39.0%
- **Moving Average:** Total Forecast = 43, Actual = 45, MAPE = 43.5%

**Explanation:**
- **Total error** measures overall volume accuracy
- **MAPE** measures daily prediction consistency

**Example:**
```
Chronos-2 daily: [1.0, 1.0, 1.0, 0.8, 0.9] → Consistent, lower daily errors
Moving Average:  [0.5, 1.5, 0.3, 1.8, 0.2] → Variable, higher daily errors
```

Even though Moving Average total (43) is closer to actual (45) than Chronos-2 (40), Chronos-2 has better **daily accuracy** (lower MAPE).

## Industry Standards

### APICS Guidelines
- **MAPE < 25%:** Excellent
- **MAPE 25-50%:** Good
- **MAPE 50-75%:** Acceptable
- **MAPE > 75%:** Poor

### Our Expected Ranges (by SKU Classification)
- **A-X (High value, low variability):** 10-25%
- **B-X, C-X:** 15-35%
- **A-Y, B-Y:** 20-45%
- **C-Y:** 30-50%
- **A-Z, B-Z:** 30-70%
- **C-Z (Low value, high variability):** 50-100%

## Known Limitations of MAPE

1. **Asymmetric Penalty:**
   - Under-forecasting (stockout) penalized more than over-forecasting (excess inventory)
   - Example: Actual=1, Forecast=0 → 100% error
   - Example: Actual=1, Forecast=2 → 100% error (but less critical)

2. **Small Values:**
   - Very small actuals can inflate MAPE
   - We handle this by skipping actual=0 days

3. **Not Suitable for:**
   - Intermittent demand (many zeros)
   - Very low volume items
   - Items with extreme variability

## Alternative Metrics (Future Consideration)

### sMAPE (Symmetric MAPE)
**Formula:** `sMAPE = (100/n) × Σ|Actual - Forecast| / ((Actual + Forecast)/2)`

**Advantage:** Treats over/under-forecasting symmetrically

**When to Use:** When over-forecasting is as costly as under-forecasting

### MASE (Mean Absolute Scaled Error)
**Formula:** `MASE = MAE / MAE_naive`

**Advantage:** Scale-independent, compares to naive forecast

**When to Use:** Comparing across different SKUs or time periods

## Best Practices Summary

✅ **What We're Doing Right:**
1. Using industry-standard APICS MAPE formula
2. Calculating per-day (not totals)
3. Handling zero actuals correctly
4. Providing multiple metrics (MAPE, MAE, RMSE, Bias)
5. Using expected ranges based on SKU classification

⚠️ **Considerations:**
1. MAPE alone doesn't tell the full story (use with MAE, RMSE, Bias)
2. For intermittent demand, consider additional metrics
3. Total forecast vs actual is useful for budget planning (separate from MAPE)

## Recommendations

1. **Keep current implementation** - It follows industry best practices
2. **Display multiple metrics** - MAPE, MAE, RMSE, Bias (we do this ✅)
3. **Show both daily accuracy (MAPE) and total accuracy** - Help users understand the difference
4. **Consider adding sMAPE** - For cases where over/under-forecasting should be treated equally
5. **Document the difference** - Help users understand why MAPE can differ from total error

