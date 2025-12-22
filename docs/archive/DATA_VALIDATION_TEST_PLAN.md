# Data Validation Test Plan

**Purpose:** Verify that all displayed data in the Test Bed is mathematically correct and matches backend calculations.

## Critical Questions to Answer

1. ✅ **Are quality metrics (MAPE, RMSE, MAE) calculated correctly?**
2. ✅ **Do frontend calculations match backend API responses?**
3. ✅ **Are forecast values aligned with actual dates correctly?**
4. ✅ **Is SKU classification accurate?**
5. ✅ **Are sample counts correct?**
6. ✅ **Do forecast totals match sum of individual predictions?**

---

## Test Cases

### 1. Quality Metrics Validation

#### Test 1.1: MAPE Calculation
**Backend Formula:** `MAPE = (100/n) × Σ|Actual - Forecast|/Actual`

**Test Steps:**
1. Generate forecast for a product with known actuals
2. Extract actuals and forecasts from API response
3. Manually calculate MAPE using the formula
4. Compare with displayed MAPE

**Expected:** Frontend MAPE = Backend MAPE (within 0.1% tolerance)

**Validation Script:**
```python
# Manual MAPE calculation
actuals = [1.0, 0.9, 1.1, 1.2, 0.8]
forecasts = [1.2, 0.8, 1.0, 1.3, 0.9]

errors = []
for a, f in zip(actuals, forecasts):
    if a > 0:
        errors.append(abs(a - f) / a)

mape = (100.0 / len(errors)) * sum(errors)
# Should match backend calculation
```

#### Test 1.2: RMSE Calculation
**Backend Formula:** `RMSE = √[(1/n) × Σ(Actual - Forecast)²]`

**Test Steps:**
1. Use same data as Test 1.1
2. Manually calculate RMSE
3. Compare with displayed RMSE

**Expected:** Frontend RMSE = Backend RMSE (within 0.01 tolerance)

#### Test 1.3: MAE Calculation
**Backend Formula:** `MAE = (1/n) × Σ|Actual - Forecast|`

**Test Steps:**
1. Use same data as Test 1.1
2. Manually calculate MAE
3. Compare with displayed MAE

**Expected:** Frontend MAE = Backend MAE (within 0.01 tolerance)

#### Test 1.4: Bias Calculation
**Backend Formula:** `Bias = (1/n) × Σ(Forecast - Actual)`

**Test Steps:**
1. Use same data as Test 1.1
2. Manually calculate Bias
3. Compare with displayed Bias

**Expected:** Frontend Bias = Backend Bias (within 0.01 tolerance)

---

### 2. Frontend vs Backend Comparison

#### Test 2.1: API Response Validation
**Test Steps:**
1. Generate forecast via Test Bed
2. Open browser DevTools → Network tab
3. Capture API response from `/api/experiments/forecast`
4. Capture API response from `/api/experiments/quality/{itemId}`
5. Compare frontend-displayed metrics with API response

**Expected:**
- Frontend metrics match API response exactly
- No discrepancies in values

#### Test 2.2: In-Memory Calculation (skip_persistence=true)
**Test Steps:**
1. Generate forecast with `skip_persistence=true` (Test Bed mode)
2. Frontend calculates metrics in-memory
3. Compare in-memory calculation with backend formula
4. Verify calculation logic matches `QualityCalculator`

**Expected:**
- In-memory calculation uses same formula as backend
- Results match backend calculation

---

### 3. Forecast Data Validation

#### Test 3.1: Forecast Date Alignment
**Test Steps:**
1. Generate 30-day forecast
2. Check forecast start date = `training_end_date + 1` (for backtesting)
3. Verify forecast dates are sequential (no gaps)
4. Verify forecast dates don't overlap with training data

**Expected:**
- Forecast dates start from correct date
- All dates sequential
- No date overlaps

#### Test 3.2: Forecast Value Totals
**Test Steps:**
1. Extract all forecast values for a method
2. Sum all `point_forecast` values
3. Compare with displayed "Forecasted" total in header

