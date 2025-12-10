# Frontend MVP Roadmap

**Version:** 1.0.0  
**Last Updated:** 2025-01-27  
**Status Update:** 2025-01-27 - Recommendations page fixes completed (infinite loop, API integration, type mismatches)  
**Tech Stack:** Nuxt 4, Vue 3, AG Grid (Free), Chart.js, Nuxt UI

---

## Executive Summary

This roadmap outlines the MVP frontend development plan for the Forecaster Enterprise platform. The MVP focuses on three core pages: **Dashboard**, **Inventory**, and **Recommendations**, using AG Grid (free version) for data tables and Chart.js (free) for visualizations.

---

## Technology Stack

### Previous Project Reference
The previous project (`/old/ecommerce-agent/frontend`) used:
- **Chart.js** - For charts (line, bar charts) with zoom plugin
- **Custom HTML Table** - Simple table component (no advanced features)

**Decision for New Project:**
- ✅ **Use Chart.js** - Free, no licensing costs, team already has experience
- ✅ **Upgrade to AG Grid** - Replace custom table with powerful grid (sorting, filtering, AI Toolkit)

### Core Framework
- **Nuxt 4** - Vue.js framework with SSR/SSG capabilities
- **Vue 3** - Progressive JavaScript framework
- **Nuxt UI** - Component library (already integrated)
- **TypeScript** - Type safety

### Data Visualization
- **AG Grid Community Edition (Free)** - Data tables with sorting, filtering, pagination
  - **AI Toolkit** - Natural language query interface (free tier)
  - **License:** Free for commercial use (Community Edition)
  - **Upgrade from:** Custom HTML table (previous project)
- **Chart.js** - Charting library for dashboards (FREE, no licensing costs)
  - **License:** MIT License - Free for unlimited commercial use
  - **Vue Integration:** `vue-chartjs` package
  - **Previous usage:** Used in previous project with zoom plugin
  - **Decision:** Free, no licensing costs, perfect for multiple customer installations

### Additional Libraries
- **lucide-vue-next** - Icon library (already integrated)
- **nuxt-auth-utils** - Authentication (already integrated)
- **zod** - Schema validation (already integrated)

---

## Licensing Requirements & Future Costs

### AG Grid Community Edition (Current - Free)
- ✅ **Free for commercial use**
- ✅ Includes: Sorting, filtering, pagination, column resizing, row selection
- ✅ AI Toolkit available in free version
- ❌ Does NOT include: Advanced features (pivoting, tree data, server-side row model, Excel export, etc.)

**Future Upgrade Considerations:**
- **AG Grid Enterprise** - Required for:
  - Server-side row model (for large datasets)
  - Advanced Excel export
  - Pivoting and aggregation
  - Tree data with grouping
  - **Estimated Cost:** $1,500/year per developer (as of 2025)
  - **Decision Point:** When dataset exceeds 10,000 rows or advanced features needed

### Chart.js - Charting Library

**Chart.js** is our charting library - completely free with no licensing costs:

- ✅ **100% Free** - MIT License, no commercial restrictions
- ✅ **No per-instance costs** - Deploy to unlimited customers
- ✅ **Vue integration** - `vue-chartjs` package available
- ✅ **Feature-rich** - Line, bar, area, pie, radar charts
- ✅ **Zoom & Pan** - `chartjs-plugin-zoom` plugin (already used in previous project)
  - Mouse wheel zoom
  - Drag to zoom
  - Ctrl + Drag to pan
  - Reset zoom functionality
- ✅ **Time series support** - Built-in time scale for timeline charts
- ✅ **Well-documented** - Large community, extensive examples
- ✅ **Lightweight** - Small bundle size
- ✅ **Proven in previous project** - Team already has experience with zoom functionality

---

## MVP Pages Selection

Based on user stories and workflows, the MVP will focus on three core pages:

### 1. Dashboard (Priority: P0)
**User Stories:** US-CEO-001, US-CEO-002, US-PROC-004

**Features:**
- High-level KPIs (Total SKUs, Inventory Value, Understocked/Overstocked counts)
- Top 5 understocked products (clickable to inventory)
- Top 5 overstocked products (clickable to inventory)
- Historical trend charts (Chart.js)
- Time period selector (daily, weekly, monthly)
- Quick actions (refresh, export)

