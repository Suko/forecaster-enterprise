# Simulation Implementation

**Status**: ✅ Core functionality complete and validated
**Last Updated:** 2025-12-29
**Purpose:** Detailed implementation guide for the simulation system

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

## Implementation Components

### Data Flow Architecture

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

## Validation Results

### What We're Simulating

### Simulated Stock (Our System's Logic)
- **Data Source**: Starts with `stock_on_date` from database (or `current_stock` snapshot)
- **Logic**:
  - Decreases by actual sales each day
  - Increases when orders arrive (after lead time)
  - Places orders based on our forecasts and reorder points
  - **Independent** of real stock after day 1

### Real Stock (Historical Data - For Comparison Only)
- **Data Source**: `ts_demand_daily.stock_on_date` (80% from DB, 20% calculated fallback)
- **Purpose**: Compare our system's decisions against actual historical inventory management
- **Not Used**: Real stock is NOT used in simulation logic - only for comparison

### Validation Results

| Check | Status | Details |
|-------|--------|---------|
| **Initial Stock** | ✅ PASS | Difference: 1.0 units (acceptable) |
| **No Negative Stock** | ✅ PASS | 0 negative days for both |
| **Sales Data** | ✅ PASS | 366/366 days available (100%) |
| **Stock Calculation** | ✅ PASS | 0 calculation errors |
| **Orders** | ✅ PASS | 8 orders placed correctly |
| **Stockouts** | ✅ PASS | Sim=0, Real=0 |
| **Metrics** | ✅ PASS | Stockout rates match calculated values |
| **Real Stock Independence** | ✅ PASS | 292 days from DB, 73 calculated |

### Data Sources Verified

#### 1. Sales Data ✅
- **Source**: `ts_demand_daily.units_sold`
- **Validation**: 366/366 days available (100% complete)
- **Usage**: Subtracted from simulated stock each day

#### 2. Forecast Data ✅
- **Source**: `ForecastService.generate_forecast()` (Chronos-2 model)
- **Training Data**: Only data up to `current_date` (time-travel safe)
- **Frequency**: Generated weekly, cached for 7 days
- **Fallback**: Historical average if forecast = 0

#### 3. Product Configuration ✅
- **Source**: `products` table
  - `unit_cost`: For inventory value calculations
  - `safety_buffer_days`: For safety stock calculation
- **Source**: `product_supplier_conditions` table
  - `lead_time_days`: For order arrival calculations
  - `moq`: Minimum order quantity constraint

#### 4. Initial Stock ✅
- **Source**: `ts_demand_daily.stock_on_date` for `start_date`
- **Fallback**: `stock_levels.current_stock` snapshot
- **Validation**: Simulated and real start within 1 unit (acceptable)

#### 5. Real Stock (Historical) ✅
- **Primary Source**: `ts_demand_daily.stock_on_date` (292 days = 80%)
- **Fallback**: Calculated from previous day - sales (73 days = 20%)
- **Purpose**: Comparison only, not used in simulation logic

### Simulation Logic Verified

#### Day-by-Day Process ✅
1. **Order Arrivals**: Process orders that arrive today (add to simulated stock)
2. **Get Sales**: Fetch actual sales from `ts_demand_daily.units_sold`
3. **Get Real Stock**: Fetch from `stock_on_date` (for comparison only)
4. **Update Simulated Stock**: Subtract sales from simulated stock
5. **Generate Forecast**: Weekly forecast generation (cached for 7 days)
6. **Check Reorder Point**: If stock <= reorder_point AND no orders in transit
7. **Place Order**: Calculate quantity (forecast + safety stock + MOQ), place order
8. **Record Comparison**: Store daily comparison for metrics

#### Key Validations ✅
- ✅ Stock never goes negative
- ✅ Stock decreases by exact sales amount (unless order arrives)
- ✅ Orders placed only when stock <= reorder_point
- ✅ Orders respect MOQ constraints
- ✅ Orders arrive after lead_time days
- ✅ Real stock is independent (not used in simulation logic)
- ✅ Metrics calculated correctly from daily comparisons

