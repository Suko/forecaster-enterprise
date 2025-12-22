# Frontend vs Backend Calculation Comparison

## Summary

✅ **All calculation formulas match between frontend and backend**

---

## MAPE (Mean Absolute Percentage Error)

### Backend (`backend/forecasting/services/quality_calculator.py`)
```python
def calculate_mape(actuals: List[float], forecasts: List[float]) -> Optional[float]:
    if len(actuals) != len(forecasts):
        return None
    errors = []
    for actual, forecast in zip(actuals, forecasts):
        if actual > 0:
            errors.append(abs(actual - forecast) / actual)
    if not errors:
        return None
    return (100.0 / len(errors)) * sum(errors)
```

### Frontend (`frontend/app/pages/experiments/testbed.vue`)
```typescript
const calculateMAPE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors: number[] = [];
  for (let i = 0; i < actuals.length; i++) {
    const actual = actuals[i];
    const forecast = forecasts[i];
    if (actual !== undefined && forecast !== undefined && actual > 0) {
      errors.push(Math.abs((actual - forecast) / actual));
    }
  }
  if (errors.length === 0) return null;
  return (100.0 / errors.length) * errors.reduce((sum, e) => sum + e, 0);
};
```

**Status:** ✅ **MATCH** - Same formula, same logic

---

## MAE (Mean Absolute Error)

### Backend
```python
def calculate_mae(actuals: List[float], forecasts: List[float]) -> Optional[float]:
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    errors = [abs(a - f) for a, f in zip(actuals, forecasts)]
    return sum(errors) / len(errors)
```

### Frontend
```typescript
const calculateMAE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? Math.abs(a - f) : 0;
  });
  return errors.reduce((sum, e) => sum + e, 0) / errors.length;
};
```

**Status:** ✅ **MATCH** - Same formula, same logic

---

## RMSE (Root Mean Squared Error)

### Backend
```python
def calculate_rmse(actuals: List[float], forecasts: List[float]) -> Optional[float]:
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    squared_errors = [(a - f) ** 2 for a, f in zip(actuals, forecasts)]
    mse = sum(squared_errors) / len(squared_errors)
    return math.sqrt(mse)
```

### Frontend
```typescript
const calculateRMSE = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const squaredErrors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? Math.pow(a - f, 2) : 0;
  });
  const mse = squaredErrors.reduce((sum, e) => sum + e, 0) / squaredErrors.length;
  return Math.sqrt(mse);
};
```

**Status:** ✅ **MATCH** - Same formula, same logic

---

## Bias

### Backend
```python
def calculate_bias(actuals: List[float], forecasts: List[float]) -> Optional[float]:
    if len(actuals) != len(forecasts) or len(actuals) == 0:
        return None
    errors = [f - a for a, f in zip(actuals, forecasts)]
    return sum(errors) / len(errors)
```

### Frontend
```typescript
const calculateBias = (actuals: number[], forecasts: number[]): number | null => {
  if (actuals.length !== forecasts.length || actuals.length === 0) return null;
  const errors = actuals.map((a, i) => {
    const f = forecasts[i];
    return f !== undefined ? f - a : 0;
  });
  return errors.reduce((sum, e) => sum + e, 0) / errors.length;
};
```

**Status:** ✅ **MATCH** - Same formula, same logic

---

## Key Differences (Minor)

### Frontend Additional Checks
- Frontend checks for `undefined` values (TypeScript safety)
- Frontend uses `!== undefined` checks before calculations
- These are defensive programming practices and don't affect correctness

### Backend Simplicity
- Backend assumes valid data (Python type hints ensure this)
- Backend uses list comprehensions (more Pythonic)

---

## Conclusion

✅ **All calculation formulas are identical between frontend and backend**

The frontend calculations will produce the same results as the backend when given the same input data.

---

## Validation Recommendations

1. **Test with Real Data** - Use the validation script to compare actual API responses
2. **Check Date Alignment** - Verify forecast dates match actual dates correctly
3. **Verify Totals** - Ensure forecast totals = sum of individual predictions
4. **Check Sample Counts** - Verify sample counts match number of matching dates

See `docs/DATA_VALIDATION_TEST_PLAN.md` for detailed validation steps.

