# Simulation System Documentation

**Status:** Design Phase  
**Last Updated:** 2025-12-22  
**Purpose:** Validate system effectiveness by simulating real-world operation over historical period

---

## Executive Summary

The simulation system runs the **exact same production logic** with historical data filtered by date, automatically following system recommendations, and comparing outcomes against reality. This validates that the system would have made better decisions if it had been running in the past.

**Goal:** Answer the question: *"If we had run this system 12 months ago, would it have minimized stockouts and reduced inventory value?"*

---

## System Flow

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
└───────────────┘                      │ - Arrivals     │
        │                              └───────────────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                      ┌───────────────┐
│ Forecast      │                      │ Stock Update  │
│ Service       │                      │ stock = stock │
│ (training_end │                      │   - sales     │
│  _date param) │                      │   + arrivals  │
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

## Detailed Simulation Flow

### Day-by-Day Execution

```
┌──────────────────────────────────────────────────────────────┐
│ Day N (e.g., 2024-01-15)                                      │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  STEP 1: Data Filtering                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ SELECT * FROM ts_demand_daily                        │   │
│  │ WHERE client_id = X AND date_local <= '2024-01-15'  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  STEP 2: Forecast Generation                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ forecast_service.generate_forecast(                  │   │
│  │   training_end_date='2024-01-15',                    │   │
│  │   prediction_length=30                               │   │
│  │ )                                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  STEP 3: Inventory Calculation                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ inventory_calc.calculate_reorder_point()             │   │
│  │ inventory_calc.calculate_safety_stock()              │   │
│  │ IF current_stock <= reorder_point:                   │   │
│  │   order_qty = recommended_quantity                   │   │
│  │   place_order(item_id, order_qty, lead_time)         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  STEP 4: Process Order Arrivals                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ FOR each order placed earlier:                      │   │
│  │   IF order.arrival_date == current_date:            │   │
│  │     simulated_stock[item_id] += order.quantity       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  STEP 5: Update Stock from Sales                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ simulated_stock[item_id] -= actual_sales[item_id]   │   │
│  │ (from real historical data for this day)            │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  STEP 6: Comparison                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ IF simulated_stock[item_id] <= 0:                    │   │
│  │   simulated_stockouts += 1                           │   │
│  │                                                       │   │
│  │ IF real_stock[item_id] <= 0:                        │   │
│  │   real_stockouts += 1                                 │   │
│  │                                                       │   │
│  │ inventory_value_sim += simulated_stock * unit_cost   │   │
│  │ inventory_value_real += real_stock * unit_cost       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HISTORICAL DATA SOURCES                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ts_demand_daily (12 months)                                │
│  ├─ date_local: 2024-01-01 to 2024-12-22                   │
│  ├─ item_id, location_id, units_sold                        │
│  └─ Used for: Training forecasts, actual sales comparison   │
│                                                              │
│  stock_levels (snapshot at start_date)                     │
│  ├─ Initial stock levels on 2024-01-01                      │
│  └─ Used for: Starting point of simulation                   │
│                                                              │
│  purchase_orders (historical)                                │
│  ├─ What orders were actually placed                        │
│  └─ Used for: Comparing recommendations vs reality         │
│                                                              │
│  products (static)                                           │
│  ├─ lead_time_days, unit_cost, safety_stock_days           │
│  └─ Used for: Inventory calculations                        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  SIMULATION STATE TRACKING                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  simulation_state = {                                        │
│    "current_date": date,                                     │
│    "stock_levels": {item_id: quantity},                     │
│    "orders_placed": [                                        │
│      {                                                       │
│        "date": "2024-01-10",                                │
│        "item_id": "SKU123",                                  │
│        "quantity": 100,                                      │
│        "lead_time_days": 7,                                  │
│        "arrival_date": "2024-01-17"                          │
│      }                                                       │
│    ],                                                        │
│    "orders_arriving_today": [...],                           │
│    "metrics": {                                              │
│      "stockouts": 0,                                         │
│      "inventory_value": 0.0,                                 │
│      "service_level": 0.0                                    │
│    }                                                         │
│  }                                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
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

## Implementation Approach

### Phase 1: Core Simulation (No External Dependencies)

**Initial implementation will use only existing services:**
- ✅ `ForecastService` - Already supports `training_end_date` parameter
- ✅ `InventoryCalculator` - Existing reorder point and safety stock logic
- ✅ `ETLService` - Data access patterns already established
- ✅ No new dependencies - Pure Python, uses existing codebase

**Benefits:**
- Fast implementation using proven components
- No external library dependencies
- Easy to test and debug
- Validates existing system logic

### Future Enhancement: Darts Library Integration (Optional)

The [Darts library](https://unit8co.github.io/darts/index.html) could be added later for:
- Model comparison (test Darts models vs Chronos-2)
- Probabilistic forecasting enhancements
- Additional validation layer

**Decision:** Defer Darts integration until core simulation is validated.

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

## Implementation Plan

### Git Branch Strategy

**Branch:** `feature/simulation-system`

```bash
# Create feature branch
git checkout -b feature/simulation-system

# Work on simulation implementation
# ... make changes ...

# Commit and push
git add backend/services/simulation_service.py
git commit -m "feat: Add simulation system for historical validation"
git push origin feature/simulation-system
```

**Merge Strategy:** Merge to `main` after:
- ✅ All tests passing
- ✅ Documentation complete
- ✅ Code review approved
- ✅ Initial simulation run successful

### Implementation Steps

1. **Design Review** ✅ (This document)
2. **Create Feature Branch** ✅ `feature/simulation-system`
3. **Implementation**
   - Create `SimulationService`
   - Build date filtering wrapper
   - Implement order simulator
   - Build comparison engine
   - Add API endpoint
4. **Testing**
   - Unit tests for each component
   - Integration test with real historical data
   - Validate metrics calculations
5. **Results Analysis**
   - Generate first simulation report
   - Validate metrics
   - Iterate on improvements
6. **Merge to Main**
   - Code review
   - Update documentation
   - Merge PR

---

**Document Owner:** Development Team  
**Related Docs:**
- [Forecasting Integration](../backend/FORECASTING_INTEGRATION.md)
- [System Contracts](CONTRACTS.md)
- [Darts Library](https://unit8co.github.io/darts/index.html)

