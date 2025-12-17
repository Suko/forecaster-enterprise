# Next Steps - Development Priorities

**Last Updated:** 2025-12-16  
**Status:** Active Development Plan  
**Scope:** Post-MVP completion priorities

---

## Executive Summary

The backend MVP (Phases 1-4) is **complete** ✅, and the frontend MVP is **~87% complete** ✅. This document outlines the prioritized next steps to complete the MVP and prepare for production.

---

## Priority Order

### 1. Data Validation - **COMPLETED** ✅
**Goal:** Ensure data quality, completeness, and accuracy of computed metrics shown on frontend

**Status:** All validation tasks completed and tested.

**Completed:**
- ✅ `services/data_validation_service.py` - Unified validation service
- ✅ `POST /api/v1/etl/validate` - Validation endpoint with full report
- ✅ `GET /api/v1/system/status` - System status endpoint
- ✅ Raw data quality checks (dates, formats, ranges)
- ✅ Data completeness checks (relationships, orphans)
- ✅ Computed metrics validation (DIR, stockout risk, status, inventory value)
- ✅ Frontend-backend consistency checks (format, range validation)
- ✅ Stockout risk range fix: Backend returns 0-1 (frontend multiplies by 100)
- ✅ Unit tests + Integration tests + Real data tests

**Documentation:**
- `docs/backend/DATA_VALIDATION_API.md` - API reference
- `docs/backend/VALIDATION_USAGE_GUIDE.md` - Usage guide
- `docs/backend/VALIDATION_PROOF.md` - Proof & guarantees

**Key Files:**
- `backend/services/data_validation_service.py`
- `backend/api/etl.py` (validation endpoint)
- `backend/api/monitoring.py` (system status endpoint)
- `backend/schemas/monitoring.py`
- `backend/tests/test_services/test_data_validation_service.py`
- `backend/tests/test_services/test_validation_real_data.py`

---

### 2. Forecasting Integration - **WEEK 2** ✅ **COMPLETED - 2025-12-17** (HIGH PRIORITY)
**Goal:** Use forecasts in regular inventory endpoints (dashboard, products, recommendations)

**Problem:** 
- Forecasting works, but only used in `/api/v1/forecast/inventory/calculate`
- Dashboard and product list use **historical data only** (last 30 days)
- Not using forward-looking forecasts for planning

**Completed Testing:**
- ✅ Manual forecast test script (`scripts/manual_forecast_test.py`) - Tests forecast generation and metrics comparison
- ✅ Forecast validation script (`scripts/validate_forecast_results.py`) - Validates forecast integrity
- ✅ Verified metrics calculation with forecast data (DIR, stockout risk)
- ✅ Confirmed forecast results are stored correctly in database

**Tasks:**
- [x] Add `_get_latest_forecast_demand()` to `InventoryService` ✅ **COMPLETED - 2025-12-17**
- [x] Modify `get_products()` to use forecasts when available ✅ **COMPLETED - 2025-12-17**
- [x] Add auto-refresh logic (background forecast if stale) ✅ **COMPLETED - 2025-12-17**
- [x] Add indicator in API response: `using_forecast` field ✅ **COMPLETED - 2025-12-17**
- [x] Add forecast freshness check (use forecast if < 7 days old) ✅ **COMPLETED - 2025-12-17**
- [x] Modify `DashboardService.get_dashboard_data()` to use forecasts ✅ **COMPLETED - 2025-12-17**
- [x] Modify `RecommendationsService.get_recommendations()` to use forecasts ✅ **COMPLETED - 2025-12-17**
- [x] Add forecast validation to `DataValidationService` ✅ **COMPLETED - 2025-12-17**
- [x] Create integration tests for forecast usage ✅ **COMPLETED - 2025-12-17**
- [x] Define accuracy tracking approach ✅ **COMPLETED - 2025-12-17**

**Files to Modify:**
- `backend/services/inventory_service.py`
- `backend/services/dashboard_service.py`
- `backend/services/data_validation_service.py`

**Documentation:** 
- `docs/backend/FORECASTING_INTEGRATION.md` - Integration plan ✅ **UPDATED**
- `docs/backend/FORECASTING_TESTING_AND_FREQUENCY.md` - Testing & frequency guide

