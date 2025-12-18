# API Reference

**Source of Truth:** FastAPI OpenAPI (`/openapi.json`)  
**Base URL:** `http://localhost:8000`  
**Last Generated:** 2025-12-17

> **Note:** This document should be regenerated from the OpenAPI schema (`/openapi.json`) when API endpoints change. The canonical source of truth is the FastAPI application's OpenAPI schema, accessible at `/docs` (Swagger UI) or `/openapi.json` (JSON schema).

---

## Quick Start (Frontend)

```typescript
// 1. Login
const form = new URLSearchParams();
form.append('username', 'user@example.com');
form.append('password', 'password');

const res = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: form.toString()
});
const { access_token } = await res.json();

// 2. Use token in requests
const headers = { 'Authorization': `Bearer ${access_token}` };

// 3. Example: dashboard
const dashboard = await fetch('http://localhost:8000/api/v1/dashboard', { headers }).then(r => r.json());
```

---

## Endpoints (Canonical)

## Etl

### `POST /api/v1/etl/sync/locations`

**Summary:** Sync Locations

Sync locations from external source

Requires authentication and client context.
Preserves app-managed locations (is_synced = false).

**Request Body**
- `application/json` → `SyncLocationsRequest`

**Responses**
- `200` `SyncResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/etl/sync/products`

**Summary:** Sync Products

Sync products from external source

Requires authentication and client context.

**Request Body**
- `application/json` → `SyncProductsRequest`

**Responses**
- `200` `SyncResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/etl/sync/sales-history`

**Summary:** Sync Sales History

Sync sales history from external source to ts_demand_daily table

Requires authentication and client context.

**Request Body**
- `application/json` → `SyncSalesHistoryRequest`

**Responses**
- `200` `SyncResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/etl/sync/stock-levels`

**Summary:** Sync Stock Levels

Sync stock levels from external source

Requires authentication and client context.

**Request Body**
- `application/json` → `SyncStockLevelsRequest`

**Responses**
- `200` `SyncResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/etl/validate`

**Summary:** Validate Data

Validate data quality, completeness, and computed metrics

Requires authentication and client context.
Returns comprehensive validation report.

**Request Body**
- `application/json` → `ValidationRequest`

**Responses**
- `200` `ValidationReport` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Auth

### `POST /api/v1/auth/login`

**Summary:** Login

Login endpoint - returns JWT access token
Rate limited to prevent brute force attacks

**Request Body**
- `application/x-www-form-urlencoded` → `Body_login_api_v1_auth_login_post`

**Responses**
- `200` `Token` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/auth/me`

**Summary:** Get Current User Info

Get current authenticated user information

**Responses**
- `200` `UserResponse` — Successful Response

### `GET /api/v1/auth/me/preferences`

**Summary:** Get User Preferences

Get current user's preferences

**Responses**
- `200` `UserPreferencesResponse` — Successful Response

### `PUT /api/v1/auth/me/preferences`

**Summary:** Update User Preferences

Update current user's preferences

**Request Body**
- `application/json` → `UserPreferencesUpdate`

**Responses**
- `200` `UserPreferencesResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/auth/register`

**Summary:** Register

Register a new user
Rate limited to prevent abuse
Password validation: 8-128 characters

**Request Body**
- `application/json` → `UserCreate`

**Responses**
- `201` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/auth/users`

**Summary:** List Users

List all users (admin only)

**Responses**
- `200` `array` — Successful Response

### `POST /api/v1/auth/users`

**Summary:** Create User Endpoint

Create a new user (admin only)

**Request Body**
- `application/json` → `UserCreate`