**Components:**
- KPI cards (4 cards)
- Trend charts (2-3 charts: inventory value, stock levels, sales trends)
- Top products table (AG Grid - simple table)
- Quick action buttons

**API Endpoints:**
- `GET /api/v1/dashboard`

---

### 2. Inventory (Priority: P0)
**User Stories:** US-PROC-001, US-PROC-002, US-PROC-003, US-PROC-010

**Features:**
- Product list with full filtering and sorting (AG Grid)
- Search by SKU, name, category
- Filter by: supplier, category, location, status (understocked/overstocked/normal)
- Sort by: DIR, inventory value, stockout risk, stock level
- Column visibility toggle
- Pagination (50 items per page)
- Export to CSV
- Row actions: View details, Add to cart, Edit
- Status indicators (color-coded badges)

**Components:**
- AG Grid table with:
  - Column filters (text, number, set filters)
  - Multi-column sorting
  - Row selection
  - Column resizing
  - Pagination
- Search bar
- Quick filter buttons (Understocked, Overstocked, All)
- Export button

**API Endpoints:**
- `GET /api/v1/products` (with query parameters)
- `GET /api/v1/products/{item_id}` (detail view)

**AG Grid Features Used:**
- Column definitions with filters
- Row data binding
- Client-side row model (free version)
- Custom cell renderers for status badges
- Row click handlers

---

### 3. Recommendations (Priority: P0)
**User Stories:** US-PROC-009, US-MKT-001, US-MKT-002

**Features:**
- AI-powered recommendations list (AG Grid)
- Filter by recommendation type (REORDER, URGENT, REDUCE_ORDER, PROMOTE, DEAD_STOCK)
- Filter by priority (High/Medium/Low)
- Natural language query interface (AG Grid AI Toolkit)
- Add recommendations to order planning cart
- Dismiss/ignore recommendations
- Sort by priority, inventory value, risk score

**Components:**
- AG Grid table with AI Toolkit integration
- Recommendation type filter dropdown
- Priority filter
- Natural language query input (AI Toolkit)
- Action buttons (Add to Cart, Dismiss)

**API Endpoints:**
- `GET /api/v1/order-planning/recommendations`
- `POST /api/v1/order-planning/cart/add`

**AG Grid AI Toolkit Integration:**
- Natural language queries: "Show me all products with high stockout risk"
- "Sort by inventory value descending"
- "Filter products with DIR less than 14 days"
- Schema generation from grid state
- LLM integration (requires backend LLM service)

---

## Development Phases

### Phase 1: Foundation & Setup (Week 1) ✅ **COMPLETED**
**Goal:** Set up dependencies and basic structure

**Tasks:**
- [x] Install AG Grid Community Edition ✅
  ```bash
  npm install ag-grid-vue3 ag-grid-community
  ```
- [x] Install Chart.js and zoom plugin ✅
  ```bash
  npm install chart.js vue-chartjs chartjs-plugin-zoom chartjs-plugin-annotation
  ```
  **Note:** `chartjs-plugin-zoom` enables zoom/pan functionality (already used in previous project)
- [x] Create base layout components ✅
  - [x] Sidebar navigation (using Nuxt UI dashboard layout)
  - [x] Header with user menu (using Nuxt UI dashboard layout)
  - [ ] Breadcrumbs component (not needed - using sidebar navigation)
- [x] Set up API composable for AG Grid data fetching ✅ (`useAgGrid.ts`)
- [x] Create shared types/interfaces for products, recommendations ✅
  - [x] `types/product.ts`
  - [x] `types/recommendation.ts`
  - [x] `types/dashboard.ts`
- [x] Configure AG Grid theme (Alpine theme - free) ✅

**Deliverables:**
- Dependencies installed
- Base layout structure
- Type definitions
- API integration setup

---

### Phase 2: Dashboard Page (Week 2) ✅ **COMPLETED**
**Goal:** Implement executive dashboard with KPIs and charts

**Tasks:**
- [x] Create dashboard page layout ✅
- [x] Implement KPI cards component ✅ (`components/Dashboard/KpiCard.vue`)
  - [x] Total SKUs ✅
  - [x] Total Inventory Value ✅
  - [x] Understocked Count ✅
  - [x] Overstocked Count ✅
