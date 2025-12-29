# Simulation System

**Status:** ✅ Core functionality complete and validated
**Last Updated:** 2025-12-29
**Purpose:** Validate system effectiveness by simulating real-world operation over historical periods

---

## Executive Summary

The simulation system runs the **exact same production logic** with historical data filtered by date, automatically following system recommendations, and comparing outcomes against reality. This validates that the system would have made better decisions if it had been running in the past.

**Goal:** Answer the question: *"If we had run this system 12 months ago, would it have minimized stockouts and reduced inventory value?"*

---

## System Architecture

### Production System (Real-Time)

```
┌─────────────────┐
│  ETL Service    │  Pulls sales data from external source
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ ts_demand_daily │  Historical sales data (up to today)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Forecast Service│  Generates forecast (30 days ahead)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Inventory Calc  │  Calculates reorder points, safety stock
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Recommendations │  "Order 100 units of Item X"
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  User Decision   │  User places order (or not)
└─────────────────┘
```

### Simulation System (Time Travel)

```
┌─────────────────────────────────────────────────────────────┐
│                    SIMULATION ORCHESTRATOR                    │
│  Start Date: 12 months ago  |  End Date: Today              │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Day-by-day loop
                            ▼
        ┌───────────────────────────────────────┐
        │  For each day from start to end:     │
        │  1. Filter data up to current day    │
        │  2. Generate forecast                │
        │  3. Calculate recommendations         │
        │  4. Auto-place orders (if triggered)  │
        │  5. Process order arrivals            │
        │  6. Update simulated stock            │
        │  7. Compare with real stock           │
        └───────────────────────────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│ Data Filter   │                      │ Order Sim     │
│ (Date Wrapper)│                      │ Engine        │
└───────┬───────┘                      └───────┬───────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│ ts_demand_daily│                      │ Order Tracking│
│ WHERE date <= │                      │ - Orders placed│
│ simulation_date│                      │ - Lead times   │
│               │                      │ - Arrivals     │
└───────────────┘                      └───────────────┘
        │                                       │
        └───────────────┬───────────────────────┘
                        ▼
              ┌─────────────────┐
              │ Comparison      │
              │ Engine          │
              │ - Simulated vs  │
              │   Real stock    │
              │ - Metrics calc  │
              └─────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Results Report  │
              │ - Stockout rate │
              │ - Inventory val │
              │ - Service level │
              │ - Cost savings  │
              └─────────────────┘
```

---

## Data Flow Architecture

### Data Sources

#### 1. Initial Stock Levels
**Source**: `_get_stock_snapshot()`
- **Primary**: `ts_demand_daily.stock_on_date` for `start_date`
- **Fallback**: `stock_levels.current_stock` (current snapshot)
- **Used for**: Both simulated and real stock initialization

#### 2. Daily Sales Data
**Source**: `_get_actual_sales()`
- **Table**: `ts_demand_daily.units_sold`
- **Query**: `SELECT SUM(units_sold) WHERE client_id, item_id, date_local = current_date`
- **Used for**:
  - Subtracting from simulated stock
  - Calculating real stock (when stock_on_date unavailable)

#### 3. Real Stock Levels (Historical)
**Source**: `_get_real_stock_for_date()`
- **Table**: `ts_demand_daily.stock_on_date`
- **Query**: `SELECT SUM(stock_on_date) WHERE client_id, item_id, date_local = current_date`
- **Behavior**:
  - Returns actual value if `stock_on_date` is populated (not NULL)
  - Returns `None` if `stock_on_date` is NULL (no data)
- **Used for**: Real stock comparison (independent value for each day)

#### 4. Product Configuration
**Source**: `_get_products()`
- **Table**: `products`
- **Fields**: `unit_cost`, `safety_buffer_days`, `item_id`
- **Used for**: Cost calculations, safety stock configuration

#### 5. Lead Time
**Source**: `_get_lead_time()`
- **Primary**: `product_supplier_conditions.lead_time_days` (where `is_primary = true`)
- **Fallback**: Default 7 days
- **Used for**: Reorder point calculation, order arrival dates

#### 6. MOQ (Minimum Order Quantity)
**Source**: `_get_moq()`
- **Primary**: `product_supplier_conditions.moq` (where `is_primary = true`)
- **Secondary**: `suppliers.default_moq`
- **Fallback**: `None` (no MOQ constraint)
- **Used for**: Order quantity calculation

