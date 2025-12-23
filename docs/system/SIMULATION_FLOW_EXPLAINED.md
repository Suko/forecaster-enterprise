# Simulation Flow - Detailed Explanation

**How the simulation system works, step by step**

---

## Overview

The simulation runs the **exact same production logic** day-by-day over a historical period, automatically following system recommendations, and compares outcomes against reality.

---

## Data Sources

### 1. **Initial Stock Levels** (`stock_levels` table)
```sql
SELECT item_id, SUM(current_stock) 
FROM stock_levels 
WHERE client_id = X AND item_id IN (...)
GROUP BY item_id
```
- **Source**: `backend/services/simulation_service.py::_get_stock_snapshot()`
- **What it gets**: Starting inventory for each item at `start_date`
- **Note**: Currently uses current stock levels (TODO: historical stock tracking)

### 2. **Historical Sales Data** (`ts_demand_daily` table)
```sql
SELECT units_sold 
FROM ts_demand_daily 
WHERE client_id = X 
  AND item_id = Y 
  AND date_local = '2024-11-01'
```
- **Source**: `backend/services/simulation_service.py::_get_actual_sales()`
- **What it gets**: Actual units sold for each item on each day
- **Used for**: 
  - Reducing stock: `stock = stock - actual_sales`
  - Training forecasts: Data up to `current_date`

### 3. **Product Data** (`products` table)
```sql
SELECT item_id, unit_cost, safety_buffer_days 
FROM products 
WHERE client_id = X AND item_id IN (...)
```
- **Source**: `backend/services/simulation_service.py::_get_products()`
- **What it gets**: Unit cost, safety stock days, product metadata
- **Used for**: Inventory calculations, cost tracking

### 4. **Lead Times** (`product_supplier_conditions` table)
```sql
SELECT lead_time_days 
FROM product_supplier_conditions 
WHERE client_id = X AND item_id = Y AND is_primary = true
```
- **Source**: `backend/services/simulation_service.py::_get_lead_time()`
- **What it gets**: Lead time in days for ordering
- **Fallback**: 7 days if not found
- **Used for**: Calculating when orders arrive

---

## Day-by-Day Simulation Flow

### For Each Day (from `start_date` to `end_date`):