- [x] Integrate Chart.js for trend visualization ✅ (`components/Dashboard/TrendChart.vue`)
  - [x] Chart component created (ready for data)
  - [ ] Inventory value trend (line chart) - **Placeholder ready**
  - [ ] Stock levels over time (area chart) - **Placeholder ready**
  - [ ] Sales trends (column chart) - **Placeholder ready**
- [x] Create top products display ✅ (using Nuxt UI cards, not AG Grid)
  - [x] Top 5 understocked ✅
  - [x] Top 5 overstocked ✅
- [ ] Add time period selector - **TODO**
- [x] Implement refresh functionality ✅
- [x] Add loading states ✅
- [x] Error handling ✅

**Components:**
- `components/Dashboard/KpiCard.vue`
- `components/Dashboard/TrendChart.vue`
- `components/Dashboard/TopProductsTable.vue`

**API Integration:**
- `GET /api/v1/dashboard`

**Deliverables:**
- Fully functional dashboard page
- Real-time KPI updates
- Interactive charts
- Click-through to inventory page

---

### Phase 3: Inventory Page (Week 3-4) ✅ **MOSTLY COMPLETED**
**Goal:** Implement comprehensive inventory management table

**Tasks:**
- [x] Create inventory page layout ✅
- [x] Set up AG Grid with column definitions ✅
  - [x] SKU, Product Name, Category ✅
  - [x] Current Stock, Unit Cost, Inventory Value ✅
  - [x] DIR, Stockout Risk, Status ✅
  - [ ] Actions column - **TODO**
- [x] Implement column filters ✅
  - [x] Text filter for SKU, name ✅
  - [x] Number filter for stock, DIR, risk ✅
  - [x] Set filter for category, status ✅
  - [ ] Supplier filter - **TODO** (needs supplier data in API)
- [x] Add global search functionality ✅
- [x] Implement sorting (multi-column) ✅
- [x] Add pagination ✅
- [x] Create status badge cell renderer ✅ (conditional styling)
- [ ] Implement row actions (view, edit, add to cart) - **TODO**
- [ ] Add quick filter buttons - **TODO**
- [ ] Export to CSV functionality - **TODO** (requires AG Grid Enterprise or custom implementation)
- [ ] Column visibility toggle - **TODO**
- [x] Responsive design ✅
- [x] Loading states and error handling ✅

**Components:**
- `components/Inventory/ProductGrid.vue` (main AG Grid component)
- `components/Inventory/StatusBadge.vue`
- `components/Inventory/ProductActions.vue`
- `components/Inventory/QuickFilters.vue`

**API Integration:**
- `GET /api/v1/products` (with all query parameters)
- `GET /api/v1/products/{item_id}` (detail modal/page)

**AG Grid Configuration:**
```typescript
// Example column definition
{
  field: 'item_id',
  headerName: 'SKU',
  filter: 'agTextColumnFilter',
  sortable: true,
  resizable: true
}
```

**Deliverables:**
- Fully functional inventory table
- Advanced filtering and sorting
- Export functionality
- Responsive design

---

### Phase 4: Recommendations Page (Week 5) ✅ **COMPLETED** (Core Features)
**Goal:** Implement AI-powered recommendations with natural language queries

**Tasks:**
- [x] Create recommendations page layout ✅
- [x] Set up AG Grid with recommendation columns ✅
  - [x] Type, Priority, Product Name, SKU ✅
  - [x] Reason, Suggested Quantity, Inventory Value ✅
  - [x] Actions (Add to Cart) ✅
  - [x] Cell click handler for "Add to Cart" button ✅ (Fixed: moved to grid-level event)
  - [ ] Dismiss recommendation - **TODO**
- [ ] Integrate AG Grid AI Toolkit - **PARTIAL**
  - [x] Create natural language input component ✅ (placeholder UI)
  - [ ] Set up schema generation - **TODO**
  - [ ] Connect to LLM backend - **TODO** (needs backend LLM service)
- [x] Implement recommendation type filter ✅
- [x] Add priority filter ✅
- [x] Create action handlers ✅
  - [x] Add to cart functionality ✅
  - [x] 401 error handling with redirect to login ✅
  - [ ] Dismiss recommendation - **TODO**
