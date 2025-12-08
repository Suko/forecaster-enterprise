# Covariate Management Strategy

**Status:** ⏳ **Phase 2 Feature**  
**Problem:** Covariates don't always improve forecast accuracy  
**Solution:** Adaptive covariate selection based on performance

---

## The Problem

**Covariates can sometimes hurt accuracy:**
- ❌ Add noise to the model
- ❌ Overfit to training data
- ❌ Not relevant for certain items
- ❌ Actually decrease MAPE/MAE/RMSE

**Example:**
```
Item A (no promotions):
- Without covariates: MAPE = 8.2%
- With covariates: MAPE = 12.5%  ← WORSE!

Item B (promotional):
- Without covariates: MAPE = 15.3%
- With covariates: MAPE = 7.8%  ← BETTER!
```

---

## Solution: Adaptive Covariate Selection

### Strategy Overview

**Test both approaches and use the better one:**

1. **Run forecasts with and without covariates**
2. **Compare accuracy** (MAPE, MAE, RMSE)
3. **Select the better method** per item
4. **Track performance** over time
5. **Re-evaluate periodically** (covariates may become relevant)

### Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Forecast Request                          │
│              POST /api/v1/forecast                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              ForecastService.generate_forecast()            │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌──────────────────┐          ┌──────────────────┐
│  Method 1:       │          │  Method 2:       │
│  NO Covariates   │          │  WITH Covariates │
│                  │          │                  │
│  Input:          │          │  Input:          │
│  - target only   │          │  - target        │
│                  │          │  - covariates    │
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         ▼                             ▼
┌──────────────────┐          ┌──────────────────┐
│  Forecast A      │          │  Forecast B       │
│  (no covariates) │          │  (with covariates)│
└────────┬─────────┘          └────────┬─────────┘
         │                             │
         └──────────────┬──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              Store Both Results in DB                       │
│  forecast_results:                                          │
│    - method = 'chronos-2_no_covariates'                     │
│    - method = 'chronos-2_with_covariates'                   │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Select Better Method (Historical Accuracy)          │
│                                                              │
│  IF historical_mape_with_cov < historical_mape_no_cov:      │
│    → Return Forecast B (with covariates)                    │
│  ELSE:                                                       │
│    → Return Forecast A (no covariates)                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              API Response (Better Method)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Later: When Actuals Arrive (Backfill)                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│         Compare Actual Accuracy                             │
│                                                              │
│  mape_no_cov = calculate_mape(actuals, forecast_a)          │
│  mape_with_cov = calculate_mape(actuals, forecast_b)        │
│                                                              │
│  IF mape_with_cov < mape_no_cov:                            │
│    → Update item_config: use_covariates = True              │
│  ELSE:                                                       │
│    → Update item_config: use_covariates = False             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Approach

### Phase 2.1: Dual-Method Execution

**Run both methods and compare:**

```python
# ForecastService.generate_forecast()

# 1. Run WITHOUT covariates (baseline)
forecast_no_cov = await model.predict(
    context_df=context_df[['id', 'timestamp', 'target']],  # Only target
    prediction_length=prediction_length,
)

# 2. Run WITH covariates
forecast_with_cov = await model.predict(
    context_df=context_df,  # Target + covariates
    future_covariates_df=future_covariates,
    prediction_length=prediction_length,
)

# 3. Store both results
# 4. Compare accuracy when actuals arrive
```

### Phase 2.2: Performance-Based Selection

**Select method based on historical accuracy:**

```python
# After actuals are backfilled
accuracy_no_cov = calculate_mape(actuals, forecast_no_cov)
accuracy_with_cov = calculate_mape(actuals, forecast_with_cov)

if accuracy_with_cov < accuracy_no_cov:
    recommended_method = "chronos-2_with_covariates"
else:
    recommended_method = "chronos-2_no_covariates"
```

### Phase 2.3: Per-Item Configuration

**Store preferred method per item:**

```sql
CREATE TABLE item_forecast_config (
    client_id UUID,
    item_id VARCHAR(255),
    preferred_method VARCHAR(50),  -- 'with_covariates' or 'no_covariates'
    last_evaluated_date DATE,
    accuracy_improvement NUMERIC(9,4),  -- % improvement
    PRIMARY KEY (client_id, item_id)
);
```

---

## Decision Framework

### When to Use Covariates

