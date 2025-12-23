# Simulation Scaling: 200 Products Analysis

**Goal**: Run simulations for 200 products to check:
1. **Global inventory level** (aggregated across all products)
2. **Stockout potential reductions** vs real data

**Status**: Design/Architecture Analysis (No Code Yet)

---

## Current System Capabilities

### ✅ What Already Works

1. **Aggregation Support**
   - `ComparisonEngine` already supports global metrics
   - `calculate_stockout_rate(item_id=None)` aggregates across all items
   - `calculate_inventory_value(item_id=None)` aggregates across all items
   - `calculate_service_level(item_id=None)` aggregates across all items

2. **Multi-Product Support**
   - Simulation loop already processes multiple items
   - Daily comparisons stored per item
   - Item-level results already calculated

### ⚠️ Current Limitations

1. **Performance**: Sequential processing
   - 1 product, 1 year = ~15 minutes (with weekly forecast caching)
   - 200 products × 15 min = **50 hours** (sequential) ❌ NOT FEASIBLE

2. **Response Size**: Too large for API
   - 200 products × 365 days = **73,000 daily comparisons**
   - JSON response: ~50-100MB (too large for HTTP)

3. **Forecast Generation**: One at a time
   - Each item generates forecast separately
   - No batching/parallelization

4. **Database Queries**: Per-item queries
   - Sales data: 1 query per item per day
   - Stock data: 1 query per item per day
   - 200 items × 365 days = **73,000 queries** per simulation

---

## Performance Analysis

### Current Bottlenecks

1. **Forecast Generation** (Biggest bottleneck)
   - Weekly forecast per item = 200 items × 52 weeks = 10,400 forecasts
   - Each forecast: ~5-10 seconds
   - Total: **14-28 hours** just for forecasts

2. **Database Queries** (Medium bottleneck)
   - Sales queries: 200 items × 365 days = 73,000 queries
   - Stock queries: 200 items × 365 days = 73,000 queries
   - Total: **146,000 queries** (if not batched)

3. **Memory** (Medium concern)
   - Daily comparisons: 73,000 records × ~500 bytes = **36MB**
   - Forecast cache: 10,400 entries × ~1KB = **10MB**
   - Total: ~50MB (manageable)

---

## Required Changes

### 1. **Batch Processing** (Critical)

**Current**: Process items sequentially
```python
for item_id in item_ids:  # Sequential
    # Process each item
```