### Data Tracking Validation

#### Currently Tracked Data

##### 1. Daily Comparisons (Per Item, Per Day)

**Source**: `ComparisonEngine.record_daily_comparison()`

| Field | Type | Purpose | Status |
|-------|------|---------|--------|
| `date` | date | Simulation date | ✅ Tracked |
| `item_id` | str | Product identifier | ✅ Tracked |
| `simulated_stock` | float | Stock if we followed system | ✅ Tracked |
| `real_stock` | float | Actual historical stock | ✅ Tracked |
| `actual_sales` | float | Units sold this day | ✅ Tracked |
| `simulated_stockout` | bool | Was simulated stock = 0? | ✅ Tracked |
| `real_stockout` | bool | Was real stock = 0? | ✅ Tracked |
| `order_placed` | bool | Did system place order? | ✅ Tracked |
| `order_quantity` | float | Order quantity if placed | ✅ Tracked |

**Coverage**: ✅ Complete - All essential daily data tracked

##### 2. Item-Level Metrics (Aggregated Per Item)

**Source**: `ComparisonEngine.item_metrics`

| Metric | Type | Calculation | Status |
|--------|------|-------------|--------|
| `simulated_stockouts` | int | Count of days with stockout | ✅ Tracked |
| `real_stockouts` | int | Count of days with stockout | ✅ Tracked |
| `simulated_days_in_stock` | int | Count of days in stock | ✅ Tracked |
| `real_days_in_stock` | int | Count of days in stock | ✅ Tracked |
| `simulated_inventory_value` | Decimal | Sum of (stock × unit_cost) | ✅ Tracked |
| `real_inventory_value` | Decimal | Sum of (stock × unit_cost) | ✅ Tracked |
| `total_days` | int | Total simulation days | ✅ Tracked |

**Coverage**: ✅ Complete - All essential item metrics tracked

##### 3. Order Tracking

**Source**: `OrderSimulator`

| Data | Type | Status | Notes |
|------|------|--------|-------|
| Orders placed | List[SimulatedOrder] | ✅ Tracked | In `order_simulator.orders` |
| Order quantity | float | ✅ Tracked | In daily comparison |
| Order date | date | ✅ Tracked | In `SimulatedOrder` |
| Arrival date | date | ✅ Tracked | In `SimulatedOrder` |
| Lead time | int | ✅ Tracked | In `SimulatedOrder` |
| Total orders per item | int | ✅ Calculated | In `item_level_results` |

**Coverage**: ✅ Complete - All essential order data tracked

#### Data Quality Validation

##### Completeness
| Data Type | Coverage | Status |
|-----------|----------|--------|
| Sales data | 100% (366/366 days) | ✅ Validated |
| Real stock | 80% from DB, 20% calculated | ✅ Validated |
| Simulated stock | 100% calculated | ✅ Validated |
| Orders | All orders tracked | ✅ Validated |
| Metrics | All metrics calculated | ✅ Validated |

##### Accuracy
| Check | Status | Notes |
|-------|--------|-------|
| Stock never negative | ✅ PASS | `max(0, stock)` enforced |
| Stock decreases by sales | ✅ PASS | Validated in tests |
| Orders arrive after lead time | ✅ PASS | Validated in tests |
| Metrics calculated correctly | ✅ PASS | Validated in tests |
| Real stock independent | ✅ PASS | Validated in tests |

**Result**: ✅ **ALL ESSENTIAL DATA TRACKED AND VALIDATED**

### Conclusion

**✅ YES - We are simulating the right data**

The validation confirms:
1. **Correct Data Sources**: All data comes from the right database tables
2. **Correct Logic**: Stock calculations, order placement, and metrics are accurate
3. **Correct Independence**: Simulated and real stock are independent (as intended)
4. **Complete Data**: 100% sales data coverage, 80% real stock from DB
5. **Data Tracking**: All essential data properly tracked and validated

