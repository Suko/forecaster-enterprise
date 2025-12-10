# Backend Development Roadmap

**Last Updated:** 2025-12-10  
**Status:** ✅ **BACKEND MVP COMPLETE** - Ready for Frontend Integration  
**Scope:** Complete backend system for inventory forecasting and management platform

---

## Quick Summary

This roadmap covers the **complete backend implementation** for the inventory forecasting and management platform, organized into 4 MVP phases:

- **Phase 1 (Week 1):** Data Foundation & Sync - Database models + ETL pipeline ✅ **COMPLETE**
- **Phase 2 (Week 2):** Core Inventory APIs - Products, Dashboard, Metrics ✅ **COMPLETE**
- **Phase 3 (Week 3):** Order Planning & Management - Cart, Purchase Orders, Recommendations ✅ **COMPLETE**
- **Phase 4 (Week 4):** Settings & Configuration - Thresholds, Rules ✅ **COMPLETE**

**Total MVP Timeline:** 4 weeks  
**Focus:** Enable complete ordering workflow from data sync → dashboard → recommendations → order creation

**MVP Status:** ✅ **COMPLETE** - All APIs implemented, tested, and ready for frontend integration

> **🎯 Next Step:** Frontend Integration - See [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)

> **Note:** The forecasting engine itself is already implemented. This roadmap focuses on the **inventory management and ordering system** that uses the forecasts.

---

## ⚠️ CRITICAL: Field Naming Convention

**The forecasting engine uses `item_id` as the product identifier throughout the system:**

- `ts_demand_daily.item_id` - Time series data
- `forecast_results.item_id` - Forecast outputs
- `sku_classifications.item_id` - SKU classifications
- All forecasting services expect `item_id`

**All new tables and APIs MUST use `item_id` (not `sku`) to maintain consistency with the forecasting engine.**

- ✅ **Correct:** `products.item_id`, `stock_levels.item_id`, `purchase_order_items.item_id`
- ❌ **Wrong:** `products.sku`, `stock_levels.sku` (will break forecasting integration)

**Optional:** Add `sku` column as an alias for external systems, but `item_id` is the canonical identifier.

---

## Current Status Overview

| Component | Status | Notes |
|----------|--------|-------|
| **Forecasting Engine** | ✅ Complete | Chronos-2, statistical methods, SKU classification |
| **Authentication** | ✅ Complete | JWT, service auth, user management |
| **Database Models** | ✅ Complete | All Phase 1 models created (Products, Suppliers, Orders, etc.) |
| **Database Migrations** | ✅ Complete | Inventory tables + ts_demand_daily optimization + stock_on_date |
| **Test Data Setup** | ✅ Complete | `setup_test_data.py` script + test fixtures |
| **Products API** | ✅ Complete | GET /products, GET /products/{item_id}, GET /products/{item_id}/metrics |
| **Product-Supplier API** | ✅ Complete | CRUD operations for product-supplier conditions |
| **Dashboard API** | ✅ Complete | GET /dashboard with KPIs and top products |
| **Metrics Service** | ✅ Complete | DIR, stockout risk, status calculation |
| **Order Planning Cart** | ✅ Complete | Cart management API (add, update, remove, clear) |
| **Order Suggestions** | ✅ Complete | GET /order-planning/suggestions |
| **Recommendations API** | ✅ Complete | GET /recommendations with filtering by type and role |
| **Purchase Orders API** | ✅ Complete | Create, list, get details, update status |
| **Settings API** | ✅ Complete | GET/PUT settings and recommendation rules |
| **API Testing** | ✅ Complete | Automated test suite (`test_all_apis.py`) - 10/10 core endpoints passing |
| **ETL Service Structure** | ✅ Complete | Base connectors and ETLService implemented |
| **ETL API Endpoints** | ✅ Complete | Sales history, products, stock levels, locations sync endpoints |
| **ETL Connectors** | ✅ Complete | BigQuery and SQL connector interfaces (implementation pending) |
| **ETL Scheduling** | ⏳ Phase 5 | Daily sync job (cron/scheduler or Celery) - Next |
| **Data Validation** | ⏳ Phase 5 | Data quality and completeness checks - Next |

---

## Overview

This roadmap covers the complete backend implementation for the inventory forecasting and management platform, including:
- Data synchronization (ETL)
- Database models and relationships
- API endpoints for all features
- Business logic and workflows
- Integration with forecasting engine

---

## MVP Backend Plan (Phase 1-4)

### Phase 1: Data Foundation & Test Data (Week 1)

**Goal:** Set up core database models and test data for development

> **Important:** The time series sales data table **already exists** as `ts_demand_daily`. 
> - **⚠️ CRITICAL:** The forecasting engine uses `item_id` as the product identifier throughout:
>   - `ts_demand_daily.item_id`
>   - `forecast_results.item_id`
>   - `sku_classifications.item_id`
> - **All new tables MUST use `item_id` (not `sku`) to maintain consistency with forecasting engine**
> - Field mapping: `item_id` = product identifier, `date_local` = date, `units_sold` = quantity
> - No need to create a new `sales_history` table
> - May need migration to add `location_id` and `revenue` columns if required

#### 1.1 Database Models

**Priority: P0 - Critical**

Following existing architecture pattern: `models/` directory with SQLAlchemy models

- [ ] **Sales History Model** (`models/sales.py`) - **USE EXISTING TABLE**
  - **Table: `ts_demand_daily`** (already exists)
  - **Existing fields:** `item_id` (product identifier), `date_local`, `units_sold`, `client_id`, `promotion_flag`, `holiday_flag`, `is_weekend`, `marketing_spend`
  - **⚠️ CRITICAL:** The forecasting engine uses `item_id` throughout:
    - `ts_demand_daily.item_id`
    - `forecast_results.item_id`
    - `sku_classifications.item_id`
    - All forecasting services expect `item_id`
  - **Migration needed:** 
    - Add `location_id` and `revenue` columns if required
    - **Optimize indexes for forecasting queries** (see below)
  - **Model:** Create SQLAlchemy model to match existing table structure
  - Follow existing model pattern (Base, GUID from `models/forecast.py`)
  - **Current indexes:** `(client_id, item_id)`, `(date_local)`, `(client_id, date_local)`
  
  - [ ] **Forecasting Query Optimizations** (Critical for Performance)
    - **Composite index for common query pattern:**
      - `(client_id, item_id, date_local)` - Optimizes: `WHERE client_id = X AND item_id IN (...) AND date_local BETWEEN ...`
      - This covers the most common forecasting query: fetch all data for specific items within date range
      - Supports efficient range scans and sorting by `item_id, date_local`
    
    - **If location_id is added:**
      - Composite index: `(client_id, location_id, item_id, date_local)`
      - For multi-location forecasting queries
    
    - **Covering index for bulk operations:**
      - Consider including frequently selected columns: `(client_id, item_id, date_local) INCLUDE (units_sold, promotion_flag, holiday_flag)`
      - Reduces need to access table data (PostgreSQL only)
    
    - **Partitioning consideration** (for very large datasets):
      - Partition by `date_local` (monthly or quarterly)
      - Improves query performance for date-range queries
      - Only needed if table grows to millions of rows per client
    
    - **Query pattern analysis:**
      - Forecasting engine queries: `WHERE client_id = X AND item_id IN (...) AND date_local BETWEEN ... ORDER BY item_id, date_local`
      - Current indexes may not fully optimize this pattern
      - Composite index `(client_id, item_id, date_local)` is optimal

