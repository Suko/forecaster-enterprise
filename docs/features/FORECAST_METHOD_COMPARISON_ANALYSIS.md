# Forecast Method Comparison Analysis

## Current System Design

### Available Methods (5 total)
1. **chronos-2** - ML model (most accurate, slower)
2. **statistical_ma7** - 7-day Moving Average (baseline, fast)
3. **sba** - Syntetos-Boylan Approximation (for lumpy demand)
4. **croston** - Croston's Method (for intermittent demand)
5. **min_max** - Min-Max rules (for high variability, low value)

### Current Behavior

**Forecast Generation Logic:**
- Only runs **2 methods** per forecast:
  - Primary model (user's selection, e.g., "chronos-2")
  - Baseline ("statistical_ma7") if `include_baseline=True`

**Why Only 2 Methods?**
- **Performance**: Running all 5 methods is 2.5x slower
- **Cost**: ML models (chronos-2) are computationally expensive
- **Design Philosophy**: System recommends the best method per SKU, not all methods
- **Storage**: Reduces database storage for forecast results

### The Problem

**Test Bed Use Case:**
- Users want to **compare all methods** side-by-side
- Currently only see 2 methods (primary + baseline)
- Other methods only appear if they were run in previous forecast runs
- Results from different runs have different sample counts (inconsistent)

## Solution Options

### Option 1: Add `run_all_methods` Flag (Recommended for Test Bed)

**Pros:**
- ✅ Explicit control - user chooses when to run all methods
- ✅ Doesn't break existing system (default behavior unchanged)
- ✅ Perfect for Test Bed comparison use case
- ✅ Can still optimize for production (only run recommended method)

**Cons:**
- ⚠️ Slower forecast generation (2.5x)
- ⚠️ More database storage

**Implementation:**
```python
# In ForecastRequest schema
run_all_methods: bool = Field(False, description="Run all available methods for comparison")

# In forecast_service.py
if run_all_methods:
    methods_to_run = ["chronos-2", "statistical_ma7", "sba", "croston", "min_max"]
else:
    # Current logic: primary + baseline
    methods_to_run = [primary_model]
    if include_baseline:
        methods_to_run.append("statistical_ma7")
```

### Option 2: Add `run_all_statistical` Flag

**Pros:**
- ✅ Faster than Option 1 (only statistical methods, no ML)
- ✅ Good for comparing statistical approaches

**Cons:**
- ⚠️ Still doesn't include ML model comparison
- ⚠️ Less comprehensive

### Option 3: Separate Endpoint for Test Bed

**Pros:**
- ✅ Clear separation of concerns
- ✅ Production endpoints remain optimized

**Cons:**
- ⚠️ Code duplication
- ⚠️ More maintenance

## Recommended Solution

**Use Option 1** with smart defaults:
- **Production**: `run_all_methods=False` (default) - only run recommended method
- **Test Bed**: `run_all_methods=True` - run all methods for comparison
- **Dashboard**: `run_all_methods=False` - performance critical

This gives us:
1. ✅ **No breaking changes** - default behavior unchanged
2. ✅ **Test Bed works** - can compare all methods
3. ✅ **Production optimized** - only runs what's needed
4. ✅ **Flexible** - can enable for specific use cases

## Implementation Plan

1. Add `run_all_methods` to `ForecastRequest` schema
2. Update `ForecastService.generate_forecast()` to handle this flag
3. Update Test Bed frontend to pass `run_all_methods: true`
4. Update quality metrics to show all methods from current run
5. Add performance monitoring for multi-method runs

## Performance Impact

**Current (2 methods):**
- ~2-3 seconds for 1 item
- ~30 seconds for 100 items

**With all methods (5 methods):**
- ~5-7 seconds for 1 item
- ~75 seconds for 100 items

**Mitigation:**
- Only enable for Test Bed (single item)
- Add progress indicators
- Consider async/background processing for large batches

