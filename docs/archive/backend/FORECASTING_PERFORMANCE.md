# Forecasting Integration: Performance Analysis

> **🛑 DEPRECATED**: This document has been consolidated into [forecasting/README.md](../forecasting/README.md)
>
> **Date Archived**: 2025-12-29
>
> This content is no longer maintained. Please refer to the consolidated documentation for current information.

## Performance Impact Assessment

### Current State (Historical Data Only)
**Query Pattern:**
```sql
SELECT AVG(daily_total) 
FROM (
    SELECT date_local, SUM(units_sold) as daily_total
    FROM ts_demand_daily
    WHERE client_id = ? AND item_id = ? 
      AND date_local >= ? AND date_local <= ?
    GROUP BY date_local
) daily_totals
```

**Performance:**
- ✅ Single query per product
- ✅ Indexed: `idx_ts_demand_daily_client_item_date` (composite index)
- ✅ Fast: ~10-50ms per product
- ✅ Scales: O(n) where n = number of products

### Proposed State (With Forecast Check)
**Additional Query Pattern:**
```sql
-- Check for latest forecast
SELECT fr.forecast_run_id, fr.created_at
FROM forecast_runs fr
WHERE fr.client_id = ? 
  AND fr.created_at >= NOW() - INTERVAL '7 days'
ORDER BY fr.created_at DESC
LIMIT 1;

-- Get forecast demand (if exists)
SELECT SUM(point_forecast) as total_forecast
FROM forecast_results
WHERE forecast_run_id = ? 
  AND item_id = ?
  AND date >= CURRENT_DATE
  AND date < CURRENT_DATE + INTERVAL '30 days'
```

**Performance Impact:**
- ⚠️ **+1-2 queries per request** (check forecast_run, get forecast_results)
- ⚠️ **+20-100ms per request** (depending on forecast table size)
- ⚠️ **N+1 problem risk** if done per-product in loop

## Performance Risks

### 1. **N+1 Query Problem** (HIGH RISK)
**Current code pattern:**
```python
for product in products:  # Loop through products
    metrics = await compute_product_metrics(...)  # Per-product query
```

**If we add forecast check per product:**
```python
for product in products:
    forecast = await get_latest_forecast(...)  # ❌ N queries!
    metrics = await compute_product_metrics(..., forecast)
```

**Impact:** 
- 10 products = 10 forecast queries = 200-1000ms additional latency
- 100 products = 100 forecast queries = 2-10 seconds additional latency

### 2. **Missing Indexes** (MEDIUM RISK)
**Current indexes on `forecast_results`:**
- ✅ `client_id` (indexed)
- ✅ `item_id` (indexed)
- ✅ `(forecast_run_id, item_id)` (composite)
- ✅ `(item_id, method, date)` (composite)

**Missing for our use case:**
- ❌ `(client_id, item_id, created_at)` - For finding latest forecast per item
- ❌ `(forecast_run_id, item_id, date)` - For date range queries

### 3. **Forecast Table Growth** (LOW RISK - Daily/Weekly Runs)
- Each forecast run creates 30 rows per item (30 days × 1 item)
- 100 items = 3,000 rows per run
- **Daily runs:** 90,000 rows/month (3,000 × 30 days)
- **Weekly runs:** 12,000 rows/month (3,000 × 4 weeks)
- **Impact:** Minimal - table grows slowly, queries remain fast
- **Note:** With daily/weekly runs, forecast_run_id changes infrequently → excellent caching opportunity

## Optimization Strategies

### ✅ **Strategy 1: Batch Forecast Lookup** (RECOMMENDED)
**Instead of per-product queries, fetch all at once:**

```python
# Get all products first
products = await get_products(...)

# Batch: Get latest forecast run for client
latest_run = await get_latest_forecast_run(client_id, max_age_days=7)

# Batch: Get all forecasts for all products in one query
if latest_run:
    item_ids = [p.item_id for p in products]
    forecasts = await get_forecast_demand_batch(
        forecast_run_id=latest_run.forecast_run_id,
        item_ids=item_ids
    )
else:
    forecasts = {}

# Use forecasts in loop (no additional queries)
for product in products:
    forecast_demand = forecasts.get(product.item_id)
    metrics = await compute_product_metrics(..., forecast_demand)
```

**Performance:**
- ✅ **1 query** for forecast run check
- ✅ **1 query** for all forecast results (batch)
- ✅ **Total: +2 queries** regardless of product count
- ✅ **Latency: +20-50ms** (constant, not per-product)

### ✅ **Strategy 2: Add Missing Indexes**
**Create composite index for forecast lookup:**

```sql
-- Migration: Add index for latest forecast lookup
CREATE INDEX idx_forecast_runs_client_created 
ON forecast_runs(client_id, created_at DESC);

-- Index for batch forecast query
CREATE INDEX idx_forecast_results_run_item_date 
ON forecast_results(forecast_run_id, item_id, date);
```

**Impact:**
- ✅ Forecast run lookup: 1-5ms (was 10-50ms)
- ✅ Batch forecast query: 10-30ms (was 50-200ms)

### ✅ **Strategy 3: Cache Forecast Run ID** (HIGH VALUE - Daily/Weekly Runs)
**Cache the latest forecast_run_id per client:**

```python
# Redis/memory cache
# Since forecasts run daily/weekly, cache can be longer
cache_key = f"latest_forecast_run:{client_id}"
latest_run_id = await cache.get(cache_key)

if not latest_run_id:
    latest_run = await get_latest_forecast_run(client_id)
    if latest_run:
        # Cache for 24 hours (forecast runs daily) or 7 days (weekly)
        ttl = 86400 if daily else 604800  # 24h or 7 days
        await cache.set(cache_key, latest_run.id, ttl=ttl)
        latest_run_id = latest_run.id
```

