# Backend Test Plan

This repo uses a **two-tier testing strategy** so we get fast feedback locally without forcing SQLite to emulate Postgres-only SQL.

If you need the previous checklist, see: `docs/archive/backend/TEST_PLAN.md`.

## Goals

- Keep a **fast default** test loop for day-to-day changes.
- Run a **real DB** suite for Postgres-specific behavior (SQL functions/operators, query semantics, performance-sensitive paths).

## Test Tiers (Recommended)

### Tier A — Fast (SQLite)
Use for: unit/service tests that don’t depend on Postgres-only SQL features.

- Run: `cd backend && uv run pytest tests/ -q`
- Tip: If a test requires Postgres-only SQL (e.g., `ANY`, JSONB ops), it should not be in Tier A.

### Tier B — Integration/Contract (Postgres)
Use for: API/integration tests and anything that needs real Postgres semantics.

Backend already supports this via `backend/tests/conftest.py`:
- `TEST_POSTGRES=true`
- `TEST_DATABASE_URL=postgresql+asyncpg://...`

Run examples:
- `cd backend && TEST_POSTGRES=true uv run pytest tests/ -q`
- `cd backend && TEST_POSTGRES=true uv run pytest tests/test_api/ -q`

## Markers (How We Keep Tiers Clean)

Adopt markers so SQLite runs stay stable:
- Mark Postgres-required tests with `@pytest.mark.postgres` or `@pytest.mark.integration`
- Default local run: `pytest -m "not postgres"`
- Integration run (CI/nightly): `TEST_POSTGRES=true pytest -m postgres`

## Fixtures/Data Rules (Avoid False Failures)

- Auth tests should use **real password hashing** in fixtures (avoid placeholder `hashed_password` values that make `authenticate_user()` correctly fail).
- Forecast/integration tests should provide explicit fixtures (e.g., `forecast_service`) or be marked as Tier B if they need heavy model initialization / database behavior.

## Lint / Quality Gates

- Backend lint: `cd backend && uv run ruff check .`
