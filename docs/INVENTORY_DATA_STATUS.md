# Inventory Data Status

**Question:** Do we have inventory information for both datasets (M5 and synthetic) that we can see historically?

---

## Current Status

### ✅ Current Stock Data
- **Table:** `stock_levels`
- **Fields:** `item_id`, `location_id`, `current_stock`
- **Status:** ✅ **Populated** for all products
- **Visibility:** Current stock only (snapshot in time)

### ⚠️ Historical Stock Data
- **Field:** `stock_on_date` in `ts_demand_daily` table
- **Status:** ❌ **NOT populated** (all NULL)
- **Capability:** ✅ Field exists, can be populated
- **Visibility:** Would show stock levels for each date historically

---

## What We Have

### For M5 Dataset:
- ✅ **Sales Data:** Historical sales (2015-2024) in `ts_demand_daily`
- ✅ **Current Stock:** Current stock levels in `stock_levels`
- ❌ **Historical Stock:** `stock_on_date` is NULL (not populated)

### For Synthetic Dataset:
- ✅ **Sales Data:** Synthetic sales data in `ts_demand_daily`
- ✅ **Current Stock:** Current stock levels in `stock_levels`
- ❌ **Historical Stock:** `stock_on_date` is NULL (not populated)

---

## Solution: Populate Historical Stock

**Created:** `backend/scripts/populate_historical_stock.py`

**How it works:**
1. Gets current stock from `stock_levels` table
2. Works backwards through dates in `ts_demand_daily`
3. Calculates: `stock_yesterday = stock_today + sales_today - restocking`
4. Simulates weekly restocking (Mondays)
5. Updates `stock_on_date` for each date

**Usage:**
```bash
# Populate historical stock for last 365 days
uv run python backend/scripts/populate_historical_stock.py \
    --client-id <uuid> \
    --days-back 365
```

**Automatic:** Now included in `setup_test_data.py` (Step 10)

---

## After Population

### You'll be able to:

1. **Query Historical Stock:**
```sql
SELECT 
    item_id,
    date_local,
    units_sold,
    stock_on_date
FROM ts_demand_daily
WHERE client_id = '<uuid>'
  AND item_id = 'M5_HOBBIES_1_008_CA_1_evaluation'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date_local;
```

2. **Detect Stockouts:**
```sql
SELECT 
    item_id,
    date_local,
    units_sold,
    stock_on_date
FROM ts_demand_daily
WHERE client_id = '<uuid>'
  AND stock_on_date = 0
  AND units_sold = 0  -- Likely stockout
ORDER BY date_local DESC;
```

3. **Analyze Stock Trends:**
```sql
SELECT 
    item_id,
    AVG(stock_on_date) as avg_stock,
    MIN(stock_on_date) as min_stock,
    MAX(stock_on_date) as max_stock
FROM ts_demand_daily
WHERE client_id = '<uuid>'
  AND stock_on_date IS NOT NULL
  AND date_local >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY item_id;
```

---

## Data Flow

```
┌─────────────────────────────────────┐
│  Current Stock (stock_levels)       │
│  ✅ Populated                       │
│  - item_id, location_id, stock      │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Historical Stock Calculation       │
│  ✅ populate_historical_stock.py    │
│  - Works backwards from today       │
│  - Uses sales data                  │
│  - Simulates restocking             │
└─────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│  Historical Stock (stock_on_date)   │
│  ✅ Populated                       │
│  - One value per date per SKU       │
│  - Enables historical analysis      │
└─────────────────────────────────────┘
```

---

## Verification

After running `setup_test_data.py`, verify:

```sql
-- Check if stock_on_date is populated
SELECT 
    COUNT(*) as total_records,
    COUNT(stock_on_date) as records_with_stock,
    MIN(stock_on_date) as min_stock,
    MAX(stock_on_date) as max_stock,
    AVG(stock_on_date) as avg_stock
FROM ts_demand_daily
WHERE client_id = '<your-client-uuid>'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days';

-- Should show:
-- records_with_stock > 0
-- min_stock >= 0
-- max_stock > 0
```

---

## Summary

| Data Type | M5 Dataset | Synthetic Dataset | Status |
|-----------|------------|-------------------|--------|
| **Sales Data** | ✅ Yes | ✅ Yes | Complete |
| **Current Stock** | ✅ Yes | ✅ Yes | Complete |
| **Historical Stock** | ⚠️ Can be populated | ⚠️ Can be populated | **Now Available** |

**Answer:** 
- ✅ We have current inventory info for both datasets
- ✅ We now have the capability to populate historical inventory
- ✅ Run `setup_test_data.py` to populate historical stock automatically

---

**Status:** ✅ **SOLUTION IMPLEMENTED** - Historical stock can now be populated for both M5 and synthetic datasets!
