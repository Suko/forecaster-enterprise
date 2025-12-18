# Test Plan for Inventory Management APIs

**Version:** 1.0  
**Last Updated:** 2025-12-10  
**Status:** ✅ Backend MVP Complete - Test Suite Implemented  
**Scope:** Phases 1-4 (Inventory APIs, Order Planning, Purchase Orders, Settings)

---

## Overview

This test plan covers comprehensive testing of all inventory management APIs implemented in Phases 1-4. The plan includes unit tests, integration tests, and API endpoint tests.

---

## Testing Strategy

### Test Levels

1. **Unit Tests** - Test individual service methods in isolation
2. **Integration Tests** - Test service interactions with database
3. **API Tests** - Test HTTP endpoints with authentication

### Test Framework

- **Framework:** pytest with pytest-asyncio
- **HTTP Client:** httpx.AsyncClient
- **Database:** SQLite (in-memory) for fast tests, PostgreSQL for integration tests
- **Fixtures:** Shared test fixtures in `tests/conftest.py`

---

## Test Coverage by Phase

### Phase 1 & 2: Inventory APIs

#### Products API Tests
- [ ] `test_get_products` - List products with pagination
- [ ] `test_get_products_with_filters` - Filter by category, status, supplier
- [ ] `test_get_products_with_search` - Global search functionality
- [ ] `test_get_products_with_sorting` - Sort by various fields
- [ ] `test_get_product_detail` - Get single product by item_id
- [ ] `test_get_product_metrics` - Get product metrics (DIR, risk, etc.)
- [ ] `test_get_product_suppliers` - Get suppliers for a product
- [ ] `test_add_product_supplier` - Add supplier to product
- [ ] `test_update_product_supplier` - Update supplier conditions
- [ ] `test_remove_product_supplier` - Remove supplier from product
- [ ] `test_get_products_unauthorized` - Test authentication required
- [ ] `test_get_products_wrong_client` - Test multi-tenant isolation

#### Dashboard API Tests
- [ ] `test_get_dashboard` - Get dashboard KPIs
- [ ] `test_dashboard_metrics_accuracy` - Verify KPI calculations
- [ ] `test_dashboard_top_products` - Verify top understocked/overstocked
- [ ] `test_dashboard_empty_data` - Handle empty inventory gracefully
- [ ] `test_dashboard_unauthorized` - Test authentication required

#### Metrics Service Tests
- [ ] `test_calculate_dir` - Days of Inventory Remaining calculation
- [ ] `test_calculate_stockout_risk` - Risk score calculation
- [ ] `test_determine_status` - Product status classification
- [ ] `test_calculate_inventory_value` - Inventory value calculation
- [ ] `test_compute_product_metrics` - Full metrics computation

### Phase 3: Order Planning & Purchase Orders

#### Cart API Tests
- [ ] `test_add_to_cart` - Add item to cart
- [ ] `test_add_to_cart_invalid_supplier` - Validate supplier exists
- [ ] `test_add_to_cart_below_moq` - Validate MOQ requirement
- [ ] `test_get_cart` - Get cart items
- [ ] `test_get_cart_grouped_by_supplier` - Verify supplier grouping
- [ ] `test_update_cart_item` - Update cart item quantity
- [ ] `test_update_cart_item_below_moq` - Validate MOQ on update
- [ ] `test_remove_from_cart` - Remove item from cart
- [ ] `test_clear_cart` - Clear entire cart
- [ ] `test_cart_session_isolation` - Test session-based isolation
- [ ] `test_cart_unauthorized` - Test optional authentication

#### Order Suggestions Tests
- [ ] `test_get_order_suggestions` - Get order suggestions
- [ ] `test_order_suggestions_calculation` - Verify suggestion logic
- [ ] `test_order_suggestions_filtering` - Filter by location, risk
- [ ] `test_order_suggestions_empty` - Handle no suggestions gracefully

#### Recommendations API Tests
- [ ] `test_get_recommendations` - Get all recommendations
- [ ] `test_get_recommendations_by_type` - Filter by type (REORDER, etc.)
- [ ] `test_get_recommendations_by_role` - Filter by role (CEO, PROCUREMENT, etc.)
- [ ] `test_recommendations_priority_sorting` - Verify priority ordering
- [ ] `test_dismiss_recommendation` - Dismiss a recommendation
- [ ] `test_recommendations_empty` - Handle no recommendations