**Impact:**
- ✅ Forecast run check: **0-1ms (cached)** vs 5-20ms (query)
- ✅ **Cache hit rate: ~99%** (forecast_run_id changes once per day/week)
- ✅ Reduces database load by 99%
- ✅ **Perfect for daily/weekly forecast schedule**

### ✅ **Strategy 4: Optional/Feature Flag**
**Make forecast usage optional:**

```python
# Config or feature flag
USE_FORECASTS = settings.get("use_forecasts_in_dashboard", False)

if USE_FORECASTS:
    forecast_demand = await get_latest_forecast_demand(...)
else:
    forecast_demand = None  # Use historical
```

**Impact:**
- ✅ Can disable if performance issues
- ✅ Gradual rollout possible
- ✅ A/B testing capability

### ✅ **Strategy 5: Background Pre-computation** (OPTIMAL - Daily/Weekly Runs)
**Pre-compute metrics with forecasts after each forecast run:**

```python
# Background job (Celery/cron) - Run after forecast generation
async def precompute_dashboard_metrics(forecast_run_id: UUID):
    # Triggered after forecast run completes
    products = await get_all_products(client_id)
    latest_forecast = await get_forecast_run(forecast_run_id)
    
    # Pre-compute and cache (cache until next forecast run)
    for product in products:
        metrics = compute_metrics(..., forecast=latest_forecast)
        # Cache for 24 hours (daily) or 7 days (weekly)
        ttl = 86400 if daily else 604800
        await cache.set(f"metrics:{product.item_id}", metrics, ttl=ttl)

# API endpoint uses cache
metrics = await cache.get(f"metrics:{product.item_id}")
```

**Impact:**
- ✅ API response: **0-5ms (cached)** vs 50-200ms (computed)
- ✅ **Cache valid until next forecast run** (24h or 7 days)
- ✅ **No stale data** - cache refreshed when new forecast arrives
- ✅ **Perfect for daily/weekly schedule** - compute once, serve many times

## Recommended Implementation (Daily/Weekly Forecasts)

### Phase 1: Safe Implementation (No Performance Risk)
1. ✅ **Batch forecast lookup** (Strategy 1)
2. ✅ **Add missing indexes** (Strategy 2)
3. ✅ **Cache forecast_run_id** (Strategy 3) - **HIGH VALUE for daily/weekly**
4. ✅ **Feature flag** (Strategy 4) - default OFF

**Expected Performance (with caching):**
- Current: ~50ms for 10 products
- With forecasts (cached): ~**52ms** for 10 products (+4% - negligible!)
- With 100 products: ~200ms → ~**205ms** (+2.5% - negligible!)
- **Cache hit rate: 99%** (forecast_run_id changes once per day/week)

### Phase 2: Optimal Implementation (After Forecast Run)
1. ✅ **Background pre-computation** (Strategy 5) - **Perfect for daily/weekly**
2. ✅ **Trigger after forecast generation**
3. ✅ **Cache metrics until next forecast run**

**Expected Performance (with pre-computation):**
- Current: ~50ms for 10 products
- With pre-computed forecasts: ~**50ms** (0% overhead - uses cache!)
- **Zero database queries** for forecast lookup
- **Cache valid for 24h (daily) or 7 days (weekly)**

### Phase 2: Optimization (If Needed)
1. ✅ **Cache forecast run ID** (Strategy 3)
2. ✅ **Monitor query performance**
3. ✅ **Add query logging**

### Phase 3: Advanced (If Scale Issues)
1. ✅ **Background pre-computation** (Strategy 5)
2. ✅ **Forecast table partitioning** (by date)
3. ✅ **Read replicas** for forecast queries

## Performance Targets

| Metric | Current | Target (With Forecasts) | Acceptable? |
|--------|---------|------------------------|-------------|
| Dashboard load (10 products) | 50ms | <100ms | ✅ Yes |
| Product list (100 products) | 200ms | <300ms | ✅ Yes |
| Single product detail | 20ms | <30ms | ✅ Yes |
| Forecast lookup overhead | 0ms | <20ms | ✅ Yes |

## Monitoring

**Key metrics to track:**
1. **API response time** (p50, p95, p99)
2. **Database query time** (forecast queries)
3. **Cache hit rate** (if using caching)
4. **Forecast table size** (growth rate)

**Alerts:**
- API response time > 500ms (p95)
- Forecast query time > 100ms
- Cache hit rate < 80% (if using cache)

## Conclusion (Daily/Weekly Forecast Schedule)

**Will it slow down the system?**
- **Short answer:** **No, with proper caching** (forecasts run daily/weekly)
- **Impact with caching:** +2-5ms per request (negligible)
- **Impact without caching:** +20-50ms per request (still acceptable)
- **Risk:** Very low - daily/weekly schedule is perfect for caching
- **Mitigation:** Feature flag allows disabling if issues occur

**Recommendation:**
✅ **Proceed with implementation** using:
1. **Cache forecast_run_id** (Strategy 3) - **CRITICAL for daily/weekly**
2. Batch forecast lookup (Strategy 1)
3. Missing indexes (Strategy 2)
4. **Background pre-computation** (Strategy 5) - **OPTIMAL for daily/weekly**
5. Feature flag (Strategy 4)

**Why daily/weekly is perfect:**
- ✅ Forecast_run_id changes infrequently → excellent cache hit rate (99%+)
- ✅ Can pre-compute metrics after forecast run → zero overhead on API
- ✅ Cache valid until next forecast → no stale data issues
- ✅ Background job runs during off-peak hours → no user impact

**Performance Impact:**
- **Without optimization:** +20-50ms (acceptable)
- **With caching:** +2-5ms (negligible)
- **With pre-computation:** 0ms (zero overhead)