**Needed**: Batch operations
- Batch forecast generation (multiple items at once)
- Batch database queries (fetch all items' sales for a day in one query)
- Parallel processing (async tasks for independent items)

**Impact**: 10-20x speedup

### 2. **Response Optimization** (Critical)

**Current**: Returns all daily comparisons
```python
daily_comparison=self._format_daily_comparisons()  # 73,000 records
```

**Needed**: Aggregation-only response
- Option A: Only return aggregated metrics (no daily comparisons)
- Option B: Paginated daily comparisons (if needed)
- Option C: Summary by week/month instead of daily

**Impact**: Reduces response from 50MB to <1MB

### 3. **Database Query Optimization** (High Priority)

**Current**: Per-item queries
```python
for item_id in item_ids:
    sales = await _get_actual_sales(item_id, date)  # 1 query per item
```

**Needed**: Batch queries
```python
# Fetch all items' sales for a day in one query
sales = await _get_actual_sales_batch(item_ids, date)  # 1 query for all items
```

**Impact**: Reduces queries from 146,000 to ~730 (200x reduction)

### 4. **Forecast Generation Optimization** (High Priority)

**Current**: One forecast at a time
```python
forecast = await _get_forecasted_demand(item_id, date)  # Sequential
```

**Needed**: Batch forecast generation
```python
# Generate forecasts for multiple items at once
forecasts = await _get_forecasted_demand_batch(item_ids, date)  # Parallel
```

**Impact**: 5-10x speedup for forecast generation

### 5. **Progress Tracking** (Medium Priority)

**Needed**: Async job with progress updates
- Long-running simulation (even optimized: 2-5 hours)
- Need: Job queue (Celery/Redis) or background task
- Progress endpoint: `GET /api/v1/simulation/{id}/status`
- Results endpoint: `GET /api/v1/simulation/{id}/results`

---

## Global Metrics Design

### Metrics to Track (Global Level)

1. **Global Inventory Value**
   ```
   Total Inventory Value = Σ(avg_stock_per_item × unit_cost × days)
   ```
   - Simulated: Sum of all items' average inventory value
   - Real: Sum of all items' average inventory value
   - Reduction: `(Real - Simulated) / Real × 100%`

2. **Global Stockout Rate**
   ```
   Stockout Rate = (Total Stockout Days) / (Total Item-Days)
   ```
   - Simulated: Total stockout days across all items / total item-days
   - Real: Total stockout days across all items / total item-days
   - Reduction: `(Real - Simulated) / Real × 100%`

3. **Global Service Level**
   ```
   Service Level = (Total Days In Stock) / (Total Item-Days)
   ```
   - Simulated: Total days in stock / total item-days
   - Real: Total days in stock / total item-days
   - Improvement: `Simulated - Real`

4. **Total Orders Placed**
   ```
   Total Orders = Σ(orders_per_item)
   ```
   - Compare: Simulated vs Real (if we track real orders)

5. **Category-Level Breakdown** (Optional)
   - Group by product category
   - Show metrics per category
   - Identify which categories benefit most

6. **Supplier-Level Breakdown** (Optional)
   - Group by supplier
   - Show metrics per supplier
   - Identify supplier performance

### Response Structure

```json
{
  "simulation_id": "uuid",
  "status": "completed",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "total_items": 200,
  "total_days": 366,
  
  "global_metrics": {
    "stockout_rate": {
      "simulated": 0.012,  // 1.2% of item-days
      "real": 0.048,        // 4.8% of item-days
      "reduction": 0.75     // 75% reduction
    },
    "inventory_value": {
      "simulated": 2400000,  // $2.4M average
      "real": 3100000,        // $3.1M average
      "reduction": 0.23       // 23% reduction
    },
    "service_level": {
      "simulated": 0.988,     // 98.8%
      "real": 0.952,          // 95.2%
      "improvement": 0.036    // 3.6% improvement
    },
    "total_orders": {
      "simulated": 1200,      // 1,200 orders placed
      "real": 1500            // 1,500 orders (if tracked)
    }
  },
  
  "category_breakdown": [
    {
      "category": "Electronics",
      "items": 50,
      "stockout_reduction": 0.80,
      "inventory_reduction": 0.25
    },
    // ... other categories
  ],
  
  "item_level_summary": [
    {
      "item_id": "SKU001",
      "stockout_reduction": 0.70,
      "inventory_reduction": 0.20,
      "total_orders": 6
    },
    // ... top 20 items (or paginated)
  ],
  
  "daily_comparison": null  // Not included (too large)
}
```

---

## Implementation Strategy

### Phase 1: Core Optimizations (Must Have)

1. **Batch Database Queries**
   - Create `_get_actual_sales_batch()` method
   - Create `_get_real_stock_batch()` method
   - Fetch all items' data in one query per day

2. **Response Optimization**
   - Add `include_daily_comparisons: bool = False` to request
   - Default to `False` for large simulations
   - Only include aggregated metrics

3. **Forecast Batching** (If ForecastService supports it)
   - Check if `ForecastService.generate_forecast()` can handle multiple items
   - If not, use async tasks to generate forecasts in parallel

**Estimated Time**: 2-3 days  
**Expected Performance**: 5-10x speedup (50 hours → 5-10 hours)

### Phase 2: Async Job Processing (Must Have)

1. **Background Job Queue**
   - Use Celery + Redis (or FastAPI BackgroundTasks)
   - Create simulation job endpoint
   - Store results in database or cache

2. **Progress Tracking**
   - Track: `{current_day}/{total_days}`, `{current_item}/{total_items}`
   - Status endpoint: `GET /api/v1/simulation/{id}/status`
   - Results endpoint: `GET /api/v1/simulation/{id}/results`

3. **Job Management**
   - List running/completed simulations
   - Cancel running simulations
   - Cleanup old results

**Estimated Time**: 2-3 days  
**Expected Performance**: User doesn't wait (async)

### Phase 3: Advanced Optimizations (Nice to Have)

1. **Parallel Item Processing**
   - Process multiple items concurrently (async tasks)
   - Use asyncio.gather() for independent items

2. **Forecast Caching Across Items**
   - Cache forecasts by date (not just by item)
   - If multiple items need forecast for same date, reuse

3. **Sampling Mode**
   - Option to simulate only subset of items (e.g., top 50 by sales)
   - Extrapolate results to full catalog

**Estimated Time**: 2-3 days  
**Expected Performance**: Additional 2-3x speedup

---

## Performance Targets

### After Phase 1 (Batch Queries + Response Optimization)
- **200 products, 1 year**: 5-10 hours
- **Response size**: <1MB (aggregated only)
- **Feasible**: ✅ Yes (run overnight)

### After Phase 2 (Async Jobs)
- **User experience**: Submit job, check progress, get results
- **No blocking**: ✅ User doesn't wait

### After Phase 3 (Full Optimization)
- **200 products, 1 year**: 2-5 hours
- **Feasible**: ✅ Yes (reasonable runtime)

---

## Data Volume Estimates

### Daily Comparisons (If Included)
- 200 products × 365 days = **73,000 records**
- Size: ~50-100MB JSON
- **Recommendation**: Don't include by default

### Aggregated Metrics (Always Included)
- Global metrics: ~1KB
- Category breakdown: ~10KB (10 categories)
- Item-level summary: ~100KB (200 items)
- **Total**: ~111KB ✅ Manageable

---

## Use Cases

### 1. **Global Inventory Level Check**
```
Question: "What would our total inventory value be if we used our system?"
Answer: Global metrics.inventory_value.simulated
```

### 2. **Stockout Reduction Potential**
```
Question: "How much could we reduce stockouts?"
Answer: Global metrics.stockout_rate.reduction (e.g., 75% reduction)
```

### 3. **Category Analysis**
```
Question: "Which product categories benefit most?"
Answer: category_breakdown sorted by stockout_reduction
```

### 4. **ROI Calculation**
```
Question: "What's the financial impact?"
Answer: 
  - Inventory reduction: $700K (23% of $3.1M)
  - Stockout reduction: X% fewer lost sales
  - Total savings: $XXX
```

---

## Recommendations

### Immediate (Before 200 Products)
1. ✅ **Batch database queries** - Critical for performance
2. ✅ **Response optimization** - Critical for API usability
3. ✅ **Async job processing** - Critical for user experience

### Short Term (After 200 Products Works)
4. **Category breakdown** - Useful for analysis
5. **Supplier breakdown** - Useful for supplier management
6. **Sampling mode** - For quick tests

### Long Term (Future Enhancements)
7. **Real-time progress updates** (WebSocket)
8. **Comparison reports** (PDF/Excel export)
9. **Historical simulation tracking** (save results, compare runs)

---

## Conclusion

**Current System**: ✅ Already supports global aggregation  
**Performance**: ❌ Not feasible for 200 products (50 hours)  
**Solution**: Batch queries + async jobs + response optimization  
**Target**: 2-5 hours for 200 products, 1 year

**Key Insight**: The system architecture already supports global metrics - we just need to optimize performance and response size.

