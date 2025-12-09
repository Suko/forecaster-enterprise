# Learning from Darts: Data Quality Practices

## Overview

We analyzed Darts' `TimeSeries` implementation to learn best practices for data quality validation. This document summarizes what we learned and how we've applied it.

## Key Learnings from Darts

### 1. Time Index Frequency Consistency

**Darts Requirement:**
- TimeSeries requires a consistent frequency (daily, weekly, etc.)
- Missing dates cause errors unless `fill_missing_dates=True` is set
- Time index must have a `freq` attribute or be inferrable

**Darts Error Example:**
```
ValueError: The time index is missing the `freq` attribute, and the frequency 
could not be directly inferred. This probably comes from inconsistent date 
frequencies with missing dates.
```

**Our Implementation:**
- ✅ Check for missing dates in time series
- ✅ Detect frequency consistency
- ✅ Option to fill missing dates (like Darts' `fill_missing_dates=True`)
- ✅ Warn about inconsistent frequencies

### 2. Missing Date Handling

**Darts Approach:**
```python
TimeSeries.from_dataframe(
    df,
    time_col="timestamp",
    value_cols="target",
    fill_missing_dates=True,  # Fill missing dates
    freq="D",                  # Explicit frequency
    fillna_value=0             # Fill NaN with 0
)
```

**Our Implementation:**
- ✅ `fill_missing_dates` parameter (matches Darts)
- ✅ Fill missing dates with NaN, then fillna with 0 (zero-demand days)
- ✅ Preserve time series continuity

### 3. NaN Value Handling

**Darts Approach:**
- `fillna_value` parameter allows replacing NaN during TimeSeries creation
- Default behavior: NaN values are preserved (may cause model issues)

**Our Implementation:**
- ✅ Multiple strategies: `zero`, `forward_fill`, `value`, `error`
- ✅ Default: Fill with 0 (zero-demand days for sales)
- ✅ Warn about high NaN percentages (>50%)

### 4. Duplicate Date Handling

**Darts Behavior:**
- Darts may aggregate duplicate dates (depending on model)
- Best practice: Remove duplicates before creating TimeSeries

**Our Implementation:**
- ✅ Detect duplicate timestamps
- ✅ Remove duplicates (keep first occurrence)
- ✅ Warn about duplicates

### 5. Data Type Validation

**Darts Requirements:**
- Timestamp column must be datetime
- Value columns must be numeric
- Type conversion happens automatically (with warnings)

**Our Implementation:**
- ✅ Validate timestamp is datetime
- ✅ Convert target to numeric (handles Decimal from database)
- ✅ Validate all numeric columns

## Enhanced Data Validator

We created `EnhancedDataValidator` that implements Darts' practices:

### Features

1. **Time Index Validation** (`validate_time_index`)
   - Checks for missing dates
   - Validates frequency consistency
   - Option to fill missing dates
   - Detects duplicate timestamps

2. **NaN Value Validation** (`validate_nan_values`)
   - Multiple fill strategies
   - Warns about high NaN percentages
   - Handles target column specially

3. **Complete Validation** (`validate_complete`)
   - Combines all checks
   - Returns cleaned DataFrame
   - Comprehensive reporting

### Usage

```python
from forecasting.services.data_validator_enhanced import EnhancedDataValidator

# Complete validation (like Darts' TimeSeries.from_dataframe)
is_valid, report, cleaned_df, error = EnhancedDataValidator.validate_complete(
    context_df=df,
    item_id="SKU001",
    min_history_days=7,
    expected_freq="D",
    fill_missing_dates=True,  # Like Darts' fill_missing_dates
    fillna_strategy="zero",   # Like Darts' fillna_value=0
)

if is_valid:
    # Use cleaned_df for forecasting
    pass
else:
    # Handle errors
    print(error)
```

## Comparison: Darts vs Our Implementation

| Feature | Darts | Our Implementation |
|---------|-------|-------------------|
| **Time Frequency Check** | ✅ Required | ✅ Validated |
| **Missing Date Detection** | ✅ Error if missing | ✅ Detected + optional fill |
| **Fill Missing Dates** | ✅ `fill_missing_dates=True` | ✅ `fill_missing_dates=True` |
| **NaN Handling** | ✅ `fillna_value` parameter | ✅ Multiple strategies |
| **Duplicate Detection** | ⚠️ May aggregate | ✅ Detected + removed |
| **Frequency Inference** | ✅ Automatic | ✅ Automatic |
| **Business Rules** | ❌ Not included | ✅ Negative values, etc. |

## Best Practices (From Darts)

1. **Always specify frequency** when you know it
   ```python
   # Good
   TimeSeries.from_dataframe(df, freq="D")
   
   # Better
   TimeSeries.from_dataframe(df, freq="D", fill_missing_dates=True)
   ```

2. **Handle missing dates explicitly**
   - Fill with 0 for zero-demand days (sales)
   - Or forward-fill for covariates

3. **Validate before creating TimeSeries**
   - Check for missing dates
   - Check for duplicates
   - Check for NaN values

4. **Use consistent data types**
   - Timestamps: datetime
   - Values: numeric

## Integration with Our System

### Current Usage

Our `DataValidator` (original) is used in:
- `forecast_service.py` - Before sending data to models
- `test_forecast_accuracy.py` - For validation reports

### Enhanced Usage (Recommended)

Use `EnhancedDataValidator` for:
- ✅ More comprehensive validation (matches Darts)
- ✅ Better missing date handling
- ✅ Automatic data cleaning
- ✅ Detailed reporting

### Migration Path

1. **Phase 1 (Current)**: Use `DataValidator` (basic checks)
2. **Phase 2 (Recommended)**: Migrate to `EnhancedDataValidator`
3. **Phase 3 (Future)**: Integrate with Darts for comparison

## Example: Before vs After

### Before (Basic Validation)
```python
# Only checks: empty, columns, negative values
is_valid, report, error = DataValidator.validate_context_data(df, "SKU001")
```

### After (Enhanced Validation)
```python
# Checks: time index, missing dates, NaN, duplicates, frequency
is_valid, report, cleaned_df, error = EnhancedDataValidator.validate_complete(
    df, "SKU001", fill_missing_dates=True, fillna_strategy="zero"
)
# cleaned_df is ready for forecasting (like Darts' TimeSeries)
```

## References

- [Darts TimeSeries Documentation](https://unit8co.github.io/darts/generated_api/darts.timeseries.html)
- [Darts User Guide](https://unit8co.github.io/darts/userguide/timeseries.html)
- Our Implementation: `backend/forecasting/services/data_validator_enhanced.py`

---
*Last updated: 2025-12-08*