**Use covariates when:**
- ✅ Item has frequent promotions (>10% of days)
- ✅ Item shows strong holiday effects
- ✅ Marketing campaigns are active
- ✅ Historical accuracy is better with covariates
- ✅ Item is in promotional category

**Don't use covariates when:**
- ❌ Item has no promotions
- ❌ Item shows no holiday effects
- ❌ No marketing activity
- ❌ Historical accuracy is worse with covariates
- ❌ Item is stable/commodity (no external factors)

### Automatic Detection

```python
def should_use_covariates(item_id: str, historical_data: pd.DataFrame) -> bool:
    """
    Determine if covariates should be used for this item.
    
    Rules:
    1. If historical accuracy shows covariates help → Use them
    2. If item has promotions > 10% of days → Use them
    3. If item has marketing spend > 0 → Use them
    4. Otherwise → Don't use them
    """
    # Check historical performance
    if has_better_accuracy_with_covariates(item_id):
        return True
    
    # Check promotion frequency
    promo_frequency = (historical_data['promotion_flag'].sum() / len(historical_data)) * 100
    if promo_frequency > 10:
        return True
    
    # Check marketing activity
    if historical_data['marketing_spend'].sum() > 0:
        return True
    
    # Default: don't use covariates
    return False
```

---

## Performance Tracking

### Store Both Results

**Always store forecasts from both methods:**

```sql
-- forecast_results table already supports this:
INSERT INTO forecast_results (..., method) VALUES
    (..., 'chronos-2_no_covariates'),
    (..., 'chronos-2_with_covariates');
```

### Compare Accuracy

```python
# After actuals are backfilled
def compare_covariate_performance(item_id: str, forecast_run_id: UUID):
    """Compare accuracy of with/without covariates"""
    
    # Get results for both methods
    results_no_cov = get_results(item_id, forecast_run_id, method='chronos-2_no_covariates')
    results_with_cov = get_results(item_id, forecast_run_id, method='chronos-2_with_covariates')
    
    # Calculate accuracy
    mape_no_cov = calculate_mape(actuals, results_no_cov)
    mape_with_cov = calculate_mape(actuals, results_with_cov)
    
    # Determine winner
    if mape_with_cov < mape_no_cov:
        improvement = ((mape_no_cov - mape_with_cov) / mape_no_cov) * 100
        return {
            'winner': 'with_covariates',
            'improvement_pct': improvement,
            'mape_no_cov': mape_no_cov,
            'mape_with_cov': mape_with_cov
        }
    else:
        degradation = ((mape_with_cov - mape_no_cov) / mape_no_cov) * 100
        return {
            'winner': 'no_covariates',
            'degradation_pct': degradation,
            'mape_no_cov': mape_no_cov,
            'mape_with_cov': mape_with_cov
        }
```

---

## Configuration Options

### Global Configuration

**System-wide setting:**

```python
# config.py
FORECAST_CONFIG = {
    'use_covariates_by_default': False,  # Start conservative
    'covariate_evaluation_period_days': 30,  # Re-evaluate monthly
    'min_accuracy_improvement_pct': 5.0,  # Require 5% improvement
}
```

### Per-Item Override

**Manual override for specific items:**

```python
# item_forecast_config table
item_config = {
    'SKU001': {'use_covariates': True},   # Force use
    'SKU002': {'use_covariates': False},  # Force disable
    'SKU003': {'use_covariates': 'auto'}, # Auto-detect
}
```

### API Override

**Request-level override:**

```python
# API request
POST /api/v1/forecast
{
    "item_ids": ["SKU001"],
    "use_covariates": true,  # Override default
    "prediction_length": 30
}
```

---

## Implementation Phases

### Phase 2.1: Dual Execution (MVP for Covariates)

**What:**
- Run both with/without covariates
- Store both results
- Return the one with better historical accuracy

**Time:** 1 week

**Code:**
```python
# ForecastService
async def generate_forecast(...):
    # Run both methods
    results_no_cov = await model.predict(context_df[['id', 'timestamp', 'target']], ...)
    results_with_cov = await model.predict(context_df, future_covariates_df, ...)
    
    # Store both
    await store_results(results_no_cov, method='chronos-2_no_covariates')
    await store_results(results_with_cov, method='chronos-2_with_covariates')
    
    # Select based on historical performance
    recommended = select_better_method(item_id, historical_performance)
    return recommended
```