- [x] Add recommendation badge renderer (color by type) ✅
- [x] Loading states ✅
- [x] Error handling ✅
- [x] Fix infinite loop issue ✅ (Fixed: moved data loading to onMounted)
- [x] Fix API integration ✅ (Verified: full stack integration working)
- [x] Fix priority type mismatch ✅ (Fixed: backend now returns 'high' instead of 'urgent')

**Components:**
- `components/Recommendations/RecommendationsGrid.vue`
- `components/Recommendations/AIQueryInput.vue`
- `components/Recommendations/RecommendationBadge.vue`
- `components/Recommendations/RecommendationActions.vue`

**API Integration:**
- [x] `GET /api/v1/recommendations` ✅ (Fixed: endpoint corrected from `/api/v1/order-planning/recommendations`)
- [x] `POST /api/v1/order-planning/cart/add` ✅
- [x] Frontend server route proxy ✅ (`server/api/recommendations.get.ts`)
- [x] Composable for fetching recommendations ✅ (`useRecommendations`)
- [x] Backend service integration ✅ (`RecommendationsService`)

**AG Grid AI Toolkit Setup:**
```typescript
// Get structured schema for LLM
const gridStateStructuredSchema = gridApi.getStructuredSchema();

// Create LLM-compatible schema
const schema = {
  type: 'object',
  properties: {
    gridState: gridStateStructuredSchema,
    propertiesToIgnore: { type: 'array', items: { type: 'string' } },
    explanation: { type: 'string' }
  }
};
```

**Deliverables:**
- Recommendations table with AI Toolkit
- Natural language query interface
- Action handlers for recommendations

---

### Phase 5: Integration & Polish (Week 6) 🔄 **IN PROGRESS**
**Goal:** Connect pages, add navigation, polish UX

**Tasks:**
- [x] Add navigation between pages ✅
  - [x] Sidebar menu ✅ (using Nuxt UI dashboard layout)
  - [ ] Breadcrumbs - **Not needed** (using sidebar navigation)
  - [x] Click-through from dashboard to inventory ✅
- [x] Implement order planning cart integration ✅
  - [ ] Cart badge in header - **TODO**
  - [x] Add to cart from recommendations ✅
  - [ ] Add to cart from inventory - **TODO**
- [x] Add loading states across all pages ✅
- [x] Error handling and user feedback ✅
- [x] Responsive design testing ✅ (basic responsive done)
- [ ] Performance optimization - **TODO**
  - [ ] Lazy loading for charts - **TODO**
  - [ ] Virtual scrolling for large tables (if needed) - **TODO**
- [ ] Accessibility improvements - **TODO**
- [ ] Browser testing (Chrome, Firefox, Safari) - **TODO**

**Components:**
- `components/Layout/Sidebar.vue`
- `components/Layout/Header.vue`
- `components/Layout/CartBadge.vue`

**Deliverables:**
- Fully integrated MVP
- Smooth navigation
- Polished UX

---

## Technical Specifications

### AG Grid Configuration

**Theme:** Alpine (free theme)

**Column Features (Free Version):**
- ✅ Column sorting (single and multi-column)
- ✅ Column filtering (text, number, date, set)
- ✅ Column resizing
- ✅ Column moving
- ✅ Row selection
- ✅ Pagination
- ✅ Cell editing (basic)
- ✅ Custom cell renderers
- ❌ Server-side row model (Enterprise only)
- ❌ Excel export (Enterprise only)
- ❌ Pivoting (Enterprise only)

**AI Toolkit Integration:**
```typescript
// In RecommendationsGrid.vue
import { AgGridVue } from 'ag-grid-vue3';
import { getStructuredSchema } from 'ag-grid-community';

// Get schema for natural language queries
const getSchema = () => {
  return gridApi.getStructuredSchema({
    exclude: ['columnVisibility'], // Optional: exclude features
    columns: {
      // Optional: add column descriptions for LLM
      item_id: { description: 'Product SKU identifier' },
      dir: { description: 'Days of inventory remaining' }
    }
  });
};
```

### Chart.js Configuration

**Chart Types:**
- Line charts (trends)
- Area charts (stock levels)
- Bar/Column charts (comparisons)
- Pie charts (distribution - if needed)

**Theme:** Custom theme matching Nuxt UI colors

