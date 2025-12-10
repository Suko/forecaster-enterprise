# API Reference

**Backend Version:** 1.0.0  
**Base URL:** `http://localhost:8000`  
**Last Updated:** 2025-12-10

---

## Table of Contents

1. [Authentication](#authentication)
2. [Products & Inventory](#products--inventory)
3. [Dashboard](#dashboard)
4. [Order Planning](#order-planning)
5. [Purchase Orders](#purchase-orders)
6. [Settings](#settings)

---

## Authentication

### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

## Products & Inventory

### List Products
```http
GET /api/v1/products?page=1&page_size=50&search=keyword&category=Electronics&status=understocked&sort=dir&order=desc
Authorization: Bearer <token>
```

**Query Parameters:**
- `page` (int, default: 1) - Page number
- `page_size` (int, default: 50, max: 100) - Items per page
- `search` (string, optional) - Global search
- `category` (string, optional) - Filter by category
- `supplier_id` (UUID, optional) - Filter by supplier
- `location_id` (string, optional) - Filter by location
- `status` (string, optional) - "understocked" | "normal" | "overstocked"
- `min_dir`, `max_dir` (float, optional) - DIR range
- `min_risk`, `max_risk` (float, optional) - Risk range (0-1)
- `min_stock`, `max_stock` (int, optional) - Stock range
- `sort` (string, optional) - Field to sort by
- `order` (string, default: "asc") - "asc" | "desc"

**Response:**
```json
{
  "items": [
    {
      "item_id": "SKU001",
      "product_name": "Product Name",
      "category": "Electronics",
      "current_stock": 100,
      "unit_cost": "10.00",
      "dir": 30.5,
      "stockout_risk": 0.15,
      "status": "normal",
      "inventory_value": "1000.00"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 50,
  "total_pages": 3
}
```

### Get Product Details
```http
GET /api/v1/products/{item_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "item_id": "SKU001",
  "product_name": "Product Name",
  "category": "Electronics",
  "description": "Product description",
  "unit_cost": "10.00",
  "current_stock": 100,
  "suppliers": [
    {
      "supplier_id": "uuid",
      "supplier_name": "Supplier Name",
      "moq": 10,
      "lead_time_days": 14,
      "supplier_cost": "9.50"
    }
  ]
}
```

### Get Product Metrics
```http
GET /api/v1/products/{item_id}/metrics
Authorization: Bearer <token>
```

**Response:**
```json
{
  "item_id": "SKU001",
  "current_stock": 100,
  "dir": 30.5,
  "stockout_risk": 0.15,
  "status": "normal",
  "forecasted_demand_30d": "10.00",
  "inventory_value": "1000.00"
}
```

### Get Product Suppliers
```http
GET /api/v1/products/{item_id}/suppliers
Authorization: Bearer <token>
```

### Add Supplier to Product
```http
POST /api/v1/products/{item_id}/suppliers
Authorization: Bearer <token>
Content-Type: application/json

{
  "supplier_id": "uuid",
  "moq": 10,
  "lead_time_days": 14,
  "supplier_cost": "9.50"
}
```

### Update Supplier Conditions
```http
PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "moq": 20,
  "lead_time_days": 21,
  "supplier_cost": "9.00"
}
```

### Remove Supplier from Product
```http
DELETE /api/v1/products/{item_id}/suppliers/{supplier_id}
Authorization: Bearer <token>
```

---

## Dashboard

### Get Dashboard
```http
GET /api/v1/dashboard
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_products": 150,
  "total_value": "150000.00",
  "understocked_count": 25,
  "overstocked_count": 10,
  "high_risk_count": 5,
  "top_understocked": [
    {
      "item_id": "SKU001",
      "product_name": "Product Name",
      "dir": 5.2,
      "stockout_risk": 0.85
    }
  ],
  "top_overstocked": [
    {
      "item_id": "SKU002",
      "product_name": "Product Name 2",
      "dir": 120.5,
      "stockout_risk": 0.05
    }
  ]
}
```

---

## Order Planning

### Add to Cart
```http
POST /api/v1/order-planning/cart/add
Authorization: Bearer <token>
X-Session-ID: session-id (optional)
Content-Type: application/json

{
  "item_id": "SKU001",
  "supplier_id": "uuid",
  "quantity": 20,
  "notes": "Optional notes"
}
```

**Response:**
```json
{
  "item_id": "SKU001",
  "supplier_id": "uuid",
  "quantity": 20,
  "unit_cost": "10.00",
  "total_cost": "200.00",
  "notes": "Optional notes"
}
```

### Get Cart
```http
GET /api/v1/order-planning/cart
Authorization: Bearer <token>
X-Session-ID: session-id (optional)
```

**Response:**
```json
{
  "items": [
    {
      "item_id": "SKU001",
      "product_name": "Product Name",
      "supplier_name": "Supplier Name",
      "quantity": 20,
      "unit_cost": "10.00",
      "total_cost": "200.00"
    }
  ],
  "total_items": 1,
  "total_value": "200.00",
  "grouped_by_supplier": {
    "supplier-uuid": [...]
  }
}
```

### Update Cart Item
```http
PUT /api/v1/order-planning/cart/{item_id}
Authorization: Bearer <token>
X-Session-ID: session-id
Content-Type: application/json

{
  "quantity": 30
}
```

### Remove from Cart
```http
DELETE /api/v1/order-planning/cart/{item_id}
Authorization: Bearer <token>
X-Session-ID: session-id
```

### Clear Cart
```http
POST /api/v1/order-planning/cart/clear
Authorization: Bearer <token>
X-Session-ID: session-id
```

### Get Order Suggestions
```http
GET /api/v1/order-planning/suggestions?location_id=LOC001&min_risk=0.5
Authorization: Bearer <token>
```

**Query Parameters:**
- `location_id` (string, optional)
- `min_risk` (float, optional)

**Response:**
```json
{
  "suggestions": [
    {
      "item_id": "SKU001",
      "product_name": "Product Name",
      "current_stock": 10,
      "suggested_quantity": 50,
      "reason": "Low stock",
      "supplier_id": "uuid",
      "supplier_name": "Supplier Name"
    }
  ]
}
```

### Get Recommendations
```http
GET /api/v1/order-planning/recommendations?recommendation_type=REORDER&role=PROCUREMENT
Authorization: Bearer <token>
```

**Query Parameters:**
- `recommendation_type` (string, optional) - "REORDER" | "URGENT" | "REDUCE_ORDER" | "DEAD_STOCK" | "PROMOTE"
- `role` (string, optional) - "CEO" | "PROCUREMENT" | "MARKETING"

**Response:**
```json
[
  {
    "type": "REORDER",
    "priority": "high",
    "item_id": "SKU001",
    "product_name": "Product Name",
    "reason": "DIR below threshold",
    "suggested_quantity": 50,
    "supplier_id": "uuid",
    "supplier_name": "Supplier Name"
  }
]
```

---

## Purchase Orders

### Create Purchase Order
```http
POST /api/v1/purchase-orders
Authorization: Bearer <token>
Content-Type: application/json

{
  "supplier_id": "uuid",
  "items": [
    {
      "item_id": "SKU001",
      "quantity": 20,
      "unit_cost": "10.00"
    }
  ],
  "notes": "Optional notes"
}
```

### Create PO from Cart
```http
POST /api/v1/purchase-orders/from-cart
Authorization: Bearer <token>
X-Session-ID: session-id
Content-Type: application/json

{
  "supplier_id": "uuid",
  "notes": "Optional notes"
}
```

**Response:**
```json
{
  "id": "po-uuid",
  "po_number": "PO-2025-001",
  "supplier_id": "uuid",
  "supplier_name": "Supplier Name",
  "status": "pending",
  "total_amount": "200.00",
  "items": [
    {
      "item_id": "SKU001",
      "product_name": "Product Name",
      "quantity": 20,
      "unit_cost": "10.00",
      "total_cost": "200.00"
    }
  ],
  "created_at": "2025-12-10T10:00:00Z",
  "created_by": "user@example.com"
}
```

### List Purchase Orders
```http
GET /api/v1/purchase-orders?status=pending&supplier_id=uuid&page=1&page_size=50
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` (string, optional) - "pending" | "confirmed" | "shipped" | "received" | "cancelled"
- `supplier_id` (UUID, optional)
- `page` (int, default: 1)
- `page_size` (int, default: 50)

**Response:**
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

### Get Purchase Order Details
```http
GET /api/v1/purchase-orders/{po_id}
Authorization: Bearer <token>
```

### Update PO Status
```http
PATCH /api/v1/purchase-orders/{po_id}/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "status": "confirmed"
}
```

---

## Settings

### Get Settings
```http
GET /api/v1/settings
Authorization: Bearer <token>
```

**Response:**
```json
{
  "client_id": "uuid",
  "safety_buffer_days": 7,
  "understocked_threshold": 14,
  "overstocked_threshold": 90,
  "dead_stock_days": 90,
  "recommendation_rules": {
    "enabled_types": ["REORDER", "URGENT"],
    "role_rules": {
      "PROCUREMENT": ["REORDER", "URGENT"]
    }
  }
}
```

### Update Settings
```http
PUT /api/v1/settings
Authorization: Bearer <token>
Content-Type: application/json

{
  "safety_buffer_days": 10,
  "understocked_threshold": 20,
  "overstocked_threshold": 100,
  "dead_stock_days": 120
}
```

### Get Recommendation Rules
```http
GET /api/v1/settings/recommendation-rules
Authorization: Bearer <token>
```

### Update Recommendation Rules
```http
PUT /api/v1/settings/recommendation-rules
Authorization: Bearer <token>
Content-Type: application/json

{
  "enabled_types": ["REORDER", "URGENT"],
  "role_rules": {
    "PROCUREMENT": ["REORDER", "URGENT"],
    "CEO": ["URGENT"]
  },
  "min_inventory_value": 100,
  "min_risk_score": 0.5
}
```

---

## Error Responses

### Standard Error
```json
{
  "detail": "Error message"
}
```

### Validation Error
```json
{
  "detail": [
    {
      "loc": ["body", "quantity"],
      "msg": "value must be greater than 0",
      "type": "value_error"
    }
  ]
}
```

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Unprocessable Entity
- `500` - Internal Server Error

---

## Data Types

### Product Status
```typescript
"understocked" | "normal" | "overstocked"
```

### PO Status
```typescript
"pending" | "confirmed" | "shipped" | "received" | "cancelled"
```

### Recommendation Type
```typescript
"REORDER" | "URGENT" | "REDUCE_ORDER" | "DEAD_STOCK" | "PROMOTE"
```

### Role
```typescript
"CEO" | "PROCUREMENT" | "MARKETING"
```

---

**For integration examples, see [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md)**

