# Data Volume Analysis - Forecasting System

**Date:** 2025-12-06  
**Purpose:** Calculate storage requirements and data growth projections

---

## Quick Answer

**Per SKU per day:**
- **Phase 1 (MVP):** ~1-2 KB per day (1 forecast run + 30 result rows)
- **Phase 2 (With Covariates):** ~2-4 KB per day (1 forecast run + 60 result rows)
- **1000 SKUs, 30-day forecasts:** ~30-60 MB per day

---

## Data Volume Calculation

### Per Forecast Run

**Table: `forecast_runs`**
- **1 row per forecast execution**
- **Size:** ~200-300 bytes per row

**Fields:**
```sql
forecast_run_id (UUID)        = 16 bytes
client_id (UUID)              = 16 bytes
user_id (VARCHAR)             = ~20 bytes
primary_model (VARCHAR)       = ~15 bytes
prediction_length (INT)       = 4 bytes
item_ids (JSONB)              = ~50 bytes (for 1-10 items)
recommended_method (VARCHAR)  = ~20 bytes
status (VARCHAR)              = ~10 bytes
error_message (TEXT)          = 0-200 bytes (usually NULL)
created_at (TIMESTAMPTZ)      = 8 bytes
```

**Total:** ~150-300 bytes per forecast run

### Per Forecast Result

**Table: `forecast_results`**
- **N rows per forecast run** (where N = prediction_length)
- **Size:** ~150-200 bytes per row

**Fields:**
```sql
result_id (UUID)              = 16 bytes
forecast_run_id (UUID)        = 16 bytes
client_id (UUID)              = 16 bytes
item_id (VARCHAR)             = ~20 bytes
method (VARCHAR)              = ~25 bytes
date (DATE)                   = 4 bytes
horizon_day (INT)             = 4 bytes
point_forecast (NUMERIC)      = 8 bytes
p10 (NUMERIC)                 = 8 bytes
p50 (NUMERIC)                 = 8 bytes
p90 (NUMERIC)                 = 8 bytes
actual_value (NUMERIC)        = 8 bytes (NULL initially)
created_at (TIMESTAMPTZ)      = 8 bytes
```

**Total:** ~150-200 bytes per result row

---

## Scenarios

### Scenario 1: Phase 1 (MVP) - Single Method

**Assumptions:**
- 1 forecast run per SKU per day
- 30-day prediction length
- 1 method (chronos-2 OR statistical_ma7)

**Per SKU per day:**
```
forecast_runs:     1 row  × 250 bytes  = 250 bytes
forecast_results:  30 rows × 175 bytes  = 5,250 bytes
─────────────────────────────────────────────────
Total:                                   5,500 bytes
                                         ≈ 5.4 KB
```

**Per 1000 SKUs per day:**
```
5.4 KB × 1,000 = 5.4 MB per day
```

**Per month (30 days):**
```
5.4 MB × 30 = 162 MB per month
```

**Per year:**
```
162 MB × 12 = 1.94 GB per year
```

---

### Scenario 2: Phase 2 - Dual Method (With/Without Covariates)

**Assumptions:**
- 1 forecast run per SKU per day
- 30-day prediction length
- 2 methods (with covariates + without covariates)

**Per SKU per day:**
```
forecast_runs:     1 row  × 250 bytes  = 250 bytes
forecast_results:  60 rows × 175 bytes  = 10,500 bytes (30 × 2 methods)
─────────────────────────────────────────────────
Total:                                   10,750 bytes
                                         ≈ 10.5 KB
```

**Per 1000 SKUs per day:**
```
10.5 KB × 1,000 = 10.5 MB per day
```

**Per month (30 days):**
```
10.5 MB × 30 = 315 MB per month
```

**Per year:**
```
315 MB × 12 = 3.78 GB per year
```

---

### Scenario 3: Multiple Forecasts per Day

**Assumptions:**
- 2 forecast runs per SKU per day (manual + automatic)
- 30-day prediction length
- 2 methods

**Per SKU per day:**
```
forecast_runs:     2 rows × 250 bytes  = 500 bytes
forecast_results:  120 rows × 175 bytes = 21,000 bytes (30 × 2 methods × 2 runs)
─────────────────────────────────────────────────
Total:                                   21,500 bytes
                                         ≈ 21 KB
```

**Per 1000 SKUs per day:**
```
21 KB × 1,000 = 21 MB per day
```

---

## Storage Projections

### Small Business (100 SKUs)

| Phase | Per Day | Per Month | Per Year |
|-------|---------|-----------|----------|
| Phase 1 | 540 KB | 16 MB | 194 MB |
| Phase 2 | 1.05 MB | 32 MB | 378 MB |

### Medium Business (1,000 SKUs)