**Example with Zoom:**
```typescript
import { Line } from 'vue-chartjs';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, TimeScale } from 'chart.js';
import zoomPlugin from 'chartjs-plugin-zoom';

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement, 
  Title, Tooltip, Legend, TimeScale, zoomPlugin
);

const chartData = {
  labels: dates,
  datasets: [{
    label: 'Inventory Value',
    data: values,
    borderColor: 'rgb(59, 130, 246)',
    backgroundColor: 'rgba(59, 130, 246, 0.1)',
    tension: 0.4
  }]
};

const chartOptions = {
  responsive: true,
  plugins: {
    title: { display: true, text: 'Inventory Value Trend' },
    legend: { display: true },
    zoom: {
      zoom: {
        wheel: { enabled: true },
        pinch: { enabled: true },
        mode: 'x' // Zoom horizontally (timeline)
      },
      pan: {
        enabled: true,
        mode: 'x', // Pan horizontally
        modifierKey: 'ctrl'
      }
    }
  },
  scales: {
    x: {
      type: 'time', // Time scale for timeline
      time: { unit: 'day' }
    },
    y: { 
      beginAtZero: true, 
      title: { display: true, text: 'Value (€)' } 
    }
  }
};

// Reset zoom function
const resetZoom = () => {
  chartRef.value.chart.resetZoom();
};
```

---

## File Structure

```
frontend/
├── app/
│   ├── components/
│   │   ├── Dashboard/
│   │   │   ├── KpiCard.vue
│   │   │   ├── TrendChart.vue
│   │   │   └── TopProductsTable.vue
│   │   ├── Inventory/
│   │   │   ├── ProductGrid.vue
│   │   │   ├── StatusBadge.vue
│   │   │   ├── ProductActions.vue
│   │   │   └── QuickFilters.vue
│   │   ├── Recommendations/
│   │   │   ├── RecommendationsGrid.vue
│   │   │   ├── AIQueryInput.vue
│   │   │   ├── RecommendationBadge.vue
│   │   │   └── RecommendationActions.vue
│   │   └── Layout/
│   │       ├── Sidebar.vue
│   │       ├── Header.vue
│   │       └── CartBadge.vue
│   ├── composables/
│   │   ├── useApi.ts (existing)
│   │   ├── useAgGrid.ts (new)
│   │   └── useCharts.ts (new)
│   ├── types/
│   │   ├── product.ts
│   │   ├── recommendation.ts
│   │   └── dashboard.ts
│   ├── pages/
│   │   ├── dashboard.vue (enhance existing)
│   │   ├── inventory/
│   │   │   ├── index.vue (new)
│   │   │   └── [id].vue (detail page - future)
│   │   └── recommendations/
│   │       └── index.vue (new)
│   └── layouts/
│       └── dashboard.vue (enhance existing)
```

---

## API Integration Patterns

### AG Grid Data Fetching

```typescript
// composables/useAgGrid.ts
export const useAgGridProducts = () => {
  const { $fetch } = useNuxtApp();
  const config = useRuntimeConfig();

  const fetchProducts = async (params: {
    page: number;
    pageSize: number;
    sortModel?: any[];
    filterModel?: any;
    search?: string;
  }) => {
    const queryParams = new URLSearchParams({
      page: params.page.toString(),
      page_size: params.pageSize.toString(),
      ...(params.search && { search: params.search }),
      ...(params.sortModel && { 
        sort: params.sortModel[0]?.colId,
        order: params.sortModel[0]?.sort 
      })
    });

    const response = await $fetch(
      `${config.public.apiBaseUrl}/api/v1/products?${queryParams}`,
      {
        headers: {
          Authorization: `Bearer ${useUserSession().data.value?.access_token}`
        }
      }
    );

    return {
      rowData: response.items,
      totalRows: response.total
    };
  };

  return { fetchProducts };
};
```

### Chart.js Data Fetching

```typescript
// composables/useCharts.ts
export const useDashboardCharts = () => {
  const { $fetch } = useNuxtApp();
  const config = useRuntimeConfig();

  const fetchTrendData = async (period: string) => {
    const response = await $fetch(
      `${config.public.apiBaseUrl}/api/v1/dashboard/trends?period=${period}`,
      {
        headers: {
          Authorization: `Bearer ${useUserSession().data.value?.access_token}`
        }
      }
    );
    return response;
  };

  return { fetchTrendData };
};
```

