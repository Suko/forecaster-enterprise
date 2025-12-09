# Using Darts for Testing

**Purpose:** Use Darts library as a reference implementation and for additional baseline models in testing.

## Why Use Darts?

1. **Reference Implementation**: Darts' `Chronos2Model` provides a standardized way to validate our custom implementation
2. **Additional Baselines**: Access to more baseline models (ARIMA, Exponential Smoothing, NaiveMean, etc.)
3. **Built-in Metrics**: Standardized metric calculations (MAPE, MAE, RMSE)
4. **Backtesting Utilities**: Built-in backtesting functionality
5. **Data Validation**: Better error handling and data format validation

## Installation

Darts is already installed in the project:

```bash
cd backend
uv add darts
```

## Usage Examples

### 1. Diagnostic Script

We have a diagnostic script that compares Darts vs our implementation:

```bash
cd backend
uv run python scripts/diagnose_chronos.py
```

This helps identify issues with our custom Chronos-2 wrapper.

### 2. Test Suite

We have pytest tests that use Darts:

```bash
cd backend
uv run pytest tests/test_forecasting/test_darts_comparison.py -v
```

**Available Tests:**
- `test_darts_vs_our_chronos2` - Compare Darts Chronos2Model with our custom implementation
- `test_darts_baseline_models` - Test additional baseline models (Exponential Smoothing, NaiveMean)
- `test_darts_metrics_consistency` - Validate that Darts metrics match our calculations
- `test_multiple_skus_with_darts` - Quick validation across multiple SKUs

### 3. Quick Validation

Use Darts for quick model validation without full test infrastructure:

```python
from darts import TimeSeries
from darts.models import NaiveMean
from darts.metrics import mape, mae

# Load data
series = TimeSeries.from_dataframe(df, time_col="date", value_cols="target")

# Split train/test
train, test = series.split_before(0.8)

# Quick baseline test
model = NaiveMean()
model.fit(train)
prediction = model.predict(len(test))

# Calculate metrics
mape_val = mape(test, prediction)
mae_val = mae(test, prediction)

print(f"MAPE: {mape_val:.2f}%, MAE: {mae_val:.2f}")
```

## Benefits

### ✅ What Darts Helps With

1. **Validation**: Compare our implementation against Darts' reference
2. **Baseline Models**: Quick access to statistical models for comparison
3. **Metrics**: Standardized metric calculations
4. **Debugging**: Better error messages when data format is wrong
5. **Quick Tests**: Fast validation without full database setup

### ⚠️ Limitations

1. **Chronos-2 Parameters**: Darts' Chronos2Model requires `input_chunk_length` and `output_chunk_length` parameters
2. **MAPE with Zeros**: Darts' MAPE fails when actual values contain zeros (use MAE instead)
3. **Backtesting API**: Import path may vary between Darts versions
4. **Performance**: Darts models may be slower for production use

## Best Practices

1. **Use Darts for Testing**: Great for validation and comparison
2. **Use Our Implementation for Production**: Our custom wrapper is optimized for our use case
3. **Handle Zeros**: Always check for zeros before calculating MAPE
4. **Compare Metrics**: Use both MAPE and MAE for comprehensive evaluation

## Example: Quick Model Comparison

```python
import asyncio
from darts import TimeSeries
from darts.models import NaiveMean, ExponentialSmoothing
from darts.metrics import mape, mae
from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model

async def compare_models(train_data, test_data):
    """Compare multiple models quickly"""
    
    train_series = TimeSeries.from_dataframe(train_data, time_col="timestamp", value_cols="target")
    test_series = TimeSeries.from_dataframe(test_data, time_col="timestamp", value_cols="target")
    
    results = {}
    
    # Darts NaiveMean
    naive = NaiveMean()
    naive.fit(train_series)
    naive_pred = naive.predict(30)
    results["NaiveMean"] = {"mae": mae(test_series, naive_pred)}
    
    # Our Chronos-2
    our_model = OurChronos2Model()
    await our_model.initialize()
    our_pred_df = await our_model.predict(context_df=train_data, prediction_length=30)
    our_pred = TimeSeries.from_dataframe(our_pred_df, time_col="timestamp", value_cols="point_forecast")
    results["OurChronos2"] = {"mae": mae(test_series, our_pred)}
    
    return results
```

## Integration with Test Framework

Darts tests are integrated into our test suite:

- **Location**: `tests/test_forecasting/test_darts_comparison.py`
- **Run**: `uv run pytest tests/test_forecasting/test_darts_comparison.py`
- **Purpose**: Validate our implementation and test additional baselines

## Summary

**Darts is excellent for:**
- ✅ Testing and validation
- ✅ Quick baseline comparisons
- ✅ Debugging data format issues
- ✅ Reference implementation

**Use our custom implementation for:**
- ✅ Production forecasting
- ✅ Performance-critical paths
- ✅ Custom features and optimizations

---
*See also: `scripts/diagnose_chronos.py` for diagnostic tool*

