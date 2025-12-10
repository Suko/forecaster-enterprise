# Frontend Integration Guide

**For:** Frontend Developers  
**Backend Status:** ✅ MVP Complete - Ready for Integration  
**Last Updated:** 2025-12-10

---

## Quick Start

### 1. Base URL
```
Development: http://localhost:8000
Production: <TBD>
```

### 2. Authentication Flow
```typescript
// 1. Register or Login
POST /api/v1/auth/login
Body: { "email": "user@example.com", "password": "password" }
Response: { "access_token": "...", "token_type": "bearer" }

// 2. Use token in all requests
Headers: { "Authorization": "Bearer <token>" }
```

### 3. First API Call
```typescript
// Get dashboard
GET /api/v1/dashboard
Headers: { "Authorization": "Bearer <token>" }
```

---

## Authentication

### Login
```typescript
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

### Using the Token
Include in all authenticated requests:
```typescript
headers: {
  "Authorization": `Bearer ${token}`,
  "Content-Type": "application/json"
}
```

### Session-Based Cart (Optional)
For anonymous cart operations:
```typescript
headers: {
  "X-Session-ID": "user-session-id",  // Optional
  "Authorization": "Bearer <token>"    // Optional if logged in
}
```

---

## Core APIs

### Products

#### List Products
```typescript
GET /api/v1/products?page=1&page_size=50&search=keyword&category=Electronics

Query Parameters:
- page: number (default: 1)
- page_size: number (default: 50, max: 100)
- search: string (optional) - Global search
- category: string (optional) - Filter by category
- supplier_id: UUID (optional) - Filter by supplier
- location_id: string (optional) - Filter by location
- status: string (optional) - "understocked" | "normal" | "overstocked"
- min_dir, max_dir: number (optional) - Filter by DIR range
- min_risk, max_risk: number (optional) - Filter by risk range
- min_stock, max_stock: number (optional) - Filter by stock range
- sort: string (optional) - Field to sort by
- order: "asc" | "desc" (default: "asc")

Response:
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

#### Get Product Details
```typescript
GET /api/v1/products/{item_id}

Response:
{
  "item_id": "SKU001",
  "product_name": "Product Name",
  "category": "Electronics",
  "description": "Product description",
  "unit_cost": "10.00",
  "current_stock": 100,
  "suppliers": [...]
}
```

#### Get Product Metrics
```typescript
GET /api/v1/products/{item_id}/metrics

Response:
{
  "item_id": "SKU001",
  "current_stock": 100,
  "dir": 30.5,              // Days of Inventory Remaining
  "stockout_risk": 0.15,     // 0-1 scale
  "status": "normal",        // "understocked" | "normal" | "overstocked"
  "forecasted_demand_30d": "10.00",
  "inventory_value": "1000.00"
}
```

### Dashboard

```typescript
GET /api/v1/dashboard

Response:
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
  "top_overstocked": [...]
}
```

### Cart

#### Add to Cart
```typescript
POST /api/v1/order-planning/cart/add
Headers: {
  "Authorization": "Bearer <token>",
  "X-Session-ID": "session-id"  // Optional
}

Body:
{
  "item_id": "SKU001",
  "supplier_id": "uuid",
  "quantity": 20,
  "notes": "Optional notes"
}

Response:
{
  "item_id": "SKU001",
  "supplier_id": "uuid",
  "quantity": 20,
  "unit_cost": "10.00",
  "total_cost": "200.00",
  "notes": "Optional notes"
}
```

#### Get Cart
```typescript
GET /api/v1/order-planning/cart
Headers: {
  "Authorization": "Bearer <token>",
  "X-Session-ID": "session-id"  // Optional
}

Response:
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

#### Update Cart Item
```typescript
PUT /api/v1/order-planning/cart/{item_id}
Headers: {
  "Authorization": "Bearer <token>",
  "X-Session-ID": "session-id"
}

Body:
{
  "quantity": 30
}
```

#### Remove from Cart
```typescript
DELETE /api/v1/order-planning/cart/{item_id}
Headers: {
  "Authorization": "Bearer <token>",
  "X-Session-ID": "session-id"
}
```

### Recommendations

```typescript
GET /api/v1/order-planning/recommendations?recommendation_type=REORDER&role=PROCUREMENT

