# Next Steps - Development Priorities

**Last Updated:** 2025-12-29  
**Status:** Roadmap (vNext)  
**Scope:** Post-v1 improvements (not a v1 contract)

---

## Executive Summary

v1 is considered complete. This document captures **future improvements** and follow-up work.

**Recently Completed:**
- ✅ **Test Bed Feature** - Complete Experiments page with Test Bed & ROI Calculator (2025-12-22)
  - Multi-method forecast comparison
  - SKU classification and system recommendations
  - Backtesting with actual data validation
  - See: `../archive/releases/v1.0.0/CHANGELOG_TEST_BED.md`
- ✅ Data Validation - Validation service with quality checks
- ✅ Forecasting Integration - Forecasts used in dashboard, products, and recommendations
- ✅ ETL Bug Fix - Fixed `location_id` missing in sales history sync
- ✅ Performance Optimization - Major bottlenecks resolved (indexes, parallel forecasts, async inventory calcs) (2025-12-29)
- ✅ Simulation System (Core) - Service + API + validation docs + baseline tests (2025-12-29)
  - `POST /api/v1/simulation/run`
  - Baseline tests: unit + service invariants + API validation

---

## Current Priorities

### 1. Frontend Polish (Optional)
**Goal:** Complete MVP UX and user-facing features

**Dashboard**
- [ ] Connect Chart.js to real trend data API
- [ ] Add time period selector (daily, weekly, monthly)

**Inventory Page**
- [ ] Row actions (view details, edit, add to cart)
- [ ] Status tabs and quick filters
- [ ] Cart indicators and bulk actions
- [ ] Export functionality (Excel/CSV)
- [ ] Column management
- [ ] Enhanced product information display
- [ ] **Product Detail Page** — Full SKU view with history + forecast chart ⭐

**Integration**
- [ ] Cart badge in header
- [ ] Add to cart from inventory page
- [ ] Last sync date indicator in header

**See Full Plan:** `docs/roadmap/features/INVENTORY_IMPROVEMENTS.md`

---

### 2. Empty State Handling (Deferred)
**Goal:** Improve first-time user experience

**Backend**
- [ ] Extend system status response to support onboarding/empty-states (clear next actions, per-data-type flags)
- [ ] Enhance API responses with helpful messages when data is empty

**Frontend (Optional)**
- [ ] Add frontend proxy route: `GET /api/system/status` → backend `GET /api/v1/system/status`
- [ ] Create reusable `EmptyState.vue` component
- [ ] Add empty states to Dashboard, Inventory, and Cart pages
- [ ] Add contextual help messages

---

### 3. ETL Scheduling
**Goal:** Enable production data sync from external sources

**Backend**
- [ ] Complete connector implementations (BigQuery and SQL connectors have placeholder TODOs)
- [ ] ETL scheduling setup (Celery + Redis/RabbitMQ OR cron + background tasks)
- [ ] Daily sync job with error handling and retries
- [ ] Sync status tracking endpoint: `GET /api/v1/etl/sync/status`
- [ ] Manual trigger endpoint: `POST /api/v1/etl/sync/trigger` (admin only)

**Frontend**
- [ ] ETL status dashboard (if needed)

---

### 4. Simulation System (Follow-ups)
**Goal:** Make simulation runs reliable at scale and easy to interpret

**Follow-up tasks**
- [ ] Add provenance/coverage fields for real stock + sales (data quality visibility)
- [ ] Add API response size controls (e.g., `include_daily_comparison=false` / pagination)
- [ ] Remove/gate “limit to first 5 items” behavior for all-items runs
- [ ] Expand automated tests (forecast fallback paths, real-stock fallback paths, multi-item invariants)

**Docs**
- System overview: `docs/system/SIMULATION_SYSTEM.md`
- Implementation + tests: `docs/system/SIMULATION_IMPLEMENTATION.md`

---

## Post-MVP Features (Future)

### Phase 6: Advanced Features
- [ ] Marketing Campaigns API
- [ ] Locations API (full CRUD)
  - [ ] Location deletion validation (check dependencies across `stock_levels`, `ts_demand_daily`, `inventory_metrics`)
- [ ] Analytics & Reporting endpoints
- [ ] Export/Import functionality

### Phase 7: Performance & Scale
- [ ] Load testing and optimization
- [ ] Database partitioning for large datasets

### Phase 9: ABC Classification Configuration
- [ ] Make ABC classification configurable per client (thresholds, look-back period, quantity vs sales)

### Phase 10: Product Exclusions
- [ ] Allow excluding products from ABC/forecast/ETL/recommendations (UI + API)

### Phase 11: Working Orders & Manufacturing System
- [ ] Full plan: `docs/roadmap/features/WORKING_ORDERS_FEATURE.md`

---

## Implementation Timeline (Indicative)

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Frontend Polish (Optional) | Inventory UX improvements + header integration |
| **Week 2** | ETL Scheduling | Automated daily sync, status tracking, error handling |
| **Week 3** | Simulation Follow-ups | Provenance/coverage + response controls + expanded tests |

---

## Related Documentation

- [Integration (v1)](../system/INTEGRATION.md)
- [Deployment & CI/CD Approaches](../system/DEPLOYMENT_CICD_APPROACHES.md)
- [Simulation System](../system/SIMULATION_SYSTEM.md)
- [Inventory Improvements](features/INVENTORY_IMPROVEMENTS.md)
- [Purchase Order Improvements](features/PURCHASE_ORDER_IMPROVEMENTS.md)
- [Dashboard Improvements](features/DASHBOARD_IMPROVEMENTS.md)
- [Working Orders Feature Plan](features/WORKING_ORDERS_FEATURE.md)

---

**Document Owner:** Development Team  
**Last Updated:** 2025-12-29  
**Next Review:** After ETL Scheduling + Simulation Follow-ups