**Expected:**
- Sum of individual forecasts = Header "Forecasted" value

#### Test 3.3: Actual Value Totals
**Test Steps:**
1. Extract all actual values for backtesting period
2. Sum all `actual_value` values
3. Compare with displayed "Actual" total in header

**Expected:**
- Sum of individual actuals = Header "Actual" value

#### Test 3.4: Sample Count Validation
**Test Steps:**
1. Count number of forecast-actual pairs
2. Compare with displayed "Samples" in table

**Expected:**
- Sample count = Number of matching dates between forecast and actuals
- Sample count ≤ Forecast horizon (30 days)

---

### 4. SKU Classification Validation

#### Test 4.1: ABC Classification
**Test Steps:**
1. Get revenue data for all products
2. Calculate ABC class manually:
   - Sort by revenue descending
   - A = Top 80% revenue
   - B = Next 15% revenue
   - C = Bottom 5% revenue
3. Compare with displayed ABC class

**Expected:**
- Displayed ABC class matches manual calculation

#### Test 4.2: XYZ Classification
**Test Steps:**
1. Get historical sales data for product
2. Calculate Coefficient of Variation (CV):
   - CV = std(units_sold) / mean(units_sold)
3. Classify:
   - X = CV < 0.5
   - Y = 0.5 ≤ CV < 1.0
   - Z = CV ≥ 1.0
4. Compare with displayed XYZ class

**Expected:**
- Displayed XYZ class matches manual calculation

#### Test 4.3: Demand Pattern
**Test Steps:**
1. Calculate Average Demand Interval (ADI):
   - ADI = number_of_periods / number_of_non_zero_periods
2. Calculate CV²
3. Classify:
   - Regular: ADI ≤ 1.32
   - Intermittent: ADI > 1.32
   - Lumpy: ADI > 1.32 AND CV² > 0.49
4. Compare with displayed demand pattern

**Expected:**
- Displayed demand pattern matches manual calculation

#### Test 4.4: Recommended Method
**Test Steps:**
1. Get ABC, XYZ, and demand pattern
2. Apply recommendation rules:
   - Lumpy → SBA
   - Intermittent → Croston
   - A-X, B-X, C-X → Chronos-2
   - etc.
3. Compare with displayed recommended method

**Expected:**
- Displayed recommended method matches rule-based calculation

---

### 5. Model Comparison Table Validation

#### Test 5.1: All Methods Have Metrics
**Test Steps:**
1. Generate forecast with `run_all_methods=true`
2. Check each method in table has:
   - MAPE (or N/A)
   - RMSE (or N/A)
   - MAE (or N/A)
   - Bias (or N/A)
   - Samples count

**Expected:**
- All 5 methods have complete metrics
- No missing values (except N/A when appropriate)

#### Test 5.2: Metrics Match Individual Calculations
**Test Steps:**
1. For each method in table:
   - Extract forecast values
   - Extract actual values
   - Calculate metrics manually
   - Compare with table values

**Expected:**
- Table metrics match manual calculations

#### Test 5.3: System Recommendation Badge
**Test Steps:**
1. Check which method has "✓ System Choice" badge
2. Verify it matches `skuClassification.recommended_method`

**Expected:**
- Badge appears on correct method
- Matches classification recommendation

---

### 6. Edge Cases