| Phase | Per Day | Per Month | Per Year |
|-------|---------|-----------|----------|
| Phase 1 | 5.4 MB | 162 MB | 1.94 GB |
| Phase 2 | 10.5 MB | 315 MB | 3.78 GB |

### Large Business (10,000 SKUs)

| Phase | Per Day | Per Month | Per Year |
|-------|---------|-----------|----------|
| Phase 1 | 54 MB | 1.62 GB | 19.4 GB |
| Phase 2 | 105 MB | 3.15 GB | 37.8 GB |

---

## Database Indexes

**Additional storage for indexes:**
- Indexes add ~20-30% overhead
- **Phase 1:** ~1.2-1.5× base size
- **Phase 2:** ~1.2-1.5× base size

**Example (1000 SKUs, Phase 2):**
```
Base data:     3.78 GB/year
Indexes:       ~0.75 GB/year
────────────────────────────
Total:         ~4.5 GB/year
```

---

## Data Retention

### Recommended Retention Policies

**Forecast Runs:**
- **Active:** Keep last 90 days (for recent analysis)
- **Archive:** Keep last 2 years (for historical comparison)
- **Delete:** Older than 2 years (unless needed for compliance)

**Forecast Results:**
- **Active:** Keep last 90 days (for accuracy tracking)
- **Archive:** Keep last 1 year (for seasonal analysis)
- **Delete:** Older than 1 year (unless actuals are backfilled)

### Storage Savings

**With 90-day retention:**
```
Phase 2, 1000 SKUs:
- 90 days × 10.5 MB = 945 MB (vs 3.78 GB/year)
- Savings: ~75% reduction
```

---

## Performance Considerations

### Query Performance

**Indexes Required:**
```sql
-- Fast lookups by item
CREATE INDEX idx_results_item_date ON forecast_results(item_id, date);

-- Fast lookups by forecast run
CREATE INDEX idx_results_run ON forecast_results(forecast_run_id);

-- Fast lookups by client
CREATE INDEX idx_results_client ON forecast_results(client_id);
```

**Query Patterns:**
- Get latest forecast for item: `O(log n)` with index
- Get forecast history: `O(n)` where n = days retained
- Compare methods: `O(n)` where n = result rows

### Insert Performance

**Bulk Insert:**
- Insert 30-60 rows per forecast run
- Use batch inserts for efficiency
- **Expected:** ~10-50ms per forecast run

---

## Compression

### PostgreSQL Compression

**TOAST (The Oversized-Attribute Storage Technique):**
- Automatically compresses large text/JSONB fields
- `item_ids` (JSONB) may be compressed
- `error_message` (TEXT) may be compressed

**Estimated savings:** 10-20% for text-heavy data

### Table-Level Compression

**PostgreSQL 14+ (if using):**
- Can enable table compression
- **Estimated savings:** 30-50% for numeric-heavy data

**Example:**
```
Phase 2, 1000 SKUs, uncompressed: 3.78 GB/year
Phase 2, 1000 SKUs, compressed:   ~2.5 GB/year
```

---

## Summary Table

### Per SKU per Day

| Scenario | Forecast Runs | Result Rows | Size |
|----------|--------------|-------------|------|
| **Phase 1 (MVP)** | 1 | 30 | ~5.4 KB |
| **Phase 2 (Dual Method)** | 1 | 60 | ~10.5 KB |
| **Phase 2 (2 Runs/Day)** | 2 | 120 | ~21 KB |

### Annual Storage (1000 SKUs)

| Scenario | Uncompressed | With Indexes | Compressed |
|----------|--------------|--------------|------------|
| **Phase 1** | 1.94 GB | 2.3 GB | ~1.5 GB |
| **Phase 2** | 3.78 GB | 4.5 GB | ~2.5 GB |

### Key Takeaways

1. ✅ **Small footprint:** ~5-10 KB per SKU per day
2. ✅ **Scalable:** 1000 SKUs = ~4-5 GB/year (with indexes)
3. ✅ **Manageable:** 90-day retention reduces to ~1 GB/year
4. ✅ **Efficient:** Indexes add ~20% overhead (acceptable)

---

## Recommendations

### Storage Strategy

1. **Start with 90-day retention** (reduce to 1 year if needed)
2. **Enable compression** (PostgreSQL 14+)
3. **Archive old data** (move to cold storage after 1 year)
4. **Monitor growth** (set up alerts at 80% capacity)

### Performance Strategy

1. **Create indexes** on frequently queried columns
2. **Partition tables** by date (if >10M rows)
3. **Use batch inserts** for forecast results
4. **Monitor query performance** (slow query log)

### Cost Estimation (Cloud)

**AWS RDS PostgreSQL (1000 SKUs, Phase 2):**
- Storage: ~5 GB/year = ~$0.12/month (gp3, $0.115/GB-month)
- I/O: Minimal (mostly inserts)
- **Total:** ~$1.50/year for storage

**Very affordable!** ✅

