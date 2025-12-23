# Dashboard Improvements - Feature Plan

**Last Updated:** 2025-12-17  
**Status:** Planning Phase  
**Scope:** Dashboard UI/UX improvements and enhancements

---

## User Goal

**Primary task:** "Get a quick overview of inventory health and take action on critical issues"

Users come to the dashboard to:
1. See high-level KPIs (total SKUs, inventory value, problem counts)
2. Identify products needing immediate attention (understocked, overstocked)
3. Navigate to detailed views (click through to inventory)
4. Track trends over time (optional)

---

## Current State

- ✅ Backend API complete (`GET /api/v1/dashboard`)
- ✅ Basic dashboard page with KPI cards
- ✅ Chart.js integration (ready for data)
- ✅ Top products table component
- ⚠️ Contract note: `stockout_risk` is **0–1** in API responses (multiply by 100 for % display)
- ❌ Charts not connected to data
- ❌ No trend/historical data visualization
- ❌ Limited interactivity
- ❌ No time period selector
- ❌ No empty state handling

---

## Feature Plan

### 1. Enhanced KPI Cards

**Goal:** Clear, actionable KPI display

**Recommended Dashboard Indicators (6-8 cards max):**

| Priority | Indicator | Backend Field | Why It Matters |
|----------|-----------|---------------|----------------|
| **P0** | **Critical Issues** | Calculate from `top_understocked[]` | Products with stockout risk > 80% - immediate action needed |
| **P0** | **At-Risk Value** | Sum `inventory_value` where `stockout_risk > 0.5` | Financial impact of potential stockouts |
| **P0** | **Inventory Health** | Calculate: `(normal_count / total_skus) * 100` | Overall inventory status (0-100%) |
| **P1** | **Total Inventory Value** | `metrics.total_inventory_value` | Total capital tied up in inventory |
| **P1** | **Average Days of Cover** | `metrics.average_dir` | How long inventory will last on average |
| **P1** | **Overstocked Value** | `metrics.overstocked_value` | Capital tied up in excess inventory |
| **P2** | **Total SKUs** | `metrics.total_skus` | Scale indicator (less actionable) |
| **P2** | **Reorder Needed** | `metrics.understocked_count` | Count of products needing reorder |
| **P1** | **Dead Stock Value** | Calculate from `status=dead_stock` | Value of products with no sales (configurable days) |

**Recommended Layout (7 cards):**
1. **Critical Issues** — Count of products with stockout risk > 80% (🔴 Red)
2. **At-Risk Value** — € value of inventory at risk (🔴 Red if > threshold)
3. **Inventory Health** — % of products in healthy state (🟢 Green if > 80%)
4. **Total Inventory Value** — € total value (🟢 Neutral)
5. **Average Days of Cover** — Average DIR (🟠 Orange if < 30 days)
6. **Overstocked Value** — € value of excess inventory (🟡 Yellow if > threshold)
7. **Dead Stock Value** — € value of products with no sales (⚫ Gray)
   - Sub-text: "No sales for 90+ days" (show threshold from settings)
   - Action: "View Dead Stock" → Navigate to `?status=dead_stock`

**Why Dead Stock Matters:**
- Shows capital tied up in non-moving inventory
- Actionable: Can promote, discount, or liquidate
- Threshold is configurable (default: 90 days)
- Helps identify products that need marketing attention

**Dead Stock Implementation Status:**
- ❌ Status: `"dead_stock"` is **not** returned by products API yet (requires last-sale-date logic)
- ❌ Filter: `GET /api/v1/products?status=dead_stock` is not functional until products status supports dead stock
- ✅ Settings: `dead_stock_days` (default: 90 days, configurable)
- ✅ Recommendations: `DEAD_STOCK` recommendation type
- ❌ Not included in dashboard metrics (needs calculation)