```
┌─────────────────────────────────────────────────────────────┐
│ DAY N (e.g., 2024-11-15)                                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ STEP 1: Process Order Arrivals                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ FOR each order placed earlier:                       │   │
│ │   IF order.arrival_date == current_date:             │   │
│ │     simulated_stock[item_id] += order.quantity       │   │
│ │     mark order as received                           │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ STEP 2: For Each Item                                       │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 2a. Get Actual Sales (Historical Data)              │   │
│ │   actual_sales = ts_demand_daily WHERE              │   │
│ │     client_id = X AND item_id = Y AND              │   │
│ │     date_local = current_date                       │   │
│ │                                                      │   │
│ │ 2b. Check Reorder Point (BEFORE subtracting sales) │   │
│ │   stock_before_sales = simulated_stock[item_id]    │   │
│ │                                                      │   │
│ │ 2c. Subtract Sales                                  │   │
│ │   simulated_stock[item_id] -= actual_sales         │   │
│ │   real_stock[item_id] -= actual_sales              │   │
│ │                                                      │   │
│ │ 2d. Generate Forecast (Weekly, Cached)             │   │
│ │   IF day % 7 == 0:                                  │   │
│ │     forecast = ForecastService.generate_forecast(  │   │
│ │       training_end_date = current_date,            │   │
│ │       item_ids = [item_id]                         │   │
│ │     )                                               │   │
│ │     cache[item_id, current_date] = forecast         │   │
│ │   ELSE:                                             │   │
│ │     forecast = cache[most_recent]                   │   │
│ │                                                      │   │
│ │ 2e. If Forecast = 0, Use Historical Average       │   │
│ │   IF forecast == 0:                                 │   │
│ │     historical_avg = AVG(units_sold) FROM          │   │
│ │       ts_demand_daily WHERE date_local >=           │   │
│ │       current_date - 30 days                        │   │
│ │     forecast = historical_avg * 30                  │   │
│ │                                                      │   │
│ │ 2f. Calculate Inventory Metrics                    │   │
│ │   avg_daily_demand = forecast / 30                 │   │
│ │   safety_stock = InventoryCalculator.              │   │
│ │     calculate_safety_stock(                        │   │
│ │       avg_daily_demand,                            │   │
│ │       lead_time_days,                              │   │
│ │       safety_stock_days,                           │   │
│ │       service_level                                │   │
│ │     )                                               │   │
│ │   reorder_point = InventoryCalculator.            │   │
│ │     calculate_reorder_point(                       │   │
│ │       avg_daily_demand,                            │   │
│ │       lead_time_days,                              │   │
│ │       safety_stock                                 │   │
│ │     )                                               │   │
│ │                                                      │   │
│ │ 2g. Check if Order Needed                          │   │
│ │   orders_in_transit = orders WHERE                 │   │
│ │     item_id = Y AND not received AND               │   │
│ │     arrival_date > current_date                    │   │
│ │                                                      │   │
│ │   IF stock_before_sales <= reorder_point AND       │   │
│ │      len(orders_in_transit) == 0:                  │   │
│ │     recommended_qty = InventoryCalculator.        │   │
│ │       calculate_recommended_order_quantity(        │   │
│ │         forecast_demand,                            │   │
│ │         safety_stock,                               │   │
│ │         current_stock                              │   │
│ │       )                                             │   │
│ │     order = OrderSimulator.place_order(            │   │
│ │       item_id, quantity, current_date,             │   │
│ │       lead_time_days                                │   │
│ │     )                                               │   │
│ │     order.arrival_date = current_date +            │   │
│ │       lead_time_days                                │   │
│ │                                                      │   │
│ │ 2h. Record Daily Comparison                        │   │
│ │   ComparisonEngine.record_daily_comparison(       │   │
│ │     date = current_date,                            │   │
│ │     item_id = Y,                                    │   │
│ │     simulated_stock = simulated_stock[Y],          │   │
│ │     real_stock = real_stock[Y],                     │   │
│ │     unit_cost = product.unit_cost,                  │   │
│ │     order_placed = (order != None),                │   │
│ │     order_quantity = order.quantity                │   │
│ │   )                                                 │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                              │
│ STEP 3: Move to Next Day                                    │
│   current_date += 1 day                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Components & What They Do

### 1. **ForecastService.generate_forecast()**
**Location**: `backend/forecasting/services/forecast_service.py`

**What it does**:
1. Fetches historical data from `ts_demand_daily` up to `training_end_date`
2. Classifies SKU (ABC-XYZ analysis)
3. Selects forecasting method (Chronos-2, SBA, etc.)
4. Generates forecast for next 30 days
5. Returns `ForecastRun` with results

**Data flow**:
```
ts_demand_daily (WHERE date_local <= training_end_date)
    ↓
DataAccess.fetch_historical_data()
    ↓
SKUClassifier.classify() → Select method
    ↓
Model.predict() → Generate forecast
    ↓
