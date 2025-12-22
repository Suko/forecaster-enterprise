# Experiments Page Migration Plan

**Last Updated:** 2025-12-18  
**Status:** ✅ **COMPLETED** - Phase 1 (Test Bed & ROI Calculator)  
**Source:** `/Users/mihapro/Development/ecommerce/old/ecommerce-agent/frontend/src/views/Experimental.vue`

---

## Executive Summary

Migrate the Experiments page from the old ecommerce-agent project to the new Forecaster Enterprise application. The page includes:
- **Test Bed** - Forecast vs Actual comparison tool
- **ROI Calculator** - Forecasting ROI exploration tool

**Key Differences:**
- Use Nuxt UI components instead of custom UI components
- Remove client selector (client already selected via authentication)
- Adapt to current project structure (Nuxt 3, TypeScript, composables pattern)
- **CRITICAL: Use existing forecasting endpoints** - don't create duplicate forecast generation logic
- **CRITICAL: Dynamic model support** - use whatever models are available, don't hardcode "Kumo" or "Chronos"

## Adaptation Strategy

### Use Existing Forecast Infrastructure

**DO:**
- ✅ Use existing `POST /api/v1/forecast` endpoint to generate forecasts
- ✅ Reuse `forecast_runs` and `forecast_results` tables
- ✅ Support all available models dynamically (chronos-2, statistical_ma7, sba, croston, min_max)
- ✅ **REUSE EXISTING**: `GET /api/v1/forecast/forecasts/quality/{item_id}` - Already calculates MAPE/statistics
- ✅ **REUSE EXISTING**: `QualityCalculator` service - Already has MAPE, MAE, RMSE, Bias calculations
- ✅ **REUSE EXISTING**: `POST /api/v1/forecast/forecasts/actuals` - Already backfills actual values
- ✅ Test the actual forecasting system (not a separate testbed system)

**DON'T:**
- ❌ Create duplicate forecast generation logic
- ❌ Hardcode model names like "Kumo" or "Chronos" 
- ❌ Create separate testbed-specific forecast endpoints
- ❌ Ignore the existing model selection infrastructure

### Model Selection

The system supports multiple models:
- **Primary ML Model**: `chronos-2` (default)
- **Baseline Models**: `statistical_ma7`, `sba`, `croston`, `min_max`
- Models are selected via `primary_model` parameter and `include_baseline` flag
- Testbed should allow users to select which model(s) to test
- Display all models that were run in the comparison chart

---

## Current State Analysis

### Old Project Structure
```
frontend/src/views/
  ├── Experimental.vue          # Main container with tabs
  ├── TestBed.vue                 # Test Bed component
  ├── TestbedCovariate.vue        # Covariate test bed (not migrating)
  └── ROICalculator.vue          # ROI Calculator component
```

### New Project Structure
```
frontend/app/
  ├── pages/
  │   └── experiments/           # NEW: Create this directory
  │       ├── index.vue          # Main experiments page with tabs
  │       ├── testbed.vue        # Test Bed page
  │       └── roi-calculator.vue # ROI Calculator page
  ├── composables/
  │   └── useExperiments.ts      # NEW: Composable for experiments API calls
  └── types/
      └── experiments.ts         # NEW: TypeScript types
```

---

## Component Breakdown

### 1. Main Experiments Page (`/experiments`)

**File:** `frontend/app/pages/experiments/index.vue`

**Functionality:**
- Tab navigation between Test Bed and ROI Calculator
- URL hash-based routing (`#testbed`, `#roi`)
- No client selector (client already selected via auth)

**Nuxt UI Components to Use:**
- `UTabs` for tab navigation
- `UCard` for content containers
- `UButton` for actions

**Implementation Notes:**
- Use Nuxt 3 `<NuxtPage>` or conditional rendering based on active tab
- Store active tab in URL hash for bookmarking
- Remove `ClientSelector` component (not needed)

---

### 2. Test Bed Component (`/experiments/testbed`)

**File:** `frontend/app/pages/experiments/testbed.vue`

**Functionality:**
- **Filters (all supported):**
  - Store/Location dropdown (All Stores or specific location)
  - SKU/Product dropdown (All SKUs or specific product)
  - Category dropdown (All Categories or specific category)
  - Supplier dropdown (All Suppliers or specific supplier)
- **Forecast Configuration:**
  - Forecast Model selection (dynamic based on available models)
  - Forecast Horizon (days) input (e.g., 30 days)
  - Auto-calculated cutoff date: max_date - horizon_days
  - **Covariates checkbox: NOT included** (deferred to later phase)
- **Generate & Compare:**
  - "Generate Forecast & Compare" button
  - Generate forecast charts comparing:
    - Historical data (with optional rolling average)
    - Primary model forecast (e.g., chronos-2)
    - Baseline model forecast (e.g., statistical_ma7, if include_baseline=true)
    - Actual ground truth
  - Display MAPE statistics for each model
- **Chart Options (Current Phase - Basic):**
  - Rolling Average toggle (3, 7, 14, 30 day windows)
  - Show/Hide rolling average line on chart
