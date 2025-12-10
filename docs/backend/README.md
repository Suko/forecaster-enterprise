# Backend Documentation

**Status:** ✅ MVP Complete - Ready for Frontend  
**Last Updated:** 2025-12-10

---

## Quick Start

```bash
cd forecaster_enterprise/backend

# 1. Run migrations
uv run alembic upgrade head

# 2. Set up test data
uv run python scripts/setup_test_data.py --client-id <uuid>

# 3. Start server
uv run uvicorn main:app --reload

# 4. Run tests
uv run pytest tests/test_api/test_inventory_api.py -v
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| **[API_REFERENCE.md](./API_REFERENCE.md)** | Complete API docs for frontend integration |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System architecture and design |
| **[BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md)** | Implementation history (Phases 1-4) |
| **[TEST_PLAN.md](./TEST_PLAN.md)** | Testing strategy and coverage |

---

## API Endpoints Summary

### Auth
- `POST /api/v1/auth/login` → JWT token

### Products
- `GET /api/v1/products` → List with filters
- `GET /api/v1/products/{item_id}` → Details
- `GET /api/v1/products/{item_id}/metrics` → DIR, risk, status

### Dashboard
- `GET /api/v1/dashboard` → KPIs and top products

### Cart
- `POST /api/v1/order-planning/cart/add`
- `GET /api/v1/order-planning/cart`
- `GET /api/v1/order-planning/recommendations`

### Purchase Orders
- `POST /api/v1/purchase-orders`
- `GET /api/v1/purchase-orders`
- `PATCH /api/v1/purchase-orders/{id}/status`

### Settings
- `GET /api/v1/settings`
- `PUT /api/v1/settings`

---

## Key Info

- **Auth:** `Authorization: Bearer <token>`
- **Product ID:** Use `item_id` (not `sku`)
- **Multi-tenant:** All data isolated by `client_id` (from JWT)

---

## Test Status

- ✅ Inventory API: 9/9 passing
- ✅ Core workflows: functional
- Coverage: 59% overall, 100% models/schemas
