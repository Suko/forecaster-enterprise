# Hierarchical Forecasting Strategy

**Date:** 2025-12-08  
**Status:** 📋 **Phase 3+ Planning**  
**Priority:** After SKU Classification & Covariates  
**Industry Standard:** Bottom-Up with Reconciliation

---

## The Problem

> "Should we forecast SKU001 at Store A, Store B, Store C separately, or aggregate all sales together?"

**Reality:**
- ✅ **Aggregated forecasts are more accurate** (more data, less noise)
- ✅ **But we need location-level forecasts** (inventory planning per store)
- ✅ **Must be consistent** (sum of locations = total)

---

## Industry Standard: Hierarchical Forecasting

### The Hierarchy

```
                    Total Company
                         │
        ┌────────────────┼────────────────┐
        │                │                │
    Country A        Country B        Country C
        │                │                │
    ┌────┴────┐      ┌────┴────┐      ┌────┴────┐
    │         │      │         │      │         │
  Region 1  Region 2 Region 3  Region 4 Region 5  Region 6
    │         │      │         │      │         │
  ┌─┴─┐     ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐   ┌─┴─┐
  S1  S2    S3  S4   S5  S6   S7  S8   S9  S10  S11  S12
  │   │     │   │    │   │    │   │    │   │    │   │
  └───┴─────┴───┴────┴───┴────┴───┴────┴───┴────┴───┘
         SKU001 at each location (bottom level)
```

### Three Approaches

| Approach | How It Works | Pros | Cons | Industry Use |
|----------|--------------|------|------|--------------|
| **Bottom-Up** | Forecast each SKU-location, sum up | Simple, location-specific | Less accurate (noisy data) | ❌ Rarely used alone |
| **Top-Down** | Forecast total, split by % | Very accurate (more data) | Assumes stable proportions | ❌ Rarely used alone |
| **Middle-Out** | Forecast at middle level, reconcile | Balanced | Complex | ⚠️ Sometimes used |
| **Bottom-Up + Reconciliation** | Forecast bottom, reconcile to top | ✅ Best of both | More complex | ✅ **Industry Standard** |

---

## Industry Standard: Bottom-Up with Reconciliation

### How It Works

```
Step 1: Forecast at Bottom Level (SKU × Location)
├── Forecast SKU001 at Store A
├── Forecast SKU001 at Store B
├── Forecast SKU001 at Store C
└── (More data = better accuracy)

Step 2: Aggregate Bottom Forecasts
├── Sum: Store A + Store B + Store C = Total SKU001
└── (This is the "base forecast")

Step 3: Forecast at Top Level (Aggregated)
├── Forecast SKU001 total (all stores combined)
└── (More accurate due to more data)

Step 4: Reconcile (Make Consistent)
├── Compare: Bottom-up sum vs Top-down forecast
├── Adjust bottom forecasts proportionally
└── Ensure: Sum of locations = Total
```

### Reconciliation Methods

| Method | Formula | When to Use |
|--------|---------|-------------|
| **Proportional** | `adj_loc = base_loc × (top_forecast / sum_base)` | Most common |
| **MinT (Minimum Trace)** | Statistical optimization | Best accuracy |
| **OLS (Ordinary Least Squares)** | Linear regression | Fast, good |
| **WLS (Weighted Least Squares)** | Weighted by volume | High-value SKUs |

**Industry Standard:** **Proportional Reconciliation** (80% of systems)

---

## Our Data Structure

### Current Schema

```sql
-- Bottom level: SKU × Location × Date
ts_demand_daily (
    client_id,
    item_id,        -- SKU
    location_id,    -- Store/Warehouse
    date_local,
    units_sold      -- Target variable
)

-- Location hierarchy (if exists)
locations (
    location_id,
    parent_location_id,  -- For hierarchy
    country,
    region,
    store_type
)
```

### Aggregation Levels

| Level | Grain | Example |
|-------|-------|---------|
| **Bottom** | `(item_id, location_id, date)` | SKU001 at Store A |
| **Location Total** | `(item_id, date)` aggregated by location | SKU001 at Store A+B+C |
| **Item Total** | `(item_id, date)` all locations | SKU001 total |
| **Category Total** | `(category, date)` all items | All SKUs in category |
| **Client Total** | `(date)` all items | Total sales |

---

## Implementation Strategy

### Phase 1: Simple Aggregation (Current)

**What we do now:**
- Forecast at `(item_id, location_id)` level
- No aggregation, no reconciliation
- Works for single-location clients

