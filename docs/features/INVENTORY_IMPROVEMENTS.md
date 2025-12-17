# Inventory Page Improvements - Feature Plan

**Last Updated:** 2025-01-27  
**Status:** Planning Phase  
**Scope:** Inventory management UI/UX improvements

---

## User Goal

**Primary task:** "Find products that need attention and take action quickly"

Users come to the inventory page to:
1. See which products need ordering (understocked, at risk, stockout)
2. Review overall inventory health
3. Take action (add to cart, export, view details)

---

## Current State

- ✅ Basic inventory table with AG Grid
- ✅ Product listing with SKU, category, stock, cost
- ✅ Basic filtering and sorting
- ✅ View and Cart actions per row
- ❌ No status tabs/filters
- ❌ No cart indicator
- ❌ No bulk actions
- ❌ No export

---

## Feature Plan

### 0. Header: Last Sync Date Indicator

**Goal:** Show when data was last synchronized from external sources

**Features:**
- [ ] **Last Sync Indicator in Header:**
  - Display: "Last sync: 2 hours ago" or "Last sync: Dec 17, 2024 14:30"
  - Location: Top right of header (next to user menu, before cart badge)
  - Format: Relative time ("2 hours ago") or absolute ("Dec 17, 14:30")
  - Color: Gray (neutral, informational)
  - Icon: Clock/sync icon (🕐 or 🔄)

- [ ] **What to Show:**
  - **Option 1:** Most recent `updated_at` from synced tables
    - Check: `products.updated_at`, `stock_levels.updated_at`, `ts_demand_daily` (max date)
    - Show most recent across all data types
  - **Option 2:** Last ETL sync timestamp (if tracked)
    - Track last successful ETL sync in settings or separate table
    - More accurate for "when was data synced from external source"

- [ ] **Tooltip:**
  - Hover shows: "Data last synchronized from external source"
  - Show breakdown: "Products: 2h ago, Stock: 1h ago, Sales: 3h ago"

- [ ] **Refresh Indicator:**
  - Show "Syncing..." when ETL sync is in progress
  - Update automatically after sync completes

**UI Design:**
```
Header:
  [Logo] [Dashboard] [Inventory] ...    [🕐 Last sync: 2h ago] [Cart: 3] [User Menu]
```

**Implementation:**
- Add to `Header.vue` component (global, visible on all pages)
- Create `LastSyncIndicator.vue` component
- API: `GET /api/v1/monitoring/last-sync` (needs to be created)
  - Returns: `{ last_sync: "2024-12-17T14:30:00Z", data_types: { products: "...", stock: "...", sales: "..." } }`
- Or calculate client-side from product/stock `updated_at` timestamps
- Use relative time library (e.g., `date-fns` formatDistance)

**Backend Implementation Options:**
1. **Query most recent `updated_at` from synced tables:**
   ```sql
   SELECT MAX(updated_at) FROM (
     SELECT MAX(updated_at) FROM products WHERE client_id = ? AND is_synced = true
     UNION ALL
     SELECT MAX(updated_at) FROM stock_levels WHERE client_id = ?
     UNION ALL
     SELECT MAX(date_local) FROM ts_demand_daily WHERE client_id = ?
   )
   ```

2. **Track ETL sync timestamps:**
   - Add `last_sync_timestamp` to `ClientSettings` or create `sync_log` table
   - Update on successful ETL sync

---

### 1. Status Tabs (Quick Filters)

**Goal:** One-click access to common inventory views

**Backend Already Provides These Statuses:**
| Status Value | Condition | Configurable |
|--------------|-----------|--------------|
| `out_of_stock` | Stock = 0 | No |
| `understocked` | DIR < threshold | Yes (default: 14 days) |
| `normal` | DIR within range | Yes |
| `overstocked` | DIR > threshold | Yes (default: 90 days) |
| `dead_stock` | No sales for X days | Yes (default: 90 days) |
| `unknown` | No DIR data | No |

