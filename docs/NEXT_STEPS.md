# Next Steps - Development Priorities

**Last Updated:** 2025-01-27  
**Status:** Active Development Plan  
**Scope:** Post-MVP completion priorities

---

## Executive Summary

The backend MVP (Phases 1-4) is **complete** ✅, and the frontend MVP is **~87% complete** ✅. This document outlines the prioritized next steps to complete the MVP and prepare for production.

---

## Priority Order

### 1. Empty State Handling (Backend + Frontend) - **WEEK 1**
**Goal:** Unblock onboarding and improve first-time user experience

**Why First:** When users first start the application, they see empty states. Without proper handling, this creates confusion and poor UX.

**Backend Tasks:**
- [ ] Create system status endpoint: `GET /api/v1/system/status`
  - Returns: `initialized`, `has_products`, `has_locations`, `has_suppliers`, `has_sales_data`, `setup_instructions`
  - Helps frontend detect empty state
- [ ] Enhance API responses with helpful messages when data is empty
  - Dashboard: "No inventory data yet. Import your data or run setup.sh to get started."
  - Products: "No products found. Sync your product catalog or run setup.sh for test data."
  - Recommendations: "No recommendations available. Ensure you have products and inventory data."

**Frontend Tasks:**
- [ ] Create reusable `EmptyState.vue` component
- [ ] Add empty states to Dashboard, Inventory, and Recommendations pages
- [ ] Implement onboarding flow for first-time users
- [ ] Add help tooltips and setup guidance
- [ ] Call system status API to detect initialization state

**Deliverables:**
- System status endpoint working
- Empty state components in all pages
- Onboarding flow functional
- Clear guidance for first-time users

**Estimated Time:** 1 week

---

### 2. Frontend Polish (Charts, Row Actions, Filters) - **WEEK 2**
**Goal:** Complete MVP UX and user-facing features

**Why Second:** These are visible user-facing features that complete the MVP experience. Users interact with these daily.

**Dashboard Tasks:**
- [ ] Connect Chart.js to real trend data API
  - Inventory value trend (line chart)
  - Stock levels over time (area chart)
  - Sales trends (column chart)
- [ ] Add time period selector (daily, weekly, monthly)
- [ ] Implement data fetching for historical trends

**Inventory Page Tasks:**
- [ ] Row actions (view details, edit, add to cart)
- [ ] Quick filter buttons (Understocked, Overstocked, All)
- [ ] Export to CSV functionality (custom implementation - AG Grid Enterprise not needed)
- [ ] Column visibility toggle
- [ ] Product detail modal/page

**Recommendations Page Tasks:**
- [ ] Dismiss recommendation functionality
- [ ] Empty state handling (when no recommendations available)
- [ ] Complete AG Grid AI Toolkit integration (if backend LLM service available)

**Integration Tasks:**
- [ ] Cart badge in header (show cart item count)
- [ ] Add to cart from inventory page
- [ ] Navigation improvements

**Deliverables:**
- Fully functional dashboard with real charts
- Complete inventory table with all actions
- Polished recommendations page
- Seamless navigation between features

**Estimated Time:** 1 week

---

### 3. Data Validation - **WEEK 3**
**Goal:** Ensure data quality and completeness

**Why Third:** Data quality is critical before production. Need to validate data before setting up automated ETL.

**Backend Tasks:**
- [ ] **Data Quality Checks:**
  - Validate date ranges (min 3 weeks, max 2 years)
  - Validate SKU format (alphanumeric + underscores, 1-255 chars)
  - Check for missing required fields
  - Validate numeric ranges (quantity >= 0, cost >= 0)
  - Detect and flag outliers
- [ ] **Data Completeness Checks:**
  - Ensure all `item_id` in `ts_demand_daily` exist in products
  - Ensure all `location_id` in `ts_demand_daily` exist in locations (if location_id column exists)
  - Flag orphaned records
  - Check for missing supplier assignments
- [ ] **Data Validation Service:**
  - Create `services/data_validation_service.py`
  - Reuse patterns from `forecasting/services/data_validator.py`
  - Endpoint: `POST /api/v1/etl/validate` (returns validation report)
- [ ] **Validation Reports:**
  - JSON response with validation results
  - Categorize issues (errors, warnings, info)
  - Provide actionable recommendations