**Limitation:**
- If client has 10 stores, we forecast 10 times
- No benefit from aggregated data

### Phase 2A: Aggregated Forecasting (Recommended)

**Strategy:**
1. **Detect hierarchy** (multiple locations per SKU?)
2. **Forecast at both levels:**
   - Bottom: `(item_id, location_id)` - for location-specific needs
   - Top: `(item_id)` aggregated - for accuracy
3. **Reconcile** (if needed)

**Decision Logic:**

```python
def should_aggregate(item_id: str, client_id: str) -> bool:
    """
    Decide: Forecast separately or aggregate?
    """
    locations = get_locations_for_sku(item_id, client_id)
    
    # Rule 1: Single location → No aggregation needed
    if len(locations) == 1:
        return False
    
    # Rule 2: Low volume per location → Aggregate
    avg_volume_per_location = get_avg_volume(item_id, locations)
    if avg_volume_per_location < 10:  # Low volume
        return True
    
    # Rule 3: High correlation between locations → Aggregate
    correlation = calculate_location_correlation(item_id, locations)
    if correlation > 0.7:  # High correlation
        return True
    
    # Rule 4: Different countries → Forecast separately
    countries = get_countries(locations)
    if len(countries) > 1:
        return False  # Different markets
    
    # Default: Aggregate for accuracy
    return True
```

### Phase 2B: Full Hierarchical Reconciliation

**Advanced:** Implement MinT or OLS reconciliation for maximum accuracy.

---

## Aggregation Rules by Scenario

### Scenario 1: Multiple Stores, Same Country

```
SKU001 sold at:
- Store A (USA): 50 units/day
- Store B (USA): 30 units/day
- Store C (USA): 20 units/day

Strategy: ✅ AGGREGATE
├── Forecast: SKU001 total (100 units/day)
├── Split proportionally: A=50%, B=30%, C=20%
└── Result: More accurate than separate forecasts
```

### Scenario 2: Multiple Countries

```
SKU001 sold at:
- Store A (USA): 50 units/day
- Store B (UK): 30 units/day
- Store C (DE): 20 units/day

Strategy: ⚠️ MIXED
├── Aggregate by country: USA total, UK total, DE total
├── Forecast each country separately (different markets)
└── Then reconcile within country
```

### Scenario 3: High-Value vs Low-Value Locations

```
SKU001 sold at:
- Store A (Flagship): 200 units/day
- Store B (Outlet): 10 units/day
- Store C (Outlet): 5 units/day

Strategy: ✅ WEIGHTED AGGREGATION
├── Forecast: SKU001 total
├── Weight by historical volume
└── Adjust low-volume stores proportionally
```

### Scenario 4: Intermittent Demand

```
SKU001 sold at:
- Store A: Regular demand (daily)
- Store B: Intermittent (weekly)
- Store C: Lumpy (monthly)

Strategy: ⚠️ SEPARATE FORECASTING
├── Store A: Use Chronos-2 (regular)
├── Store B: Use Croston (intermittent)
├── Store C: Use Min/Max rules (lumpy)
└── Then aggregate results
```

---

## Database Design for Hierarchical Forecasting

### Option 1: Forecast at Multiple Levels (Recommended)

```sql
-- Forecast results table (extend current)
forecast_results (
    forecast_run_id,
    item_id,
    location_id,        -- NULL for aggregated forecasts
    aggregation_level,  -- 'location', 'item', 'category', 'client'
    date,
    point_forecast,
    method
)

-- Example rows:
-- SKU001 at Store A (bottom level)
item_id='SKU001', location_id='store_a', aggregation_level='location'

-- SKU001 total (aggregated)
item_id='SKU001', location_id=NULL, aggregation_level='item'

-- Reconciliation metadata
forecast_reconciliation (
    forecast_run_id,
    item_id,
    reconciliation_method,  -- 'proportional', 'mint', 'ols'
    bottom_sum,
    top_forecast,
    adjustment_factor,
    reconciled_forecasts JSONB  -- Adjusted location forecasts
)
```

### Option 2: Location Hierarchy Table

```sql
-- If locations have hierarchy
location_hierarchy (
    location_id,
    parent_location_id,  -- NULL for top level
    level,                -- 'store', 'region', 'country', 'global'
    country_code,
    region_code
)

-- Example:
-- Store A → Region West → Country USA → Global
```

---

## API Design

### Forecast Request