**API Filter:** `GET /api/v1/products?status=understocked`

**Tabs (using backend statuses):**
| Tab | Filter Value | Description |
|-----|--------------|-------------|
| **All** | (none) | All products |
| **Needs Action** | `understocked,out_of_stock` | Products requiring ordering |
| **Healthy** | `normal` | Good stock levels |
| **Overstocked** | `overstocked` | Too much inventory |
| **Problems** | `dead_stock,unknown` | Dead stock or missing data |

**UI Design:**
```
[All 50] [Needs Action 22] [Healthy 18] [Overstocked 8] [Problems 2]
```

**UX Notes:**
- Each tab shows count badge
- Active tab highlighted (brand accent color)
- Tabs persist in URL (`?status=needs-action`)
- "Needs Action" combines `understocked` + `out_of_stock` from backend

**Implementation:**
- Use Nuxt UI tabs component
- Call API with `status` filter parameter
- Backend already supports comma-separated status values
- **Counts:** Use `GET /api/v1/dashboard` for `understocked_count`, `overstocked_count`, `total_skus`
  - Missing: `normal_count`, `dead_stock_count` (calculate client-side or extend dashboard API)

---

### 2. Status Column & Indicators

**Goal:** Instant visual understanding of product health

**Status Badge (one per row):**
| Backend Status | Display | Color | Badge |
|----------------|---------|-------|-------|
| `out_of_stock` | Stockout | Red | 🔴 |
| `understocked` | Low Stock | Orange | 🟠 |
| `normal` | OK | Green | 🟢 |
| `overstocked` | Excess | Yellow | 🟡 |
| `dead_stock` | Dead Stock | Gray | ⚫ |
| `unknown` | Unknown | Light Gray | ⚪ |

**Days Left Column:**
- Show days until stockout (e.g., "13 days")
- Show stockout date (e.g., "Dec 04")
- Color-coded by urgency
- Tooltip with details (daily sales rate, forecast)

**UI Design:**
```
Status      Days Left
[🟠 At Risk]  13 days (Dec 04)
[🔴 Stockout] 0 days
[🟢 OK]       45 days (Jan 15)
```

**Implementation:**
- `ProductStatusBadge.vue` component
- Status calculated from DIR vs thresholds
- Tooltip with expanded details

---

### 3. Product Actions

**Goal:** Fast actions on products — single or bulk

#### Row Actions (per product):
- **View** — Open product detail modal/page
- **Cart** — Add to cart (changes to "✓ In Cart" if already added)
- **More** — Dropdown: View Forecast, Edit, View History

#### Cart Indicator:
- Show "✓" or cart icon when product is in cart
- Show quantity if already in cart (e.g., "3 in cart")
- Change "Add to Cart" button to "Remove" when in cart

#### Bulk Actions:
- Checkbox column for multi-select
- Selection toolbar appears when rows selected:
  ```
  [5 selected] [Add to Cart] [Export Selected] [Clear Selection]
  ```
- Select all/none toggle

#### Cart Badge (Header):
- Show total items in cart (e.g., badge with "3")
- Click navigates to cart page
- Updates in real-time

**Implementation:**
- AG Grid row selection
- `BulkActionsToolbar.vue` — appears on selection
- `CartIndicator.vue` — in-row indicator
- Cart state via composable (`useCart`)

---

### 4. Export

**Goal:** Export inventory data for analysis

**Features:**
- Export button in toolbar
- Export current filtered view
- Dropdown: "Export to Excel", "Export to CSV"
- Include visible columns only
- Filename: `inventory_YYYY-MM-DD.xlsx`

**Bulk Export:**
- Export selected rows only (when rows selected)
- "Export Selected (5)" button in bulk toolbar

**Implementation:**
- Use `xlsx` library (free, MIT license) for Excel
- Native CSV generation
- Client-side generation (no API needed)

---

### 5. Column Management

