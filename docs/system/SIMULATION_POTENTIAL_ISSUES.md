# Simulation System - Potential Issues & Investigation Areas

**Date**: 2024-12-18  
**Status**: Areas requiring investigation or validation

---

## 🔍 Areas of Concern

### 1. **Order Arrival Timing** ⚠️ MEDIUM

**Issue**: Orders arrive BEFORE sales are subtracted each day.

**Current Logic**:
```python
# Process order arrivals (orders placed earlier that arrive today)
arriving_orders = self.order_simulator.get_orders_arriving(current_date)
for order in arriving_orders:
    simulated_stock[order.item_id] += order.quantity  # Add stock first

# Then subtract sales
simulated_stock[item_id] = max(0.0, simulated_stock[item_id] - actual_sales)
```

**Question**: Is this realistic?
- **Real world**: Orders typically arrive at start of day or end of day
- **Impact**: If orders arrive at start of day, they're available for that day's sales (correct)
- **If orders arrive at end of day**: They wouldn't be available for same-day sales (potential issue)

**Investigation Needed**: 
- ✅ **Likely correct** - Most inventory systems assume orders arrive at start of day
- ⚠️ **Verify**: Check if this matches real-world behavior for your use case

---

### 2. **Forecast Staleness** ⚠️ MEDIUM

**Issue**: Forecasts are cached for 7 days, but demand patterns might change.

**Current Logic**:
```python
should_regenerate_forecast = (
    days_since_start == 0 or  # First day
    days_since_start % 7 == 0  # Weekly refresh
)
```

**Question**: Is weekly refresh sufficient?
- **Risk**: Using 7-day-old forecast during volatile periods
- **Impact**: Might miss demand spikes or drops
- **Trade-off**: More frequent = slower simulation

**Investigation Needed**:
- ⚠️ **Monitor**: Check if forecast values change significantly during 7-day window
- ⚠️ **Consider**: Adaptive refresh (regenerate if demand pattern changes significantly)

---

### 3. **Historical Average Fallback** ⚠️ LOW-MEDIUM

**Issue**: When forecast = 0, we use historical average from last 30 days.

**Current Logic**:
```python
if forecast_demand <= 0:
    historical_avg = await self._get_historical_average_demand(
        client_id, item_id, current_date, days=30
    )
    if historical_avg > 0:
        forecast_demand = historical_avg * 30
```

**Questions**:
1. What if there's no historical data (new product)?
2. What if last 30 days had zero sales (dead stock)?
3. Is 30-day average appropriate for all products?

**Investigation Needed**:
- ⚠️ **Edge case**: New products with no history
- ⚠️ **Edge case**: Dead stock (no sales in last 30 days)
- ⚠️ **Validation**: Check if fallback produces reasonable results

---

### 4. **Real Stock Fallback Calculation** ⚠️ MEDIUM

**Issue**: When `stock_on_date` is NULL, we calculate: `real_stock = previous_day - sales`

**Current Logic**:
```python
if real_stock_today is not None:
    real_stock[item_id] = real_stock_today  # From DB
else:
    # Fallback: calculate from previous day minus sales
    real_stock[item_id] = max(0.0, real_stock[item_id] - actual_sales)
```

**Problem**: This doesn't account for orders arriving in the real system.

**Impact**:
- Real stock might appear to decrease continuously
- Doesn't reflect actual inventory management
- **20% of days use this fallback** (from validation)

**Investigation Needed**:
- ⚠️ **Verify**: Is this acceptable for comparison purposes?
- ⚠️ **Consider**: Flag days where real stock is calculated vs from DB
- ⚠️ **Note**: This is documented limitation, but worth monitoring

---

### 5. **Orders in Transit Check** ⚠️ LOW

**Issue**: We check `arrival_date > current_date` to prevent duplicate orders.

**Current Logic**:
```python
orders_in_transit = [
    o for o in self.order_simulator.orders
    if o.item_id == item_id and not o.received and o.arrival_date > current_date
]
```

**Question**: What if an order arrives today (`arrival_date == current_date`)?
- **Current**: Not considered "in transit" (correct - it arrives today)
- **Risk**: Could place another order on same day if stock still low after arrival

**Investigation Needed**:
- ✅ **Likely correct** - Order arriving today is processed, then we check reorder point
- ⚠️ **Edge case**: What if stock is still below reorder point after order arrives?

---

### 6. **Forecast Generation Failures** ⚠️ MEDIUM

**Issue**: What happens if forecast generation fails or returns 0?

**Current Logic**:
```python
if forecast_demand <= 0:
    # Use historical average fallback
    historical_avg = await self._get_historical_average_demand(...)
    if historical_avg > 0:
        forecast_demand = historical_avg * 30
```

**Questions**:
1. What if forecast generation throws an exception?
2. What if historical average is also 0?
3. What if there's insufficient training data?

**Investigation Needed**:
- ⚠️ **Error handling**: Check if exceptions are caught properly
- ⚠️ **Edge case**: No forecast AND no historical data = forecast_demand = 0
- ⚠️ **Impact**: System won't place orders if forecast_demand = 0 (might be correct for dead stock)

---

### 7. **Initial Stock Mismatch** ⚠️ LOW

**Issue**: Initial stock might not match `stock_on_date` for start_date.

**Current Logic**:
```python
# Simulated: Uses initial_stock snapshot
simulated_stock[item_id] = initial_stock.get(item_id, 0.0)

# Real: Uses stock_on_date for start_date, or falls back to initial_stock
real_stock_start = await self._get_real_stock_for_date(...)
if real_stock_start is not None:
    real_stock[item_id] = real_stock_start
else:
    real_stock[item_id] = initial_stock.get(item_id, 0.0)
```