- **Chart Options (Future - When Covariates Added):**
  - Show Promotions (promo_flag) - Toggle vertical orange shaded regions
  - Show Holidays (holiday_flag) - Toggle vertical purple shaded regions
  - Show Weekends (is_weekend) - Toggle faint gray vertical lines
  - Show Stockouts (0 sales) - Highlight periods with zero sales
  - Show Rolling Average Window - Dropdown (3, 7, 14, 30 days)
- **Additional Features:**
  - Test history (last 5 tests) with ability to reload/delete
  - Chart visualization using Chart.js (already configured)
  - Date range display (available min/max dates)
  - Performance metrics display (MAPE, RMSE, MAE) - when available

**Key Features:**
- **Filter Section (All Supported):**
  - Store/Location dropdown: "All Stores" + specific locations
  - SKU/Product dropdown: "All SKUs" + specific products  
  - Category dropdown: "All Categories" + specific categories
  - Supplier dropdown: "All Suppliers" + specific suppliers
- **Forecast Configuration:**
  - Forecast Model dropdown: Dynamic based on available models
  - Forecast Horizon (days): Number input (default: 30)
  - Auto-calculated cutoff: "Cutoff will be auto-calculated as: max date - horizon days"
  - **Covariates checkbox: NOT included** (deferred to later phase - as requested)

**What's Included:**
- ✅ All 4 filter dropdowns (Store, SKU, Category, Supplier)
- ✅ Forecast Model selection
- ✅ Forecast Horizon input
- ✅ Auto-calculated cutoff date
- ✅ Generate Forecast & Compare button
- ✅ Chart visualization with all models
- ✅ MAPE/statistics display
- ✅ Basic chart options (Rolling Average toggle)

**What's Excluded (Deferred to Covariates Phase):**
- ❌ Covariates checkbox ("Use Covariates (Promo, Holiday, Weekend)")
- ❌ Covariate-based forecast generation
- ❌ Chart options for covariates (will be added when covariates are implemented):
  - ❌ Show Promotions (promo_flag) - vertical orange shaded regions
  - ❌ Show Holidays (holiday_flag) - vertical purple shaded regions
  - ❌ Show Weekends (is_weekend) - faint gray vertical lines
  - ❌ Show Stockouts (0 sales) - highlight zero sales periods
  - ❌ Chart.js annotation plugin integration
  - ❌ Chart.js zoom plugin integration
  - ❌ Interactive chart features (zoom, pan, crosshair)
  - ❌ Performance metrics display (MAPE, RMSE, MAE badges)
- **Generate & Compare:**
  - "Generate Forecast & Compare" button
  - Applies all filters to forecast request
  - Calculates cutoff_date = max_date - horizon_days
- **Additional Features:**
  - Date range validation (min/max from backend)
  - Rolling average toggle (3, 7, 14, 30 day windows)
  - localStorage persistence for last test configuration
  - Test history caching and management

**Backend API Requirements:**
- **USE EXISTING**: `GET /api/v1/locations` - Get locations/stores for filter
- **USE EXISTING**: `GET /api/v1/suppliers` - Get suppliers for filter
- **USE EXISTING**: `GET /api/v1/products` - Get products (supports category, supplier_id, location_id filters)
- **NEW**: `GET /api/v1/products/categories` - Get unique categories (or extract from products)
- **USE EXISTING**: `POST /api/v1/forecast` - Generate forecast (reuse existing endpoint)
- **USE EXISTING**: `GET /api/v1/forecast/forecasts/quality/{item_id}` - Get MAPE/statistics (already exists!)
- **USE EXISTING**: `POST /api/v1/forecast/forecasts/actuals` - Backfill actual values (already exists!)
- **USE EXISTING**: `QualityCalculator` service - Already calculates MAPE, MAE, RMSE, Bias
- **NEW**: `GET /api/v1/forecast/date-range` - Get available date range from ts_demand_daily
- **NEW**: `GET /api/v1/forecast/models` - List available models (chronos-2, statistical_ma7, sba, croston, min_max)
- **NEW**: `GET /api/v1/forecast/testbed/history` - Get test history (optional, can use forecast_runs table)

**Filter Integration:**
- When filters are applied, use them to filter `item_ids` before calling forecast endpoint
- Store filter: Filter products by `location_id` in stock_levels
- SKU filter: Use specific `item_id`
- Category filter: Filter products by `category`
- Supplier filter: Filter products by `supplier_id` via product_supplier_conditions

**Key Adaptation:**
- **DO NOT** hardcode "Kumo" or "Chronos" - use whatever models are available in the system
- **REUSE existing quality/accuracy infrastructure** - no need to duplicate MAPE calculation
- Use existing forecast infrastructure to test it
- Model selection should be dynamic based on available models
- Support multiple models (primary + baseline) as the existing endpoint does
- For testbed: Generate forecast → Backfill actuals from ts_demand_daily → Call quality endpoint

**Nuxt UI Components to Use:**
- `USelect` for all dropdowns (Store, SKU, Category, Supplier, Forecast Model)
- `UInput` for number inputs (Forecast Horizon)
- `UCard` for sections
- `UButton` for "Generate Forecast & Compare" action
- `UCheckbox` for rolling average toggle (current phase)
- `UCheckbox` for chart options (future - when covariates added):
  - Show Promotions
  - Show Holidays
  - Show Weekends
  - Show Stockouts