**Alternative: Business-Focused Indicators:**
- **Stockout Risk Score** — Aggregate risk (0-100%)
- **Reorder Urgency** — Products needing immediate action
- **Capital Efficiency** — Inventory turnover ratio (if sales data available)
- **Forecast Coverage** — % of products with active forecasts
- **Dead Stock Value** — Value of products with no sales (if data available)

**UI Enhancements:**
- [ ] **Color-coded cards (by urgency):**
  - 🔴 **Red (Critical):** Critical Issues, At-Risk Value (if high)
    - Action: "View Critical Issues" → Navigate to inventory `?status=understocked&min_risk=0.8`
  - 🟠 **Orange (Warning):** Average DIR (if < 30 days)
    - Action: "View Low Stock" → Navigate to inventory `?status=understocked`
  - 🟡 **Yellow (Caution):** Overstocked Value (if > threshold)
    - Action: "View Overstocked" → Navigate to inventory `?status=overstocked`
  - 🟢 **Green (Healthy):** Inventory Health (if > 80%), Total Value (neutral)
    - Action: "View All Products" → Navigate to inventory

- [ ] **Card Design:**
  - Large number (primary metric)
  - Label (what it means)
  - Sub-text (context, e.g., "5 products" or "€12,450")
  - **Condition/Threshold** (for dead stock: "No sales for 90+ days")
  - Icon (visual indicator)
  - Click action (navigate to relevant view)

- [ ] **Example Cards:**
  ```
  ┌─────────────────────┐      ┌─────────────────────┐
  │  🔴 Critical Issues  │      │  ⚫ Dead Stock Value │
  │      12              │      │    €23,450          │
  │  Products at risk   │      │  5 products         │
  │  €45,200 value       │      │  No sales 90+ days  │
  │  [View Issues →]     │      │  [View Dead Stock →]│
  └─────────────────────┘      └─────────────────────┘
  ```

- [ ] **Trend indicators (future):**
  - Show up/down arrows vs previous period
  - Percentage change (e.g., "+12% vs last week")
  - Requires historical data API

- [ ] **Tooltips:**
  - Explain what each metric means
  - Show calculation details
  - Example: "Critical Issues = Products with stockout risk > 80%"

**Implementation:**
- Enhance existing `KpiCard.vue` component
- Add color logic based on thresholds
- Add navigation handlers
- Use Nuxt UI Card component with color variants

---

### 2. Top Products Cards/List

**Goal:** Quick visual overview of products needing attention

**Current Data (Backend Already Provides):**
- ✅ `top_understocked[]` — Top 10 understocked products
  - Sorted by: `stockout_risk` (desc), then `inventory_value` (desc)
  - Fields: `item_id`, `product_name`, `current_stock`, `dir`, `stockout_risk`, `inventory_value`
- ✅ `top_overstocked[]` — Top 10 overstocked products
  - Sorted by: `inventory_value` (desc)
  - Same fields as understocked

**UI Design (Card-based, not tables):**
- [ ] **Two-column card layout:**
  - Left: "Critical Issues" (top 5 understocked)
  - Right: "Overstocked" (top 5 overstocked)
  - Responsive: Stack on mobile

- [ ] **Product Cards (compact):**
  - Product name (truncated if long)
  - Status badge (🔴 Critical, 🟠 High, 🟡 Medium)
  - Key metric: "13 days left" or "€2,920 value"
  - Click → Navigate to inventory with product filter

- [ ] **Visual indicators:**
  - Color-coded cards (red for critical, orange for high risk)
  - Progress bar for stockout risk
  - Icon indicators (⚠️ for understocked, 📦 for overstocked)

- [ ] **"View All" links:**
  - "View All Understocked (22)" → Navigate to inventory `?status=understocked`
  - "View All Overstocked (8)" → Navigate to inventory `?status=overstocked`

- [ ] **Empty states:**
  - "All products are well-stocked! 🎉"
  - "Inventory levels are optimized! ✅"

**Implementation:**
- Create `TopProductsCard.vue` component (not table)
- Use Nuxt UI Card component
- Compact card design (name + key metric + badge)
- Click handlers for navigation

