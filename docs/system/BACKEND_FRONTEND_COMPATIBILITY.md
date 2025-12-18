# Backend/Frontend Compatibility & Blockers

**Last Updated:** 2025-12-17  
**Status:** Active Audit (keep updated as fixes land)  
**Scope:** API contracts, data shapes, and backend/frontend alignment

---

## Executive Summary

This document captures **current backend/frontend mismatches** and **decision blockers** that impact the plans in:
- `docs/NEXT_STEPS.md`
- `docs/features/*`

Goal: make issues **actionable**, make contracts **explicit**, and prevent future drift.

---

## P0 Blockers (Fix Before Feature Work)

### 1) Forecasts Do Not Persist Reliably
- **Status:** ✅ Fixed
- **What was wrong:** `ForecastService.generate_forecast()` did not commit/return on the success path due to indentation/flow, so `forecast_runs` / `forecast_results` could fail to persist.
- **Where:** `backend/forecasting/services/forecast_service.py`
- **Impact:** Forecast-dependent screens (dashboard, products, recommendations, suggestions) become nondeterministic.
- **Validation:** `backend/tests/test_forecasting/test_forecast_service.py`

### 2) Tenant Isolation Can Be Bypassed (client_id Selection)
- **Status:** ✅ Fixed
- **What was wrong:** `client_id` from request body was accepted **before** checking JWT or validating a service key.
- **Where:** `backend/auth/service_auth.py`
- **Impact:** A user call could potentially force a different tenant context (critical security risk).
- **Decision:** `client_id` from request body must be accepted **only** when a valid `X-API-Key` is present (service calls).
- **Validation:** `backend/tests/test_forecasting/test_api_auth.py`

### 3) API Base Path Is Inconsistent (`/auth/*` vs `/api/v1/*`)
- **Status:** ✅ Fixed
- **Decision:** Canonical auth base path is `/api/v1/auth/*`.
- **Where:** `backend/main.py`, frontend server routes
- **Legacy:** `/auth/*` is still served for backward compatibility but is deprecated.

### 4) `stockout_risk` Scale Mismatch (0–1 vs 0–100)
- **Status:** ✅ Fixed
- **What was wrong:** Backend returns `stockout_risk` as a **0–1 decimal**, but parts of the frontend treated it as **0–100**.
- **Where:** backend: `backend/services/dashboard_service.py`; frontend: `frontend/app/pages/dashboard.vue`
- **Impact:** Wrong badges, priorities, and decision-making in UI.
- **Decision:** Keep **0–1** in APIs (machine-friendly), multiply by 100 only at display time.

---

## P1 Contract Gaps (Blocks Planned UI/UX)

### Inventory Filters Are Advertised But Not Applied
- **Status:** ✅ Fixed via Option A (filter in SQL against latest `inventory_metrics`)
- **Change:** `get_products` now joins the most recent `inventory_metrics` per item_id and applies metric filters in SQL so pagination/total counts stay consistent.
- **Where:** `backend/services/inventory_service.py`
- **Validation:** `backend/tests/test_api/test_inventory_api.py::test_get_products_metric_filters`
- **Ops:** Seed/refresh `inventory_metrics` with `backend/scripts/refresh_inventory_metrics.py --client-id <client_id>` (or schedule the script) so metric filters have data to act on.

### Product Status Enum Differs From Docs (dead_stock not in products)
- **What’s wrong:** Product metrics status does not currently compute `dead_stock` (requires last sale date), but docs assume it exists in products/dashboard.
- **Where:** `backend/services/metrics_service.py` (TODO: last_sale_date), `backend/services/dashboard_service.py`
- **Impact:** “Dead Stock” tabs/metrics won’t work as described until implemented.

### Cart Response Missing `lead_time_days` (ETA cannot be computed)
- **What’s wrong:** Cart items return `moq` but not `lead_time_days`.
- **Where:** `backend/api/orders.py`, `backend/schemas/order.py`
- **Impact:** Blocks “Expected delivery date” UX in `docs/features/PURCHASE_ORDER_IMPROVEMENTS.md`.

### Missing/Planned Endpoints Referenced by Feature Docs
- `GET /api/v1/monitoring/last-sync` (referenced, not implemented)
- `GET /api/v1/dashboard/trends` (referenced, not implemented)
- `GET /api/v1/products/{item_id}/history` (referenced, not implemented)
- `GET /api/v1/forecasts/sku/{item_id}` (referenced, not implemented)

### Recommendations “Deprecated” vs Still Used in UI
- **Status:** ✅ Fixed (fully deprecated in UI)
- **Decision:** Deprecate the Recommendations page and remove it from the frontend navigation and copy; focus UX on Inventory + Cart/Purchase Orders.
- **Where:** `frontend/app/layouts/dashboard.vue`, `frontend/app/pages/purchase-orders/draft.vue`
- **Note:** Backend recommendation endpoints can remain temporarily, but the UI no longer links to them.

### API Docs Drift (High Confusion Risk)
- `docs/backend/API_REFERENCE.md` contains outdated paths and response shapes.
- **Decision Needed:** Make OpenAPI the source-of-truth and either (a) generate this doc or (b) enforce a “docs update required” checklist.

---

## Testing: How To Validate What Exists Today

### Backend

Run API locally:
```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

Run tests + lint:
```bash
cd backend
uv run pytest tests/ -v
uv run ruff check .
```

Quick smoke:
```bash
./backend/test_endpoints.sh
```

### Frontend

Run UI locally:
```bash
cd frontend
bun run dev
```

Lint/format checks:
```bash
cd frontend
bun run lint
bun run format:check
```

### Minimal Manual Contract Smoke (curl)

```bash
# Health (no auth)
curl -s http://localhost:8000/health

# Login (OAuth2PasswordRequestForm)
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=password" | jq -r .access_token)

# Dashboard
curl -s http://localhost:8000/api/v1/dashboard -H "Authorization: Bearer $TOKEN"
```

---

## Preventing Future Drift (Process)

### Source of Truth
- **Backend:** Pydantic schemas + OpenAPI (`/docs`) are the contract.
- **Frontend:** `frontend/app/types/*` and `frontend/server/api/*` must match backend schema shapes and paths.
- **Docs:** any doc that describes an endpoint must be updated together with the code change.

### Definition of Done (Contract-Sensitive Changes)
When changing an endpoint/response:
1. Update backend schema + router
2. Update/regen `docs/backend/API_REFERENCE.md`
3. Update frontend server proxy route + TS types
4. Add/adjust backend tests for the contract change
5. Run: backend tests + ruff, frontend lint + format check