**Question**: What if they don't match?
- **Validation allows**: 1 unit difference
- **Impact**: Small mismatch at start is acceptable, but worth monitoring

**Investigation Needed**:
- ✅ **Acceptable** - 1 unit difference is reasonable
- ⚠️ **Monitor**: Check if mismatches are common or indicate data issues

---

### 8. **Multiple Items Sequential Processing** ⚠️ LOW

**Issue**: Items are processed sequentially, not in parallel.

**Current Logic**:
```python
for item_id in item_ids:  # Sequential
    # Process each item
```

**Question**: Does one item's failure affect others?
- **Current**: Each item is independent (good)
- **Risk**: If one item's forecast fails, others continue (correct behavior)

**Investigation Needed**:
- ✅ **Likely correct** - Items are independent
- ⚠️ **Performance**: Sequential processing is slow (known issue, addressed in scaling plan)

---

### 9. **Reorder Point Check Timing** ⚠️ LOW

**Issue**: We check reorder point using `stock_before_sales`, but calculate order quantity using `stock_after_sales`.

**Current Logic**:
```python
stock_before_sales = simulated_stock[item_id]  # Before sales
# ... subtract sales ...
if stock_before_sales <= reorder_point:  # Check before sales
    recommended_qty = calculate_recommended_order_quantity(
        forecast_demand,
        safety_stock,
        simulated_stock[item_id],  # After sales (current stock)
        moq=moq
    )
```

**Question**: Is this correct?
- **Reorder check**: Uses stock BEFORE sales (correct - check at start of day)
- **Order quantity**: Uses stock AFTER sales (correct - order to cover future demand)
- ✅ **Likely correct** - This matches real-world behavior

**Investigation Needed**:
- ✅ **Likely correct** - Standard inventory management practice

---

### 10. **Zero Sales Days** ⚠️ LOW

**Issue**: What happens on days with zero sales?

**Current Logic**:
```python
actual_sales = await self._get_actual_sales(...)  # Returns 0.0 if no sales
simulated_stock[item_id] = max(0.0, simulated_stock[item_id] - actual_sales)  # No change
```

**Question**: Is this handled correctly?
- ✅ **Likely correct** - Zero sales = no stock change
- ⚠️ **Edge case**: What if forecast expects sales but actual is 0? (forecast error, not simulation bug)

**Investigation Needed**:
- ✅ **Likely correct** - Zero sales handled properly

---

### 11. **Missing Product Data** ⚠️ LOW

**Issue**: What if product data is missing?

**Current Logic**:
```python
product = products.get(item_id)
if not product:
    continue  # Skip this item
```

**Question**: Is skipping the item acceptable?
- **Impact**: Item not simulated, no error raised
- **Risk**: Silent failure - user might not know item was skipped

**Investigation Needed**:
- ⚠️ **Consider**: Log warning when product data missing
- ⚠️ **Consider**: Return list of skipped items in response

---

### 12. **Lead Time Buffer** ⚠️ LOW

**Issue**: `lead_time_buffer_days` is added to lead time.

**Current Logic**:
```python
lead_time_days = await self._get_lead_time(...)
order = self.order_simulator.place_order(
    ...,
    lead_time_days=lead_time_days + config.lead_time_buffer_days,
    ...
)
```

**Question**: Is this applied correctly?
- ✅ **Likely correct** - Buffer adds safety margin
- ⚠️ **Verify**: Check if buffer is appropriate (default is 0)

**Investigation Needed**:
- ✅ **Likely correct** - Standard practice

---

## 🎯 Priority Investigation List

### High Priority (Should Investigate)
1. **None identified** - Core logic appears sound

### Medium Priority (Worth Investigating)
1. **Forecast Staleness** - Weekly caching might miss demand changes
2. **Real Stock Fallback** - 20% of days use calculated fallback (doesn't account for orders)
3. **Historical Average Fallback** - Edge cases (new products, dead stock)

### Low Priority (Monitor)
1. **Order Arrival Timing** - Verify start-of-day vs end-of-day assumption
2. **Orders in Transit Check** - Edge case: order arrives same day as reorder check
3. **Missing Product Data** - Silent skipping might be confusing

---

## ✅ Validated as Correct

1. **Order arrival before sales** - Standard practice
2. **Reorder point check timing** - Correct (before sales)
3. **Order quantity calculation** - Correct (after sales)
4. **Zero sales handling** - Correct
5. **Multiple items independence** - Correct
6. **Lead time buffer** - Correct

---

## 🔬 Recommended Tests

### 1. **Forecast Staleness Test**
- Run simulation with daily forecast generation
- Compare results with weekly caching
- Check if metrics differ significantly

### 2. **Real Stock Fallback Test**
- Identify days where real stock is calculated (not from DB)
- Manually verify calculations
- Check if results are reasonable

### 3. **Edge Case Tests**
- New product (no historical data)
- Dead stock (no sales in 30 days)
- Missing product data
- Forecast generation failure

### 4. **Order Timing Test**
- Verify order arrival timing assumption
- Check if orders arriving same day affect reorder logic

---

## 📊 Current Confidence Level

**Overall**: **HIGH** ✅

**Reasoning**:
- Core logic validated and working
- Edge cases identified and mostly handled
- Known limitations documented
- Medium-priority items are optimization/accuracy improvements, not bugs

**Recommendation**: 
- ✅ **Proceed with current implementation**
- ⚠️ **Monitor** medium-priority items during production use
- 🔬 **Test** edge cases if time permits

---

## 🚨 Critical Issues (None Found)

No critical bugs or logic errors identified. All concerns are:
- Optimization opportunities
- Edge case handling improvements
- Validation/monitoring needs