Query Parameters:
- recommendation_type: "REORDER" | "URGENT" | "REDUCE_ORDER" | "DEAD_STOCK" | "PROMOTE"
- role: "CEO" | "PROCUREMENT" | "MARKETING"

Response:
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

### Purchase Orders

#### Create PO from Cart
```typescript
POST /api/v1/purchase-orders/from-cart
Headers: {
  "Authorization": "Bearer <token>",
  "X-Session-ID": "session-id"
}

Body:
{
  "supplier_id": "uuid",
  "notes": "Optional notes"
}

Response:
{
  "id": "po-uuid",
  "po_number": "PO-2025-001",
  "supplier_id": "uuid",
  "supplier_name": "Supplier Name",
  "status": "pending",
  "total_amount": "200.00",
  "items": [...],
  "created_at": "2025-12-10T10:00:00Z"
}
```

#### List Purchase Orders
```typescript
GET /api/v1/purchase-orders?status=pending&supplier_id=uuid

Query Parameters:
- status: "pending" | "confirmed" | "shipped" | "received" | "cancelled"
- supplier_id: UUID (optional)
- page: number (default: 1)
- page_size: number (default: 50)
```

#### Update PO Status
```typescript
PATCH /api/v1/purchase-orders/{po_id}/status

Body:
{
  "status": "confirmed"
}
```

### Settings

```typescript
// Get settings
GET /api/v1/settings

// Update settings
PUT /api/v1/settings
Body:
{
  "safety_buffer_days": 7,
  "understocked_threshold": 14,
  "overstocked_threshold": 90,
  "dead_stock_days": 90
}

// Get recommendation rules
GET /api/v1/settings/recommendation-rules

// Update recommendation rules
PUT /api/v1/settings/recommendation-rules
Body:
{
  "enabled_types": ["REORDER", "URGENT"],
  "role_rules": {
    "PROCUREMENT": ["REORDER", "URGENT"]
  },
  "min_inventory_value": 100,
  "min_risk_score": 0.5
}
```

---

## Error Handling

### Standard Error Response
```typescript
{
  "detail": "Error message"
}

// Validation errors
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
- `400` - Bad Request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `422` - Unprocessable Entity (validation error)
- `500` - Internal Server Error

---

## Data Types

### Product Status
```typescript
type ProductStatus = "understocked" | "normal" | "overstocked"
```

### PO Status
```typescript
type POStatus = "pending" | "confirmed" | "shipped" | "received" | "cancelled"
```

### Recommendation Types
```typescript
type RecommendationType = 
  | "REORDER" 
  | "URGENT" 
  | "REDUCE_ORDER" 
  | "DEAD_STOCK" 
  | "PROMOTE"
```

### Roles
```typescript
type Role = "CEO" | "PROCUREMENT" | "MARKETING"
```

---

## Common Patterns

### Pagination
All list endpoints support pagination:
```typescript
{
  page: 1,
  page_size: 50,
  total: 150,
  total_pages: 3
}
```

### Filtering
Most list endpoints support filtering:
```typescript
?status=understocked&min_dir=10&max_dir=30
```

### Sorting
Most list endpoints support sorting:
```typescript
?sort=dir&order=desc
```

---

## Integration Checklist

### Phase 1: Core Features
- [ ] Authentication (login, token management)
- [ ] Products list page
- [ ] Product detail page
- [ ] Dashboard page

### Phase 2: Order Planning
- [ ] Shopping cart
- [ ] Add to cart
- [ ] Recommendations display
- [ ] Order suggestions

### Phase 3: Purchase Orders
- [ ] Create PO from cart
- [ ] PO list page
- [ ] PO detail page
- [ ] Update PO status

### Phase 4: Settings
- [ ] Settings page
- [ ] Update thresholds
- [ ] Recommendation rules

---

## Testing

### Test User
```bash
Email: test@example.com
Password: (set via registration)
```

### Test Data
Use `scripts/setup_test_data.py` to create test data:
```bash
cd forecaster_enterprise/backend
uv run python scripts/setup_test_data.py --client-id <uuid>
```

---

## Support

- **API Reference**: See [API_REFERENCE.md](./API_REFERENCE.md)
- **Backend Status**: See [BACKEND_MVP_COMPLETE.md](./BACKEND_MVP_COMPLETE.md)
- **Testing**: See [TESTING_CHECKLIST.md](./TESTING_CHECKLIST.md)

---

**Ready to start? Begin with authentication and the dashboard API!**

