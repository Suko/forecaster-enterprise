# Integration (Frontend ↔ Backend)

This document defines the **stable v1 integration rules** between frontend and backend.

## Source of Truth

- **API contract:** FastAPI OpenAPI (`/openapi.json`) and `docs/backend/API_REFERENCE.md` (generated).
- **System rules:** `docs/system/CONTRACTS.md`.
- **Project rules:** `docs/standards/STANDARDS.md`.

## Required Before Merge / Release

- Backend checks: see `docs/standards/STANDARDS.md`
- Docs drift check: `./scripts/check_docs_drift.sh`

## Authentication (v1)

- User calls: `Authorization: Bearer <token>` (client context from JWT)
- Service calls: `X-API-Key: <key>` (tenant selection rules in `docs/system/CONTRACTS.md`)

