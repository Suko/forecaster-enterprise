# Backend Audit Report (2025-12-29)

Scope: `backend/` (FastAPI + SQLAlchemy async). Focused on architecture, DB/transactions, performance/scalability, consistency/edge cases, error handling, maintainability, and practical abuse surface.

## Executive Summary

**Top risks (P0):**
- Multi-tenant correctness bugs in API response mapping (missing `client_id` filters; `scalar_one()` assumptions) can cause 500s and potential cross-tenant data leakage.
- Cart session identity mismatch across endpoints (`user.id` vs `user.email`) likely breaks cart → PO flow for authenticated users.
- Startup crash when Sentry enabled (`os.getenv(...)` used without importing `os`).

**Top scalability risks (P1):**
- Inventory list and recommendations perform per-item metric computation and repeated DB queries (N+1 patterns, high query volume per request).
- ETL “replace” and cart→PO sequences commit mid-flow without a single transaction boundary (risk of partial state).

## Findings by Dimension

### 1) Architecture
- Clear package-level separation exists: API (`backend/api/*`), services (`backend/services/*`), persistence (`backend/models/*`), schemas (`backend/schemas/*`).
- API layer frequently “shapes” responses with extra persistence logic (additional queries inside route handlers), increasing duplication and making service boundaries porous (e.g., cart/PO endpoints).
- Inventory domain is a “wide” service (querying + metrics + supplier/location expansion + background task orchestration), increasing coupling and refactor cost:
  - `backend/services/inventory_service.py` (notably `get_products` and background task code).
- Service dependency cycles / local imports indicate coupling:
  - `MetricsService` imports `InventoryService` for buffer logic (local import), while `InventoryService` depends on `MetricsService`.

### 2) Database & Transactions
- Session lifecycle: `get_db()` yields an `AsyncSession` and closes it (`backend/models/database.py`). There is no consistent “rollback-on-exception” policy in route handlers; some code catches broadly and continues.
- Non-atomic multi-step writes:
  - ETL “replace” deletes and commits before insert/upsert (`backend/services/etl/etl_service.py`).
  - Cart→PO flow commits inside `create_purchase_order` and again after cart deletions (`backend/services/purchase_order_service.py`), risking partial state if failures occur.
- Concurrency/race:
  - PO number generation uses `count+1` with “check exists” fallback (`backend/services/purchase_order_service.py`), not safe under concurrent creates.
- Inefficient patterns:
  - ETL upserts are per-row and will not scale for large syncs (`backend/services/etl/etl_service.py`).

### 3) Performance & Scalability
- Hot paths:
  - Inventory list (`/products`) computes metrics per product and repeatedly queries suppliers and locations per product (N+1 amplification):
    - `backend/services/inventory_service.py` (`get_products` loop).
  - Recommendations iterate all products and compute metrics and supplier data per product:
    - `backend/services/recommendations_service.py`.
- Async migration risks:
  - “Background” tasks are scheduled with `asyncio.create_task(...)` and still run inside the server process/event loop (CPU-heavy forecasting/simulation paths can still starve the loop).
- Abuse vectors:
  - `page_size` up to 1000 for `/products` (`backend/api/inventory.py`) combined with per-item computations is an easy amplification/DoS lever.
- Caching opportunities:
  - Prefer precomputed `inventory_metrics` for list views; batch-load per-request data (settings/locations/suppliers) rather than per-item queries.

### 4) Data Consistency & Edge Cases
- Multi-tenant boundary bug (P0):
  - `Product` lookups in API response mapping omit `client_id` filter and assume uniqueness with `scalar_one()`.
  - Examples:
    - `backend/api/orders.py`
    - `backend/api/purchase_orders.py`
- Cart identity mismatch (P0):
  - Cart endpoints use `session_id = user.id` when authenticated, but PO-from-cart uses `session_id = user.email`:
    - `backend/api/orders.py`
    - `backend/api/purchase_orders.py`
- Simulation scope silently truncated (misleading results):
  - Active “limit to first 5 items” logic when `item_ids` not provided (`backend/services/simulation_service.py`).
- Potential drift:
  - Some endpoints compute “live” metrics while others depend on seeded `inventory_metrics`, which may not be refreshed consistently.

### 5) Error Handling & Safety
- Leaky/internal errors:
  - Some endpoints return `detail=str(e)` for broad exceptions, exposing internal messages and producing inconsistent error responses.
- Silent failures:
  - `try/except: pass` patterns in inventory listing can hide DB/session issues and produce partial responses instead of surfacing errors.
- Dead/unreachable code:
  - Unreachable `return None` after a return in user preferences update:
    - `backend/api/auth.py`.
- Startup stability:
  - `os.getenv(...)` used without importing `os` in Sentry init:
    - `backend/main.py`.

### 6) Maintainability & Tech Debt
- God services / overly broad responsibilities:
  - `InventoryService`, `RecommendationsService`.
- Duplication:
  - Similar forecast-demand lookup and forecast-refresh scheduling logic exists in multiple services (inventory/dashboard/recommendations).
- Inconsistencies:
  - Duplicate imports, mixed patterns for shaping responses (service vs API handler), and misleading “optional user” dependencies.

### 7) Security & Abuse Surface (practical, backend)
- Highest-risk trust boundary issue:
  - Missing tenant scoping in API-layer DB queries (potential cross-tenant access via same `item_id`).
- ETL connector configuration:
  - User-supplied connection details can become SSRF/internal network access if exposed to non-admins (`backend/api/etl.py`, `backend/services/etl/connectors.py`).
- Rate limiting:
  - Mainly on auth flows; high-cost endpoints (inventory list, ETL, forecast testbed) are not consistently protected. Current limiter is in-memory and may not behave as expected behind proxies.

## Prioritized Recommendations

### P0 (Do ASAP)
- Tenant-scope all API-layer queries used for response shaping (always filter by `client_id` where applicable) and replace `scalar_one()` assumptions with safe lookups.
- Unify cart `session_id` derivation across all cart and PO-from-cart flows.
- Fix Sentry startup crash (`import os`).

### P1 (Next)
- Eliminate N+1 patterns in inventory list and recommendations by batching:
  - Batch-fetch suppliers/conditions/locations per page.
  - Prefer latest `inventory_metrics` rows for list filters/sorting; refresh asynchronously on forecast/stock updates.
- Wrap ETL “replace” and cart→PO flows in single transactions (avoid committing mid-flow).
- Replace PO number generation with a concurrency-safe strategy (DB sequence, unique constraint + retry, or server-generated UUID-based PO numbers).

### P2 (Later)
- Remove/feature-flag “limit to first 5 items” in simulation to avoid misleading outputs.
- Consolidate duplicated forecast refresh/demand lookup logic into a shared module/service.
- Standardize error responses and avoid returning raw exception strings to clients.