- [x] **Products Model** (`models/product.py`) ✅
  - Table: `products`
  - Fields: `id`, `client_id` (UUID FK), `item_id` (PRIMARY IDENTIFIER), `sku` (optional alias), `product_name`, `category`, `unit_cost`, `created_at`, `updated_at`
  - **⚠️ CRITICAL:** Use `item_id` as the primary field name to match forecasting engine
    - `item_id` must match `ts_demand_daily.item_id`
    - `item_id` must match `forecast_results.item_id`
    - `item_id` must match `sku_classifications.item_id`
  - **Optional:** Add `sku` column as alias for external systems (if different from `item_id`)
  - Unique constraint: `(client_id, item_id)`
  - Defaults: category → "Uncategorized", unit_cost → 0
  - **Note:** `item_id` is the canonical identifier used by forecasting engine. `sku` is optional alias.
  - Use existing Base, GUID patterns

- [x] **Locations Model** (`models/location.py`) ✅
  - Table: `locations`
  - Fields: `id`, `client_id` (UUID FK), `location_id` (external), `name`, `address`, `city`, `country`, `is_synced`, `created_at`
  - Unique constraint: `(client_id, location_id)`

- [x] **Stock Levels Model** (`models/stock.py`) ✅
  - Table: `stock_levels`
  - Fields: `id`, `client_id` (UUID FK), `item_id` (maps to `ts_demand_daily.item_id`), `location_id`, `current_stock`, `updated_at`
  - Unique constraint: `(client_id, item_id, location_id)`
  - **⚠️ CRITICAL:** Use `item_id` (not `sku`) to match forecasting engine
  - Foreign key: `item_id` → `products.item_id`

- [x] **Suppliers Model** (`models/supplier.py`) ✅
  - Table: `suppliers`
  - Fields: `id`, `client_id` (UUID FK), `external_id`, `name`, `contact_email`, `contact_phone`, `address`, `supplier_type`, `is_synced`, `created_at`
  - Unique constraints: `(client_id, name)`, `(client_id, external_id)`

- [x] **Product Supplier Conditions Model** (`models/product_supplier.py`) ✅
  - Table: `product_supplier_conditions`
  - Fields: `id`, `client_id` (UUID FK), `item_id` (maps to `ts_demand_daily.item_id`), `supplier_id` (FK), `moq`, `lead_time_days`, `supplier_sku`, `supplier_cost`, `packaging_unit`, `packaging_qty`, `is_primary`, `notes`, `created_at`, `updated_at`
  - Unique constraint: `(client_id, item_id, supplier_id)`
  - Foreign keys: `item_id` → `products.item_id`, `supplier_id` → `suppliers.id`
  - **⚠️ CRITICAL:** Use `item_id` (not `sku`) to match forecasting engine

- [x] **Client Settings Model** (`models/settings.py`) ✅
  - Table: `client_settings`
  - Fields: `id`, `client_id` (UUID FK, unique), `safety_buffer_days`, `understocked_threshold`, `overstocked_threshold`, `dead_stock_days`, `recommendation_rules` (JSONBType), `created_at`, `updated_at`
  - Unique constraint: `(client_id)`

- [x] **Inventory Metrics Model** (`models/inventory_metrics.py`) ✅
  - Table: `inventory_metrics`
  - Fields: `id`, `client_id` (UUID FK), `item_id` (maps to `ts_demand_daily.item_id`), `location_id`, `date`, `current_stock`, `dir`, `stockout_risk`, `forecasted_demand_30d`, `inventory_value`, `status`, `computed_at`
  - Indexes: `(client_id, item_id, location_id, date)`, `(status)`
  - Purpose: Store computed metrics for fast dashboard queries
  - **⚠️ CRITICAL:** Use `item_id` (not `sku`) to match forecasting engine
  - Foreign key: `item_id` → `products.item_id`

- [x] **Purchase Orders Model** (`models/purchase_order.py`) ✅
  - Table: `purchase_orders`
  - Fields: `id`, `client_id` (UUID FK), `po_number`, `supplier_id` (FK), `status`, `order_date`, `expected_delivery_date`, `total_amount`, `shipping_method`, `shipping_unit`, `notes`, `created_by`, `created_at`, `updated_at`
  - Table: `purchase_order_items`
  - Fields: `id`, `po_id` (FK), `item_id` (FK to products.item_id), `quantity`, `unit_cost`, `total_price`, `packaging_unit`, `packaging_qty`
  - **⚠️ CRITICAL:** Use `item_id` (not `sku`) to match forecasting engine

#### 1.2 Test Data Setup

**Priority: P0 - Critical**

- [x] **Test Data Script** (`scripts/setup_test_data.py`) ✅
  - Create test client (or use existing demo client)
  - Generate sample products (20-50 SKUs) -I think we have them
  - **Generate sample `ts_demand_daily` data** (3+ weeks of data)
    - Use existing `import_csv_to_ts_demand_daily.py` pattern or direct SQL inserts
    - Fields: `item_id` (SKU), `date_local`, `units_sold`, `client_id`
    - Optionally add covariates: `promotion_flag`, `holiday_flag`, `is_weekend`
  - Generate sample stock levels
  - Generate sample locations (2-3 locations)
  - Generate sample suppliers (3-5 suppliers)
  - Link products to suppliers with MOQ/lead time
  - Set default client settings

- [x] **Test Data Fixtures** (`tests/fixtures/test_inventory_data.py`) ✅
  - Reusable test data for unit tests
  - Factory functions for creating test records
  - Follow existing test fixture patterns