---

## Testing Strategy

### Unit Tests
- Component rendering
- API composable functions
- Utility functions

### Integration Tests
- Page navigation
- API calls
- AG Grid interactions
- Chart rendering

### E2E Tests (Future)
- Complete user workflows
- Order planning flow
- Dashboard interactions

---

## Performance Considerations

### AG Grid Optimization
- Use client-side row model (free version limitation)
- Implement pagination for datasets > 1000 rows
- Lazy load data on scroll (if needed)
- Debounce search/filter inputs

### Chart.js Optimization
- Limit data points (aggregate for long time ranges)
- Lazy load charts (load on tab/view)
- Use data decimation plugin for large datasets
- Enable tree-shaking to reduce bundle size

### General
- Code splitting for routes
- Lazy load heavy components
- Image optimization
- Caching API responses

---

## Accessibility

### AG Grid
- Keyboard navigation (built-in)
- Screen reader support
- ARIA labels

### Chart.js
- Accessible chart options (ARIA labels)
- Screen reader support
- Keyboard navigation (via plugins)

### General
- Semantic HTML
- Proper heading hierarchy
- Color contrast (WCAG AA)
- Focus indicators

---

## Future Enhancements (Post-MVP)

### Phase 6: Additional Pages
- [ ] Order Planning Cart page
- [ ] Purchase Orders list
- [ ] Product detail page
- [ ] Settings page enhancements

### Phase 7: Advanced Features
- [ ] Real-time updates (WebSocket)
- [ ] Advanced filtering (saved filters)
- [ ] Custom dashboards
- [ ] Export to Excel (requires AG Grid Enterprise)

### Phase 8: Mobile Optimization
- [ ] Mobile-responsive tables
- [ ] Touch gestures
- [ ] Mobile-specific layouts

---

## Dependencies to Install

```bash
# AG Grid
npm install ag-grid-vue3 ag-grid-community

# Chart.js with zoom plugin
npm install chart.js vue-chartjs chartjs-plugin-zoom chartjs-plugin-annotation

# Type definitions (included in chart.js)
```

---

## Success Criteria

### MVP Completion
- ✅ Dashboard displays real-time KPIs
- ✅ Inventory table with full filtering/sorting
- ✅ Recommendations with AI Toolkit integration
- ✅ Navigation between all pages
- ✅ Responsive design (desktop + tablet)
- ✅ Error handling and loading states
- ✅ API integration working

### Performance Targets
- Page load time < 2 seconds
- Table filtering < 500ms
- Chart rendering < 1 second
- Smooth scrolling (60fps)

---

## Risk Mitigation

### AG Grid Free Version Limitations
**Risk:** May need Enterprise features later  
**Mitigation:** Start with free version, evaluate Enterprise when needed

### Chart.js Licensing
**Risk:** None - MIT License, completely free  
**Mitigation:** 
- ✅ No licensing costs for any number of installations
- ✅ No per-instance fees
- ✅ Free for unlimited commercial use

### Performance with Large Datasets
**Risk:** Client-side row model may be slow  
**Mitigation:** Implement pagination, consider server-side model (Enterprise) if needed

---

## Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Foundation | 1 week | Dependencies & structure |
| Phase 2: Dashboard | 1 week | Dashboard page |
| Phase 3: Inventory | 2 weeks | Inventory table |
| Phase 4: Recommendations | 1 week | Recommendations page |
| Phase 5: Integration | 1 week | Polished MVP |
| **Total** | **6 weeks** | **Complete MVP** |

---

## Next Steps

1. **Review and approve roadmap**
2. **Set up development environment**
3. **Install dependencies (Phase 1)**
4. **Begin Phase 2: Dashboard development**

---

**Document Owner:** Frontend Team  
**Last Review:** 2025-01-27  
**Next Review:** After Phase 1 completion

---

## Current Status Summary (Updated: 2025-01-27)

### 🔧 Recent Fixes (2025-01-27):
- **Recommendations Page:**
  - ✅ Fixed infinite loop issue (moved data loading from `onGridReady` to `onMounted`)
  - ✅ Fixed API endpoint (corrected to `/api/v1/recommendations`)
  - ✅ Fixed cell click handler (moved from column definition to grid-level event)
  - ✅ Fixed priority type mismatch (backend now returns 'high' instead of 'urgent')
  - ✅ Added concurrent call prevention
  - ✅ Verified full API integration stack (frontend → server route → backend → service)

