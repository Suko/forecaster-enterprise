# Stock Aggregation: Locations vs Time Series

**Question:** How does stock aggregation work between `stock_levels` (per location) and `ts_demand_daily` (aggregated)?

---

## Data Structure

### `stock_levels` Table (Per Location)
```sql
CREATE TABLE stock_levels (
    item_id VARCHAR(255),
    location_id VARCHAR(50),  -- ✅ Has location
    current_stock INTEGER,    -- Stock at THIS location
    ...
    UNIQUE (client_id, item_id, location_id)
);
```

**Example:**
```
SKU: M5_HOBBIES_1_008_CA_1_evaluation
├── Location: WH-001 → 200 units
├── Location: WH-002 → 100 units
└── Location: STORE-001 → 50 units
Total: 350 units
```

### `ts_demand_daily` Table (Aggregated at SKU Level)
```sql
CREATE TABLE ts_demand_daily (
    item_id VARCHAR(255),
    date_local DATE,
    units_sold NUMERIC,       -- Sales aggregated across all locations
    stock_on_date INTEGER,    -- Stock aggregated across all locations
    ...
    -- ❌ NO location_id column
    PRIMARY KEY (item_id, date_local, client_id)
);
```

**Example:**
```
SKU: M5_HOBBIES_1_008_CA_1_evaluation
Date: 2025-01-27
├── units_sold: 15 (total across all locations)
└── stock_on_date: 350 (SUM of all locations)
```

---

## Aggregation Logic

### Current Stock → Historical Stock

**Step 1: Get Total Current Stock**
```sql
SELECT SUM(current_stock) as total_stock
FROM stock_levels
WHERE client_id = '...' AND item_id = 'M5_HOBBIES_1_008_CA_1_evaluation';
-- Result: 350 (200 + 100 + 50)
```

**Step 2: Calculate Historical Stock (Backwards)**
```
For each date (working backwards from today):
  stock_on_date = stock_next_day + units_sold_today - restocking_today
```

**Step 3: Update `stock_on_date`**
```sql
UPDATE ts_demand_daily
SET stock_on_date = 350  -- Aggregated total
WHERE item_id = 'M5_HOBBIES_1_008_CA_1_evaluation'
  AND date_local = '2025-01-27';
```

---

## Why This Design?

### ✅ Benefits:
1. **Simplified Time Series:** One row per SKU per date (not per location)
2. **Easier Analysis:** Can query stock trends without location complexity
3. **Matches Sales Data:** `units_sold` is also aggregated (no location_id)
4. **Forecasting:** Forecasting engine works at SKU level, not location level

### ⚠️ Limitations:
1. **No Location-Level History:** Can't see which location had stockouts
2. **Aggregation Loss:** Can't track stock movement between locations

### 💡 Future Enhancement:
If needed, could add `ts_demand_daily_location` table:
```sql
CREATE TABLE ts_demand_daily_location (
    item_id VARCHAR(255),
    location_id VARCHAR(50),  -- ✅ Per location
    date_local DATE,
    units_sold NUMERIC,
    stock_on_date INTEGER,
    ...
);
```

---

## Implementation

### Current Implementation ✅

**File:** `backend/scripts/populate_historical_stock.py`

```python
# Get current stock (SUM across all locations)
stock_result = await session.execute(
    text("""
        SELECT COALESCE(SUM(current_stock), 0) as total_stock
        FROM stock_levels
        WHERE client_id = :client_id
          AND item_id = :item_id
    """),
    {"client_id": client_id, "item_id": item_id}
)
current_stock = int(stock_result.scalar() or 0)

# Calculate backwards and update stock_on_date
# (one value per SKU per date, aggregated across locations)
```

### Metrics Service ✅

**File:** `backend/services/metrics_service.py`

```python
# Get stock levels (all locations)
stock_levels = stock_result.scalars().all()

# Sum across all locations
total_stock = sum(sl.current_stock for sl in stock_levels)

# Use total_stock for DIR calculation
```

---

## Query Examples

### Get Total Stock Per SKU (Current)
```sql
SELECT 
    item_id,
    SUM(current_stock) as total_stock,
    COUNT(DISTINCT location_id) as num_locations
FROM stock_levels
WHERE client_id = '<uuid>'
GROUP BY item_id;
```

### Get Historical Stock (Aggregated)
```sql
SELECT 
    item_id,
    date_local,
    units_sold,
    stock_on_date  -- Already aggregated across locations
FROM ts_demand_daily
WHERE client_id = '<uuid>'
  AND item_id = 'M5_HOBBIES_1_008_CA_1_evaluation'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date_local DESC;
```

### Compare Current vs Historical
```sql
-- Current stock (from stock_levels)
SELECT 
    s.item_id,
    SUM(s.current_stock) as current_total
FROM stock_levels s
WHERE s.client_id = '<uuid>'
GROUP BY s.item_id

UNION ALL

-- Historical stock (from ts_demand_daily, most recent)
SELECT 
    t.item_id,
    t.stock_on_date as current_total
FROM ts_demand_daily t
WHERE t.client_id = '<uuid>'
  AND t.date_local = (
      SELECT MAX(date_local)
      FROM ts_demand_daily
      WHERE client_id = t.client_id
        AND item_id = t.item_id
  );
```

---

## Summary

| Aspect | `stock_levels` | `ts_demand_daily` |
|--------|---------------|-------------------|
| **Granularity** | Per location | Per SKU (aggregated) |
| **Location ID** | ✅ Yes | ❌ No |
| **Stock Field** | `current_stock` | `stock_on_date` |
| **Aggregation** | N/A (per location) | SUM across locations |
| **Use Case** | Current inventory | Historical trends |

**Key Point:** 
- ✅ Each location has its own stock in `stock_levels`
- ✅ `ts_demand_daily.stock_on_date` = SUM of stock across ALL locations
- ✅ This matches the aggregated nature of `units_sold` (also no location_id)

---

**Status:** ✅ **CORRECTLY IMPLEMENTED** - Stock is properly aggregated across locations for historical tracking!