- `USelect` for Rolling Average Window dropdown (3, 7, 14, 30 days)
- `UAlert` for errors/info messages
- `UFormGroup` for form organization

**Charts:**
- Use existing Chart.js setup (`plugins/chartjs.client.ts`)
- Use `vue-chartjs` Line chart component
- **CRITICAL: Copy exact chart design and functionality from old project**
- See "Chart Design & Functionality" section below for detailed specifications

**Composable:**
- `useExperiments.ts` - Handle all testbed API calls
- Methods: 
  - `fetchAvailableModels()` - Get list of available models
  - `fetchLocations()` - Get available locations/stores (reuse `GET /api/v1/locations`)
  - `fetchCategories()` - Get unique categories (new endpoint or extract from products)
  - `fetchSuppliers()` - Get available suppliers (reuse `GET /api/v1/suppliers`)
  - `fetchProducts()` - Get products with filters (reuse `GET /api/v1/products`)
  - `applyFiltersToItemIds()` - Helper to filter item_ids based on Store/SKU/Category/Supplier filters
  - `generateTestbedForecast()` - Call existing `POST /api/v1/forecast` with:
    - Filtered item_ids (based on filters)
    - Selected model as primary_model
    - include_baseline=true
    - prediction_length = horizon_days
  - `backfillActualsFromHistory()` - Call `POST /api/v1/forecast/forecasts/actuals` to backfill from ts_demand_daily
  - `getQualityMetrics()` - Call existing `GET /api/v1/forecast/forecasts/quality/{item_id}` to get MAPE/statistics
  - `fetchDateRange()` - Get available date range
  - `fetchTestbedHistory()` - Get past testbed runs (optional, from forecast_runs)

---

### 3. ROI Calculator Component (`/experiments/roi-calculator`)

**File:** `frontend/app/pages/experiments/roi-calculator.vue`

**Functionality:**
- Interactive sliders for:
  - Annual revenue (€500K - €50M)
  - Inventory distortion % (10-30%)
  - Current forecast accuracy/MAPE (20-60%)
  - Improved forecast accuracy/MAPE (5-50%)
- Real-time calculations:
  - Cost comparison (current vs improved)
  - Annual savings
  - Error reduction percentage
  - Savings curve visualization
- Charts:
  - Bar chart: Cost comparison
  - Line chart: Savings vs accuracy curve
  - Bar chart: Savings at different accuracy levels
- Help section explaining how to find current MAPE

**Key Features:**
- All calculations client-side (no backend needed)
- Currency formatting (EUR)
- Responsive sliders with formatted display
- Example scenarios and explanations

**Nuxt UI Components to Use:**
- `USlider` for input sliders
- `UCard` for sections
- `UAccordion` or `UDisclosure` for help section
- `UButton` for actions (if needed)

**Charts:**
- Use Chart.js Bar and Line charts
- Same styling as Test Bed charts

**Composable:**
- No backend calls needed (pure client-side calculations)
- Can create `useROICalculator.ts` for calculation logic if desired

---

## Backend API Requirements

### New Endpoints Needed

#### 1. Test Bed Forecast Generation
**USE EXISTING ENDPOINT**: `POST /api/v1/forecast`

Request Body (adapt existing ForecastRequest):
```json
{
  "item_ids": ["item_id_1"],
  "prediction_length": 7,  // horizon_days
  "model": "chronos-2",     // or user-selected model
  "include_baseline": true  // to get statistical_ma7 as well
}
```

Response: Existing ForecastResponse format

**Then call comparison endpoint to get actuals and statistics:**

#### 2. Test Bed Workflow (REUSE EXISTING ENDPOINTS)

**Step 1: Generate Forecast**
```
POST /api/v1/forecast
Request: { item_ids, prediction_length, model, include_baseline }
Response: ForecastResponse with forecast_run_id
```

**Step 2: Backfill Actuals from ts_demand_daily**
```
POST /api/v1/forecast/forecasts/actuals
Request: { item_id, actuals: [{ date, actual_value }] }
Response: BackfillActualsResponse
```
**Note:** For testbed, fetch actuals from `ts_demand_daily` for dates after cutoff_date, then backfill

**Step 3: Get Quality Metrics (MAPE/Statistics)**
```
GET /api/v1/forecast/forecasts/quality/{item_id}?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
Response: QualityResponse { mape, mae, rmse, bias, sample_size }
```
**Note:** Call this for each method that was run (chronos-2, statistical_ma7, etc.)

**Step 4: Get Forecast Results for Charting**
```
Query forecast_results table directly or via ForecastService.get_forecast_results()
```

**Key Points:**
- ✅ **All endpoints already exist** - no new comparison endpoint needed!
- ✅ Use existing `QualityCalculator` service for MAPE/statistics
- ✅ Supports any models that were run (primary + baseline)
- ✅ Model names are dynamic, not hardcoded
- ✅ Testbed workflow: Generate → Backfill → Get Quality → Display