#### 1.3 Database Migrations

**Priority: P0 - Critical**

- [x] **Create Alembic Migrations** ✅
  - Migration: `269603316338_add_inventory_management_tables.py`
  - Creates all inventory management tables
  - Multi-tenant support (client_id on all tables)
  - Tested migration structure

- [x] **Optimize `ts_demand_daily` for Forecasting** (Critical) ✅
  - Migration: `95dfb658e5b7_optimize_ts_demand_daily_for_forecasting.py`
  - Added composite index: `(client_id, item_id, date_local)`
  - Optimizes forecasting engine queries

- [x] **Add `stock_on_date` to `ts_demand_daily`** ✅
  - Migration: `92b51207e018_add_stock_at_end_of_day_to_ts_demand_.py`
  - Added `stock_on_date` column for stockout detection
  - Can be synced from external systems or manually updated

---

### Phase 2: Core Inventory APIs (Week 2)

**Goal:** Enable viewing and managing inventory data

Following existing architecture:
- **API Layer:** `api/inventory.py` (route handlers)
- **Schema Layer:** `schemas/inventory.py` (Pydantic models)
- **Service Layer:** `services/inventory_service.py` (business logic)
- **Model Layer:** `models/` (SQLAlchemy models)

**Goal:** Enable viewing and managing inventory data

#### 2.1 Products API

**Priority: P0 - Critical**

**Architecture Pattern:**
- Route: `api/inventory.py` → `get_products()`, `get_product()`, `get_product_metrics()`
- Schema: `schemas/inventory.py` → `ProductResponse`, `ProductListResponse`, `ProductFilters`
- Service: `services/inventory_service.py` → `InventoryService.get_products()`, `get_product()`
- Model: `models/product.py` → `Product` (SQLAlchemy)

- [x] **GET /api/v1/products** ✅
  - Route handler: `api/inventory.py::get_products()`
  - Dependency: `get_current_client()` (from `auth/dependencies.py`)
  - Query params: 
    - `page`, `page_size` (pagination)
    - `search` (global search across SKU, name, category)
    - `category` (filter by category)
    - `supplier_id` (filter by supplier)
    - `location_id` (filter by location)
    - `status` (understocked/overstocked/normal)
    - `sort` (column name)
    - `order` (asc/desc)
    - `min_dir`, `max_dir` (range filter)
    - `min_risk`, `max_risk` (range filter)
    - `min_stock`, `max_stock` (range filter)
  - Service: `InventoryService.get_products(client_id, filters)`
  - Response: Paginated list with filters
  - Include: `item_id`, name, category, stock, cost, DIR, risk score, supplier, status
  - **Note:** Response uses `item_id` (not `sku`) to match forecasting engine
  - Support for data table requirements:
    - Sortable columns (any field)
    - Filterable columns (text, numeric, categorical)
    - Multi-column sorting
    - Export filtered/sorted results

- [x] **GET /api/v1/products/{item_id}** ✅
  - Route handler: `api/inventory.py::get_product()`
  - Service: `InventoryService.get_product(client_id, item_id)`
  - Response: Full product details
  - Include: All fields + history + campaigns + orders
  - **Note:** Parameter is `item_id` to match forecasting engine

- [x] **GET /api/v1/products/{item_id}/metrics** ✅
  - Route handler: `api/inventory.py::get_product_metrics()`
  - Service: `InventoryService.get_product_metrics(client_id, item_id)`
  - Response: DIR, stockout risk, forecasted demand, inventory value
  - Computed on-the-fly or from `inventory_metrics` table
  - **Note:** Parameter is `item_id` to match forecasting engine

#### 2.2 Dashboard API

**Priority: P0 - Critical**

**Architecture Pattern:**
- Route: `api/inventory.py` → `get_dashboard()`
- Schema: `schemas/inventory.py` → `DashboardResponse`
- Service: `services/inventory_service.py` → `InventoryService.get_dashboard()`

- [x] **GET /api/v1/dashboard** ✅
  - Route handler: `api/inventory.py::get_dashboard()`
  - Dependency: `get_current_client()`
  - Service: `InventoryService.get_dashboard(client_id)`
  - Response:
    ```json
    {
      "metrics": {
        "total_skus": int,
        "total_inventory_value": decimal,
        "understocked_count": int,
        "overstocked_count": int,
        "average_dir": decimal,
        "understocked_value": decimal,
        "overstocked_value": decimal
      },
      "top_understocked": [...],
      "top_overstocked": [...]
    }
    ```
  - Logic:
    - Aggregate from `inventory_metrics` or compute on-the-fly
    - Top 5 understocked (sorted by risk score)
    - Top 5 overstocked (sorted by DIR desc)

#### 2.3 Inventory Metrics Calculation

**Priority: P0 - Critical**

**Architecture Pattern:**
- Service: `services/inventory_metrics_service.py` (business logic)
- Domain: `forecasting/applications/inventory/` (if complex calculations)

- [x] **Inventory Metrics Service** ✅
  - Created `services/metrics_service.py`
  - Class: `MetricsService`
  - Methods:
    - `calculate_dir()` - Calculates Days of Inventory Remaining
    - `calculate_stockout_risk()` - Risk score based on DIR vs lead time + buffer
    - `determine_status()` - Classifies products (understocked/overstocked/normal/dead_stock)
    - `calculate_inventory_value()` - Stock × unit cost
    - `compute_product_metrics()` - Computes all metrics for a product
  - Uses client settings for thresholds
  - Queries `ts_demand_daily` for historical demand

- [x] **Dashboard Service** ✅
  - Created `services/dashboard_service.py`
  - Class: `DashboardService`
  - Method: `get_dashboard_data()` - Aggregates KPIs and top products

- [ ] **GET /api/v1/inventory/metrics/refresh**
  - Route handler: `api/inventory.py` → `refresh_metrics()`
  - Service: `InventoryMetricsService.compute_all_metrics(client_id)`
  - Manual trigger to recalculate all metrics
  - Background job with status tracking (use Celery or async task)

#### 2.4 Suppliers API

**Priority: P1 - High**

**Architecture Pattern:**
- Route: `api/suppliers.py` → `get_suppliers()`, `get_supplier()`, `create_supplier()`, etc.
- Schema: `schemas/supplier.py` → `SupplierResponse`, `SupplierCreate`, `SupplierUpdate`
- Service: `services/supplier_service.py` → `SupplierService`