---

### 3. Trend Charts

**Goal:** Visualize inventory trends over time

**Current State:**
- ✅ Chart.js integrated (`TrendChart.vue` component exists)
- ❌ No trend data API endpoint
- ❌ Charts not connected to data

**Features:**
- [ ] **Time Period Selector:**
  - Buttons: "7 Days", "30 Days", "90 Days", "1 Year"
  - Default: "30 Days"
  - Update charts on selection

- [ ] **Chart Types:**
  - **Inventory Value Trend** — Line chart showing total value over time
  - **Understocked/Overstocked Count** — Line chart showing problem counts
  - **Average DIR Trend** — Line chart showing DIR over time
  - **Status Distribution** — Pie/donut chart (understocked, normal, overstocked)

- [ ] **Chart Interactions:**
  - Hover to see exact values
  - Click data point → Navigate to inventory for that date
  - Zoom/pan (Chart.js plugin already available)

**Backend API Needed:**
- [ ] `GET /api/v1/dashboard/trends?period=30d` — Returns historical metrics
  - Response: Array of `{ date, total_value, understocked_count, overstocked_count, average_dir }`
  - Data source: `inventory_metrics` table or calculated from historical data

**Implementation:**
- Create trend data API endpoint (backend)
- Connect `TrendChart.vue` to API
- Add time period selector component
- Use Chart.js line, bar, and pie charts

---

### 4. Quick Actions

**Goal:** Fast access to common tasks

**Features:**
- [ ] **Action Buttons:**
  - "View All Understocked" → Navigate to inventory `?status=understocked`
  - "View All Overstocked" → Navigate to inventory `?status=overstocked`
  - "Create Purchase Order" → Navigate to cart/order planning
  - "View Cart" → Navigate to order planning cart (with Order Suggestions)

- [ ] **Quick Filters:**
  - "Critical Issues" — Products with stockout risk > 80%
  - "High Value" — Products with inventory value > threshold
  - "Dead Stock" — Products with no sales (navigate to `?status=dead_stock`)

**Implementation:**
- Add action buttons to dashboard header
- Use Nuxt UI Button component
- Navigate using Nuxt router

---

### 5. Empty State Handling

**Goal:** Guide users when no data exists

**Features:**
- [ ] **Empty State Component:**
  - Show when `total_skus === 0`
  - Message: "No inventory data yet"
  - Actions:
    - "Import Products" → Link to ETL/import page
    - "Run Setup Script" → Instructions or button
    - "View Documentation" → Link to setup guide

- [ ] **Partial Empty States:**
  - No understocked: "All products are well-stocked! 🎉"
  - No overstocked: "Inventory levels are optimized! ✅"
  - No trends: "Not enough data for trends yet"

**Implementation:**
- Create `EmptyState.vue` component
- Check `total_skus === 0` in dashboard
- Show appropriate message based on data state

---

### 6. Header: Last Sync Date Indicator

**Goal:** Show when data was last synchronized from external sources

**Features:**
- [ ] **Last Sync Indicator in Header:**
  - Display: "Last sync: 2 hours ago" or "Last sync: Dec 17, 2024 14:30"
  - Location: Top right of header (next to user menu)
  - Format: Relative time ("2 hours ago") or absolute ("Dec 17, 14:30")
  - Color: Gray (neutral, informational)
  - Icon: Clock/sync icon

- [ ] **What to Show:**
  - **Option 1:** Most recent `updated_at` from any synced table
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
  [Logo] [Dashboard] [Inventory] ...    [Last sync: 2h ago] [User Menu]
