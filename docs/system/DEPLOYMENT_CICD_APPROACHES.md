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

## Approach: GitHub Actions Builds Image → Push → Deploy Stage/Prod

Good when:
- You want repeatable builds and deploy control.
- You want to promote the **same image** from stage → production.

```
GitHub Actions (CI)
  ┌───────────────────────────────────────────────────────────┐
  │ 1) docker build                                           │
  │ 2) run tests (inside repo or inside container)             │
  │ 3) tag image with vX.Y.Z + commit SHA                       │
  │ 4) push to registry (GHCR)                                  │
  └───────────────────────────────────────────────────────────┘
                        |
                        v
                 Container Registry
                        |
                        v
Stage Deploy (CD)
  ┌───────────────────────────────────────────────────────────┐
  │ 1) pull image tag (vX.Y.Z)                                 │
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

### Release versioning

Use git tags `vX.Y.Z` as the release identifier (examples: `v0.1.0`, `v0.1.1`).
Build/push images on tag creation, then deploy **by tag** to stage and production.

### How it’s triggered in this repo

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `backend-ci.yml` | PRs | Lint + tests (no deploy) |
| `docker-build.yml` | PRs (Dockerfile changes) | Verify Dockerfile builds before merge |
| `release-images.yml` | Tag push (`v*`) | Build + push to GHCR |
| `deploy-stage.yml` | Manual (`workflow_dispatch`) | Deploy to stage (placeholder) |
| `deploy-production.yml` | Manual (`workflow_dispatch`) | Deploy to prod (placeholder, requires approval) |

Notes:
- Frontend is in a separate repository; its CI/CD is handled there.
- Deploy workflows are placeholders until you wire them to your hosts (typically via SSH).

### Release commands

```bash
# create a release tag
git tag v0.0.1
git push origin v0.0.1

# then run GitHub Actions:
# - Release Images (vX.Y.Z)  (publishes images)
# - Deploy Stage (image_tag=v0.0.1)
# - Deploy Production (image_tag=v0.0.1)  (after approval)
```

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

| Gate | Workflow | When |
|------|----------|------|
| Docs drift check | `docs-contract.yml` | PRs |
| Backend lint + tests | `backend-ci.yml` | PRs |
| Dockerfile builds | `docker-build.yml` | PRs (when Dockerfile or deps change) |
| Release build/push | `release-images.yml` | Tag push (`v*`) |

Optional (recommended): Add a smoke step to `release-images.yml` that boots the image and verifies `/ready` returns 200.

---

## Alternative CI/CD Platforms

### Self-Hosted GitLab CI/CD
**When to choose:** Cost avoidance, full infrastructure control, existing server capacity.

**Setup Requirements:**
- GitLab instance on your server (Docker container)
- GitLab runners (Docker-based, on your server)
- GitLab container registry
- `.gitlab-ci.yml` instead of GitHub workflows

**Key Differences:**
- `gitlab-ci.yml` syntax (stages, jobs, artifacts)
- GitLab environments instead of GitHub environments
- GitLab CI/CD variables for secrets
- GitLab registry for container images
- **Zero cost** - runs on your existing server

**Quick Setup (1-2 days):**
1. **Install GitLab:** `docker run -d --name gitlab gitlab/gitlab-ce:latest`
2. **Convert workflows:** GitHub Actions → `.gitlab-ci.yml`
3. **Register runners:** `gitlab-runner register` on your server
4. **Configure registry** and update image references
5. **Test pipeline** locally before going live

**Cost Savings:** Eliminates GitHub Actions minute costs entirely

---

## Wiring Stage/Production Deploy Workflows (SSH + Docker Compose)

`Deploy Stage` and `Deploy Production` workflows exist but are placeholders until you connect them to your servers:

- `.github/workflows/deploy-stage.yml`
- `.github/workflows/deploy-production.yml`

### Minimal wiring plan

1) **Create GitHub Environments**
- Environment: `stage`
- Environment: `production` (set required reviewers for approval gating)

2) **Add environment secrets (typical)**
- `DEPLOY_HOST` (e.g. `stage.example.com`)
- `DEPLOY_USER` (e.g. `ubuntu`)
- `DEPLOY_SSH_KEY` (private key for the deploy user)
- `DEPLOY_PATH` (remote folder containing `docker-compose.yml`, e.g. `/opt/forecaster`)
- Optional: any runtime secrets you don’t want in the repo (or keep them in a remote `.env` file on the server)

3) **Implement the workflow steps**
- SSH into the host
- `cd $DEPLOY_PATH`
- `docker compose pull` (pull the `vX.Y.Z` tag you passed as `image_tag`)
- `docker compose up -d`
- Run smoke checks (at minimum: `curl /ready`; ideally call a small `scripts/smoke.sh` against the deployed base URL)

### Example remote commands (what the workflow should run)

```bash
cd /opt/forecaster
docker compose pull
docker compose up -d
curl -fsS http://localhost:8000/ready
```

Notes:
- For multi-instance deployments, run migrations as a single step/job (avoid multiple replicas racing migrations).
- Prefer deploying by `vX.Y.Z` so stage and production run the exact same artifact.

---

## Alembic Migration Safety (Don’t Break / Don’t “Destroy” DB)

### What you already have

- The Docker entrypoint runs migrations before starting the app (`backend/docker-entrypoint.sh` runs `alembic upgrade head`).
- In Postgres, most DDL migrations are transactional: if a migration fails mid-way, the transaction is rolled back and the DB is not left half-changed.

### What to be careful about

- **Non-transactional DDL exists** (example: `CREATE INDEX CONCURRENTLY`). If you ever use it, failures can leave partial artifacts and require manual cleanup.
- **Destructive changes** (dropping tables/columns, changing types in-place) are the biggest risk. Prefer “expand/contract” patterns instead.
- **Multi-instance deploys**: if you run multiple backend replicas, do not let all replicas race to run migrations. Run migrations as a single job/step, then roll out app replicas.

### Pragmatic migration policy (recommended)

- **Never “drop” immediately**: add new columns/tables first; backfill; switch reads/writes; only remove later (or not at all).
- **Two-step constraints**: add nullable → backfill data → add NOT NULL/constraints in a later migration.
- **Stage-first rule**: every migration is applied to stage (with prod-like data shape) before production.
- **Backup before prod migrations**: automated snapshot/backup + documented restore procedure.

### Verification commands (safe preflight)

From repo root (local or in a CI runner):

- Check there is only one head and migrations apply cleanly:
  - `cd backend && uv run alembic heads`
  - `cd backend && uv run alembic upgrade head`
- Confirm current revision after deploy:
  - `cd backend && uv run alembic current`

### Failover / rollback reality

- **App rollback is easy** (deploy previous image tag).
- **DB rollback is not always safe**. Prefer forward-fix migrations over downgrades, unless you explicitly test `downgrade()` paths and keep migrations backward-compatible.