#### 3. Available Models Endpoint (NEW)
```
GET /api/v1/forecast/models

Response:
{
  "models": [
    { "id": "chronos-2", "name": "Chronos-2", "type": "ml" },
    { "id": "statistical_ma7", "name": "Moving Average (7-day)", "type": "statistical" },
    { "id": "sba", "name": "SBA", "type": "statistical" },
    { "id": "croston", "name": "Croston", "type": "statistical" },
    { "id": "min_max", "name": "Min/Max", "type": "statistical" }
  ]
}
```

#### 4. Test Bed History Endpoint (OPTIONAL)
```
GET /api/v1/forecast/testbed/history?limit=5

Response:
[
  {
    "cache_key": string,
    "cutoff_date": "YYYY-MM-DD",
    "horizon_days": number,
    "history_weeks": number,
    "item_id": number,
    "statistics_kumo": { "mape": number },
    "statistics_chronos": { "mape": number },
    "statistics": { "mape": number, "rmse": number },
    "data_version": string,
    "created_at": "ISO datetime"
  }
]
```

#### 5. Delete Test Bed Cache (OPTIONAL)
```
DELETE /api/v1/forecast/testbed/{cache_key}
```

#### 6. Date Range Endpoint
```
GET /api/v1/forecast/date-range

Response:
{
  "min_date": "YYYY-MM-DD" | null,
  "max_date": "YYYY-MM-DD" | null
}
```

#### 7. Top Products Endpoint (or modify existing)
```
GET /api/v1/products?limit=5&sort=sales_count&order=desc
```
Or add dedicated endpoint:
```
GET /api/v1/products/top?limit=5
```

---

## Implementation Steps

### Phase 1: Backend APIs (0.5-1 day)
1. **Create available models endpoint** (NEW)
   - File: `backend/api/forecast.py` (add new route)
   - Use `ModelFactory.list_models()` to get available models
   - Return model metadata (id, name, type)

2. **Create date range endpoint** (NEW)
   - Query `ts_demand_daily` for min/max dates per client
   - File: `backend/api/forecast.py` or `backend/api/inventory.py`

3. **Create helper endpoints for filter options** (NEW)
   - `GET /api/v1/products/categories` - Get unique categories (or extract from products endpoint)
   - **Note:** Locations and Suppliers already have endpoints (`GET /api/v1/locations`, `GET /api/v1/suppliers`)
   - Products endpoint already supports category/supplier/location filtering

4. **Create helper service for testbed** (NEW, OPTIONAL)
   - File: `backend/services/testbed_service.py`
   - Helper methods:
     - `fetch_actuals_from_history()` - Get actuals from ts_demand_daily for backfilling
     - `format_testbed_response()` - Format data for frontend charting
   - **Note:** Uses existing `QualityCalculator` and `ForecastService` - no duplication

5. **Testbed history** (OPTIONAL)
   - Can reuse `forecast_runs` table with filter for testbed runs
   - Or create separate endpoint if needed

**Note:** All filter endpoints already exist:
- Locations: `GET /api/v1/locations`
- Suppliers: `GET /api/v1/suppliers`
- Products: `GET /api/v1/products` (supports category, supplier_id, location_id filters)
- Categories: Can extract from products or create dedicated endpoint

**Key Point:** Most functionality already exists! We just need helper endpoints and utilities.

### Phase 2: Frontend Structure (1 day)
1. Create experiments directory structure
2. Create TypeScript types (`types/experiments.ts`)
3. Create composable (`composables/useExperiments.ts`)
4. Set up routing in Nuxt

### Phase 3: Main Experiments Page (0.5 day)
1. Create `pages/experiments/index.vue`
2. Implement tab navigation with Nuxt UI
3. Add URL hash routing
4. Remove client selector

### Phase 4: Test Bed Component (2-3 days)
1. Create `pages/experiments/testbed.vue`
2. **Implement Filter Section:**
   - Store/Location dropdown (All Stores + specific locations)
   - SKU/Product dropdown (All SKUs + specific products)
   - Category dropdown (All Categories + specific categories)
   - Supplier dropdown (All Suppliers + specific suppliers)
   - All using Nuxt UI `USelect` component
3. **Implement Forecast Configuration:**
   - Forecast Model dropdown - Call `GET /api/v1/forecast/models` to populate
   - Forecast Horizon input (number, default 30 days)
   - Display auto-calculated cutoff: "Cutoff will be auto-calculated as: max date - horizon days"
   - **DO NOT include covariates checkbox** (deferred to later)
4. **Implement Generate Button:**
   - "Generate Forecast & Compare" button (Nuxt UI Button)
   - Calculate cutoff_date = max_date - horizon_days
   - Apply all filters to get filtered item_ids:
     - If Store selected: Filter products by location_id in stock_levels
     - If SKU selected: Use specific item_id
     - If Category selected: Filter products by category
     - If Supplier selected: Filter products by supplier_id via product_supplier_conditions
   - Pass filtered item_ids to forecast request
5. **Generate forecast** - Call existing `POST /api/v1/forecast` endpoint with:
   - Filtered item_ids (based on filters)
   - Selected model as primary_model
   - include_baseline=true (to get baseline comparison)
   - prediction_length = horizon_days