**Implementation Details:**
- ✅ `_get_latest_forecast_demand()` - Checks forecast freshness (<7 days) in InventoryService
- ✅ `_batch_get_latest_forecast_demand()` - Batch forecast lookup in DashboardService
- ✅ `_trigger_forecast_refresh()` - Background forecast refresh (non-blocking) in both services
- ✅ Auto-refresh: Detects stale forecasts and triggers refresh automatically
- ✅ `using_forecast` field in `ProductResponse` schema
- ✅ `_validate_forecasts()` - Comprehensive forecast validation in DataValidationService

**Files Modified:**
- ✅ `backend/services/inventory_service.py` - Forecast integration + auto-refresh
- ✅ `backend/services/dashboard_service.py` - Forecast integration + auto-refresh
- ✅ `backend/services/recommendations_service.py` - Forecast integration + auto-refresh
- ✅ `backend/services/data_validation_service.py` - Forecast validation
- ✅ `backend/schemas/inventory.py` - Added `using_forecast` field
- ✅ `backend/tests/test_services/test_forecast_integration.py` - Integration tests

**Documentation Created:**
- ✅ `docs/backend/FORECAST_ACCURACY_TRACKING.md` - Accuracy tracking guide

**Estimated Time:** 3-5 days  
**Status:** ✅ **100% COMPLETE** - All forecast integration tasks completed, including testing and accuracy tracking

---

### 3. Frontend Polish (Charts, Row Actions, Filters) - **WEEK 3** (OPTIONAL)
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

### 2. Empty State Handling (Backend + Frontend) - **WEEK 2** ⬇️ (DEFERRED)
**Goal:** Unblock onboarding and improve first-time user experience

**Why Second:** When users first start the application, they see empty states. Without proper handling, this creates confusion and poor UX. **Note:** Frontend tasks are optional if frontend is not a priority.

**Backend Tasks:**
- [ ] Create system status endpoint: `GET /api/v1/system/status`
  - **Authentication:** Requires JWT token (`Authorization: Bearer <token>`)
  - **Access:** Authenticated users only (uses `get_current_client` dependency)
  - **Response Schema:**

    ```python
    class SystemStatusResponse(BaseModel):
        initialized: bool  # True if any data exists
        has_products: bool  # True if products table has records
        has_locations: bool  # True if locations table has records
        has_suppliers: bool  # True if suppliers table has records
        has_sales_data: bool  # True if ts_demand_daily has records
        has_stock_levels: bool  # True if stock_levels has records
        setup_instructions: Optional[str] = None  # Guidance for first-time setup
        data_quality: Optional[Dict[str, Any]] = None  # Basic data quality metrics
    ```

  - **Implementation:** Check each table for existence of records filtered by `client_id`
  - **Location:** Add to `backend/api/monitoring.py` or create `backend/api/system.py`
  - **Schema File:** Add `SystemStatusResponse` to `backend/schemas/monitoring.py` or new schema file
- [ ] Enhance API responses with helpful messages when data is empty
  - Dashboard: "No inventory data yet. Set up ETL sync to connect your data source."
  - Products: "No products found. Configure ETL sync to import your product catalog."
  - Recommendations: "No recommendations available. Ensure ETL sync is running and data is loaded."

**Frontend Tasks:** (OPTIONAL - Skip if frontend not a priority)
- [ ] Create reusable `EmptyState.vue` component
- [ ] Add empty states to Dashboard, Inventory, and Recommendations pages
  - Show clear message: "No data available. Set up ETL sync to connect your data source."
  - Link to ETL configuration page (if exists) or show setup instructions
  - Display sync status if ETL is configured but not yet synced
- [ ] Add contextual help messages (not full onboarding flow)
  - Tooltips explaining what each section needs
  - Link to [Data Requirements](../DATA_REQUIREMENTS.md) documentation
  - Show "Waiting for sync" status when ETL is configured but no data yet
- [ ] Call system status API to detect initialization state