```json
{
  "item_ids": ["SKU001"],
  "location_ids": ["store_a", "store_b", "store_c"],  // Optional
  "aggregation_strategy": "auto",  // 'auto', 'aggregate', 'separate'
  "reconciliation_method": "proportional",  // 'proportional', 'mint', 'none'
  "prediction_length": 30
}
```

### Forecast Response

```json
{
  "forecast_run_id": "abc123",
  "item_id": "SKU001",
  "aggregation_applied": true,
  "locations_forecasted": ["store_a", "store_b", "store_c"],
  
  "forecasts": {
    "aggregated": {
      "location_id": null,
      "point_forecast": 100,
      "method": "chronos2"
    },
    "locations": [
      {
        "location_id": "store_a",
        "point_forecast": 50,  // Reconciled from aggregated
        "original_forecast": 48,  // Before reconciliation
        "adjustment_factor": 1.04
      },
      {
        "location_id": "store_b",
        "point_forecast": 30,
        "original_forecast": 29,
        "adjustment_factor": 1.03
      },
      {
        "location_id": "store_c",
        "point_forecast": 20,
        "original_forecast": 19,
        "adjustment_factor": 1.05
      }
    ]
  },
  
  "reconciliation": {
    "method": "proportional",
    "top_forecast": 100,
    "bottom_sum": 96,
    "adjustment_factor": 1.042
  }
}
```

---

## Implementation Phases

> **Note:** This is Phase 3+ (after SKU Classification and Covariates).  
> See `PHASE_2_KICKOFF.md` for current priorities.

### Phase 3A: Basic Aggregation (4 weeks)

**Week 1-2: Detection & Routing**
- [ ] Detect multi-location SKUs
- [ ] Decision logic: aggregate vs separate
- [ ] Location correlation analysis

**Week 3: Aggregated Forecasting**
- [ ] Aggregate data: `(item_id, date)` across locations
- [ ] Forecast at aggregated level
- [ ] Store both aggregated and location-level forecasts

**Week 4: Simple Reconciliation**
- [ ] Proportional reconciliation
- [ ] Ensure consistency: sum = total
- [ ] API response with both levels

### Phase 3B: Advanced Reconciliation (2 weeks)

- [ ] MinT reconciliation (statistical)
- [ ] OLS reconciliation
- [ ] Weighted reconciliation by volume

### Phase 3C: Full Hierarchy (Future)

- [ ] Country/Region hierarchy
- [ ] Multi-level reconciliation
- [ ] Category-level aggregation

---

## Industry References

### Academic
- **Hyndman & Athanasopoulos** (2018) - "Forecasting: Principles and Practice"
  - Chapter 10: Hierarchical Forecasting
  - MinT reconciliation method

- **Wickramasuriya et al.** (2019)
  - "Optimal Forecast Reconciliation for Hierarchical and Grouped Time Series"
  - MinT (Minimum Trace) method

### Enterprise Systems
- **SAP IBP**: Bottom-up with MinT reconciliation
- **Oracle Demand Planning**: Bottom-up with proportional reconciliation
- **Blue Yonder**: Bottom-up with OLS reconciliation
- **o9 Solutions**: Multi-level reconciliation

---

## Decision Matrix

| Scenario | Strategy | Reconciliation |
|----------|----------|----------------|
| Single location | Separate | None |
| Multiple locations, same country | Aggregate | Proportional |
| Multiple countries | Aggregate by country | Proportional within country |
| High correlation (>0.7) | Aggregate | Proportional |
| Low correlation (<0.3) | Separate | None |
| Intermittent demand | Separate | None |
| High volume per location (>50/day) | Separate or Aggregate | Optional |
| Low volume per location (<10/day) | Aggregate | Proportional |

---

## Key Takeaways

1. ✅ **Aggregate when possible** - More data = better accuracy
2. ✅ **Reconcile for consistency** - Sum of parts = whole
3. ✅ **Separate when markets differ** - Different countries/regions
4. ✅ **Start simple** - Proportional reconciliation (80% of value)
5. ✅ **Scale up** - MinT/OLS for advanced needs

---

## Next Steps

1. **Analyze current data:**
   - How many SKUs have multiple locations?
   - What's the correlation between locations?
   - Volume distribution per location?

2. **Design database schema:**
   - Extend `forecast_results` for aggregation levels
   - Add `forecast_reconciliation` table

3. **Implement Phase 2A:**
   - Detection logic
   - Aggregated forecasting
   - Simple reconciliation

---

*Planning document - No code yet*