ForecastRun + ForecastResult (stored in memory if skip_persistence=True)
```

**Called by**: `SimulationService._get_forecasted_demand()`

---

### 2. **InventoryCalculator**
**Location**: `backend/forecasting/applications/inventory/calculator.py`

**Methods used**:

#### `calculate_safety_stock()`
```python
safety_stock = avg_daily_demand × safety_stock_days × (1 + z × 0.2)
# Where z = Z-score for service level (95% = 1.65)
```

#### `calculate_reorder_point()`
```python
reorder_point = (avg_daily_demand × lead_time_days) + safety_stock
```

#### `calculate_recommended_order_quantity()`
```python
recommended_qty = forecasted_demand + safety_stock - current_stock
# If recommended_qty < MOQ, use MOQ
```

**Called by**: `SimulationService.run_simulation()` (step 2f)

---

### 3. **OrderSimulator**
**Location**: `backend/services/simulation/order_simulator.py`

**What it does**:
- Tracks orders placed during simulation
- Calculates arrival dates: `arrival_date = order_date + lead_time_days`
- Returns orders arriving on a specific date
- Prevents duplicate orders (checks `orders_in_transit`)

**Key methods**:
- `place_order()`: Creates `SimulatedOrder` with arrival date
- `get_orders_arriving(date)`: Returns orders arriving today
- `mark_order_received()`: Marks order as received

**Called by**: `SimulationService.run_simulation()` (steps 1, 2g)

---

### 4. **ComparisonEngine**
**Location**: `backend/services/simulation/comparison_engine.py`

**What it does**:
- Records daily comparisons: simulated stock vs real stock
- Tracks stockouts, inventory value, service level
- Calculates aggregate metrics at end

**Key methods**:
- `record_daily_comparison()`: Records one day's data
- `calculate_stockout_rate()`: % of days with stockout
- `calculate_inventory_value()`: Average inventory value
- `calculate_service_level()`: % of days in stock

**Called by**: `SimulationService.run_simulation()` (step 2h, final metrics)

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    INITIALIZATION                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ 1. Get Initial Stock (stock_levels table)                  │
│    simulated_stock = {item_id: quantity}                     │
│    real_stock = {item_id: quantity}  (same starting point)  │
│                                                              │
│ 2. Get Products (products table)                             │
│    products = {item_id: Product(unit_cost, safety_days)}     │
│                                                              │
│ 3. Initialize OrderSimulator (empty)                        │
│    orders = []                                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              DAY-BY-DAY LOOP (365 iterations)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  FOR each day from start_date to end_date:                  │
│                                                              │
│    ┌────────────────────────────────────────────────────┐  │
│    │ A. Process Arrivals                                │  │
│    │    orders_arriving = OrderSimulator.get_orders()   │  │
│    │    FOR order in orders_arriving:                    │  │
│    │      simulated_stock[order.item_id] += order.qty    │  │
│    └────────────────────────────────────────────────────┘  │
│                                                              │
│    ┌────────────────────────────────────────────────────┐  │
│    │ B. For Each Item                                   │  │
│    │                                                     │  │
│    │  1. Get Actual Sales                               │  │
│    │     actual_sales = ts_demand_daily WHERE           │  │
│    │       date_local = current_date                    │  │
│    │                                                     │  │
│    │  2. Check Reorder Point (before sales)            │  │
│    │     stock_before = simulated_stock[item_id]       │  │
│    │                                                     │  │
│    │  3. Subtract Sales                                 │  │
│    │     simulated_stock -= actual_sales               │  │
│    │     real_stock -= actual_sales                     │  │
│    │                                                     │  │
│    │  4. Generate Forecast (weekly)                     │  │
│    │     IF day % 7 == 0:                               │  │
│    │       forecast = ForecastService.generate_forecast(│  │
│    │         training_end_date = current_date           │  │
│    │       )                                            │  │
│    │       Uses: ts_demand_daily WHERE date <= current  │  │
│    │     ELSE:                                          │  │
│    │       forecast = cache[most_recent]                │  │
│    │                                                     │  │
│    │  5. Calculate Inventory Metrics                   │  │
│    │     avg_daily = forecast / 30                      │  │
│    │     safety_stock = f(avg_daily, lead_time, ...)  │  │
│    │     reorder_point = f(avg_daily, lead_time, ...)  │  │
│    │                                                     │  │
│    │  6. Place Order (if needed)                       │  │
│    │     IF stock_before <= reorder_point AND          │  │
│    │        no_orders_in_transit:                       │  │
│    │       qty = calculate_recommended_order_quantity()│  │
│    │       order = OrderSimulator.place_order()        │  │
│    │       order.arrival_date = current_date + lead    │  │
│    │                                                     │  │
│    │  7. Record Comparison                             │  │
│    │     ComparisonEngine.record_daily_comparison(     │  │
│    │       simulated_stock, real_stock, ...            │  │
│    │     )                                              │  │
│    └────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL METRICS                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ ComparisonEngine calculates:                                 │
│   - Stockout rate (simulated vs real)                       │
│   - Inventory value (simulated vs real)                     │
│   - Service level (simulated vs real)                       │
│   - Total cost (simulated vs real)                          │
│                                                              │
│ Calculate improvements:                                      │
│   - Stockout reduction %                                     │
│   - Inventory reduction %                                    │
│   - Cost savings $                                           │
│   - Service level improvement %                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Database Queries Used

### 1. **Get Initial Stock**
```sql
SELECT item_id, SUM(current_stock) as total_stock
FROM stock_levels
WHERE client_id = :client_id
  AND item_id IN (:item_ids)