**Goal:** Users customize which columns they see

**Default Columns (6-7):**
1. SKU / Product Name
2. Category
3. Status (badge)
4. Stock
5. Days Left
6. Supplier
7. Actions

**Additional Columns (toggle on):**
- Unit Cost
- Inventory Value
- ABC Classification
- Lead Time
- MOQ
- Location breakdown

**Column Toggle:**
- "Columns" button in toolbar
- Dropdown with checkboxes
- Save preferences to localStorage
- "Reset to Default" option

**Implementation:**
- AG Grid column visibility API
- `ColumnVisibilityDropdown.vue` component
- **Persist via existing API:**
  - `GET /api/v1/me/preferences` — Load saved columns
  - `PUT /api/v1/me/preferences` — Save column selection
  - Structure: `{ "inventory_columns": ["sku", "status", "stock", ...] }`
  - Syncs across devices (already implemented!)

---

### 6. Enhanced Product Info

**Goal:** Show key details without leaving the table

**Expandable Cells:**
- **Supplier:** "Supplier 2 Primary | MOQ: 15 | Lead: 6d"
  - Expandable: "► Show 1 more" for multiple suppliers
- **Location:** "Main Warehouse: 167"
  - Expandable: "► Show 1 more" for multiple locations

**ABC Classification:**
- Badge in optional column (A/B/C)
- Color: A=green, B=yellow, C=gray
- **API:** `GET /api/v1/skus/{item_id}/classification` (already exists!)
  - Returns: `abc_class`, `xyz_class`, `demand_pattern`, `forecastability_score`
- Tooltip: Show full classification details (ABC, XYZ, demand pattern)

**Inventory Value:**
- Calculated: Stock × Unit Cost
- Format: "€2,920"
- Sortable

---

### 7. Product Detail Page (SKU View)

**Goal:** Comprehensive view of a single product with history and forecasts

**Route:** `/inventory/[item_id]` or `/products/[item_id]`

**Navigation:**
- Click on product row in inventory table → Opens detail page
- "View" action button in row → Opens detail page
- Back button → Returns to inventory list

**Page Sections:**

#### 7.1 Product Information Card
- **Header:** Product name + Status badge (Critical/Warning/OK/Unknown)
- **Details Grid (read-only or editable):**
  - SKU / Item ID
  - Category
  - Current Stock
  - Unit Cost
  - Days of Inventory Remaining (DIR)
  - Stockout Risk (%)
  - ABC Classification (A/B/C badge)
  - XYZ Classification
  - Demand Pattern (Regular/Intermittent/Lumpy)

#### 7.2 Supplier Information
- Primary supplier name, contact
- MOQ, Lead Time
- Secondary suppliers (expandable)
- "Add to Cart" button with suggested quantity

#### 7.3 Stock per Location (if multi-location)
- Table: Location | Stock Qty | Status
- Per-location status badges

#### 7.4 History & Forecast Chart ⭐
**Key feature from testbed — most important visualization**

- **Chart Type:** Line chart (Chart.js or Highcharts)
- **Data Series:**
  - 📈 **Historical Sales** (solid blue line) — Daily `units_sold` from `ts_demand_daily`
  - 📉 **Inventory Level** (solid gray/blue area) — Historical stock levels
  - 🔮 **Forecast** (dashed red/orange line) — Future predictions from `forecast_results`
  - 📊 **Rolling Average** (dashed purple line, optional) — 7-day moving average
  - 🎯 **Reorder Point** (horizontal dashed line) — Threshold indicator

- **Time Range Selector:**
  - Buttons: 30d | 60d | 90d | 1 Year | All
  - Chart updates on selection
  - Default: 90 days

- **Covariate Overlays (optional):**
  - Promotion periods (orange bands)
  - Holiday periods (purple bands)
  - Weekend shading (light gray)
  - Stockout periods (red bands with "Stockout" label)

