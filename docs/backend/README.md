# Backend Documentation

**Status:** ✅ MVP Complete + Data Validation Complete  
**Last Updated:** 2025-12-16

---

## Quick Start

### First-Time Setup (Recommended)
```bash
cd forecaster_enterprise/backend

# Run automated setup script
./setup.sh

# Or with custom options
./setup.sh --admin-email admin@example.com --admin-password mypassword
```

### Manual Setup
```bash
cd forecaster_enterprise/backend

# 1. Run migrations
uv run alembic upgrade head

# 2. Create admin user (optional)
uv run python create_user.py admin@example.com password123 --admin

# 3. Set up test data
uv run python scripts/setup_test_data.py --client-name "Demo Client"

# 4. Start server
uv run uvicorn main:app --reload

# 5. Run tests
uv run pytest tests/test_api/test_inventory_api.py -v
```

---

## Documentation

| Doc | Purpose |
|-----|---------|
| **[API_REFERENCE.md](./API_REFERENCE.md)** | Complete API docs for frontend integration |
| **[ARCHITECTURE.md](./ARCHITECTURE.md)** | System architecture and design |
| **[BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md)** | Implementation history (Phases 1-4) |
| **[FORECASTING_ROADMAP.md](./FORECASTING_ROADMAP.md)** | Forecasting module roadmap |
| **[FORECASTING_INTEGRATION.md](./FORECASTING_INTEGRATION.md)** | Forecasting integration gap analysis |
| **[FORECASTING_PERFORMANCE.md](./FORECASTING_PERFORMANCE.md)** | Performance impact analysis |
| **[FORECASTING_TESTING_AND_FREQUENCY.md](./FORECASTING_TESTING_AND_FREQUENCY.md)** | Testing & frequency recommendations |
| **[SUPPLIER_MANAGEMENT_GUIDE.md](./SUPPLIER_MANAGEMENT_GUIDE.md)** | Supplier & MOQ management |
| **[TEST_PLAN.md](./TEST_PLAN.md)** | Testing strategy and coverage |

### Data Validation (✅ Completed)

| Doc | Purpose |
|-----|---------|
| **[DATA_VALIDATION_API.md](./DATA_VALIDATION_API.md)** | Validation API reference |
| **[VALIDATION_USAGE_GUIDE.md](./VALIDATION_USAGE_GUIDE.md)** | When and how to use validation |
| **[VALIDATION_PROOF.md](./VALIDATION_PROOF.md)** | Proof & guarantees |

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

### Monitoring & Validation
- `GET /api/v1/monitoring/system/status` → System status
- `POST /api/v1/etl/validate` → Data validation

---

## Key Info

- **Auth:** `Authorization: Bearer <token>`
- **Product ID:** Use `item_id` (not `sku`)
- **Multi-tenant:** All data isolated by `client_id` (from JWT)

---

## Test Status

- ✅ Inventory API: 9/9 passing
- ✅ Core workflows: functional
- ✅ Data Validation: Complete
- Coverage: 59% overall, 100% models/schemas

## Recent Completions

### Data Validation (2025-12-16) ✅
- `DataValidationService` - Unified validation service
- `POST /api/v1/etl/validate` - Validation endpoint
- `GET /api/v1/monitoring/system/status` - System status
- Computed metrics validation (DIR, stockout risk, status)
- Frontend-backend consistency checks
- Real data tests