GROUP BY item_id
```

### 2. **Get Daily Sales** (called 365 × N items times)
```sql
SELECT COALESCE(SUM(units_sold), 0) as total_sales
FROM ts_demand_daily
WHERE client_id = :client_id
  AND item_id = :item_id
  AND date_local = :sale_date
```

### 3. **Get Historical Average** (fallback when forecast = 0)
```sql
SELECT AVG(daily_total) as avg_demand
FROM (
    SELECT date_local, SUM(units_sold) as daily_total
    FROM ts_demand_daily
    WHERE client_id = :client_id
      AND item_id = :item_id
      AND date_local >= :start_date
      AND date_local < :end_date
    GROUP BY date_local
) daily_totals
```

### 4. **Forecast Generation** (via ForecastService)
```sql
-- ForecastService uses DataAccess which queries:
SELECT item_id as id, date_local as timestamp, units_sold as target,
       promotion_flag, holiday_flag, is_weekend, marketing_spend
FROM ts_demand_daily
WHERE client_id = :client_id
  AND item_id IN (:item_ids)
  AND date_local >= :start_date
  AND date_local <= :end_date  -- training_end_date
ORDER BY item_id, date_local
```

### 5. **Get Lead Time**
```sql
SELECT lead_time_days
FROM product_supplier_conditions
WHERE client_id = :client_id
  AND item_id = :item_id
  AND is_primary = true
LIMIT 1
```

---

## Key Calculations

### Reorder Point Formula
```
reorder_point = (avg_daily_demand × lead_time_days) + safety_stock
```

Where:
- `avg_daily_demand = forecast_demand / 30`
- `safety_stock = avg_daily_demand × safety_stock_days × (1 + z × 0.2)`
- `z = 1.65` for 95% service level

### Recommended Order Quantity
```
recommended_qty = forecasted_demand + safety_stock - current_stock
```

### Stock Update
```
simulated_stock = max(0, simulated_stock - actual_sales + order_arrivals)
```

---

## Optimization: Weekly Forecast Caching

**Problem**: Generating forecast every day = 365 forecasts × N items = very slow

**Solution**: Generate forecast weekly, cache for 7 days

```
Day 0:   Generate forecast → Cache
Day 1-6: Use cached forecast
Day 7:   Generate new forecast → Update cache
Day 8-13: Use cached forecast
Day 14:  Generate new forecast → Update cache
...
```

**Result**: 365 days = ~52 forecasts instead of 365 (7x faster)

---

## What Gets Compared

### Daily Comparison (recorded every day for every item)
- `simulated_stock`: Stock level if we followed system recommendations
- `real_stock`: Actual stock level (what really happened)
- `simulated_stockout`: Did simulated stock go to 0?
- `real_stockout`: Did real stock go to 0?
- `order_placed`: Did system recommend an order?
- `order_quantity`: How much was ordered?

### Final Metrics (aggregated)
- **Stockout Rate**: % of days with stockout
- **Inventory Value**: Average inventory value over period
- **Service Level**: % of days in stock
- **Total Cost**: Inventory carrying cost

### Improvements (simulated vs real)
- **Stockout Reduction**: (real - simulated) / real × 100%
- **Inventory Reduction**: (real - simulated) / real × 100%
- **Cost Savings**: real_cost - simulated_cost
- **Service Level Improvement**: simulated - real

---

## Summary

**The simulation:**
1. ✅ Uses real historical sales data (`ts_demand_daily`)
2. ✅ Generates forecasts using existing `ForecastService` (with `training_end_date`)
3. ✅ Calculates inventory recommendations using `InventoryCalculator`
4. ✅ Automatically places orders when reorder point is hit
5. ✅ Tracks order arrivals (lead time simulation)
6. ✅ Compares simulated outcomes vs real outcomes
7. ✅ Calculates improvement metrics

**It's running the exact same production logic, just in the past!**


