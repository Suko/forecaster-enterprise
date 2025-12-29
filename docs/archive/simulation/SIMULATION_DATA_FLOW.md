# Simulation Data Flow

> **🛑 DEPRECATED**: This document has been consolidated into [SIMULATION_SYSTEM.md](../system/SIMULATION_SYSTEM.md)
>
> **Date Archived**: 2025-12-29
>
> This content is no longer maintained. Please refer to the consolidated documentation for current information.

## Overview
This document explains how data flows through the simulation system, step by step.

## Data Sources

### 1. Initial Stock Levels
**Source**: `_get_stock_snapshot()`
- **Primary**: `ts_demand_daily.stock_on_date` for `start_date`
- **Fallback**: `stock_levels.current_stock` (current snapshot)
- **Used for**: Both simulated and real stock initialization

### 2. Daily Sales Data
**Source**: `_get_actual_sales()`
- **Table**: `ts_demand_daily.units_sold`
- **Query**: `SELECT SUM(units_sold) WHERE client_id, item_id, date_local = current_date`
- **Used for**: 
  - Subtracting from simulated stock
  - Calculating real stock (when stock_on_date unavailable)

### 3. Real Stock Levels (Historical)
**Source**: `_get_real_stock_for_date()`
- **Table**: `ts_demand_daily.stock_on_date`
- **Query**: `SELECT SUM(stock_on_date) WHERE client_id, item_id, date_local = current_date`
- **Behavior**:
  - Returns actual value if `stock_on_date` is populated (not NULL)
  - Returns `None` if `stock_on_date` is NULL (no data)
- **Used for**: Real stock comparison (independent value for each day)

### 4. Product Configuration
**Source**: `_get_products()`
- **Table**: `products`
- **Fields**: `unit_cost`, `safety_buffer_days`, `item_id`
- **Used for**: Cost calculations, safety stock configuration

### 5. Lead Time
**Source**: `_get_lead_time()`
- **Primary**: `product_supplier_conditions.lead_time_days` (where `is_primary = true`)
- **Fallback**: Default 7 days
- **Used for**: Reorder point calculation, order arrival dates

### 6. MOQ (Minimum Order Quantity)
**Source**: `_get_moq()`
- **Primary**: `product_supplier_conditions.moq` (where `is_primary = true`)
- **Secondary**: `suppliers.default_moq`
- **Fallback**: `None` (no MOQ constraint)
- **Used for**: Order quantity calculation

### 7. Forecasted Demand
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

## Day-by-Day Simulation Flow

### For Each Day:

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
      └─ order_quantity (if placed)

3. MOVE TO NEXT DAY
   └─ current_date += 1 day
```

## Key Data Flow Points

### Simulated Stock Calculation
```
Day 0: initial_stock (from snapshot)
Day 1: initial_stock + orders_arriving - sales
Day 2: Day1_stock + orders_arriving - sales
...
```

### Real Stock Calculation
```
Day 0: stock_on_date[0] OR initial_stock
Day 1: stock_on_date[1] (independent from DB) OR Day0_stock - sales
Day 2: stock_on_date[2] (independent from DB) OR Day1_stock - sales
...
```

### Forecast Generation
```
Day 0: Generate forecast using data up to Day 0
Day 1-6: Use cached forecast from Day 0
Day 7: Generate forecast using data up to Day 7
Day 8-13: Use cached forecast from Day 7
...
```

## Validation Checklist

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

## Next Steps: Validation Process

1. **Run simulation** for one product
2. **Check data sources** - verify all queries return expected data
3. **Validate calculations** - manually verify a few days
4. **Compare results** - simulated vs real metrics
5. **Review edge cases** - stockouts, zero sales, missing data