#### Purchase Orders API Tests
- [ ] `test_create_purchase_order` - Create PO from items
- [ ] `test_create_purchase_order_from_cart` - Create PO from cart
- [ ] `test_create_po_validation` - Validate MOQ, supplier, etc.
- [ ] `test_get_purchase_orders` - List purchase orders
- [ ] `test_get_purchase_orders_filtered` - Filter by status, supplier
- [ ] `test_get_purchase_order_detail` - Get PO details
- [ ] `test_update_po_status` - Update PO status
- [ ] `test_update_po_status_invalid` - Validate status transitions
- [ ] `test_create_po_removes_from_cart` - Verify cart cleanup

### Phase 4: Settings

#### Settings API Tests
- [ ] `test_get_settings` - Get client settings
- [ ] `test_update_settings` - Update settings
- [ ] `test_update_settings_validation` - Validate threshold constraints
- [ ] `test_get_recommendation_rules` - Get recommendation rules
- [ ] `test_update_recommendation_rules` - Update recommendation rules
- [ ] `test_settings_affect_recommendations` - Verify rules affect recommendations
- [ ] `test_settings_defaults` - Test default settings creation

---

## Test Data Requirements

### Fixtures Needed

1. **Test Client** - Created in `conftest.py`
2. **Test User** - Created in `conftest.py` with client_id
3. **Test Products** - Sample products with various statuses
4. **Test Suppliers** - Sample suppliers
5. **Test Stock Levels** - Stock levels for testing metrics
6. **Test Product-Supplier Links** - MOQ, lead time data
7. **Test Sales History** - `ts_demand_daily` data for forecasting

### Test Data Setup

Use `tests/fixtures/test_inventory_data.py` for reusable test data factories.

---

## Test Execution

### Run All Tests
```bash
cd forecaster_enterprise/backend
uv run pytest
```

### Run Specific Test File
```bash
uv run pytest tests/test_api/test_inventory_api.py
```

### Run with Coverage
```bash
uv run pytest --cov=. --cov-report=html
```

### Run Integration Tests (PostgreSQL)
```bash
TEST_POSTGRES=true uv run pytest tests/test_api/
```

### Run Specific Test
```bash
uv run pytest tests/test_api/test_inventory_api.py::test_get_products
```

---

## Test Organization

### Directory Structure
```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── test_data_loader.py       # CSV data loader
│   └── test_inventory_data.py     # Inventory test data factories
├── test_api/
│   ├── test_inventory_api.py      # Products, Dashboard APIs
│   ├── test_orders_api.py          # Cart, Suggestions, Recommendations
│   ├── test_purchase_orders_api.py # Purchase Orders API
│   └── test_settings_api.py       # Settings API
├── test_services/
│   ├── test_inventory_service.py   # InventoryService tests
│   ├── test_metrics_service.py     # MetricsService tests
│   ├── test_cart_service.py        # CartService tests
│   ├── test_recommendations_service.py # RecommendationsService tests
│   └── test_purchase_order_service.py  # PurchaseOrderService tests
└── test_models/
    └── test_inventory_models.py    # Model validation tests
```

---

## Success Criteria

### Coverage Goals
- **Unit Tests:** >80% code coverage for services
- **API Tests:** 100% endpoint coverage
- **Integration Tests:** All critical workflows tested

### Quality Goals
- All tests pass consistently
- Tests run in < 5 minutes (unit tests)
- Tests are isolated and independent
- Tests use realistic data
- Tests verify error handling

---

## Known Test Gaps

1. **Cart API** - Needs products with suppliers in test data
2. **Purchase Orders** - Needs cart items or manual item creation
3. **Product-Supplier CRUD** - POST/DELETE operations need verification
4. **Recommendation Dismiss** - Needs recommendation ID from actual recommendations

---

## Next Steps

1. ✅ Create test plan (this document)
2. ✅ Create test fixtures for inventory data
3. ✅ Implement API endpoint tests (Inventory API - 9/9 passing)
4. ✅ Implement unit tests for services
5. ✅ Add integration tests for workflows
6. ✅ Create remaining API test files (Orders, Purchase Orders, Settings)
7. ⏳ Set up CI/CD test execution (not now)
8. ✅ Generate coverage reports

---

## Related Documents

- [Backend/Frontend Compatibility & Blockers](../../system/BACKEND_FRONTEND_COMPATIBILITY.md) - Current smoke testing commands
- [BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md) - Implementation roadmap
- [ARCHITECTURE.md](../../backend/ARCHITECTURE.md) - System architecture