- **Interactivity:**
  - Zoom: Scroll wheel or drag-select
  - Pan: Ctrl + drag
  - Hover tooltip: Date, Sales, Stock, Forecast value
  - "Reset Zoom" button

- **Stockout Detection:**
  - Highlight periods with zero/low sales + low stock
  - Show estimated lost sales badge
  - Example: "Stockout: 5 days | Est. lost: 120 units"

**UI Design:**
```
┌─ History & Forecast ───────────────────────────────────────┐
│  [30d] [60d] [90d] [1Y] [All]           [Reset Zoom]       │
│                                                            │
│  Units                                                     │
│   ▲                                                        │
│  100│     ╭──╮                    ╭╮    ┊ ┊ ┊  (forecast)  │
│   75│   ╭─╯  ╰──╮    ╭───╮      ╭╯ ╰╮   ┊ ┊ ┊              │
│   50│ ╭─╯       ╰──╭─╯   ╰──╮╭──╯    ╰──┊─┊─┊───           │
│   25│─╯            │        ╰╯         ┊ ┊ ┊               │
│    0├─────────────────────────────────────────────► Date   │
│     Oct         Nov         Dec         Jan (forecast)     │
│                                                            │
│  ─── Actual Sales  ─ ─ Forecast  ─ ─ Reorder Point         │
│  █ Stockout Period  █ Promo Period                         │
└────────────────────────────────────────────────────────────┘
```

#### 7.5 Monthly Sales Summary Table
- Aggregated monthly data
- Columns: Month | Total Sales | Revenue | Avg Price | Days with Sales
- Totals row at bottom

#### 7.6 Actions
- **Add to Cart** — With suggested quantity
- **Edit Product** — Modal or inline editing
- **View Purchase Orders** — Link to POs for this product
- **Export History** — Download CSV of historical data

**Implementation:**

**New Files:**
- `app/pages/inventory/[item_id].vue` — Product detail page
- `app/components/inventory/ProductHistoryChart.vue` — History + Forecast chart
- `app/components/inventory/ProductInfoCard.vue` — Product information card
- `app/components/inventory/MonthlySalesTable.vue` — Monthly aggregation table

**APIs Needed:**
- ✅ `GET /api/v1/products/{item_id}` — Product details (already exists)
- ✅ `GET /api/v1/skus/{item_id}/classification` — ABC/XYZ classification (already exists)
- 🆕 `GET /api/v1/products/{item_id}/history` — Historical sales data
  - Returns: `[{ date, units_sold, stock_level, promo_flag, holiday_flag }]`
  - Query params: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- ✅ `GET /api/v1/forecasts/sku/{item_id}` — Forecast data (already exists)
  - Returns: `[{ date, point_forecast, lower_bound, upper_bound }]`

**Chart Libraries:**
- **Option 1:** Chart.js (already in project) + chartjs-plugin-zoom + chartjs-plugin-annotation
- **Recommendation:** Chart.js (already used, free, sufficient)

---

## UI/UX Guidelines

### Visual Hierarchy
1. **Status tabs** — Top, most prominent
2. **Search + Toolbar** — Below tabs
3. **Table** — Main content area
4. **Bulk toolbar** — Appears on selection (sticky bottom or top)

### Color Coding
- Use status colors consistently (red=bad, green=good)
- Subtle row highlighting for status (optional)
- Don't overwhelm — color for emphasis, not decoration

### Progressive Disclosure
- Start with minimal columns
- Let users add complexity via "Columns" toggle
- Tooltips for detailed info
- Expandable cells for multi-value fields

### Performance
- Virtual scrolling for large datasets (AG Grid built-in)
- Lazy load expanded details
- Debounce search input

---

## Implementation Phases

### Phase 1: Core (Week 1)
**Priority: High**

- [ ] Last sync date indicator in header (global component)
- [ ] Status tabs (All, Needs Action, Healthy, Overstocked, Problems)
  - Backend already provides: `status` field and `?status=` filter