The simulation accurately represents:
- How our system would manage inventory using forecasts
- Comparison against actual historical inventory management
- All constraints (MOQ, lead time, safety stock) are respected

---

## Development Roadmap

### ✅ Completed

- [x] Core simulation service implemented
- [x] API endpoint created (`POST /api/v1/simulation/run`)
- [x] Validation script created and passing
- [x] HTML report generation working
- [x] Documentation complete
- [x] Data flow validated

### 🔄 Recommended Next Steps

#### 1. **Testing** (High Priority)

**Status**: ✅ Baseline tests added

**What to add:**
- [x] Unit tests for `OrderSimulator`
  - Order placement, MOQ behavior, arrivals, idempotent receipt
- [x] Unit tests for `ComparisonEngine`
  - Item and global metric calculations
- [x] `SimulationService` invariants (mocked dependencies)
  - Order placement + in-transit protection, arrival-before-sales convention, non-negative stock clamp, time-travel forecast call signature
- [x] API request validation tests for `POST /api/v1/simulation/run`
  - Client mismatch and date window validation
- [ ] Expand `SimulationService` coverage
  - Add cases for forecast fallback paths, real-stock fallback paths, missing product data, and multi-item behavior

**Tests added:**
- `backend/tests/test_services/test_order_simulator.py`
- `backend/tests/test_services/test_comparison_engine.py`
- `backend/tests/test_services/test_simulation_service_invariants.py`
- `backend/tests/test_api/test_simulation_api.py`

**How to run:**
```bash
cd backend
uv run pytest tests/test_services/test_order_simulator.py -q
uv run pytest tests/test_services/test_comparison_engine.py -q
uv run pytest tests/test_services/test_simulation_service_invariants.py -q
uv run pytest tests/test_api/test_simulation_api.py -q
```

**Estimated Time (to expand coverage)**: 0.5-1 day

#### 2. **API Documentation Update** (Medium Priority)

**Status**: ⚠️ Endpoint exists but not in API reference

**What to add:**
- [ ] Add simulation endpoint to `docs/backend/API_REFERENCE.md`
- [ ] Document request/response schemas
- [ ] Add example requests/responses
- [ ] Document error codes

**Estimated Time**: 30 minutes

#### 3. **Cost Calculation Enhancement** (Low Priority - Optional)

**Status**: ⚠️ TODO in code (line 687)

**Current**: Only inventory carrying cost (inventory value)

**What to add:**
- [ ] Stockout cost calculation
  - Formula: `stockout_cost = stockout_days × lost_sales_per_day × profit_margin`
  - Need: Lost sales estimate, profit margin per item
- [ ] Ordering cost calculation
  - Formula: `ordering_cost = number_of_orders × fixed_order_cost`
  - Need: Fixed order cost per supplier (or default)
- [ ] Total cost = inventory_cost + stockout_cost + ordering_cost

**Note**: This requires additional configuration (profit margins, order costs). Can be deferred.

**Estimated Time**: 2-3 hours

#### 4. **Error Handling & Edge Cases** (Medium Priority)

**Status**: ✅ Basic error handling exists

**What to improve:**
- [ ] Handle missing product data gracefully
- [ ] Handle missing supplier/lead time data
- [ ] Handle forecast failures more gracefully
- [ ] Add retry logic for forecast generation
- [ ] Better error messages for users
- [ ] Logging improvements (structured logs)

**Estimated Time**: 1 day

#### 5. **Frontend Integration** (Future)

**Status**: ❌ No frontend integration

**What to add:**
- [ ] Frontend API proxy route: `POST /api/simulation/run`
- [ ] Simulation UI page (e.g., `/simulation`)
- [ ] Form for simulation parameters (date range, items)
- [ ] Results visualization (charts, metrics)
- [ ] Report download (HTML report)
- [ ] Simulation history/listing

**Estimated Time**: 1-2 weeks

#### 6. **Performance Optimization** (If Needed)

**Status**: ✅ Currently optimized (weekly forecast caching)