### ✅ Completed Phases:
- **Phase 1: Foundation & Setup** - 100% Complete
- **Phase 2: Dashboard Page** - 90% Complete (charts need data integration)
- **Phase 3: Inventory Page** - 85% Complete (missing some advanced features)
- **Phase 4: Recommendations Page** - 95% Complete (Core features working, AI Toolkit needs backend LLM service)

### 🔄 In Progress:
- **Phase 5: Integration & Polish** - 60% Complete

### 📊 Overall Progress: **~87% Complete** (Updated: Recommendations page fixes)

### 🎯 Remaining Tasks:
1. **Dashboard:**
   - [ ] Connect Chart.js to real trend data API
   - [ ] Add time period selector

2. **Inventory:**
   - [ ] Row actions (view details, edit, add to cart)
   - [ ] Quick filter buttons
   - [ ] Export to CSV (custom implementation)
   - [ ] Column visibility toggle

3. **Recommendations:**
   - [x] API integration ✅ (Fixed: endpoint, infinite loop, type mismatches)
   - [x] Add to cart functionality ✅ (Fixed: cell click handler)
   - [x] Error handling and auth redirect ✅
   - [ ] Complete AG Grid AI Toolkit integration (needs backend LLM service)
   - [ ] Dismiss recommendation functionality
   - [ ] Empty state handling (when no recommendations available)

4. **Integration:**
   - [ ] Cart badge in header
   - [ ] Performance optimization
   - [ ] Accessibility improvements
   - [ ] Browser testing

### 🚀 Next Steps:
1. Test with real data (run `backend/setup.sh` to populate test data)
2. Connect Chart.js to dashboard trend API
3. Implement remaining inventory features
4. Complete AI Toolkit integration
5. Performance and accessibility polish

---

## Known Issues & Future Improvements

### First-Time Setup & Empty State Handling

**Issue:** When the application is first started, the setup script creates an admin user but other data (products, inventory, recommendations) is not yet populated. The frontend should handle this gracefully with proper empty states and onboarding.

**Current State:**
- ✅ User can log in after running `setup.sh` (admin user created)
- ⚠️ Dashboard shows zeros/empty when no data exists
- ⚠️ Inventory table shows "No Rows To Show" without helpful messaging
- ⚠️ Recommendations page shows empty without guidance
- ⚠️ No onboarding flow for first-time users

**TODO - Frontend Improvements:**
- [ ] **Empty State Components:**
  - [ ] Create `EmptyState.vue` component for reusable empty states
  - [ ] Add empty state to Dashboard when no products exist
  - [ ] Add empty state to Inventory table when no products loaded
  - [ ] Add empty state to Recommendations when no recommendations available

- [ ] **Onboarding Flow:**
  - [ ] Detect first-time setup (check system status API)
  - [ ] Show welcome/onboarding modal or page for new installations
  - [ ] Provide clear instructions: "Run `backend/setup.sh` to populate test data"
  - [ ] Add link to setup documentation or quick start guide

- [ ] **Empty State Messages:**
  - [ ] Dashboard: "No inventory data yet. Import your data or run setup.sh to get started."
  - [ ] Inventory: "No products found. Sync your product catalog or run setup.sh for test data."
  - [ ] Recommendations: "No recommendations available. Ensure you have products and inventory data."

- [ ] **System Status Check:**
  - [ ] Call `GET /api/v1/system/status` (when backend implements it)
  - [ ] Show initialization status in UI
  - [ ] Display setup progress/checklist

- [ ] **User Guidance:**
  - [ ] Add help tooltips explaining how to populate data
  - [ ] Link to setup documentation from empty states
  - [ ] Consider adding a "Quick Start" button that triggers test data import (if backend supports it)

**Example Empty State Component:**
```vue
<EmptyState
  icon="i-lucide-package"
  title="No Products Found"
  description="Your inventory is empty. Import your product catalog or run setup.sh to load test data."
  action-label="View Setup Guide"
  action-link="/docs/setup"
/>
```

**Related Backend Work:**
- See Backend Roadmap for system status endpoint and initialization checks