- [ ] Status badge column
- [ ] Days Left column
- [ ] Cart indicator on products
- [ ] Cart badge in header

### Phase 2: Actions (Week 2)
**Priority: High**

- [ ] Bulk selection (checkbox column)
- [ ] Bulk actions toolbar
- [ ] Bulk "Add to Cart"
- [ ] Excel/CSV export
- [ ] Export selected rows

### Phase 3: Polish (Week 3)
**Priority: Medium**

- [ ] Column visibility toggle
- [ ] Expandable supplier/location cells
- [ ] ABC classification column
- [ ] Inventory value column
- [ ] Save column preferences

### Phase 4: Product Detail Page (Week 4)
**Priority: High**

- [ ] Create product detail page (`app/pages/inventory/[item_id].vue`)
- [ ] Product information card with status badge
- [ ] Supplier information section
- [ ] History & Forecast chart ⭐
  - Historical sales line
  - Inventory level area
  - Forecast line (dashed)
  - Reorder point line
  - Stockout period highlighting
- [ ] Time range selector (30d/60d/90d/1Y/All)
- [ ] Chart zoom/pan capabilities
- [ ] Monthly sales summary table
- [ ] Navigation from inventory table row click
- [ ] 🆕 Backend: `GET /api/v1/products/{item_id}/history` endpoint

**Deliverables:**
- Full product detail page
- Interactive history + forecast chart
- Drill-down from inventory table

---

## Technical Notes

### Components
| Component | Purpose |
|-----------|---------|
| `LastSyncIndicator.vue` | Last sync date in header (global) |
| `InventoryStatusTabs.vue` | Tab navigation with counts |
| `ProductStatusBadge.vue` | Status badge (OK, At Risk, etc.) |
| `CartIndicator.vue` | In-row cart status |
| `BulkActionsToolbar.vue` | Selection actions |
| `ExportDropdown.vue` | Export options |
| `ColumnVisibilityDropdown.vue` | Column toggle |
| **Product Detail Page:** | |
| `ProductInfoCard.vue` | Product information with status |
| `ProductHistoryChart.vue` | History + Forecast chart (Chart.js) |
| `MonthlySalesTable.vue` | Monthly aggregation table |
| `TimeRangeSelector.vue` | 30d/60d/90d/1Y/All buttons |

### API Status

**Already Implemented — Products:**
- ✅ `GET /api/v1/products` — Full metrics: `status`, `dir`, `stockout_risk`, `inventory_value`
- ✅ `GET /api/v1/products?status=understocked` — Filter by status
- ✅ `GET /api/v1/products?search=&category=&supplier_id=&location_id=` — All filters
- ✅ `GET /api/v1/products?min_dir=&max_dir=&min_risk=&max_risk=` — Range filters
- ✅ `GET /api/v1/products?sort=dir&order=asc` — Sorting
- ✅ `GET /api/v1/products/{item_id}` — Product detail with all metrics
- ✅ `GET /api/v1/products/{item_id}/suppliers` — All suppliers for product

**Already Implemented — Dashboard (status counts!):**
- ✅ `GET /api/v1/dashboard` — Returns:
  - `metrics.understocked_count` — Count for "Needs Action" tab
  - `metrics.overstocked_count` — Count for "Overstocked" tab
  - `metrics.total_skus` — Count for "All" tab
  - `top_understocked[]` — Top products needing action
  - `top_overstocked[]` — Top overstocked products

**Already Implemented — SKU Classification:**
- ✅ `GET /api/v1/skus/{item_id}/classification` — Returns:
  - `abc_class` (A/B/C)
  - `xyz_class` (X/Y/Z)
  - `demand_pattern` (regular, intermittent, lumpy, seasonal)
  - `forecastability_score` (0-100)
  - `recommended_method` (ARIMA, ETS, etc.)

