# Stock Data Quick Reference

**High-level guide:** What stock means in different tables

---

## TL;DR

| Table | Stock Field | What It Means |
|-------|-------------|---------------|
| `stock_levels` | `current_stock` | **Where stock is** (per location) |
| `ts_demand_daily` | `stock_on_date` | **Total stock available** (aggregated, per date) |

---

## The Two Stock Tables

### 1. `stock_levels` - Current Stock Per Location

**Purpose:** Track where inventory is physically located

**Structure:**
```
item_id: M5_HOBBIES_1_008_CA_1_evaluation
├── location_id: WH-001 → current_stock: 200 units
├── location_id: WH-002 → current_stock: 100 units
└── location_id: STORE-001 → current_stock: 50 units
```

**Use Case:**
- "How much stock do we have at Warehouse 1?"
- "Which location has the most inventory?"
- Current inventory management

**Key Point:** ✅ Has `location_id` - each location tracked separately

---

### 2. `ts_demand_daily` - Historical Stock (Aggregated)

**Purpose:** Track total stock available over time for analysis

**Structure:**
```
item_id: M5_HOBBIES_1_008_CA_1_evaluation
date_local: 2025-01-27
├── units_sold: 15 (total across all locations)
└── stock_on_date: 350 (SUM of all locations: 200+100+50)
```

**Use Case:**
- "What was our total stock 30 days ago?"
- "Did we have a stockout last month?"
- Historical trend analysis
- DIR calculations

**Key Point:** ❌ No `location_id` - aggregated at SKU level

---

## Why Two Tables?

### Different Granularities

**`stock_levels`:**
- ✅ Location-level detail
- ✅ Current snapshot only
- ✅ "Where is the stock?"

**`ts_demand_daily.stock_on_date`:**
- ✅ SKU-level aggregation
- ✅ Historical time series
- ✅ "How much total stock did we have?"

### Matches Sales Data

Sales data (`units_sold` in `ts_demand_daily`) is also aggregated at SKU level (no `location_id`), so stock data matches the same granularity for consistent analysis.

---

## How They Relate

```
┌─────────────────────────────────────┐
│  stock_levels (Current)             │
│  ───────────────────────             │
│  SKU + Location → Stock             │
│  M5_001 @ WH-001 → 200              │
│  M5_001 @ WH-002 → 100              │
│  M5_001 @ STORE-001 → 50            │
└─────────────────────────────────────┘
              │
              │ SUM across locations
              ▼
┌─────────────────────────────────────┐
│  ts_demand_daily (Historical)       │
│  ────────────────────────────        │
│  SKU + Date → Total Stock           │
│  M5_001 on 2025-01-27 → 350         │
│  (200 + 100 + 50)                   │
└─────────────────────────────────────┘
```

---

## Common Questions

### Q: Why not track stock per location in `ts_demand_daily`?

**A:** Sales data is aggregated at SKU level (no `location_id`), so stock matches the same granularity for consistent analysis and forecasting.

### Q: Can I see location-level stock history?

**A:** Not currently. `ts_demand_daily` is aggregated. For location-level history, you'd need a separate `ts_demand_daily_location` table (future enhancement).

### Q: How is `stock_on_date` calculated?

**A:** 
1. Get current stock from `stock_levels` (sum across locations)
2. Work backwards through dates
3. For each date: `stock_yesterday = stock_today + sales_today - restocking`
4. Store in `stock_on_date`

See: `backend/scripts/populate_historical_stock.py`

---

## Summary

| Aspect | `stock_levels` | `ts_demand_daily.stock_on_date` |
|--------|---------------|--------------------------------|
| **Granularity** | Per location | Per SKU (aggregated) |
| **Time** | Current only | Historical (per date) |
| **Location ID** | ✅ Yes | ❌ No |
| **Formula** | Direct value | SUM across locations |
| **Use For** | Inventory management | Trend analysis, DIR |

**Remember:**
- ✅ Each location has its own stock in `stock_levels`
- ✅ `stock_on_date` = total stock across all locations
- ✅ This matches how `units_sold` is also aggregated

---

**Related Docs:**
- [STOCK_AGGREGATION.md](./STOCK_AGGREGATION.md) - Detailed technical explanation
- [DATA_MODEL.md](./DATA_MODEL.md) - Complete data model
- [INVENTORY_DATA_STATUS.md](./INVENTORY_DATA_STATUS.md) - What data exists