6. **Backfill actuals** - Fetch from ts_demand_daily and call `POST /api/v1/forecast/forecasts/actuals`
7. **Get quality metrics** - Call `GET /api/v1/forecast/forecasts/quality/{item_id}` for each method
8. **Implement chart visualization (Chart.js) - COPY EXACT DESIGN**
   - Use exact chart configuration from "Chart Design & Functionality" section
   - **Dynamic data series** - render all models that were run (primary + baseline)
   - Model colors can be assigned dynamically or use a color mapping
   - Implement rolling average calculation function
   - Implement data preparation logic (null padding, date alignment)
   - Ensure tooltips, interactions, and legend match old design
   - **Do NOT hardcode model names** - use actual model names from API
9. Implement test history section (optional)
10. Add localStorage persistence
11. Add rolling average toggle
12. Connect to backend APIs

### Phase 5: ROI Calculator Component (1-2 days)
1. Create `pages/experiments/roi-calculator.vue`
2. Implement sliders (Nuxt UI Slider)
3. Implement calculation logic
4. **Implement charts (Chart.js) - COPY EXACT DESIGN**
   - Use exact chart configurations from "Chart Design & Functionality" section
   - Implement all 3 charts (Bar, Line, Bar) with exact styling
   - Implement currency formatting function (EUR, de-DE locale)
   - Ensure real-time updates as sliders change
   - Match tooltip formatting and axis labels
5. Add help section (Nuxt UI Accordion)
6. Add currency formatting

### Phase 6: Testing & Polish (1 day)
1. Test all functionality
2. Verify Nuxt UI component usage
3. Test responsive design
4. Verify client isolation (multi-tenant)
5. Update navigation/menu to include Experiments page

---

## Files to Create

### Backend
- `backend/services/testbed_service.py` - Testbed helper utilities (optional, for convenience)
  - Helper methods to fetch actuals from ts_demand_daily and format responses
  - **Uses existing** `QualityCalculator` and `ForecastService` - no duplication
- `backend/schemas/testbed.py` - Pydantic schemas for testbed endpoints (if needed)
- **Note:** Reuse existing:
  - `forecast_runs` and `forecast_results` tables
  - `QualityCalculator` service (MAPE, MAE, RMSE, Bias)
  - `POST /api/v1/forecast/forecasts/actuals` endpoint
  - `GET /api/v1/forecast/forecasts/quality/{item_id}` endpoint

### Frontend
- `frontend/app/pages/experiments/index.vue` - Main experiments page
- `frontend/app/pages/experiments/testbed.vue` - Test Bed component
- `frontend/app/pages/experiments/roi-calculator.vue` - ROI Calculator component
- `frontend/app/composables/useExperiments.ts` - Experiments composable
- `frontend/app/types/experiments.ts` - TypeScript types
- `frontend/server/api/forecast/testbed.post.ts` - Testbed API proxy
- `frontend/server/api/forecast/testbed/history.get.ts` - History API proxy
- `frontend/server/api/forecast/testbed/[key].delete.ts` - Delete cache proxy
- `frontend/server/api/forecast/date-range.get.ts` - Date range proxy

---

## Files to Modify

### Backend
- `backend/api/forecast.py` - Add models endpoint and date-range endpoint
- **Reuse existing endpoints:**
  - `POST /api/v1/forecast` - Forecast generation
  - `POST /api/v1/forecast/forecasts/actuals` - Backfill actuals
  - `GET /api/v1/forecast/forecasts/quality/{item_id}` - Get MAPE/statistics
- **Reuse existing services:**
  - `QualityCalculator` - MAPE/statistics calculations
  - `ForecastService` - Forecast generation and results

### Frontend
- `frontend/app/layouts/dashboard.vue` - Add Experiments to navigation (if needed)
- `frontend/server/api/products.get.ts` - Add top products support (if needed)

---

## Chart Design & Functionality

### Test Bed Charts - Exact Specifications

**Chart Type:** Line Chart (Chart.js)

**Chart Configuration:**
```typescript
{
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 3,
  scales: {
    y: { 
      beginAtZero: true, 
      title: { display: true, text: 'Order Count (7-day rolling)' },
      ticks: { precision: 0 }
    },
    x: { 
      title: { display: true, text: 'Time (Weeks)' },
      ticks: { maxRotation: 45, minRotation: 45 }
    }
  },
  plugins: {
    legend: { 
      display: true,
      position: 'top',
      labels: { padding: 15, usePointStyle: true }
    },
    title: { display: false },
    tooltip: {
      mode: 'index',
      intersect: false
    }
  },
  interaction: {
    mode: 'nearest',
    axis: 'x',
    intersect: false
  }
}
```

**Data Series (in order, dynamic based on available models):**

1. **Historical Data**
   - Label: `Historical (${weeks} weeks)`
   - Border Color: `rgb(107, 114, 128)` (gray-500)
   - Background Color: `rgba(107, 114, 128, 0.1)`
   - Point Radius: `3`
   - Point Style: `'circle'`
   - Tension: `0.1`
   - Border Width: `2`