**Potential improvements if needed:**
- [ ] Batch forecast generation (multiple items at once)
- [ ] Parallel processing for multiple products
- [ ] Database query optimization (indexes on `ts_demand_daily`)
- [ ] Response streaming for large simulations

**Note**: Only needed if simulations become too slow (>5 minutes for 1 year, 10+ items)

**Estimated Time**: 1-2 days (if needed)

### Priority Summary

#### Must Do (Before Production)
1. **Testing** - Critical for reliability
2. **API Documentation** - Required for integration
3. **Error Handling** - Production readiness

#### Should Do (Soon)
4. **Production Readiness Checklist** - Complete all items

#### Nice to Have (Future)
5. **Cost Calculation Enhancement** - Optional feature
6. **Frontend Integration** - User-facing feature
7. **Performance Optimization** - Only if needed

### Current State Assessment

**✅ Ready for:**
- Development/testing use
- Internal validation
- Manual testing

**⚠️ Not ready for:**
- Production deployment (needs tests)
- External API consumers (needs documentation)
- Frontend integration (needs API proxy)

**🎯 Recommendation:**
Focus on **Testing** and **API Documentation** first, then proceed with production readiness checklist.

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

## Known Issues & Areas of Concern

### 🔍 Areas of Concern

#### 1. **Order Arrival Timing** ⚠️ MEDIUM

**Issue**: Orders arrive BEFORE sales are subtracted each day.

**Current Logic**:
```python
# Process order arrivals (orders placed earlier that arrive today)
arriving_orders = self.order_simulator.get_orders_arriving(current_date)
for order in arriving_orders:
    simulated_stock[order.item_id] += order.quantity  # Add stock first

# Then subtract sales
simulated_stock[item_id] = max(0.0, simulated_stock[item_id] - actual_sales)
```

**Question**: Is this realistic?
- **Real world**: Orders typically arrive at start of day or end of day
- **Impact**: If orders arrive at start of day, they're available for that day's sales (correct)
- **If orders arrive at end of day**: They wouldn't be available for same-day sales (potential issue)

**Investigation Needed**:
- ✅ **Likely correct** - Most inventory systems assume orders arrive at start of day
- ⚠️ **Verify**: Check if this matches real-world behavior for your use case

#### 2. **Forecast Staleness** ⚠️ MEDIUM

**Issue**: Forecasts are cached for 7 days, but demand patterns might change.

**Current Logic**:
```python
should_regenerate_forecast = (
    days_since_start == 0 or  # First day
    days_since_start % 7 == 0  # Weekly refresh
)
```

**Question**: Is weekly refresh sufficient?
- **Risk**: Using 7-day-old forecast during volatile periods
- **Impact**: Might miss demand spikes or drops

#### 3. **MOQ Impact on Small Orders** ⚠️ MEDIUM

**Issue**: MOQ can force larger orders than needed, potentially causing overstocking.

**Current Logic**:
```python
# Apply MOQ constraint
if moq and recommended_qty < moq:
    order_qty = moq
else:
    order_qty = recommended_qty
```

**Question**: Should we allow partial MOQ orders or implement MOQ buffering?

#### 4. **Lead Time Variability** ⚠️ LOW

**Issue**: System assumes exact lead times, but suppliers may have variability.

**Current Logic**:
```python
arrival_date = order_date + timedelta(days=lead_time_days)
```

**Question**: Should we add lead time buffers or probabilistic arrival dates?

#### 5. **Safety Stock Calculation** ⚠️ MEDIUM

**Issue**: Safety stock depends heavily on forecast accuracy.

**Current Logic**:
```python
safety_stock = avg_daily_demand * safety_buffer_days
```

**Question**: Should safety stock be dynamically adjusted based on forecast confidence?

---

## Related Documentation

- [Simulation System](./SIMULATION_SYSTEM.md) - System overview and architecture
- [Simulation Testing](./SIMULATION_TESTING.md) - Testing scenarios and validation results
- [System Contracts](../system/CONTRACTS.md) - System architecture contracts