#### 7. Forecasted Demand
**Source**: `_get_forecasted_demand()`
- **Service**: `ForecastService.generate_forecast()`
- **Model**: Chronos-2
- **Training Data**: `ts_demand_daily.units_sold` up to `current_date`
- **Parameters**:
  - `training_end_date = current_date` (time-travel: only use data up to this date)
  - `prediction_length = 30` days
  - `skip_persistence = True` (don't save to DB)
- **Optimization**: Generated weekly (every 7 days), cached for intermediate days
- **Fallback**: Historical average (last 30 days) if forecast = 0
- **Used for**: Safety stock, reorder point, order quantity calculations

### Day-by-Day Simulation Flow

```
1. PROCESS ORDER ARRIVALS
   ├─ Get orders arriving today (from OrderSimulator)
   ├─ Add order quantity to simulated_stock
   └─ Mark orders as received

2. FOR EACH ITEM:

   A. GET ACTUAL SALES
      └─ Query: ts_demand_daily.units_sold for current_date

   B. GET REAL STOCK
      ├─ Query: ts_demand_daily.stock_on_date for current_date
      ├─ If available: Use database value (independent)
      └─ If NULL: Calculate from previous day - sales

   C. UPDATE SIMULATED STOCK
      └─ simulated_stock = simulated_stock - actual_sales

   D. GENERATE FORECAST (if needed)
      ├─ Check: Is it day 0 or day % 7 == 0?
      ├─ If yes: Generate forecast using data up to current_date
      ├─ Cache forecast for next 7 days
      └─ If no: Use cached forecast

   E. CALCULATE INVENTORY METRICS
      ├─ avg_daily_demand = forecast_demand / 30
      ├─ safety_stock = calculate_safety_stock(...)
      ├─ reorder_point = calculate_reorder_point(...)
      └─ Get lead_time, moq from database

   F. CHECK REORDER POINT
      ├─ stock_before_sales <= reorder_point?
      ├─ No orders in transit?
      └─ If both true: Place order

   G. PLACE ORDER (if needed)
      ├─ recommended_qty = calculate_recommended_order_quantity(...)
      ├─ Apply MOQ constraint
      ├─ Create SimulatedOrder with:
      │  ├─ order_date = current_date
      │  ├─ arrival_date = current_date + lead_time
      │  └─ quantity = recommended_qty
      └─ Store in OrderSimulator

   H. RECORD DAILY COMPARISON
      ├─ simulated_stock
      ├─ real_stock
      ├─ actual_sales
      ├─ order_placed (boolean)
      ├─ order_quantity (if placed)

3. MOVE TO NEXT DAY
   └─ current_date += 1 day
```

### Key Data Flow Points

#### Simulated Stock Calculation
```
Day 0: initial_stock (from snapshot)
Day 1: initial_stock + orders_arriving - sales
Day 2: Day1_stock + orders_arriving - sales
...
```

#### Real Stock Calculation
```
Day 0: stock_on_date[0] OR initial_stock
Day 1: stock_on_date[1] (independent from DB) OR Day0_stock - sales
Day 2: stock_on_date[2] (independent from DB) OR Day1_stock - sales
...
```

#### Forecast Generation
```
Day 0: Generate forecast using data up to Day 0
Day 1-6: Use cached forecast from Day 0
Day 7: Generate forecast using data up to Day 7
Day 8-13: Use cached forecast from Day 7
...
```

---

## Implementation Architecture

### Service Structure

```
backend/services/
├── simulation_service.py          # Main orchestrator
│   ├── SimulationService
│   │   ├── run_simulation()
│   │   ├── _simulate_day()
│   │   ├── _process_orders()
│   │   └── _calculate_metrics()
│   │
│   └── SimulationState           # State tracking
│       ├── current_date
│       ├── stock_levels
│       ├── orders_placed
│       └── metrics
│
├── simulation/
│   ├── data_filter.py            # Date filtering wrapper
│   │   └── filter_data_by_date()
│   │
│   ├── order_simulator.py        # Order tracking & arrivals
│   │   ├── place_order()
│   │   ├── process_arrivals()
│   │   └── get_orders_arriving()
│   │
│   └── comparison_engine.py    # Metrics & comparison
│       ├── compare_stockouts()
│       ├── compare_inventory_value()
│       └── generate_report()
```

### API Endpoint

```
POST /api/v1/simulation/run
{
  "client_id": "uuid",
  "start_date": "2024-01-01",
  "end_date": "2024-12-22",
  "item_ids": ["SKU-001", "SKU-002", ...],  # Optional: specific items
  "simulation_config": {
    "auto_place_orders": true,
    "lead_time_buffer_days": 0,
    "min_order_quantity": 1
  }
}

Response:
{
  "simulation_id": "uuid",
  "status": "completed",
  "results": {
    "stockout_rate": {"simulated": 0.012, "real": 0.048},
    "inventory_value": {"simulated": 2400000, "real": 3100000},
    "service_level": {"simulated": 0.988, "real": 0.952},
    "total_cost": {"simulated": 2800000, "real": 3500000},
    "improvements": {
      "stockout_reduction": 0.75,
      "inventory_reduction": 0.23,
      "cost_savings": 700000
    }
  },
  "daily_comparison": [...],
  "item_level_results": [...]
}
```

---

## Results Visualization

### 1. Executive Summary Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│           SIMULATION RESULTS - 12 MONTH PERIOD              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  PRIMARY METRICS                                             │
│  ┌──────────────┬──────────────┬──────────────┬──────────┐ │
│  │ Metric       │ Simulated    │ Real         │ Change   │ │
│  ├──────────────┼──────────────┼──────────────┼──────────┤ │
│  │ Stockout Rate│ 1.2%         │ 4.8%         │ -75% ⬇️   │ │
│  │ Inv. Value   │ $2.4M        │ $3.1M        │ -23% ⬇️   │ │
│  │ Service Level│ 98.8%        │ 95.2%        │ +3.6% ⬆️  │ │
│  │ Total Cost   │ $2.8M        │ $3.5M        │ -20% ⬇️   │ │
│  └──────────────┴──────────────┴──────────────┴──────────┘ │
│                                                              │
│  IMPROVEMENT SUMMARY                                         │
│  ✅ Stockouts prevented: 142 events                          │
│  ✅ Inventory reduction: $700K                              │
│  ✅ Cost savings: $700K annually                            │
│  ✅ Service level improvement: +3.6%                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 2. Time Series Comparison Chart

```
Inventory Value Over Time (Simulated vs Real)

$4.0M ┤
      │                    ╭─────── Real ────────╮
$3.5M ┤                   ╱                       ╲
      │                  ╱                         ╲
$3.0M ┤                 ╱                           ╲
      │        ╭───────╯                             ╲
$2.5M ┤       ╱                                        ╲
      │      ╱                                          ╲
$2.0M ┤  ╭───╯                                            ╲
      │ ╱                                                  ╲
$1.5M ┼─╯                                                    ╲
      │                                                      ╲
$1.0M ┤                                                       ╲
      │
      └──────────────────────────────────────────────────────
      Jan  Feb  Mar  Apr  May  Jun  Jul  Aug  Sep  Oct  Nov  Dec

      ──── Simulated (following system recommendations)
      ──── Real (what actually happened)
```

### 3. Stockout Events Timeline

```
Stockout Events Comparison

Jan ─────────────────────────────────────────────────────────
    Real:    ████ ██ █████ ████ ██ (12 events)
    Sim:     ██ █ (2 events) ✅ 83% reduction

Feb ─────────────────────────────────────────────────────────
    Real:    ████ ████ ████ ██ (11 events)
    Sim:     ██ (1 event) ✅ 91% reduction

Mar ─────────────────────────────────────────────────────────
    Real:    ████ ████ ████ ████ (12 events)
    Sim:     ██ █ (2 events) ✅ 83% reduction

... (continues for 12 months)
```

### 4. Item-Level Performance Table

```
┌──────────┬──────────────┬──────────────┬──────────────┬──────────┐
│ Item ID  │ Stockouts    │ Inv. Value   │ Improvement  │ Status   │
│          │ Sim | Real   │ Sim | Real   │              │          │
├──────────┼──────────────┼──────────────┼──────────────┼──────────┤
│ SKU-001  │  0  │   5    │ $45K│ $62K   │ -27% ⬇️      │ ✅ Great │
│ SKU-002  │  1  │  12    │ $38K│ $51K   │ -25% ⬇️      │ ✅ Great │
│ SKU-003  │  2  │   8    │ $52K│ $48K   │ +8% ⬆️       │ ⚠️  Over │
│ SKU-004  │  0  │   3    │ $29K│ $41K   │ -29% ⬇️      │ ✅ Great │
│ ...      │ ... │  ...   │ ... │  ...   │ ...          │ ...      │
└──────────┴──────────────┴──────────────┴──────────────┴──────────┘
```

### 5. Forecast Accuracy Context

```
Forecast Quality vs System Performance

┌─────────────────────────────────────────────────────────────┐
│  High Forecast Accuracy → Better Inventory Decisions        │
│                                                              │
│  MAPE < 20%:  ████████████ 95% of items avoided stockouts  │
│  MAPE 20-40%: ████████     78% of items avoided stockouts  │
│  MAPE 40-60%: ████         62% of items avoided stockouts  │
│  MAPE > 60%:   ██           45% of items avoided stockouts  │
│                                                              │
│  Insight: Even with imperfect forecasts, system              │
│           recommendations improve outcomes                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Metrics Definitions

### Primary Metrics

1. **Stockout Rate**
   ```
   stockout_rate = (days_with_stockout / total_days) × 100
   Target: < 2%
   ```

2. **Inventory Value**
   ```
   inventory_value = Σ(stock_level × unit_cost)
   Target: 15-30% reduction vs baseline
   ```

3. **Service Level**
   ```
   service_level = (days_in_stock / total_days) × 100
   Target: > 98%
   ```

4. **Total Cost**
   ```
   total_cost = inventory_carrying_cost + stockout_cost + ordering_cost
   Target: Minimize while maintaining service level
   ```

### Secondary Metrics

5. **Excess Inventory**
   ```
   excess_inventory = items_with_stock > 90_days_demand
   Target: < 5% of items
   ```

6. **Order Efficiency**
   ```
   order_frequency = number_of_orders / time_period
   Target: Fewer, larger orders (economies of scale)
   ```

---

## Success Criteria

### System Validation Goals

✅ **Stockout Prevention**
- Simulated stockout rate < 2%
- At least 50% reduction vs real stockout rate

✅ **Inventory Optimization**
- 15-30% reduction in inventory value
- Maintain service level > 98%

✅ **Cost Efficiency**
- Total cost lower than baseline
- Positive ROI from system recommendations

✅ **Forecast Quality**
- MAPE < 40% for majority of items
- Forecast accuracy correlates with inventory performance

---

## Data Validation Checklist

### ✅ Data Integrity Checks

1. **Initial Stock**
   - [ ] Both simulated and real start with same value (or stock_on_date for start_date)
   - [ ] Initial stock > 0 for items being simulated

2. **Daily Sales**
   - [ ] Sales data exists for all days in range
   - [ ] Sales >= 0 (no negative values)
   - [ ] Sales match historical records

3. **Real Stock**
   - [ ] stock_on_date used when available (not NULL)
   - [ ] Each day's real stock is independent (from DB)
   - [ ] Fallback calculation only when stock_on_date is NULL

4. **Simulated Stock**
   - [ ] Stock decreases by sales amount each day
   - [ ] Stock increases when orders arrive
   - [ ] Stock never goes negative (max(0, stock))

5. **Forecast**
   - [ ] Forecast uses only data up to current_date (time-travel)
   - [ ] Forecast generated weekly (every 7 days)
   - [ ] Cached forecast used for intermediate days
   - [ ] Fallback to historical average if forecast = 0

6. **Orders**
   - [ ] Orders placed when stock <= reorder_point
   - [ ] No duplicate orders (check orders_in_transit)
   - [ ] Order quantity >= MOQ (if MOQ exists)
   - [ ] Orders arrive after lead_time days

7. **Metrics**
   - [ ] Stockout rate calculated correctly
   - [ ] Service level calculated correctly
   - [ ] Inventory value calculated correctly
   - [ ] Daily comparisons recorded for all days

---

## Related Documentation

- [Simulation Implementation](./SIMULATION_IMPLEMENTATION.md) - Implementation details and validation
- [Simulation Testing](./SIMULATION_TESTING.md) - Testing scenarios and validation results
- [System Contracts](../system/CONTRACTS.md) - System architecture contracts