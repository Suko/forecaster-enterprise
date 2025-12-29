# Deployment & CI/CD Approaches (Local / Stage / Production)

**Last Updated:** 2025-12-29  
**Purpose:** Document pragmatic deployment options that are verifiable locally, then reusable for stage and production.

---

## Core Idea: One Artifact, One Smoke Check

The most reliable setup is:

1) Build **the same Docker image** you deploy  
2) Run **the same smoke checks** (locally → stage → prod)  

This avoids “works on my machine” differences.

---

## Environments (Recommended Contract)

```
Local       Stage                Production
-----       -----                ----------
Dev data    Prod-like config     Prod config + alerts
Fast loop   Safe deploy checks   Safe deploy checks + rollback
```

Environment differences should be configuration only (env vars/secrets), not code paths.

---

## Health Contracts

Keep two endpoints distinct:

- `/health`  = process is up (no DB dependency; fast)
- `/ready`   = ready to serve traffic (DB reachable + migrations applied)

Most orchestrators (Compose/ECS/K8s) should gate traffic on `/ready`, not `/health`.

---

## Approach A (Fastest): Manual Docker Compose (Local → Stage → Prod)

Good when:
- You want the simplest path to production.
- You deploy to a single VM (or a small number of VMs) without a full platform.

```
Developer / CI
   |
   | docker compose build
   | docker compose up -d
   | curl /ready + smoke checks
   v
Local running stack

Stage/Prod (VM)
   |
   | git pull OR copy docker-compose.yml
   | docker compose pull
   | docker compose up -d
   | curl /ready + smoke checks
   v
Stage/Prod running stack
```

Verification checklist:
- `docker compose ps` shows healthy services
- `curl http://HOST:8000/health`
- `curl http://HOST:8000/api/v1/health`
- authenticated: `GET /api/v1/system/status`

Rollback (pragmatic):
- redeploy previous image tag (or previous git revision) and restart compose.

---

## Approach B (Recommended): GitHub Actions Builds Image → Push → Deploy Stage/Prod

Good when:
- You want repeatable builds and deploy control.
- You want to promote the **same image** from stage → production.

```
GitHub Actions (CI)
  ┌───────────────────────────────────────────────────────────┐
  │ 1) docker build                                           │
  │ 2) run tests (inside repo or inside container)             │
  │ 3) tag image with commit SHA                               │
  │ 4) push to registry                                        │
  └───────────────────────────────────────────────────────────┘
                        |
                        v
                 Container Registry
                        |
                        v
Stage Deploy (CD)
  ┌───────────────────────────────────────────────────────────┐
  │ 1) pull image tag (commit SHA)                             │
  │ 2) docker compose up -d                                    │
  │ 3) smoke check (/ready + basic API calls)                  │
  └───────────────────────────────────────────────────────────┘
                        |
                  promote same tag
                        v
Production Deploy (CD)
  ┌───────────────────────────────────────────────────────────┐
  │ same as stage, plus alerts and rollback procedure          │
  └───────────────────────────────────────────────────────────┘
```

Key rule: production always deploys an **existing, already-tested tag**.

Rollback:
- redeploy previous known-good tag.

---

## Approach C (Future): GitOps / Kubernetes

Good when:
- You need scaling, rollout strategies, multi-instance reliability.

```
GitHub Actions builds image -> Registry
                     |
                     v
GitOps repo updates image tag
                     |
                     v
Cluster controller reconciles:
Deployment -> readiness gates -> rollout -> rollback
```

Minimum requirements to make this work well:
- `/ready` is DB-aware
- structured logs + request IDs
- resource limits and timeouts

---

## What “Verified Locally” Means

For any approach, you should be able to run the same checks locally:

```
docker compose up -d
wait for /ready
run smoke calls
docker compose down
```

If local smoke passes but stage fails, the delta should be configuration only:
- env vars/secrets
- DB endpoint
- CORS/origins
- external integrations (ETL connectors, license service, etc.)

---

## Suggested Minimum CI Gates

Even a small team benefits from these gates:

- Docs drift check (already present)
- Backend tests: `cd backend && uv run pytest tests/ -q`
- Build + boot check: container starts, migrations run, `/ready` becomes OK