2. **Rolling Average** (conditional - only if toggle enabled)
   - Label: `${window}-day Rolling Average`
   - Border Color: `rgb(59, 130, 246)` (blue-500)
   - Background Color: `rgba(59, 130, 246, 0.1)`
   - Point Radius: `0` (no points)
   - Point Style: `'circle'`
   - Tension: `0.3`
   - Border Width: `2`
   - Border Dash: `[3, 3]` (dashed line)
   - Fill: `false`

3. **Primary Model Forecast** (e.g., chronos-2, or whatever is selected)
   - Label: `${modelName} Forecast (${horizon_days}-day) - MAPE: ${mape}%` (if MAPE available)
   - Border Color: `rgb(20, 184, 166)` (teal-500) - or dynamic based on model
   - Border Dash: `[5, 5]` (dashed line)
   - Background Color: `rgba(20, 184, 166, 0.1)`
   - Point Radius: `4`
   - Point Style: `'circle'`
   - Tension: `0.1`
   - Border Width: `2`

4. **Baseline Model Forecast** (e.g., statistical_ma7, if include_baseline=true)
   - Label: `${modelName} Forecast (${horizon_days}-day) - MAPE: ${mape}%` (if MAPE available)
   - Border Color: `rgb(236, 72, 153)` (pink-500) - or different color for baseline
   - Border Dash: `[5, 5]` (dashed line)
   - Background Color: `rgba(236, 72, 153, 0.15)`
   - Point Radius: `4`
   - Point Style: `'circle'`
   - Tension: `0.1`
   - Border Width: `2.5`

**Note:** Model names and colors should be dynamic based on available models. The system supports:
- `chronos-2` (primary ML model)
- `statistical_ma7` (baseline)
- `sba`, `croston`, `min_max` (other statistical models)

Display all models that were run (primary + baseline if enabled).

5. **Actual Ground Truth**
   - Label: `Actual Ground Truth (${horizon_days}-day)`
   - Border Color: `rgb(0, 0, 0)` (black)
   - Background Color: `rgba(0, 0, 0, 0.2)`
   - Point Radius: `5`
   - Point Style: `'rect'` (square points)
   - Tension: `0.1`
   - Border Width: `2`

**Data Preparation Logic:**
- Historical data: Full array of values, null-padded at end to match forecast length
- Rolling average: Calculated with `calculateRollingAverage()` function, null-padded at end
- Forecast data: Null-padded at start (to align with historical), then forecast values
- Actual data: Null-padded at start (to align with historical), then actual values
- Labels: Combined dates from all series, formatted as ISO date strings (YYYY-MM-DD)

**Rolling Average Calculation:**
```typescript
function calculateRollingAverage(values: number[], window: number): (number | null)[] {
  const result: (number | null)[] = []
  for (let i = 0; i < values.length; i++) {
    if (i < window - 1) {
      result.push(null) // Not enough data points
    } else {
      const sum = values.slice(i - window + 1, i + 1).reduce((a, b) => a + b, 0)
      result.push(sum / window)
    }
  }
  return result
}
```

**Chart Features:**
- Multiple data series on same chart (dynamic based on models run)
- Null values properly handled (gaps in lines)
- Tooltip shows all series values at same x-axis point
- Hover highlights nearest point across all series
- Legend shows all series with point style indicators
- X-axis dates rotated 45 degrees for readability
- Model names in legend are dynamic (use actual model names from system, not hardcoded)

---

### ROI Calculator Charts - Exact Specifications

**Chart 1: Cost Comparison (Bar Chart)**
```typescript
{
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 4,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => formatCurrency(value) // EUR formatting
      }
    }
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: any) => formatCurrency(context.parsed.y)
      }
    }
  }
}
```

**Data:**
- Labels: `[`Current (${baselineMape}% error)`, `Improved (${modelMape}% error)`]`
- Dataset:
  - Background Colors: `['rgba(239, 68, 68, 0.7)', 'rgba(34, 197, 94, 0.7)']` (red, green)
  - Border Colors: `['rgb(239, 68, 68)', 'rgb(34, 197, 94)']`
  - Border Width: `2`

**Chart 2: Savings Curve (Line Chart)**
```typescript
{
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 5,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => formatCurrency(value)
      }
    },
    x: {
      title: {
        display: true,
        text: 'Forecast Error (%)'
      }
    }
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: any) => `Savings: ${formatCurrency(context.parsed.y)}`
      }
    }
  }
}
```

**Data:**
- Labels: Accuracy range from 5% to baselineMape + 5% (in 1% increments)
- Dataset:
  - Border Color: `rgb(59, 130, 246)` (blue-500)
  - Background Color: `rgba(59, 130, 246, 0.1)`
  - Tension: `0.4`
  - Fill: `true`

**Chart 3: Savings Breakdown (Bar Chart)**
```typescript
{
  responsive: true,
  maintainAspectRatio: true,
  aspectRatio: 4.5,
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        callback: (value: any) => formatCurrency(value)
      }
    }
  },
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (context: any) => formatCurrency(context.parsed.y)
      }
    }
  }
}
```