**Responses**
- `201` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PATCH /api/v1/auth/users/{user_id}`

**Summary:** Update User Endpoint

Update user (admin only)

**Request Body**
- `application/json` → `UserUpdate`

**Responses**
- `200` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `DELETE /api/v1/auth/users/{user_id}`

**Summary:** Delete User Endpoint

Delete user (admin only)

**Responses**
- `204` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Forecast

### `POST /api/v1/forecast`

**Summary:** Create Forecast

Generate forecast for specified items.

Authentication (choose one):
- JWT token (user calls): client_id from user's JWT token (request.client_id ignored)
- Service API key (system calls): X-API-Key header + client_id in request body

Returns predictions from recommended method (primary if successful, baseline if not).
Both methods are stored in database for future quality analysis.

**Request Body**
- `application/json` → `ForecastRequest`

**Responses**
- `201` `ForecastResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/forecasts/actuals`

**Summary:** Backfill Actuals

Backfill actual values for quality testing.

Authentication (choose one):
- JWT token (user calls): client_id from user's JWT token
- Service API key (system calls): X-API-Key header (client_id from JWT/request)

Updates forecast_results.actual_value for specified item and dates.
Enables calculation of accuracy metrics (MAPE, MAE, RMSE).

**Request Body**
- `application/json` → `BackfillActualsRequest`

**Responses**
- `200` `BackfillActualsResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/forecasts/quality/{item_id}`

**Summary:** Get Quality Metrics

Get quality metrics (MAPE, MAE, RMSE, Bias) for an item.

Authentication (choose one):
- JWT token (user calls): client_id from user's JWT token
- Service API key (system calls): X-API-Key header (client_id from JWT/request)

Compares accuracy of different forecasting methods.
Requires actual values to be backfilled first.

**Responses**
- `200` `QualityResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/inventory/calculate`

**Summary:** Calculate Inventory

Calculate inventory metrics from forecasts.

Authentication (choose one):
- JWT token (user calls): client_id from user's JWT token
- Service API key (system calls): X-API-Key header + client_id in request body

Generates forecast first, then calculates inventory metrics using industry-standard formulas.

**Request Body**
- `application/json` → `InventoryCalculationRequest`

**Responses**
- `201` `InventoryCalculationResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/skus/{item_id}/classification`

**Summary:** Get Sku Classification

Get SKU classification (ABC-XYZ) for a specific item.

Authentication (choose one):
- JWT token (user calls): client_id from user's JWT token
- Service API key (system calls): X-API-Key header

Returns the latest classification for the item.

**Responses**
- `200` `SKUClassificationInfo` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Inventory

### `GET /api/v1/dashboard`

**Summary:** Get Dashboard

Get dashboard data:
- Overall metrics (total SKUs, inventory value, understocked/overstocked counts)
- Top understocked products (by risk and value)
- Top overstocked products (by value)

**Responses**
- `200` `DashboardResponse` — Successful Response

### `GET /api/v1/products`

**Summary:** Get Products

Get paginated list of products with filtering and sorting.

Supports data table requirements:
- Filterable columns (text, numeric, categorical)
- Sortable columns
- Pagination

**Responses**
- `200` `ProductListResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/products/{item_id}`

**Summary:** Get Product

Get product details by item_id.

Includes product information and computed metrics (DIR, risk, etc.).

**Responses**
- `200` `ProductDetailResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/products/{item_id}/metrics`

**Summary:** Get Product Metrics

Get product metrics (DIR, stockout risk, forecasted demand, inventory value).

Computed on-the-fly or from inventory_metrics table.

**Responses**
- `200` `ProductMetrics` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/products/{item_id}/suppliers`

**Summary:** Get Product Suppliers

Get all suppliers for a product with conditions (MOQ, lead time, etc.).

**Responses**
- `200` `array` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/products/{item_id}/suppliers`

**Summary:** Add Product Supplier

Link product to supplier with conditions (MOQ, lead time, packaging).

**Request Body**
- `application/json` → `ProductSupplierCreate`

**Responses**
- `200` `ProductSupplierResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PUT /api/v1/products/{item_id}/suppliers/{supplier_id}`

**Summary:** Update Product Supplier

Update product-supplier conditions (MOQ, lead time, packaging).

**Request Body**
- `application/json` → `ProductSupplierUpdate`

**Responses**
- `200` `ProductSupplierResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `DELETE /api/v1/products/{item_id}/suppliers/{supplier_id}`

**Summary:** Remove Product Supplier

Remove product-supplier link.

**Responses**
- `200` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Locations

### `GET /api/v1/locations`

