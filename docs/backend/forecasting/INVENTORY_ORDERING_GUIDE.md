# Inventory Ordering Guide: Which Metrics to Follow

## Quick Answer

**For inventory ordering, use:**
1. **Forecast VALUES** (the actual predictions) → How much to order
2. **MAPE/MAE** → How much safety stock to add
3. **Bias** → Check for systematic over/under-forecasting

**Don't use:**
- Total Forecast vs Actual → Only for budget validation, not operational decisions

## Detailed Explanation

### Scenario: Choosing Between Models

**Chronos-2:**
- Total Forecast: 40 units
- MAPE: 39.0%
- MAE: 0.92 units/day

**Moving Average:**
- Total Forecast: 43 units  
- Actual: 45 units
- MAPE: 43.5%
- MAE: 0.95 units/day

### For Inventory Ordering: Use Chronos-2 ✅

**Why?**
1. **Better daily accuracy (MAPE 39% vs 43.5%)**
   - Lower daily errors = fewer stockouts
   - More reliable day-to-day predictions
   - Better for reorder point calculations

2. **Lower MAE (0.92 vs 0.95)**
   - Average daily error is smaller
   - Less safety stock needed
   - Lower inventory carrying costs

3. **Total difference is small (40 vs 43 = 3 units)**
   - 3 units difference over 30 days = negligible
   - Daily accuracy matters more for operations

### How to Use Metrics for Ordering

#### Step 1: Use Forecast Values
```
Order Quantity = Sum of daily forecasts for order period
```

**Example:**
- Chronos-2 forecasts: [1.0, 1.0, 1.0, 0.8, 0.9, ...] for 30 days
- Total to order = 40 units

#### Step 2: Add Safety Stock Based on MAPE/MAE
```
Safety Stock = MAE × Safety Factor × √(Lead Time)
```

**Example:**
- MAE = 0.92 units/day
- Lead time = 7 days
- Safety factor = 2 (for 95% service level)
- Safety Stock = 0.92 × 2 × √7 ≈ 4.9 units

**Total Order = Forecast (40) + Safety Stock (5) = 45 units**

#### Step 3: Check Bias
- **Positive Bias** (over-forecasting): You might order too much
- **Negative Bias** (under-forecasting): You might have stockouts
- **Near Zero Bias**: Good balance

## Why MAPE Matters More Than Total Accuracy

### Daily Accuracy (MAPE) → Operational Impact
- **Stockouts:** Happen when daily demand > daily forecast
- **Excess Inventory:** Happens when daily demand < daily forecast
- **MAPE measures this daily risk**

### Total Accuracy → Budget Impact
- **Budget Planning:** Total forecast helps plan overall spend
- **Volume Planning:** Useful for high-level purchasing
- **Less critical for day-to-day operations**

## Real-World Example

**Scenario:** Ordering for next 30 days

**Chronos-2 (MAPE 39%, Total 40):**
- Daily forecasts: More consistent
- Lower daily errors → Fewer stockouts
- Safety stock: 5 units (based on MAE 0.92)
- **Order: 40 + 5 = 45 units**

**Moving Average (MAPE 43.5%, Total 43):**
- Daily forecasts: More variable
- Higher daily errors → More stockout risk
- Safety stock: 6 units (based on MAE 0.95)
- **Order: 43 + 6 = 49 units**

**Result:** Even though Moving Average total (43) is closer to actual (45), you'd need MORE safety stock (6 vs 5) because of worse daily accuracy.

## Decision Framework

### Use MAPE/MAE When:
✅ Setting reorder points
✅ Calculating safety stock
✅ Daily inventory management
✅ Avoiding stockouts
✅ Minimizing carrying costs

### Use Total Forecast When:
✅ Budget planning
✅ High-level purchasing decisions
✅ Volume planning (quarterly/annual)
✅ Supplier negotiations

## Best Practice Recommendation

**For inventory ordering:**
1. **Primary:** Use model with **lower MAPE** (better daily accuracy)
2. **Secondary:** Check **MAE** for safety stock calculation
3. **Tertiary:** Verify **Bias** isn't systematically wrong
4. **Ignore:** Total forecast vs actual (unless for budget validation)

**In your case:**
- **Choose Chronos-2** (MAPE 39% < 43.5%)
- Order based on its forecast values (40 units)
- Add safety stock based on its MAE (0.92 units/day)
- Total order ≈ 45 units

## Additional Considerations

### If Total Accuracy Matters More
Some businesses prioritize total volume accuracy over daily accuracy:
- **Bulk ordering** (monthly/quarterly)
- **Long lead times** (weeks/months)
- **Budget constraints** (fixed purchasing budget)

In these cases, you might choose Moving Average (43 vs 45 is closer than 40 vs 45).

### Hybrid Approach
1. Use **Chronos-2** for daily forecasts (better MAPE)
2. Adjust total if needed: If actual is consistently 45, add 5 units buffer
3. Monitor Bias: If consistently under-forecasting, add systematic adjustment

## Summary

**For inventory ordering, prioritize:**
1. ✅ **MAPE** (daily accuracy) - Most important
2. ✅ **MAE** (safety stock calculation)
3. ✅ **Bias** (systematic errors)
4. ⚠️ **Total Forecast vs Actual** - Only for budget validation

**Your case:** Choose **Chronos-2** (lower MAPE) even though total is slightly further off, because daily accuracy matters more for inventory operations.