**Data:**
- Labels: `['Current', 'Your Target', 'Even Better', 'Best Case']` (with accuracy %)
- Dataset:
  - Background Color: `rgba(59, 130, 246, 0.7)`
  - Border Color: `rgb(59, 130, 246)`
  - Border Width: `2`

**Currency Formatting:**
```typescript
function formatCurrency(value: number): string {
  return new Intl.NumberFormat('de-DE', { 
    style: 'currency', 
    currency: 'EUR',
    maximumFractionDigits: 0
  }).format(value)
}
```

**Chart Behavior:**
- All charts update in real-time as sliders change
- Tooltips show formatted currency values
- Charts are responsive and maintain aspect ratios
- Y-axis scales start at zero for proper comparison

---

## Design Considerations

### Nuxt UI Component Mapping

| Old Component | New Nuxt UI Component |
|--------------|----------------------|
| Custom Card | `UCard` |
| Custom Button | `UButton` |
| Custom Input | `UInput` |
| Custom Select | `USelect` |
| Custom Checkbox | `UCheckbox` |
| Custom Tabs | `UTabs` |
| Custom Slider | `USlider` |
| Custom Accordion | `UAccordion` or `UDisclosure` |
| Custom Alert | `UAlert` |

### Charts
- Keep Chart.js (already configured)
- Use `vue-chartjs` components
- **CRITICAL: Copy exact chart design and functionality**
  - Test Bed: 5 data series with exact colors, line styles, point styles, and interactions
  - ROI Calculator: 3 charts with exact configurations, currency formatting, and real-time updates
  - See "Chart Design & Functionality" section for complete specifications
  - All chart options, tooltips, legends, and interactions must match old project exactly

### Client Selection
- **REMOVE**: Client selector component
- Client is already selected via authentication/JWT
- All API calls automatically use current client context

---

## Testing Checklist

- [ ] Test Bed generates forecasts correctly
- [ ] Test Bed displays charts with all data series
- [ ] Test Bed history loads and displays correctly
- [ ] Test Bed history delete works
- [ ] Test Bed localStorage persistence works
- [ ] ROI Calculator calculations are correct
- [ ] ROI Calculator charts display correctly
- [ ] ROI Calculator sliders work smoothly
- [ ] Tab navigation works with URL hashes
- [ ] Client isolation works (multi-tenant)
- [ ] Responsive design works on mobile
- [ ] All Nuxt UI components render correctly
- [ ] Error handling works (network errors, validation errors)

---

## Migration Notes

### Differences from Old Project

1. **No Client Selector**: Client is already selected via authentication
2. **Nuxt UI Components**: Use Nuxt UI instead of custom components
3. **Composables Pattern**: Use composables instead of direct API calls
4. **TypeScript**: Full TypeScript support (old project had some JS)
5. **Nuxt 3**: Use Nuxt 3 patterns (auto-imports, `<script setup>`, etc.)
6. **Server Routes**: Use Nuxt server routes for API proxying

### Preserved Functionality

1. **Test Bed**: All features preserved (charts, history, rolling average)
2. **ROI Calculator**: All calculations and visualizations preserved
3. **Chart Styling**: Maintain same Chart.js styling
4. **User Experience**: Same UX flow and interactions

---

## Future Enhancements (Post-Migration)

### Phase 1: Covariates Support (Deferred)

1. **Covariates Checkbox**: Add "Use Covariates (Promo, Holiday, Weekend)" checkbox
   - Enable promo flags, holidays, weekends in forecast generation
   - Requires backend support for covariates in forecast endpoint
   - Deferred to later phase as requested

2. **Chart Options for Covariates**: Add chart visualization options
   - **Show Promotions (promo_flag)**: Toggle vertical orange shaded regions on chart
   - **Show Holidays (holiday_flag)**: Toggle vertical purple shaded regions on chart
   - **Show Weekends (is_weekend)**: Toggle faint gray vertical lines on chart
   - **Show Stockouts (0 sales)**: Highlight periods with zero sales
   - **Show Rolling Average Window**: Dropdown selector (3, 7, 14, 30 days)
   - All options should be checkboxes/toggles with default values (all enabled)
   - Chart should render vertical shaded regions for promotions/holidays
   - Chart should render faint vertical lines for weekends
   - Stockout detection: Identify periods with 0 sales and highlight them