**Summary:** Get Locations

Get paginated list of locations

**Responses**
- `200` `LocationListResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/locations`

**Summary:** Create Location

Create a new location

**Request Body**
- `application/json` → `LocationCreate`

**Responses**
- `201` `LocationResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/locations/{location_id}`

**Summary:** Get Location

Get location detail

**Responses**
- `200` `LocationResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PUT /api/v1/locations/{location_id}`

**Summary:** Update Location

Update location information

**Request Body**
- `application/json` → `LocationUpdate`

**Responses**
- `200` `LocationResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `DELETE /api/v1/locations/{location_id}`

**Summary:** Delete Location

Delete a location

**Responses**
- `204` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Monitoring

### `GET /api/v1/health`

**Summary:** Health Check

Health check endpoint (no auth required).

**Responses**
- `200` `object` — Successful Response

### `GET /api/v1/metrics`

**Summary:** Get Metrics

Get performance metrics summary.

Requires authentication.

**Responses**
- `200` `object` — Successful Response

### `GET /api/v1/system/status`

**Summary:** Get System Status

Get system initialization status

Returns status of data tables and basic data quality metrics.
Requires authentication and client context.

**Responses**
- `200` `SystemStatusResponse` — Successful Response

## Orders

### `GET /api/v1/order-planning/cart`

**Summary:** Get Cart

Get current cart items grouped by supplier

**Responses**
- `200` `CartResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/order-planning/cart/add`

**Summary:** Add To Cart

Add item to order planning cart.

Validates:
- Product exists
- Supplier exists and is linked to product
- Quantity >= MOQ

**Request Body**
- `application/json` → `CartItemCreate`

**Responses**
- `200` `CartItemResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/order-planning/cart/clear`

**Summary:** Clear Cart

Clear entire cart

**Responses**
- `200` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PUT /api/v1/order-planning/cart/{item_id}`

**Summary:** Update Cart Item

Update cart item quantity or notes

**Request Body**
- `application/json` → `CartItemUpdate`

**Responses**
- `200` `CartItemResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `DELETE /api/v1/order-planning/cart/{item_id}`

**Summary:** Remove From Cart

Remove item from cart

**Responses**
- `200` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/order-planning/suggestions`

**Summary:** Get Order Suggestions

Get order suggestions based on forecasted demand, current stock, and lead time.

Suggests products that need reordering based on:
- Forecasted demand
- Current stock
- Lead time + safety buffer

**Responses**
- `200` `OrderSuggestionsResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/recommendations`

**Summary:** Get Recommendations

Get AI-powered recommendations.

Types: REORDER, URGENT, REDUCE_ORDER, DEAD_STOCK, PROMOTE
Role: CEO, PROCUREMENT, MARKETING (filters by role-based rules)

**Responses**
- `200` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/recommendations/{recommendation_id}/dismiss`

**Summary:** Dismiss Recommendation

Dismiss a recommendation (don't show again).

Note: This is a placeholder - in production, you'd store dismissed recommendations
in a database table.

**Responses**
- `200` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Other

### `GET /`

**Summary:** Root

**Responses**
- `200` — Successful Response

### `GET /health`

**Summary:** Health

**Responses**
- `200` — Successful Response

## Purchase-Orders

### `GET /api/v1/purchase-orders`

**Summary:** Get Purchase Orders

Get paginated list of purchase orders

**Responses**
- `200` `object` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/purchase-orders`

**Summary:** Create Purchase Order

Create a new purchase order.

Can be created from:
- Direct items (provided in request)
- Cart items (use create_po_from_cart endpoint)

**Request Body**
- `application/json` → `PurchaseOrderCreate`

**Responses**
- `201` `PurchaseOrderResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/purchase-orders/from-cart`

**Summary:** Create Po From Cart

Create purchase order from cart items for a specific supplier.

Removes items from cart after creating PO.

**Responses**
- `201` `PurchaseOrderResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/purchase-orders/{po_id}`

**Summary:** Get Purchase Order

Get purchase order details

**Responses**
- `200` `PurchaseOrderResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PUT /api/v1/purchase-orders/{po_id}/status`

