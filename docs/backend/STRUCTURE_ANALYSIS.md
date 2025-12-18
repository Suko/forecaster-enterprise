# Backend Structure Analysis

This is a lightweight map of the backend codebase to help keep changes consistent and reduce “where should this go?” drift.

## High-level layout

```
backend/
├── main.py                 # FastAPI app wiring (routers, middleware)
├── api/                    # Route handlers (thin controllers)
├── services/               # Business logic
├── schemas/                # Pydantic request/response models
├── models/                 # SQLAlchemy models + migrations
├── auth/                   # JWT + service-auth helpers
├── forecasting/            # Forecasting engine (methods, services, validation)
├── etl/                    # Connectors + sync services
└── tests/                  # pytest suite (API + services + forecasting)
```

## Where to add things

- **New endpoint**: add router in `backend/api/…` → call a `backend/services/…` method → return `backend/schemas/…` response model.
- **New business rule**: implement in `backend/services/…` (keep APIs thin).
- **New DB table**: add SQLAlchemy model in `backend/models/…` + Alembic migration.
- **Contract changes**: update schema + OpenAPI + `docs/backend/API_REFERENCE.md` + frontend proxy/types (see `docs/system/CONTRACTS.md`).

## Key entrypoints

- API wiring: `backend/main.py`
- Auth dependencies: `backend/auth/`
- Inventory surface area: `backend/api/inventory.py`, `backend/services/inventory_service.py`
- Dashboard surface area: `backend/api/dashboard.py`, `backend/services/dashboard_service.py`

