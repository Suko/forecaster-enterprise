# Next Steps - Development Priorities

**Last Updated:** 2025-12-17  
**Status:** Active Development Plan  
**Scope:** Post-MVP completion priorities

---

## Executive Summary

Backend MVP (Phases 1-4) is **complete** ✅, and frontend MVP is **~87% complete** ✅. This document outlines the prioritized next steps to complete the MVP and prepare for production.

**Recently Completed:**
- ✅ Data Validation - Complete validation service with quality checks
- ✅ Forecasting Integration - Forecasts now used in dashboard, products, and recommendations
- ✅ ETL Bug Fix - Fixed `location_id` missing in sales history sync

---

## Current Priorities

### 0. Forecasting Hardening (Hotfix)
**Goal:** Ensure forecasts persist correctly and tenant isolation cannot be bypassed.

- [x] Fix `ForecastService.generate_forecast()` success path (commit/return) so `forecast_runs`/`forecast_results` persist reliably
- [x] Harden forecast endpoint auth/tenant isolation: only accept request-body `client_id` when a valid service key is present; otherwise require JWT-derived `client_id`
- Reference flow + details: `docs/backend/forecasting/README.md`

### 0.1 Backend/Frontend Contract Alignment (Blockers)
**Goal:** Make backend, frontend, and docs agree before adding more UI features.

**Compatibility Audit:** [Backend/Frontend Compatibility & Blockers](system/BACKEND_FRONTEND_COMPATIBILITY.md)

- [x] Migrate auth base path to `/api/v1/auth/*` (keep `/auth/*` as deprecated alias during transition)
- [x] Normalize `stockout_risk` scale across API + UI (recommend: **0–1 in API**, % only in UI)
- [x] Fix `GET /api/v1/products` filtering gap (status/dir/risk/stock filters) using server-side metric filters (Option A: `inventory_metrics`)
- [x] Deprecate Recommendations page (remove navigation + copy; focus on Inventory + Cart/PO)
- [x] Update docs to match actual implementation (API reference + feature plans)
  - [x] Added note to `API_REFERENCE.md` that it should be regenerated from OpenAPI schema
  - [x] **Post-forecast hook implemented**: `ForecastService.generate_forecast()` now automatically refreshes `inventory_metrics` after successful forecast generation
  - [x] **Scheduling option**: `backend/scripts/refresh_inventory_metrics.py` can still be run manually or via cron for full client refresh
  - **Implementation**: Post-forecast hook in `backend/forecasting/services/forecast_service.py` calls `InventoryMetricsService.refresh_client_metrics()` after forecast completion

### 1. Frontend Polish (Charts, Row Actions, Filters) - **WEEK 3** (OPTIONAL)
**Goal:** Complete MVP UX and user-facing features

**Dashboard:**
- [ ] Connect Chart.js to real trend data API
- [ ] Add time period selector (daily, weekly, monthly)

**Inventory Page:**
- [ ] Row actions (view details, edit, add to cart)
- [ ] Status tabs and quick filters
- [ ] Cart indicators and bulk actions
- [ ] Export functionality (Excel/CSV)
- [ ] Column management
- [ ] Enhanced product information display
- [ ] **Product Detail Page** — Full SKU view with history + forecast chart ⭐

**See Full Plan:** [Inventory Improvements](features/INVENTORY_IMPROVEMENTS.md)



**Recommendations Page:**
- [x] Deprecated and removed from the UI (use Inventory + Cart/Purchase Orders instead)

**Integration:**
- [ ] Cart badge in header
- [ ] Add to cart from inventory page
- [ ] Last sync date indicator in header

**Estimated Time:** 1 week

---

### 2. Empty State Handling - **WEEK 2** (DEFERRED)
**Goal:** Improve first-time user experience

**Backend:**
- [x] System status endpoint exists: `GET /api/v1/system/status`
- [ ] Extend system status response to support onboarding/empty-states (clear next actions, per-data-type flags)
- [ ] Enhance API responses with helpful messages when data is empty

**Frontend (OPTIONAL):**
- [ ] Add frontend proxy route: `GET /api/system/status` → backend `GET /api/v1/system/status`
- [ ] Create reusable `EmptyState.vue` component
- [ ] Add empty states to Dashboard, Inventory, and Cart pages
- [ ] Add contextual help messages

**Estimated Time:** 1 week

---