```

**Implementation:**
- Add to `Header.vue` component
- Create `LastSyncIndicator.vue` component
- API: `GET /api/v1/monitoring/last-sync` (needs to be created)
  - Returns: `{ last_sync: "2024-12-17T14:30:00Z", data_types: {...} }`
- Or calculate client-side from product/stock `updated_at` timestamps

---

### 7. Real-time Updates

**Goal:** Keep dashboard data fresh

**Features:**
- [ ] **Auto-refresh:**
  - Refresh every 5 minutes (configurable)
  - Show "Last updated: 2 minutes ago" (different from sync - this is page refresh)
  - Manual refresh button

- [ ] **Loading States:**
  - Skeleton loaders while fetching
  - Smooth transitions on data update

- [ ] **Error Handling:**
  - Show error message if API fails
  - Retry button
  - Fallback to cached data if available

**Implementation:**
- Use `useInterval` composable for auto-refresh
- Add loading state to dashboard
- Handle API errors gracefully

---

## UI/UX Guidelines

### Layout
```
┌─────────────────────────────────────────────────┐
│  Dashboard Header                               │
│  [Refresh] [Time Period: 30 Days ▼]             │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│  KPI Cards (6 cards in 3x2 grid)                │
│  [Critical Issues] [At-Risk Value] [Health %]   │
│  [Total Value] [Avg Days Cover] [Overstocked]   │
└─────────────────────────────────────────────────┘
┌──────────────────────┬──────────────────────────┐
│  Critical Issues     │  Overstocked             │
│  (Top 5 cards)       │  (Top 5 cards)           │
│  [Product Card]      │  [Product Card]          │
│  [Product Card]      │  [Product Card]          │
│  [View All (22) →]   │  [View All (8) →]        │
└──────────────────────┴──────────────────────────┘
┌─────────────────────────────────────────────────┐
│  Trend Charts                                    │
│  [Inventory Value] [Status Distribution]       │
└─────────────────────────────────────────────────┘
```

### Visual Hierarchy
1. **KPIs** — Top, most prominent (large numbers, color-coded)
2. **Top Products** — Middle, visual cards (quick scan, click to detail)
3. **Trends** — Bottom, informative (charts for historical context)

### Color Coding
- Use status colors consistently (red=critical, green=healthy)
- Charts use same color scheme as status badges
- Subtle backgrounds, not overwhelming

---

## Implementation Phases

### Phase 1: Enhanced KPIs & Header (Week 1)
**Priority: High**

- [ ] Enhance KPI cards with colors and click-through
- [ ] Create top products card components (not tables)
- [ ] Add navigation from cards to inventory
- [ ] Add empty state handling
- [ ] Add last sync date indicator to header (global)

**Deliverables:**
- Interactive KPI cards
- Product cards (visual, not tabular)
- Navigation working
- Last sync indicator in header

---

### Phase 2: Trend Charts (Week 2)
**Priority: Medium**

- [ ] Create trend data API endpoint
- [ ] Connect Chart.js to API
- [ ] Add time period selector
- [ ] Implement 2-3 chart types

**Deliverables:**
- Trend charts functional
- Time period selection working

---

### Phase 3: Polish & Real-time (Week 3)
**Priority: Medium**

- [ ] Add auto-refresh
- [ ] Add loading states
- [ ] Improve error handling
- [ ] Add quick action buttons

**Deliverables:**
- Real-time updates
- Smooth UX

---

## Technical Implementation

### Frontend Components

**Existing Components (Enhance):**
- `DashboardPage.vue` — Main dashboard page
- `KpiCard.vue` — KPI card component
- `TrendChart.vue` — Chart component (needs data connection)

**New Components:**
- `TopProductsCard.vue` — Product card (compact, visual)
- `TopProductsSection.vue` — Section with top products cards + "View All" link
- `EmptyState.vue` — Empty state component
- `TimePeriodSelector.vue` — Time period dropdown
- `QuickActions.vue` — Quick action buttons
- `StatusBadge.vue` — Status badge (reuse from inventory)
- `LastSyncIndicator.vue` — Last sync date in header (global component)

### Backend API Status

**Already Implemented:**
- ✅ `GET /api/v1/dashboard` — Returns:
  - `metrics` — All KPIs
  - `top_understocked[]` — Top 10 understocked
  - `top_overstocked[]` — Top 10 overstocked

**Needs Implementation:**
- [ ] Calculate additional indicators from existing data:
  - **Critical Issues Count:** Count products where `stockout_risk > 0.8` (from `top_understocked[]`)
  - **At-Risk Value:** Sum `inventory_value` where `stockout_risk > 0.5` (calculate from product metrics)
  - **Inventory Health %:** `(normal_count / total_skus) * 100` (calculate from status distribution)
  - **Dead Stock Count & Value:** Count and sum `inventory_value` where `status = "dead_stock"`
    - Backend already calculates `dead_stock` status (if no sales for `dead_stock_days` days)
    - Can filter products API: `GET /api/v1/products?status=dead_stock`
    - Need to aggregate in dashboard service
    - **Show threshold:** Display `dead_stock_days` from settings (e.g., "No sales for 90+ days")
- [ ] **Last Sync Date API:**
  - Option 1: `GET /api/v1/monitoring/last-sync` — Returns most recent `updated_at` from synced tables
  - Option 2: Calculate client-side from product/stock `updated_at` timestamps
  - Returns: `{ last_sync: "2024-12-17T14:30:00Z", data_types: { products: "...", stock: "...", sales: "..." } }`
- [ ] `GET /api/v1/dashboard/trends?period=30d` — Historical metrics (future)
  - Returns: `[{ date, total_value, understocked_count, overstocked_count, average_dir }, ...]`
  - Data source: `inventory_metrics` table or calculate from historical data

### Response Schema

**Current Dashboard Response (Already Complete):**
```typescript
interface DashboardResponse {
  metrics: {
    total_skus: number;
    total_inventory_value: Decimal;
    understocked_count: number;
    overstocked_count: number;
    average_dir: Decimal;
    understocked_value: Decimal;
    overstocked_value: Decimal;
    // Missing (needs to be added):
    // dead_stock_count: number;
    // dead_stock_value: Decimal;
  };
  top_understocked: Array<{
    item_id: string;
    product_name: string;
    current_stock: number;
    dir: Decimal;
    stockout_risk: Decimal;  // 0-1 decimal (multiply by 100 for %)
    inventory_value: Decimal;
  }>;
  top_overstocked: Array<{
    // Same structure as top_understocked
  }>;
  // Could add:
  // top_dead_stock: Array<{...}>;  // Top dead stock products by value
}
```

**Settings Response (for thresholds):**
```typescript
interface ClientSettingsResponse {
  dead_stock_days: number;  // Threshold for dead stock (default: 90)
  understocked_threshold: number;  // DIR threshold (default: 14)
  overstocked_threshold: number;  // DIR threshold (default: 90)
  // ... other settings
}
```

**Trend Response (Needs Implementation):**
```typescript
interface DashboardTrendsResponse {
  period: string;  // "7d", "30d", "90d", "1y"
  data: Array<{
    date: string;  // ISO date
    total_value: Decimal;
    understocked_count: number;
    overstocked_count: number;
    average_dir: Decimal;
  }>;
}
```

---

## Success Metrics

### User Experience
- ✅ User can see inventory health at a glance
- ✅ User can click through to detailed views
- ✅ User can identify critical issues quickly
- ✅ Dashboard loads < 2 seconds

### Performance
- ✅ Dashboard API response < 1 second
- ✅ Charts render < 500ms
- ✅ Smooth transitions on refresh

---

## Related Documentation

- [Backend Roadmap (Archived)](../archive/backend/BACKEND_ROADMAP.md) — Dashboard API (historical snapshot)
- [Frontend Roadmap (Archived)](../archive/frontend/FRONTEND_ROADMAP.md) — Dashboard page (historical plan)
- [Inventory Improvements](INVENTORY_IMPROVEMENTS.md) — Related inventory features
- [Next Steps](../NEXT_STEPS.md) — Current priorities

---

**Document Owner:** Development Team  
**Last Updated:** 2025-01-27  
**Status:** Planning Phase - Ready for implementation