- [ ] **GET /api/v1/suppliers**
  - Route handler: `api/suppliers.py::get_suppliers()`
  - Service: `SupplierService.get_suppliers(client_id, filters)`
  - Query params: `page`, `page_size`, `search`
  - Response: Paginated list of suppliers

- [ ] **GET /api/v1/suppliers/{id}**
  - Route handler: `api/suppliers.py::get_supplier()`
  - Service: `SupplierService.get_supplier(client_id, supplier_id)`
  - Response: Supplier details + products + order history

- [ ] **POST /api/v1/suppliers**
  - Route handler: `api/suppliers.py::create_supplier()`
  - Service: `SupplierService.create_supplier(client_id, data)`
  - Body: `name`, `contact_email`, `contact_phone`, `address`, `supplier_type`
  - Create new supplier (app-managed, `is_synced = false`)

- [ ] **PUT /api/v1/suppliers/{id}**
  - Route handler: `api/suppliers.py::update_supplier()`
  - Service: `SupplierService.update_supplier(client_id, supplier_id, data)`
  - Update supplier (only if `is_synced = false`)

- [ ] **GET /api/v1/suppliers/{id}/products**
  - Route handler: `api/suppliers.py::get_supplier_products()`
  - Service: `SupplierService.get_supplier_products(client_id, supplier_id)`
  - Get all products from this supplier
  - Include MOQ, lead time, conditions

#### 2.5 Product-Supplier Conditions API

**Priority: P0 - Critical**

**Architecture Pattern:**
- Route: `api/inventory.py` → product-supplier endpoints
- Schema: `schemas/inventory.py` → `ProductSupplierResponse`, `ProductSupplierCreate`
- Service: `services/inventory_service.py` → `InventoryService` methods

- [x] **GET /api/v1/products/{item_id}/suppliers** ✅
  - Route handler: `api/inventory.py::get_product_suppliers()`
  - Service: `InventoryService.get_product_suppliers(client_id, item_id)`
  - Response: All suppliers for this product with conditions
  - Include: MOQ, lead time, cost, packaging
  - **Note:** Parameter is `item_id` to match forecasting engine

- [x] **POST /api/v1/products/{item_id}/suppliers** ✅
  - Route handler: `api/inventory.py::add_product_supplier()`
  - Service: `InventoryService.add_product_supplier(client_id, item_id, data)`
  - Body: `supplier_id`, `moq`, `lead_time_days`, `supplier_cost`, `packaging_unit`, `packaging_qty`, `is_primary`
  - Link product to supplier with conditions
  - Validation: Ensure supplier exists, product exists (by `item_id`)

- [x] **PUT /api/v1/products/{item_id}/suppliers/{supplier_id}** ✅
  - Route handler: `api/inventory.py::update_product_supplier()`
  - Service: `InventoryService.update_product_supplier(client_id, item_id, supplier_id, data)`
  - Update MOQ, lead time, packaging (app-managed fields)

- [x] **DELETE /api/v1/products/{item_id}/suppliers/{supplier_id}** ✅
  - Route handler: `api/inventory.py::remove_product_supplier()`
  - Service: `InventoryService.remove_product_supplier(client_id, item_id, supplier_id)`
  - Remove supplier link

---

### Phase 3: Order Planning & Management (Week 3)

**Goal:** Enable order planning and purchase order creation

Following existing architecture:
- **API Layer:** `api/orders.py` (route handlers)
- **Schema Layer:** `schemas/order.py` (Pydantic models)
- **Service Layer:** `services/order_service.py` (business logic)

#### 3.1 Order Planning API

**Priority: P0 - Critical**

- [x] **GET /api/v1/order-planning/suggestions** ✅
  - Query params: `client_id`, `location_id` (optional)
  - Response: Suggested orders based on:
    - Forecasted demand
    - Current stock
    - Lead time
    - Safety buffer
  - Logic:
    - For each SKU: Calculate suggested quantity
    - Formula: `suggested_qty = max(MOQ, forecasted_demand_30d - current_stock + safety_buffer)`
    - Filter by stockout risk

- [x] **POST /api/v1/order-planning/cart/add** ✅
  - Body: `item_id`, `supplier_id`, `quantity` (optional, defaults to MOQ)
  - Validation:
    - Check supplier exists for product (by `item_id`)
    - Validate quantity >= MOQ
    - Check DIR vs lead time + buffer
  - Add to cart (session-based or user-based)

- [x] **GET /api/v1/order-planning/cart** ✅
  - Response: Current cart items grouped by supplier
  - Include: `item_id`, name, quantity, unit_cost, total_cost, MOQ, lead_time
  - **Note:** Response uses `item_id` to match forecasting engine

- [x] **PUT /api/v1/order-planning/cart/{item_id}** ✅
  - Update quantity (validate >= MOQ)

- [x] **DELETE /api/v1/order-planning/cart/{item_id}** ✅
  - Remove item from cart

- [x] **POST /api/v1/order-planning/cart/clear** ✅
  - Clear entire cart

#### 3.2 Purchase Orders API

**Priority: P0 - Critical**

- [x] **Purchase Orders Model** ✅
  - Table: `purchase_orders`
  - Fields: `id`, `client_id`, `po_number`, `supplier_id`, `status`, `order_date`, `expected_delivery_date`, `total_amount`, `shipping_method`, `shipping_unit`, `notes`, `created_by`, `created_at`
  - Table: `purchase_order_items`
  - Fields: `id`, `po_id`, `item_id`, `quantity`, `unit_cost`, `total_price`, `packaging_unit`, `packaging_qty`

- [x] **POST /api/v1/purchase-orders** ✅
  - Body: `supplier_id`, `items[]` (each with `item_id`, `quantity`, etc.), `shipping_method`, `shipping_unit`, `notes`
  - Logic:
    - Validate all items in cart for this supplier
    - Validate quantities >= MOQ
    - Calculate totals
    - Create PO with status "pending"
    - Remove items from cart
  - Response: Created PO with ID
  - **Note:** Items use `item_id` (not `sku`) to match forecasting engine

- [x] **POST /api/v1/purchase-orders/from-cart** ✅
  - Create PO directly from cart items

- [x] **GET /api/v1/purchase-orders** ✅
  - Query params: `client_id`, `status`, `supplier_id`, `page`, `page_size`
  - Response: List of orders with summary

- [x] **GET /api/v1/purchase-orders/{id}** ✅
  - Response: Full order details with items
  - Items include `item_id` (not `sku`) to match forecasting engine