### 3. ETL Scheduling - **WEEK 4**
**Goal:** Enable production data sync from external sources

**Backend Tasks:**
- [ ] Complete connector implementations (BigQuery and SQL connectors have placeholder TODOs)
- [ ] ETL scheduling setup (Celery + Redis/RabbitMQ OR cron + background tasks)
- [ ] Daily sync job with error handling and retries
- [ ] Sync status tracking endpoint: `GET /api/v1/etl/sync/status`
- [ ] Manual trigger endpoint: `POST /api/v1/etl/sync/trigger` (admin only)

**Frontend Tasks:**
- [ ] ETL status dashboard (if needed)

**Estimated Time:** 1 week

---

## Post-MVP Features (Future)

### Phase 6: Advanced Features
- [ ] Marketing Campaigns API
- [ ] Locations API (full CRUD)
  - [ ] **Location Deletion Validation**: Prevent deletion of locations that have dependencies
    - **Source of Truth**: Check these tables before allowing deletion:
      - `stock_levels.location_id` - Products with stock at that location
      - `ts_demand_daily.location_id` - Sales history records for that location
      - `inventory_metrics.location_id` - Computed inventory metrics for that location
    - **Current Implementation**: `LocationService.delete_location()` only checks `is_synced` flag
    - **Required Enhancement**: Add validation queries to check all three tables before deletion
  - [ ] **Deletion Workflow**: When attempting to delete a location with dependencies:
    - Return clear error message listing what prevents deletion (e.g., "Location has 5 products with stock, 120 sales history records")
    - Option 1: Require reassignment of stock/products to another location before deletion
    - Option 2: Provide bulk reassignment endpoint to move all dependencies to another location
    - Option 3: Allow deletion with cascade (delete all related stock/metrics/history) - **NOT RECOMMENDED** for data integrity
- [ ] Analytics & Reporting endpoints
- [ ] Export/Import functionality

### Phase 7: Performance & Scale
- [ ] Performance optimization (caching, query optimization)
- [ ] Server-side row model for AG Grid (if dataset > 10K rows)
- [ ] Database partitioning for large datasets
- [ ] Load testing and optimization

### Phase 8: Advanced ETL
- [ ] Multi-source ETL (BigQuery, SQL, CSV)
- [ ] Incremental sync (only changed data)
- [ ] Data transformation pipeline
- [ ] ETL monitoring dashboard

### Phase 9: ABC Classification Configuration
**Goal:** Make ABC classification configurable per client with customizable thresholds and settings

**Current State:**
- ✅ ABC classification exists (hardcoded 80/15/5 split)
- ❌ No configuration options (percentages, look-back period, quantity vs sales)
- ❌ No product exclusion from ABC analysis

**Features to Add:**
- [ ] Configurable ABC percentages (e.g., 70/20/10 instead of 80/15/5)
- [ ] Performance classification method (Quantity vs Sales)
- [ ] Look-back period configuration (30/60/90 days)
- [ ] Daily re-evaluation setting
- [ ] Settings UI (Prediko-style interface)
- [ ] API endpoints for configuration

**Files to Modify:**
- `backend/models/settings.py` - Add ABC configuration fields
- `backend/forecasting/services/sku_classifier.py` - Make thresholds configurable
- `backend/services/forecast_service.py` - Use configured look-back period
- `backend/api/settings.py` - Add ABC configuration endpoints
- `frontend/app/pages/settings/abc-classification.vue` - Settings UI page

---

### Phase 10: Product Exclusion System
**Goal:** System-level product exclusion list usable across ETL, forecasting, ABC classification, and other features

**Use Cases:**
- Exclude gift cards, promotional items, free products from ABC analysis
- Exclude archived/discontinued products from forecasting
- Exclude test products from ETL sync
- Exclude products from recommendations

**Features to Add:**
- [ ] Product exclusion model with reason and scope
- [ ] ETL integration (skip excluded products during sync)
- [ ] Forecasting integration (skip during forecast generation)
- [ ] ABC classification integration (exclude from analysis)
- [ ] Recommendations integration (filter from recommendations)
- [ ] API endpoints for exclusion management
- [ ] Settings UI for managing exclusions

**Files to Create/Modify:**
- `backend/models/product_exclusion.py` - New model (or extend `ClientSettings`)
- `backend/services/exclusion_service.py` - Exclusion management service
- `backend/api/products.py` - Exclusion endpoints
- `frontend/app/pages/settings/product-exclusions.vue` - Exclusion management UI