### Phase 2.2: Performance Tracking

**What:**
- Track accuracy for both methods
- Store in `forecast_method_performance` table
- Auto-select based on rolling MAPE

**Time:** 1 week

**Code:**
```python
# After actuals backfilled
async def evaluate_covariate_performance(item_id: str):
    # Compare accuracy
    comparison = compare_covariate_performance(item_id)
    
    # Update item config
    if comparison['winner'] == 'with_covariates':
        update_item_config(item_id, use_covariates=True)
    else:
        update_item_config(item_id, use_covariates=False)
```

### Phase 2.3: Automatic Detection

**What:**
- Auto-detect if covariates help
- Smart defaults based on item characteristics
- Periodic re-evaluation

**Time:** 1 week

**Code:**
```python
# Automatic detection
def should_use_covariates(item_id: str) -> bool:
    # Check historical performance
    # Check item characteristics
    # Return recommendation
```

---

## Monitoring & Alerts

### Track Covariate Effectiveness

**Metrics to monitor:**
- % of items where covariates help
- Average accuracy improvement
- Items where covariates hurt (alert!)

```python
# Dashboard metrics
covariate_effectiveness = {
    'items_helped': 45,      # 45% of items
    'items_hurt': 12,        # 12% of items
    'items_neutral': 43,      # 43% of items
    'avg_improvement_pct': 3.2,  # 3.2% average improvement
    'avg_degradation_pct': -2.1,  # 2.1% average degradation
}
```

### Alerts

**Alert when:**
- Covariates consistently hurt accuracy (>10% of items)
- Covariate data quality degrades
- Performance drops significantly

---

## Best Practices

### 1. Start Conservative

**Phase 2.1:** Run both methods, but default to no covariates
- Learn which items benefit
- Build performance history
- Don't assume covariates always help

### 2. Measure Everything

**Track accuracy for both methods:**
- Store both forecasts
- Compare when actuals arrive
- Build performance history

### 3. Re-evaluate Periodically

**Covariates may become relevant:**
- Item starts having promotions
- Marketing campaigns begin
- Seasonal patterns emerge

**Re-evaluate every 30 days**

### 4. Allow Overrides

**Manual control:**
- Force use for promotional items
- Force disable for stable items
- Auto-detect for others

### 5. Monitor Degradation

**Watch for items where covariates hurt:**
- Alert if accuracy drops >5%
- Auto-disable if consistently worse
- Investigate root cause

---

## Example Workflow

### Day 1: Initial Forecast

```python
# Generate forecast for SKU001
forecast = await generate_forecast(
    item_ids=["SKU001"],
    use_covariates="auto"  # Will run both methods
)

# Returns forecast from better method (based on history)
# But stores both for comparison
```

### Day 30: Actuals Arrive

```python
# Backfill actuals
await backfill_actuals(item_id="SKU001", actuals=[...])

# System automatically compares:
# - chronos-2_no_covariates: MAPE = 8.2%
# - chronos-2_with_covariates: MAPE = 12.5%

# Result: No covariates win (8.2% < 12.5%)
# System updates: SKU001 → use_covariates = False
```

### Day 60: Re-evaluation

```python
# Item starts having promotions
# System re-evaluates

# New comparison:
# - chronos-2_no_covariates: MAPE = 15.3%
# - chronos-2_with_covariates: MAPE = 7.8%

# Result: Covariates now win (7.8% < 15.3%)
# System updates: SKU001 → use_covariates = True
```

---

## Summary

**Key Principles:**

1. ✅ **Don't assume covariates help** - Test both methods
2. ✅ **Measure everything** - Track accuracy for both
3. ✅ **Select adaptively** - Use the better method per item
4. ✅ **Re-evaluate periodically** - Covariates may become relevant
5. ✅ **Allow overrides** - Manual control when needed

**Implementation:**
- Phase 2.1: Dual execution (run both, store both)
- Phase 2.2: Performance tracking (compare accuracy)
- Phase 2.3: Automatic detection (smart defaults)

**Result:** System automatically uses covariates only when they help, improving overall accuracy.

---

## Related Documents

- [Covariates Roadmap](COVARIATES_ROADMAP.md) - When covariates will be added
- [Expert Analysis](EXPERT_ANALYSIS.md) - Architecture recommendations
- [Data Models](DATA_MODELS.md) - Database schema for tracking