3. **Chart Enhancements for Covariates**:
   - **Vertical shaded regions** (using Chart.js annotation plugin):
     - **Promotions**: Orange vertical boxes (`rgba(251, 146, 60, 0.15)` background, `rgba(251, 146, 60, 0.3)` border)
       - Label: "Promo" (rotated -90°, orange color `#f97316`)
       - Spans consecutive days with `promo_flag = 1`
     - **Holidays**: Purple vertical boxes (`rgba(168, 85, 247, 0.2)` background, `rgba(168, 85, 247, 0.4)` border)
       - Label: "Holiday" (rotated -90°, purple color `#a855f7`)
       - Single day boxes for each `holiday_flag = 1`
     - **Weekends**: Light gray vertical boxes (`rgba(203, 213, 225, 0.3)` background, `rgba(203, 213, 225, 0.5)` border)
       - No label, just visual indicator
       - Single day boxes for each `is_weekend = 1`
     - **Stockouts**: Red vertical boxes (`rgba(239, 68, 68, 0.2)` background, `rgba(239, 68, 68, 0.4)` border)
       - Label: "Stockout" (red color `#ef4444`)
       - Spans consecutive periods with 0 sales
   - **Interactive chart features**:
     - Zoom: Drag to zoom, scroll to zoom
     - Pan: Ctrl + Drag to pan
     - Crosshair: Vertical line on hover showing all series values (custom plugin)
     - Reset Zoom button: Reset chart zoom/pan to default view
   - **Cutoff line**: Vertical dashed red line (`#ef4444`, `borderDash: [5, 5]`)
     - Label: "Cutoff: YYYY-MM-DD" (positioned at start, red color)
   - **Performance metrics display**: Top-right corner showing:
     - MAPE (pink pill badge, e.g., "12.9%")
     - RMSE (e.g., "11.03")
     - MAE (e.g., "8.52")
     - Summary: "Actual: 68.0 avg (47-108) | Forecast: 71.6 avg (56-101) | 30 days compared"
   - **Chart summary info**: Top-left showing:
     - "Historical Days: 700"
     - "Forecast Days: 30"
     - "Actual (Ground Truth): 30 days"

**Implementation Notes:**
- Chart options component: `CovariateToggles.vue` (from old project) - adapt to Nuxt UI `UCheckbox` and `USelect`
- Chart component: `ForecastChartWithCutoff.vue` (from old project) - adapt to Nuxt UI styling
- **Chart.js plugins required**:
  - `chartjs-plugin-annotation` - For vertical shaded regions (boxes) and cutoff line
  - `chartjs-plugin-zoom` - For zoom/pan functionality
  - Custom crosshair plugin - For vertical line on hover (copy from old project)
- **Chart Options Interface**:
  ```typescript
  interface CovariateSettings {
    showPromo: boolean        // Default: true
    showHoliday: boolean      // Default: true
    showWeekend: boolean      // Default: true
    showRollingAverage: boolean // Default: true
    showStockout: boolean     // Default: true
    rollingWindow: number     // Default: 7 (3, 7, 14, 30 options)
  }
  ```
- **Chart rendering details**:
  - Use Chart.js annotation plugin `box` type for all vertical regions
  - Promotions: Detect consecutive days with `promo_flag = 1`, create single box spanning all
  - Holidays: Create individual box for each day with `holiday_flag = 1`
  - Weekends: Create individual box for each day with `is_weekend = 1`
  - Stockout detection: Use `detectStockouts()` function to identify consecutive 0 sales periods
    - Detects consecutive days with `value === 0`
    - Calculates estimated lost sales based on rolling average before stockout
    - Returns `StockoutStats` with periods, total days, estimated lost sales
  - All options toggle chart elements on/off dynamically via `props.settings`
  - Labels positioned at top of chart with rotation for narrow bands
- **Stockout Detection Utility**:
  - File: `utils/stockoutDetection.ts` (copy from old project)
  - Function: `detectStockouts(historicalData, actualData, allDates, rollingWindow)`
  - Returns: `StockoutStats` with periods array and statistics
  - Used to highlight periods with zero sales on chart

### Phase 2: Additional Features

4. **TestbedCovariate**: Migrate covariate test bed if needed
5. **Talk to Data**: Migrate if needed
6. **API Integrations**: Migrate if needed
7. **Marketing Campaigns**: Already exists in old project, evaluate if needed

---

## References

- Old Project: `/Users/mihapro/Development/ecommerce/old/ecommerce-agent`
- Nuxt UI Docs: Use MCP tools to access component documentation
- Chart.js Docs: https://www.chartjs.org/
- Current Project: `/Users/mihapro/Development/ecommerce/forecaster_enterprise`

---

---

## ✅ Implementation Status (Updated 2025-12-18)

### Phase 1: Core Features - **COMPLETED** ✅

1. ✅ **Test Bed Page** (`/experiments/testbed`)
   - Forecast vs Actual comparison chart
   - Model comparison table with quality metrics
   - SKU classification display
   - System recommendation indicators
   - Rolling average visualization
   - Zoom and pan controls
   - All forecast methods comparison (run_all_methods flag)
   - In-memory quality metrics calculation (skip_persistence flag)

2. ✅ **ROI Calculator Page** (`/experiments/roi-calculator`)
   - Cost-benefit analysis
   - Interactive sliders for parameters
   - Chart visualization

3. ✅ **Backend Support**
   - `run_all_methods` flag for running all available models
   - `skip_persistence` flag for Test Bed verification (no DB writes)
   - `training_end_date` parameter for backtesting
   - SKU classification integration
   - Quality metrics calculation

4. ✅ **Documentation**
   - Test Bed System Validation guide
   - Forecast Method Comparison Analysis
   - Inventory Ordering Guide
   - Metrics Best Practices

### Phase 2: Future Enhancements

- [ ] Covariate support (deferred as planned)
- [ ] Additional chart options for covariates
- [ ] Stockout detection visualization

**Document Owner:** Development Team  
**Status:** Phase 1 Complete - Ready for Production