- [x] **PUT /api/v1/purchase-orders/{id}/status** ✅
  - Body: `status` (pending, confirmed, shipped, received, cancelled)
  - Update order status
  - Track status history

#### 3.3 Recommendations API

**Priority: P0 - Critical**

- [x] **GET /api/v1/recommendations** ✅
  - Query params: `client_id`, `type` (REORDER, PROMOTE, etc.), `role` (CEO, PROCUREMENT, MARKETING)
  - Response: List of recommendations
  - Logic:
    - Load recommendation rules from `client_settings`
    - Filter by role-based rules
    - Apply threshold filters
    - Generate recommendations:
      - REORDER: DIR < (lead_time + buffer)
      - URGENT: Stockout risk > 70%
      - REDUCE_ORDER: DIR > 90 days
      - DEAD_STOCK: No sales in X days
      - PROMOTE: DIR > 30 days, not in campaign
    - Sort by priority

- [x] **POST /api/v1/recommendations/{id}/dismiss** ✅
  - Mark recommendation as dismissed (don't show again)

---

### Phase 4: Settings & Configuration (Week 4)

**Goal:** Enable system configuration and thresholds

Following existing architecture:
- **API Layer:** `api/settings.py` (route handlers)
- **Schema Layer:** `schemas/settings.py` (Pydantic models)
- **Service Layer:** `services/settings_service.py` (business logic)

#### 4.1 Settings API

**Priority: P1 - High**

- [x] **GET /api/v1/settings** ✅
  - Query params: `client_id`
  - Response: Current client settings

- [x] **PUT /api/v1/settings** ✅
  - Body: `safety_buffer_days`, `understocked_threshold`, `overstocked_threshold`, `dead_stock_days`, `recommendation_rules`
  - Update client settings
  - Validate thresholds (e.g., overstocked > understocked)

#### 4.2 Recommendation Rules API

**Priority: P1 - High**

- [x] **GET /api/v1/settings/recommendation-rules** ✅
  - Get current recommendation rules

- [x] **PUT /api/v1/settings/recommendation-rules** ✅
  - Body: `enabled_types[]`, `role_rules{}`, `threshold_filters{}`
  - Update recommendation rules
  - Validate rule structure

---

## Additional Backend Features (Post-MVP)

### Phase 5: ETL Pipeline & Data Validation

**Goal:** Set up production data sync from external sources

> **Note:** For MVP (Phase 1-4), we work with test data. ETL is moved to Phase 5.

#### 5.1 Database Optimization for Forecasting

**Priority: P0 - Critical (Before ETL)**

**Goal:** Optimize `ts_demand_daily` table for forecasting query performance

- [x] **Create Optimized Indexes Migration** ✅
  - Migration file: `migrations/versions/95dfb658e5b7_optimize_ts_demand_daily_for_forecasting.py`
  - Add composite index: `(client_id, item_id, date_local)`
    - Name: `idx_ts_demand_daily_client_item_date`
    - Purpose: Optimize common forecasting query pattern
    - Query pattern: `WHERE client_id = X AND item_id IN (...) AND date_local BETWEEN ... ORDER BY item_id, date_local`
  
  - [ ] **If location_id column is added:**
    - Add composite index: `(client_id, location_id, item_id, date_local)`
    - Name: `idx_ts_demand_daily_client_location_item_date`
    - For multi-location forecasting queries
  
  - [x] **Analyze existing indexes:** ✅
    - Review current indexes: `idx_ts_demand_daily_client_item`, `idx_ts_demand_daily_date`, `idx_ts_demand_daily_client_date`
    - Composite index created and tested
    - Existing indexes kept for backward compatibility
  
  - [ ] **Performance Testing:**
    - Test query performance with EXPLAIN ANALYZE
    - Verify index usage in query plans
    - Measure improvement in forecast generation time
    - Test with realistic data volumes (100K+ rows per client)

- [ ] **Table Statistics & Maintenance**
  - Ensure `ANALYZE ts_demand_daily` runs regularly (auto-vacuum)
  - Monitor index bloat and rebuild if needed
  - Consider table partitioning if data grows beyond 10M rows per client

#### 5.2 ETL Service Structure

**Priority: P1 - High (Post-MVP)**

Following existing architecture:
- **Service Layer:** `services/etl/` (ETL business logic)
- **API Layer:** `api/etl.py` (sync endpoints)

- [x] **ETL Service Structure** ✅
  - Create `services/etl/` module
  - Base ETL connector interface: `ETLConnector` (abstract base class)
  - BigQuery connector: `BigQueryConnector(ETLConnector)`
  - Generic SQL connector: `SQLConnector(ETLConnector)` (for other sources)
  - Follow service pattern from `services/auth_service.py`

- [x] **Sales History Sync** (syncs to `ts_demand_daily` table) ✅
  - Endpoint: `POST /api/v1/etl/sync/sales-history`
  - Route handler: `api/etl.py::sync_sales_history()`
  - Service: `ETLService.sync_sales_history(client_id, start_date, end_date)`
  - Logic:
    - Fetch from external source (BigQuery/other)
    - Map external fields: `sku` → `item_id`, `date` → `date_local`, `quantity` → `units_sold`
    - Validate data (date range, SKU format, quantity > 0)
    - Upsert by `(client_id, item_id, date_local)` (existing primary key)
    - Handle duplicates (append or replace)
    - Minimum 3 weeks history required
    - **Note:** Table already exists, just need to populate it

- [x] **Products Sync** ✅
  - Endpoint: `POST /api/v1/etl/sync/products`
  - Route handler: `api/etl.py::sync_products()`
  - Service: `ETLService.sync_products(client_id)`
  - Logic:
    - Fetch from external source
    - Upsert by `(client_id, item_id)`
    - Default category to "Uncategorized" if missing
    - Default unit_cost to 0 if missing
    - Flag products with missing cost for review

- [x] **Stock Levels Sync** ✅
  - Endpoint: `POST /api/v1/etl/sync/stock-levels`
  - Route handler: `api/etl.py::sync_stock_levels()`
  - Service: `ETLService.sync_stock_levels(client_id)`
  - Logic:
    - Fetch from external source
    - Replace all stock levels (not append)
    - Validate: stock >= 0
    - Update `updated_at` timestamp

- [x] **Locations Sync** ✅
  - Endpoint: `POST /api/v1/etl/sync/locations`
  - Route handler: `api/etl.py::sync_locations()`
  - Service: `ETLService.sync_locations(client_id)`
  - Logic:
    - Fetch from external source
    - Upsert by `(client_id, location_id)`
    - Preserve app-managed locations (if `is_synced = false`)

- [ ] **Suppliers Sync (Optional)**
  - Endpoint: `POST /api/v1/etl/sync/suppliers`
  - Route handler: `api/etl.py::sync_suppliers()`
  - Service: `ETLService.sync_suppliers(client_id)`
  - Logic:
    - Fetch from external source (if available)
    - Upsert by `(client_id, external_id)`
    - Set `is_synced = true` for synced suppliers
    - Don't overwrite app-managed suppliers

- [ ] **Product-Supplier Links Sync (Optional)**
  - Endpoint: `POST /api/v1/etl/sync/product-suppliers`
  - Route handler: `api/etl.py::sync_product_supplier_links()`
  - Service: `ETLService.sync_product_supplier_links(client_id)`
  - Logic:
    - Fetch which SKUs belong to which suppliers
    - Create `product_supplier_conditions` records if not exist
    - Set `is_synced = true` flag
    - Don't overwrite MOQ, lead time (app-managed)

- [ ] **ETL Scheduling**
  - Daily sync job (cron/scheduler or Celery)
  - Error handling and retry logic
  - Sync status tracking
  - Notification on failures

#### 5.2 Data Validation

**Priority: P1 - High (Post-MVP)**

Following existing architecture:
- **Service Layer:** `services/data_validation_service.py`
- Reuse existing `forecasting/services/data_validator.py` patterns

- [ ] **Data Quality Checks**
  - Validate date ranges (min 3 weeks, max 2 years)
  - Validate SKU format
  - Check for missing required fields
  - Validate numeric ranges (quantity >= 0, cost >= 0)
  - Detect and flag outliers

- [ ] **Data Completeness Checks**
  - Ensure all `item_id` in `ts_demand_daily` exist in products (as `sku`)
  - Ensure all `location_id` in `ts_demand_daily` exist in locations (if location_id column exists)
  - Flag orphaned records

### Phase 6: Advanced Features

#### 6.1 Marketing Campaigns API

**Priority: P1 - High**

- [ ] **Campaigns Model**
  - Table: `campaigns`
  - Fields: `id`, `client_id`, `name`, `campaign_type`, `status`, `start_date`, `end_date`, `budget`, `created_at`
  - Table: `campaign_products`
  - Fields: `id`, `campaign_id`, `sku`, `discount`, `target_audience`

- [ ] **GET /api/v1/campaigns**
- [ ] **POST /api/v1/campaigns**
- [ ] **PUT /api/v1/campaigns/{id}**
- [ ] **DELETE /api/v1/campaigns/{id}**
- [ ] **GET /api/v1/campaigns/{id}/products**
- [ ] **GET /api/v1/products/campaign-status**

#### 6.2 Locations API

**Priority: P1 - High**

- [ ] **GET /api/v1/locations**
- [ ] **POST /api/v1/locations** (if app-managed)
- [ ] **GET /api/v1/products/{sku}/locations**
- [ ] **POST /api/v1/products/{sku}/locations** (assign to location)

#### 6.3 Export/Import API

**Priority: P2 - Medium**

- [ ] **GET /api/v1/products/export**
  - Query params: `format` (csv, excel), `filters` (same as GET /products)
  - Export filtered/sorted products

- [ ] **POST /api/v1/suppliers/import**
  - Body: CSV file
  - Parse and import suppliers

- [ ] **POST /api/v1/product-suppliers/import**
  - Body: CSV file
  - Parse and import product-supplier links with conditions

#### 6.4 Analytics & Reporting

**Priority: P2 - Medium**

- [ ] **GET /api/v1/analytics/inventory-trends**
  - Historical inventory value trends

- [ ] **GET /api/v1/analytics/forecast-accuracy**
  - Forecast accuracy metrics (MAPE, RMSE)

- [ ] **GET /api/v1/analytics/supplier-performance**
  - On-time delivery, order history

---

## API Endpoint Summary

### Core Inventory (P0)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/products` | GET | List products (filterable, sortable) | P0 |
| `/api/v1/products/{sku}` | GET | Product details | P0 |
| `/api/v1/products/{sku}/metrics` | GET | DIR, risk, forecast | P0 |
| `/api/v1/dashboard` | GET | Dashboard KPIs | P0 |
| `/api/v1/inventory/metrics/refresh` | POST | Recalculate metrics | P0 |

### Suppliers & Conditions (P0)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/suppliers` | GET | List suppliers | P1 |
| `/api/v1/suppliers/{id}` | GET | Supplier details | P1 |
| `/api/v1/suppliers` | POST | Create supplier | P1 |
| `/api/v1/products/{sku}/suppliers` | GET | Get suppliers for SKU | P0 |
| `/api/v1/products/{sku}/suppliers` | POST | Link SKU to supplier | P0 |
| `/api/v1/products/{sku}/suppliers/{supplier_id}` | PUT | Update MOQ/lead time | P0 |

### Order Planning (P0)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/order-planning/suggestions` | GET | Get order suggestions | P0 |
| `/api/v1/order-planning/cart` | GET | Get cart | P0 |
| `/api/v1/order-planning/cart/add` | POST | Add to cart | P0 |
| `/api/v1/order-planning/cart/{item_id}` | PUT | Update quantity | P0 |
| `/api/v1/order-planning/cart/{item_id}` | DELETE | Remove from cart | P0 |
| `/api/v1/purchase-orders` | POST | Create order | P0 |
| `/api/v1/purchase-orders` | GET | List orders | P0 |
| `/api/v1/purchase-orders/{id}` | GET | Order details | P0 |
| `/api/v1/purchase-orders/{id}/status` | PUT | Update status | P0 |

### Recommendations (P0)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/recommendations` | GET | Get recommendations | P0 |
| `/api/v1/recommendations/{id}/dismiss` | POST | Dismiss recommendation | P1 |

### Settings (P1)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/settings` | GET | Get settings | P1 |
| `/api/v1/settings` | PUT | Update settings | P1 |
| `/api/v1/settings/recommendation-rules` | GET | Get rules | P1 |
| `/api/v1/settings/recommendation-rules` | PUT | Update rules | P1 |

### ETL Sync (P0)

| Endpoint | Method | Purpose | Priority |
|----------|--------|---------|----------|
| `/api/v1/etl/sync/sales-history` | POST | Sync sales data | P0 |
| `/api/v1/etl/sync/products` | POST | Sync products | P0 |
| `/api/v1/etl/sync/stock-levels` | POST | Sync stock | P0 |
| `/api/v1/etl/sync/locations` | POST | Sync locations | P0 |
| `/api/v1/etl/sync/suppliers` | POST | Sync suppliers (optional) | P1 |
| `/api/v1/etl/sync/product-suppliers` | POST | Sync links (optional) | P1 |

---

## Database Schema Summary

### Core Tables (Required for MVP)

1. **ts_demand_daily** - Time series sales data (✅ **ALREADY EXISTS**, synced)
   - Fields: `item_id` (product identifier), `date_local`, `units_sold`, `client_id`, covariates
   - **⚠️ CRITICAL:** `item_id` is the canonical identifier used by forecasting engine
   - Note: May need to add `location_id` and `revenue` columns if required
2. **products** - Product master (new, synced)
   - **⚠️ CRITICAL:** Must use `item_id` (not `sku`) as primary field to match forecasting engine
3. **locations** - Warehouses/stores (new, synced)
4. **stock_levels** - Current inventory (new, synced)
5. **suppliers** - Supplier master (new, synced or app-managed)
6. **product_supplier_conditions** - MOQ, lead time (new, app-managed)
7. **client_settings** - Thresholds and rules (new, app-managed)
8. **purchase_orders** - Orders created in app (new)
9. **purchase_order_items** - Order line items (new)
10. **inventory_metrics** - Computed DIR, risk (new, system-generated)

### Relationships

- `products.item_id` ← `ts_demand_daily.item_id` (**CRITICAL: Must match for forecasting**)
- `products.item_id` ← `forecast_results.item_id` (**CRITICAL: Must match for forecasting**)
- `products.item_id` ← `sku_classifications.item_id` (**CRITICAL: Must match for forecasting**)
- `products.item_id` ← `stock_levels.item_id`
- `products.item_id` ← `product_supplier_conditions.item_id`
- `products.item_id` ← `inventory_metrics.item_id`
- `products.item_id` ← `purchase_order_items.item_id`
- `suppliers.id` ← `product_supplier_conditions.supplier_id`
- `locations.location_id` ← `ts_demand_daily.location_id` (if added)
- `locations.location_id` ← `stock_levels.location_id`

---

## Implementation Priorities

### MVP Must-Have (P0)

1. ✅ Database models (all core tables)
2. ✅ Test data setup (for development)
3. ✅ Products API (list, detail, metrics)
4. ✅ Dashboard API
5. ✅ Inventory metrics calculation (DIR, risk)
6. ✅ Product-supplier conditions API
7. ✅ Order planning cart API
8. ✅ Purchase orders API
9. ✅ Recommendations API
10. ✅ Settings API (basic)

**Note:** ETL sync moved to Phase 5. MVP uses test data.

### MVP Nice-to-Have (P1)

1. Suppliers API (full CRUD)
2. Recommendation rules configuration
3. Export functionality
4. Locations API
5. Campaigns API (if time permits)

### Post-MVP (P1-P2)

1. **ETL Pipeline** (Phase 5) - Production data sync
2. **Data Validation** (Phase 5) - Quality checks
3. Import functionality (Phase 6)
4. Analytics endpoints (Phase 6)
5. Advanced reporting (Phase 6)

### Post-MVP (P2)

1. Import functionality
2. Analytics endpoints
3. Advanced reporting
4. Real-time updates (WebSockets)
5. Batch operations

---

## Technical Stack

- **Framework:** FastAPI (existing)
- **Database:** PostgreSQL (with SQLite for dev/testing) - existing setup
- **ORM:** SQLAlchemy (existing)
- **Migrations:** Alembic (existing)
- **ETL:** Custom Python scripts (BigQuery client, generic SQL) - Phase 5
- **Scheduling:** Celery or cron (TBD) - Phase 5
- **Authentication:** JWT (already implemented)
- **Architecture:** Layered architecture (API → Service → Domain → Model)

## Architecture Compliance

All new code must follow existing architecture patterns:

### Directory Structure
```
backend/
├── api/                    # Route handlers (thin layer)
│   ├── inventory.py        # NEW: Inventory routes
│   ├── suppliers.py        # NEW: Supplier routes
│   ├── orders.py           # NEW: Order routes
│   └── settings.py         # NEW: Settings routes
├── schemas/                # Pydantic models
│   ├── inventory.py        # NEW: Inventory schemas
│   ├── supplier.py         # NEW: Supplier schemas
│   ├── order.py            # NEW: Order schemas
│   └── settings.py         # NEW: Settings schemas
├── services/               # Application services
│   ├── inventory_service.py        # NEW: Inventory business logic
│   ├── inventory_metrics_service.py # NEW: Metrics calculation
│   ├── supplier_service.py         # NEW: Supplier business logic
│   ├── order_service.py            # NEW: Order business logic
│   └── settings_service.py         # NEW: Settings business logic
├── models/                 # SQLAlchemy models
│   ├── product.py          # NEW: Product model
│   ├── supplier.py         # NEW: Supplier model
│   ├── stock.py            # NEW: Stock model
│   ├── location.py         # NEW: Location model
│   ├── purchase_order.py   # NEW: Purchase order models
│   └── settings.py         # NEW: Settings model
└── scripts/                # Utility scripts
    └── setup_test_data.py  # NEW: Test data generator
```

### Code Patterns

**Route Handler Pattern:**
```python
# api/inventory.py
from fastapi import APIRouter, Depends
from auth.dependencies import get_current_client
from services.inventory_service import InventoryService
from schemas.inventory import ProductResponse

router = APIRouter()

@router.get("/products", response_model=ProductResponse)
async def get_products(
    client: Client = Depends(get_current_client),
    # ... query params
):
    service = InventoryService()
    return await service.get_products(client.client_id, filters)
```

**Service Pattern:**
```python
# services/inventory_service.py
from models.product import Product
from sqlalchemy.orm import Session

class InventoryService:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db
    
    def get_products(self, client_id: UUID, filters: dict):
        query = self.db.query(Product).filter(Product.client_id == client_id)
        # Apply filters, pagination, sorting
        return query.all()
```

**Schema Pattern:**
```python
# schemas/inventory.py
from pydantic import BaseModel

class ProductResponse(BaseModel):
    sku: str
    product_name: str
    category: str
    # ... other fields
```

**Model Pattern:**
```python
# models/product.py
from models.database import Base
from models.forecast import GUID

class Product(Base):
    __tablename__ = "products"
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), ForeignKey("clients.client_id"), nullable=False)
    # ... other fields
```

---

## Success Criteria for MVP

- [x] All core database models created and migrated ✅
- [x] Test data script creates realistic sample data ✅
- [x] Products API returns filterable, sortable data ✅
- [x] Dashboard API returns accurate KPIs ✅
- [x] DIR and stockout risk calculated correctly ✅
- [x] Order planning cart functional ✅
- [x] Purchase orders can be created ✅
- [x] Recommendations generated based on rules ✅
- [x] Settings can be configured ✅
- [x] All P0 endpoints tested and documented ✅ (10/10 core endpoints passing)
- [x] Code follows existing architecture patterns (layered, services, schemas) ✅

---

## Next Steps

1. ✅ **Week 1:** Database models + test data setup + **optimize ts_demand_daily indexes** - **COMPLETE**
2. ✅ **Week 2:** Core APIs (products, dashboard, metrics) - **COMPLETE**
3. ✅ **Week 3:** Order planning + purchase orders - **COMPLETE**
4. ✅ **Week 4:** Settings + recommendations + testing - **COMPLETE**
5. ⏳ **Week 5+:** ETL pipeline + production data sync (Post-MVP) - **NEXT PHASE**

**Important:** Optimize `ts_demand_daily` table indexes in Week 1 to ensure forecasting performance is optimal from the start.

---

## User Stories to API Mapping

### CEO Stories

| User Story | Backend Endpoint | Phase |
|------------|------------------|-------|
| US-CEO-001: View High-Level Performance Dashboard | `GET /api/v1/dashboard` | Phase 2 |
| US-CEO-002: View Historical Performance Trends | `GET /api/v1/analytics/inventory-trends` | Phase 5 |
| US-CEO-003: Configure High-Level Data Thresholds | `PUT /api/v1/settings` | Phase 4 |
| US-CEO-004: View ROI of Forecast Improvements | `GET /api/v1/analytics/forecast-accuracy` | Phase 5 |
| US-CEO-005: Monitor Critical Inventory Issues | `GET /api/v1/dashboard` (alerts) | Phase 2 |

### Procurement Manager Stories

| User Story | Backend Endpoint | Phase |
|------------|------------------|-------|
| US-PROC-001: View Products Needing Attention | `GET /api/v1/products?status=understocked` | Phase 2 |
| US-PROC-002: Prevent Stockouts Through Order Planning | `GET /api/v1/order-planning/suggestions` | Phase 3 |
| US-PROC-003: Avoid Excessive Inventory | `GET /api/v1/products?status=overstocked` | Phase 2 |
| US-PROC-004: View Operational Clarity Dashboard | `GET /api/v1/dashboard` | Phase 2 |
| US-PROC-005: Create Purchase Orders Efficiently | `POST /api/v1/purchase-orders` | Phase 3 |
| US-PROC-006: Manage Purchase Orders | `GET /api/v1/purchase-orders`, `PUT /api/v1/purchase-orders/{id}/status` | Phase 3 |
| US-PROC-007: View Supplier Information | `GET /api/v1/suppliers/{id}` | Phase 2 |
| US-PROC-008: Identify Dead Stock | `GET /api/v1/products?dead_stock=true` | Phase 2 |
| US-PROC-009: View AI-Powered Recommendations | `GET /api/v1/recommendations` | Phase 3 |
| US-PROC-010: Search and Filter Products | `GET /api/v1/products` (with filters) | Phase 2 |
| US-PROC-011: Edit Product Information | `PUT /api/v1/products/{sku}/suppliers/{id}` (MOQ, lead time) | Phase 2 |
| US-PROC-012: Refresh Inventory Metrics | `POST /api/v1/inventory/metrics/refresh` | Phase 2 |

### Marketing Manager Stories

| User Story | Backend Endpoint | Phase |
|------------|------------------|-------|
| US-MKT-001: Identify Products to Promote | `GET /api/v1/recommendations?type=PROMOTE` | Phase 3 |
| US-MKT-002: View Products Below Marketing Threshold | `GET /api/v1/products?marketing_threshold=below` | Phase 2 |
| US-MKT-003: View Product Campaign Status | `GET /api/v1/products/campaign-status` | Phase 5 |
| US-MKT-004: Create Marketing Campaigns | `POST /api/v1/campaigns` | Phase 5 |
| US-MKT-005: View Marketing Campaigns | `GET /api/v1/campaigns` | Phase 5 |
| US-MKT-006: Edit Marketing Campaigns | `PUT /api/v1/campaigns/{id}` | Phase 5 |
| US-MKT-007: Delete Marketing Campaigns | `DELETE /api/v1/campaigns/{id}` | Phase 5 |
| US-MKT-008: View Products with Excess Inventory | `GET /api/v1/products?status=overstocked` | Phase 2 |
| US-MKT-009: Avoid Promoting Low-Stock Products | `GET /api/v1/products?status=understocked` (filter) | Phase 2 |
| US-MKT-010: View Campaign Performance Impact | `GET /api/v1/campaigns/{id}/performance` | Phase 5 |

### Shared Features

| User Story | Backend Endpoint | Phase |
|------------|------------------|-------|
| US-SHARED-001: Navigate Between Features | N/A (Frontend routing) | - |
| US-SHARED-002: View Product Details | `GET /api/v1/products/{sku}` | Phase 2 |
| US-SHARED-003: Generate Forecasts with Covariates | `POST /api/v1/forecast` (existing) | ✅ Done |
| US-SHARED-004: View Forecast Charts | `GET /api/v1/forecast/{run_id}` (existing) | ✅ Done |
| US-SHARED-005: Query Data Using Natural Language | `POST /api/v1/chat` (existing) | ✅ Done |
| US-SHARED-006: Upload Data Files | `POST /api/v1/etl/import` | Phase 5 |
| US-SHARED-007: Select Active Client/Dataset | `GET /api/v1/clients` (existing) | ✅ Done |
| US-SHARED-008: Configure System Settings | `PUT /api/v1/settings` | Phase 4 |

---

## Related Documentation

- [DATA_MODEL.md](../../DATA_MODEL.md) - Complete data model
- [WORKFLOWS.md](../../WORKFLOWS.md) - System workflows
- [USER_STORIES.md](../../USER_STORIES.md) - User requirements
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [forecasting/README.md](./forecasting/README.md) - Forecasting module
- [ROADMAP.md](./ROADMAP.md) - Forecasting engine roadmap (separate)