**Summary:** Update Purchase Order Status

Update purchase order status

**Request Body**
- `application/json` → `PurchaseOrderStatusUpdate`

**Responses**
- `200` `PurchaseOrderResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Settings

### `GET /api/v1/settings`

**Summary:** Get Settings

Get client settings

**Responses**
- `200` `ClientSettingsResponse` — Successful Response

### `PUT /api/v1/settings`

**Summary:** Update Settings

Update client settings

**Request Body**
- `application/json` → `ClientSettingsUpdate`

**Responses**
- `200` `ClientSettingsResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/settings/recommendation-rules`

**Summary:** Get Recommendation Rules

Get recommendation rules

**Responses**
- `200` `object` — Successful Response

### `PUT /api/v1/settings/recommendation-rules`

**Summary:** Update Recommendation Rules

Update recommendation rules

**Request Body**
- `application/json` → `RecommendationRulesUpdate`

**Responses**
- `200` `object` — Successful Response
- `422` `HTTPValidationError` — Validation Error

## Suppliers

### `GET /api/v1/suppliers`

**Summary:** Get Suppliers

Get paginated list of suppliers

**Responses**
- `200` `SupplierListResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /api/v1/suppliers`

**Summary:** Create Supplier

Create a new supplier

**Request Body**
- `application/json` → `SupplierCreate`

**Responses**
- `200` `SupplierResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /api/v1/suppliers/{supplier_id}`

**Summary:** Get Supplier

Get supplier detail

**Responses**
- `200` `SupplierResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PUT /api/v1/suppliers/{supplier_id}`

**Summary:** Update Supplier

Update supplier information.

If apply_to_existing is True:
- Updates product-supplier conditions where MOQ/lead_time_days match the old supplier defaults
- Only affects conditions that were using the supplier defaults (not explicit overrides)

**Request Body**
- `application/json` → `SupplierUpdate`

**Responses**
- `200` `SupplierResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

---

## Endpoints (Legacy / Deprecated)

## Auth

### `POST /auth/login`

**Deprecated:** yes

**Summary:** Login

Login endpoint - returns JWT access token
Rate limited to prevent brute force attacks

**Request Body**
- `application/x-www-form-urlencoded` → `Body_login_auth_login_post`

**Responses**
- `200` `Token` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /auth/me`

**Deprecated:** yes

**Summary:** Get Current User Info

Get current authenticated user information

**Responses**
- `200` `UserResponse` — Successful Response

### `GET /auth/me/preferences`

**Deprecated:** yes

**Summary:** Get User Preferences

Get current user's preferences

**Responses**
- `200` `UserPreferencesResponse` — Successful Response

### `PUT /auth/me/preferences`

**Deprecated:** yes

**Summary:** Update User Preferences

Update current user's preferences

**Request Body**
- `application/json` → `UserPreferencesUpdate`

**Responses**
- `200` `UserPreferencesResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `POST /auth/register`

**Deprecated:** yes

**Summary:** Register

Register a new user
Rate limited to prevent abuse
Password validation: 8-128 characters

**Request Body**
- `application/json` → `UserCreate`

**Responses**
- `201` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `GET /auth/users`

**Deprecated:** yes

**Summary:** List Users

List all users (admin only)

**Responses**
- `200` `array` — Successful Response

### `POST /auth/users`

**Deprecated:** yes

**Summary:** Create User Endpoint

Create a new user (admin only)

**Request Body**
- `application/json` → `UserCreate`

**Responses**
- `201` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `PATCH /auth/users/{user_id}`

**Deprecated:** yes

**Summary:** Update User Endpoint

Update user (admin only)

**Request Body**
- `application/json` → `UserUpdate`

**Responses**
- `200` `UserResponse` — Successful Response
- `422` `HTTPValidationError` — Validation Error

### `DELETE /auth/users/{user_id}`

**Deprecated:** yes

**Summary:** Delete User Endpoint

Delete user (admin only)

**Responses**
- `204` — Successful Response
- `422` `HTTPValidationError` — Validation Error