**Already Implemented — User Preferences:**
- ✅ `GET /api/v1/me/preferences` — Get user preferences
- ✅ `PUT /api/v1/me/preferences` — Save user preferences (for column visibility!)

**Already Implemented — Cart:**
- ✅ `GET /api/v1/order-planning/cart` — Get cart items
- ✅ `POST /api/v1/order-planning/cart/add` — Add single item to cart

**Already Implemented — Order Suggestions:**
- ✅ `GET /api/v1/order-planning/suggestions` — AI-powered order suggestions
  - `suggested_quantity`, `stockout_risk`, `reason`
  - Based on forecast + stock + lead time

**Already Implemented — Forecasts:**
- ✅ `GET /api/v1/forecasts/sku/{item_id}` — Forecast data for product
  - Returns: `[{ date, point_forecast, lower_bound, upper_bound, method }]`

**Needs Implementation:**
- [ ] `GET /api/v1/products` — Add `in_cart` field to response
- [ ] `POST /api/v1/order-planning/cart/bulk-add` — Bulk add to cart
- [ ] Status counts for all statuses (dashboard only has understocked/overstocked counts)
- [ ] `GET /api/v1/monitoring/last-sync` — Last sync timestamp (optional, can calculate client-side)
- [ ] 🆕 `GET /api/v1/products/{item_id}/history` — **Product history for chart**
  - Returns: `[{ date, units_sold, stock_level, promo_flag, holiday_flag, is_weekend }]`
  - Query params: `?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&limit=365`
  - Source: `ts_demand_daily` table (already has this data!)

### Response Schema

**Already in Backend Response (ProductResponse):**
```typescript
interface ProductResponse {
  // Core fields
  id: string;
  client_id: string;
  item_id: string;
  sku: string | null;
  product_name: string;
  category: string;
  unit_cost: number;
  safety_buffer_days: number | null;
  
  // Metrics (already computed!)
  current_stock: number;
  dir: number | null;           // Days of Inventory Remaining
  stockout_risk: number | null; // 0-100 risk score
  inventory_value: number;
  status: 'out_of_stock' | 'understocked' | 'normal' | 'overstocked' | 'dead_stock' | 'unknown';
  using_forecast: boolean;      // True if forecast data used
  
  // Relations (already included!)
  suppliers: SupplierSummary[]; // All suppliers with MOQ, lead time
  locations: LocationStockSummary[]; // Stock per location
  
  // Legacy (deprecated)
  primary_supplier_name: string | null;
  primary_supplier_moq: number | null;
  primary_supplier_lead_time_days: number | null;
}
```

**Separate Endpoint for Classification (already exists):**
```typescript
// GET /api/v1/skus/{item_id}/classification
interface SKUClassificationInfo {
  abc_class: 'A' | 'B' | 'C';
  xyz_class: 'X' | 'Y' | 'Z';
  demand_pattern: 'regular' | 'intermittent' | 'lumpy' | 'seasonal';
  forecastability_score: number; // 0-100
  recommended_method: string;
  expected_mape_range: [number, number];
  warnings: string[];
}
```

**Only Need to Add:**
```typescript
// Add to ProductResponse:
in_cart: boolean;       // Check against cart
cart_quantity?: number; // Quantity in cart
// Optional: inline abc_class for list view performance
```

---

## Success Metrics

- ✅ User can find "needs action" products in 1 click
- ✅ User can see product status at a glance
- ✅ User can bulk add to cart in 3 clicks
- ✅ User can export filtered data
- ✅ Page loads < 2 seconds

---

## Related Documentation

- [Purchase Order Improvements](PURCHASE_ORDER_IMPROVEMENTS.md) — Cart and PO flow
- [Frontend Roadmap](../frontend/FRONTEND_ROADMAP.md) — Overall frontend plan
- [Next Steps](../NEXT_STEPS.md) — Current priorities

---

**Document Owner:** Development Team  
**Last Updated:** 2025-01-27  
**Status:** Planning Phase