**Frontend Tasks:**
- [ ] Data validation UI (if needed)
  - Show validation status
  - Display validation errors/warnings
  - Provide fix suggestions

**Deliverables:**
- Data validation service implemented
- Validation endpoint working
- Validation reports generated
- Data quality checks automated

**Estimated Time:** 1 week

---

### 4. ETL Scheduling - **WEEK 4**
**Goal:** Enable production data sync from external sources

**Why Fourth:** After data validation is in place, we can safely set up automated ETL. This enables production deployment.

**Backend Tasks:**
- [ ] **ETL Scheduling Setup:**
  - Choose scheduling solution (Celery + Redis/RabbitMQ OR cron + background tasks)
  - Set up task queue infrastructure
  - Create scheduled job definitions
- [ ] **Daily Sync Job:**
  - Schedule: Daily at configurable time (e.g., 2 AM)
  - Sync order: Sales history → Products → Stock levels → Locations
  - Error handling and retry logic (exponential backoff)
  - Logging and monitoring
- [ ] **Sync Status Tracking:**
  - Store sync status in database (last_sync_time, status, error_message)
  - Endpoint: `GET /api/v1/etl/sync/status`
  - Show sync history
- [ ] **Error Handling:**
  - Retry failed syncs (max 3 retries)
  - Alert on persistent failures
  - Notification system (email/webhook)
- [ ] **Manual Trigger:**
  - Endpoint: `POST /api/v1/etl/sync/trigger` (admin only)
  - Allow manual sync for testing

**Frontend Tasks:**
- [ ] ETL status dashboard (if needed)
  - Show last sync time
  - Display sync status
  - Show sync history
  - Manual trigger button (admin only)

**Deliverables:**
- Automated daily sync working
- Sync status tracking functional
- Error handling and retries implemented
- Monitoring and alerts set up

**Estimated Time:** 1 week

---

## Implementation Timeline

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Empty State Handling | System status endpoint, empty state components, onboarding flow |
| **Week 2** | Frontend Polish | Charts with real data, complete inventory features, cart integration |
| **Week 3** | Data Validation | Validation service, quality checks, completeness checks |
| **Week 4** | ETL Scheduling | Automated daily sync, status tracking, error handling |

**Total Timeline:** 4 weeks to production-ready MVP

---

## Success Criteria

### Week 1: Empty State Handling
- ✅ System status endpoint returns accurate initialization state
- ✅ All pages show helpful empty states when no data exists
- ✅ First-time users see clear onboarding guidance
- ✅ Setup instructions are accessible from UI

### Week 2: Frontend Polish
- ✅ Dashboard charts display real trend data
- ✅ Inventory table has all actions (view, edit, add to cart)
- ✅ Export functionality works
- ✅ Cart badge shows item count
- ✅ Navigation is seamless

### Week 3: Data Validation
- ✅ Data quality checks catch common issues
- ✅ Completeness checks identify orphaned records
- ✅ Validation reports are actionable
- ✅ Validation can be run on-demand

### Week 4: ETL Scheduling
- ✅ Daily sync runs automatically
- ✅ Sync status is tracked and visible
- ✅ Errors are handled gracefully with retries
- ✅ Manual trigger works for testing

---

## Post-MVP Features (Future)

After completing the above priorities, consider:

### Phase 6: Advanced Features
- [ ] Marketing Campaigns API (US-MKT-004, US-MKT-005)
- [ ] Locations API (full CRUD)
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

---

## Related Documentation

- [Backend Roadmap](backend/BACKEND_ROADMAP.md) - Complete backend implementation plan
- [Frontend Roadmap](frontend/FRONTEND_ROADMAP.md) - Frontend MVP development plan
- [User Stories](USER_STORIES.md) - Feature requirements
- [Workflows](WORKFLOWS.md) - System workflows and decision loops
- [Quick Start](QUICK_START.md) - Setup instructions

---

## Notes

- **Empty State Handling** is prioritized first because it unblocks onboarding and improves first-time user experience
- **Frontend Polish** comes second because these are visible, user-facing features that complete the MVP
- **Data Validation** is done before ETL Scheduling to ensure data quality before automation
- **ETL Scheduling** is last because it requires data validation to be in place first

---

**Document Owner:** Development Team  
**Last Updated:** 2025-01-27  
**Next Review:** After Week 1 completion