**Deliverables:**
- System status endpoint working
- Empty state components in all pages with ETL-focused messaging (frontend optional)
- Contextual help and setup guidance (no complex onboarding flow)
- Clear messaging about ETL sync status

**Estimated Time:** 1 week

---

### 4. ETL Scheduling - **WEEK 4**
**Goal:** Enable production data sync from external sources

**Why Fourth:** After data validation is in place, we can safely set up automated ETL. This enables production deployment.

**Backend Tasks:**
- [x] **Fix Critical ETL Bug - location_id Missing in Sales History Sync:** ✅ **FIXED - 2025-12-17**
  - **Issue:** `ETLService.sync_sales_history()` did not include `location_id` in insert query
  - **Impact:** Would cause database constraint violations (primary key includes `location_id`)
  - **Location:** `backend/services/etl/etl_service.py`
  - **Fix Applied:**
    1. ✅ Extract `location_id` from external data (line 76: defaults to "UNSPECIFIED")
    2. ✅ Include `location_id` in validated_row dict
    3. ✅ Add `location_id` to INSERT statement (line 124)
    4. ✅ Update ON CONFLICT clause to use correct primary key: `(client_id, item_id, location_id, date_local)` (line 126)
  - **Reference:** Migration `1a2b3c4d5e6f_add_location_id_to_ts_demand_daily.py` defines primary key as `(client_id, item_id, location_id, date_local)`
- [ ] **Complete Connector Implementations:**
  - **Issue:** BigQuery and SQL connectors have placeholder `TODO` implementations
  - **Location:** `backend/services/etl/connectors.py`
  - **Fix Required:**
    - Implement actual queries in `BigQueryConnector.fetch_sales_history()`, `fetch_products()`, `fetch_stock_levels()`, `fetch_locations()`
    - Implement actual queries in `SQLConnector.fetch_sales_history()`, `fetch_products()`, `fetch_stock_levels()`, `fetch_locations()`
    - Ensure all methods return proper data structures matching expected schema
    - Add proper error handling and connection management
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
| **Week 1** | Data Validation | Validation service, quality checks, completeness checks, **computed metrics validation (DIR, stockout risk, status)** |
| **Week 2** | Empty State Handling | System status endpoint, empty state components (frontend optional) |
| **Week 3** | Frontend Polish (Optional) | Charts with real data, complete inventory features, cart integration |
| **Week 4** | ETL Scheduling | Automated daily sync, status tracking, error handling |

**Total Timeline:** 4 weeks to production-ready MVP

---

## Success Criteria

### Week 1: Data Validation
- ✅ Data quality checks catch common issues
- ✅ Completeness checks identify orphaned records
- ✅ **Computed metrics validation ensures DIR, stockout risk, status, and inventory value are calculated correctly**
- ✅ **Frontend-backend consistency checks verify displayed values match API responses**
- ✅ Validation reports are actionable with computed metrics validation results
- ✅ Validation can be run on-demand

### Week 2: Empty State Handling
- ✅ System status endpoint returns accurate initialization state
- ✅ All pages show helpful empty states when no data exists (frontend optional)
- ✅ Clear messaging about ETL sync setup (no complex onboarding flow needed)
- ✅ Setup instructions and data requirements accessible from UI (frontend optional)

### Week 3: Frontend Polish (Optional)
- ✅ Dashboard charts display real trend data
- ✅ Inventory table has all actions (view, edit, add to cart)
- ✅ Export functionality works
- ✅ Cart badge shows item count
- ✅ Navigation is seamless

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
- [Data Requirements](DATA_REQUIREMENTS.md) - **User-facing guide** on what data is required vs. app-managed

---

## Notes

- **Data Validation** is prioritized first because it's backend-only, critical for data integrity, and required before ETL automation
- **Empty State Handling** is second - backend system status endpoint is useful, frontend tasks are optional if frontend is not a priority
- **Frontend Polish** is optional - can be deferred if frontend is not a priority
- **ETL Scheduling** is last because it requires data validation to be in place first

---

**Document Owner:** Development Team  
**Last Updated:** 2025-12-17  
**Next Review:** After Week 2 completion (Forecast Integration ✅ Complete)