#### Test 6.1: Zero Actuals
**Test Steps:**
1. Test with product that has some zero actuals
2. Verify MAPE calculation skips zeros (doesn't divide by zero)
3. Verify sample count excludes zero days

**Expected:**
- No division by zero errors
- MAPE calculated only on non-zero actuals

#### Test 6.2: Missing Actuals
**Test Steps:**
1. Test with forecast period where some actuals are missing
2. Verify metrics only use available actuals
3. Verify sample count reflects available pairs

**Expected:**
- Metrics calculated on available data only
- Sample count = number of matching dates

#### Test 6.3: Negative Forecasts
**Test Steps:**
1. Check if any forecast values are negative
2. Verify system handles negative values correctly

**Expected:**
- No negative forecasts (or handled gracefully)
- Metrics calculated correctly with absolute values

---

## Validation Script

Create a Python script to validate data:

```python
# scripts/validate_testbed_data.py
"""
Validates Test Bed data accuracy by comparing:
1. Frontend metrics vs Backend API
2. Manual calculations vs Displayed values
3. Forecast totals vs Sum of predictions
"""

import asyncio
import httpx
from typing import Dict, List
import math

async def validate_metrics(actuals: List[float], forecasts: List[float]) -> Dict:
    """Calculate metrics manually and compare with backend"""
    
    # MAPE
    errors = []
    for a, f in zip(actuals, forecasts):
        if a > 0:
            errors.append(abs(a - f) / a)
    mape = (100.0 / len(errors)) * sum(errors) if errors else None
    
    # MAE
    mae = sum(abs(a - f) for a, f in zip(actuals, forecasts)) / len(actuals)
    
    # RMSE
    rmse = math.sqrt(sum((a - f) ** 2 for a, f in zip(actuals, forecasts)) / len(actuals))
    
    # Bias
    bias = sum(f - a for a, f in zip(actuals, forecasts)) / len(actuals)
    
    return {
        "mape": mape,
        "mae": mae,
        "rmse": rmse,
        "bias": bias,
        "sample_size": len(actuals)
    }

async def validate_forecast_totals(forecasts: List[Dict]) -> float:
    """Sum all forecast values"""
    return sum(f["point_forecast"] for f in forecasts)

async def validate_abc_classification(revenue_dict: Dict[str, float]) -> Dict[str, str]:
    """Calculate ABC classification manually"""
    sorted_skus = sorted(revenue_dict.items(), key=lambda x: x[1], reverse=True)
    total_revenue = sum(revenue_dict.values())
    
    classification = {}
    cumulative_revenue = 0
    
    for sku, revenue in sorted_skus:
        cumulative_revenue += revenue
        pct = (cumulative_revenue / total_revenue) * 100
        
        if pct <= 80:
            classification[sku] = "A"
        elif pct <= 95:
            classification[sku] = "B"
        else:
            classification[sku] = "C"
    
    return classification

# Main validation function
async def validate_testbed_data(item_id: str, forecast_run_id: str):
    """Validate all Test Bed data for a specific forecast"""
    # 1. Fetch forecast data
    # 2. Fetch actuals data
    # 3. Calculate metrics manually
    # 4. Compare with API response
    # 5. Compare with frontend display
    pass
```

---

## Manual Validation Checklist

### Quick Manual Test (5 minutes)

1. **Generate Forecast**
   - Select product: `M5_HOBBIES_1_004`
   - Generate 30-day forecast
   - Note displayed metrics

2. **Check API Response**
   - Open DevTools → Network
   - Find `/api/experiments/quality/{itemId}` request
   - Compare response with displayed metrics

3. **Verify Totals**
   - Sum forecast values from chart data
   - Compare with "Forecasted" in header
   - Sum actual values
   - Compare with "Actual" in header

4. **Check Classification**
   - Verify ABC class makes sense (high revenue = A)
   - Verify XYZ class makes sense (high variability = Z)
   - Verify recommended method matches classification rules

---

## Expected Results

✅ **All metrics match backend calculations**  
✅ **Forecast totals = sum of individual predictions**  
✅ **Sample counts = number of matching dates**  
✅ **Classification values are mathematically correct**  
✅ **No discrepancies between frontend and backend**

---

## Issues to Watch For

⚠️ **Frontend recalculating metrics differently than backend**  
⚠️ **Date misalignment causing wrong actual-forecast pairs**  
⚠️ **Sample count including/excluding wrong dates**  
⚠️ **Classification rules not matching displayed values**  
⚠️ **Totals not matching sum of individual values**

---

## Next Steps

1. **Run Manual Validation** - Use checklist above
2. **Create Automated Script** - Implement validation script
3. **Compare Results** - Document any discrepancies
4. **Fix Issues** - Correct any calculation errors
5. **Re-test** - Verify fixes