**Database Schema Options:**
```sql
-- Option 1: Separate table
CREATE TABLE product_exclusions (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    item_id VARCHAR(255) NOT NULL,
    exclusion_reason VARCHAR(255),
    excluded_from TEXT[] DEFAULT ARRAY['abc', 'forecast', 'etl', 'recommendations'],
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, item_id)
);

-- Option 2: Add to ClientSettings (JSONB)
-- client_settings.excluded_products JSONB
```

---

### Phase 11: Working Orders & Manufacturing System
**Goal:** Complete manufacturing/production order management system connecting SKUs → BOM → Raw Materials → WO Suppliers

**Scope:** Large feature package including:
- Raw Materials Catalogue
- Bill of Materials (BOM) / Product Recipes
- Product Variants
- Production Operations
- Working Orders (Production Orders)

**Current State:**
- ✅ Purchase Orders system exists (can be used as reference)
- ✅ Suppliers model has `supplier_type` field (PO/WO)
- ❌ No BOM structure
- ❌ No raw materials management
- ❌ No working orders
- ❌ No production operations

**See Full Plan:** [Working Orders Feature Plan](features/WORKING_ORDERS_FEATURE.md)

**High-Level Phases:**
1. **Foundation** - Raw Materials & BOM Structure (1-2 weeks)
2. **Production Operations** - Define workflow/operations (1 week)
3. **Working Orders Core** - Create/manage WOs (2 weeks)
4. **Frontend - Raw Materials** - Catalogue UI (1 week)
5. **Frontend - BOM Management** - Recipe UI (1-2 weeks)
6. **Frontend - Production Operations** - Operations UI (1 week)
7. **Frontend - Working Orders** - WO management UI (2 weeks)
8. **Integration** - Connect with recommendations, cart, forecasting (2 weeks)

**Total Estimated Time:** 11-13 weeks

**Key Features:**
- Raw materials catalogue (separate from finished products)
- BOM/recipe management per product/variant
- Production operations with resources, costs, sequencing
- Working orders (similar to Purchase Orders but for production)
- Integration with existing PO system and suppliers

---

## Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Forecasting Hardening + Contract Alignment | Persist forecasts, enforce tenant isolation, align risk scales + paths |
| **Week 2** | Empty State Handling | System status wiring + empty states (frontend optional) |
| **Week 3** | Frontend Polish (Optional) | Inventory actions, filters/tabs, header indicators |
| **Week 4** | ETL Scheduling | Automated daily sync, status tracking, error handling |

**Total Timeline:** 4 weeks to production-ready MVP (if frontend polish is skipped)

---

## Related Documentation

- [Backend Roadmap (Archive)](archive/backend/BACKEND_ROADMAP.md) - Historical implementation snapshot
- [Frontend Roadmap (Archive)](archive/frontend/FRONTEND_ROADMAP.md) - Historical MVP plan snapshot
- [User Stories](USER_STORIES.md) - Feature requirements
- [Workflows](WORKFLOWS.md) - System workflows and decision loops
- [Quick Start](setup/QUICK_START.md) - Setup instructions
- [Data Requirements](DATA_REQUIREMENTS.md) - User-facing guide on what data is required vs. app-managed

---

**Document Owner:** Development Team  
**Last Updated:** 2025-12-17  
**Next Review:** After Forecasting Hardening + Contract Alignment

---

## Feature Documentation

- [Working Orders Feature Plan](features/WORKING_ORDERS_FEATURE.md) - Complete manufacturing/production order system (Phase 11)
- [Inventory Improvements](features/INVENTORY_IMPROVEMENTS.md) - Comprehensive inventory page enhancements
- [Purchase Order Improvements](features/PURCHASE_ORDER_IMPROVEMENTS.md) - PO UI/UX improvements, expected delivery dates, cart enhancements
- [Dashboard Improvements](features/DASHBOARD_IMPROVEMENTS.md) - Dashboard enhancements, trend charts, interactive KPIs
- [Backend/Frontend Compatibility & Blockers](system/BACKEND_FRONTEND_COMPATIBILITY.md) - Current mismatches + decisions

**Note:** Recommendations page is deprecated. Its functionality is merged into:
- **Inventory** → "Needs Action" tab (status-based filtering)
- **Cart** → Order Suggestions panel (suggested quantities, priorities)
