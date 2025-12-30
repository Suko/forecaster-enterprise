# Deployment Flow

**Complete flow from code to running application**

---

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Deployment Flow                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Build (GitHub Actions)                                      │
│     └─▶ Tag push (v0.0.1)                                       │
│         └─▶ release-images.yml                                  │
│             ├─▶ Build Docker image (no ML deps, ~200MB)        │
│             └─▶ Push to GHCR                                    │
│                                                                 │
│  2. Deploy (GitHub Actions)                                     │
│     └─▶ Manual trigger (workflow_dispatch)                      │
│         └─▶ deploy-stage.yml                                    │
│             ├─▶ Pull image from GHCR                            │
│             ├─▶ docker compose up -d                             │
│             └─▶ Wait for /ready (up to 6 min)                   │
│                                                                 │
│  3. Container Startup (docker-entrypoint.sh)                    │
│     ├─▶ Wait for database                                       │
│     ├─▶ Run migrations                                          │
│     ├─▶ Check ML deps (torch + chronos_forecasting)             │
│     │   ├─▶ If missing → Download (2-3 min first time)         │
│     │   └─▶ If cached → Skip (~10 sec)                          │
│     ├─▶ First-time setup? (if no users)                         │
│     │   └─▶ Run setup.sh (creates users)                        │
│     └─▶ Start uvicorn                                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Flow

### Step 1: Build Image (CI)

**Trigger:** Push git tag (e.g., `v0.0.1`)

**Workflow:** `.github/workflows/release-images.yml`

**What happens:**
1. Builds Docker image from `backend/Dockerfile`
2. **No ML dependencies** in image (saves ~2GB)
3. Image contains: Python, application code, base dependencies
4. Pushes to GHCR: `ghcr.io/USER/forecaster-enterprise/backend:v0.0.1`

**Time:** ~39 seconds

**Output:** Docker image ready in GHCR

---

### Step 2: Deploy to Stage (CD)

**Trigger:** Manual (GitHub Actions → "Deploy Stage" → Run workflow)

**Workflow:** `.github/workflows/deploy-stage.yml`

**What happens:**
1. SSH to stage server
2. Pull image from GHCR
3. Stop old containers: `docker compose down`
4. Start new containers: `docker compose up -d`
5. **Wait for `/ready` endpoint** (up to 6 minutes)
   - Accounts for ML deps installation on first run
   - Uses cached deps on subsequent deployments

**Time:** 
- First deployment: ~3-5 minutes (ML deps download)
- Subsequent deployments: ~30 seconds (cached)

**Output:** Application running on stage server

---

### Step 3: Container Startup

**Script:** `backend/docker-entrypoint.sh`

**What happens (in order):**

#### 3.1 Wait for Database
```bash
# Waits until PostgreSQL is ready
until psql -c '\q'; do sleep 2; done
```

#### 3.2 Run Migrations
```bash
alembic upgrade head
```

#### 3.3 Check & Install ML Dependencies
```bash
# Check if torch and chronos_forecasting are installed
if ! python -c "import torch; import chronos_forecasting"; then
  # Download PyTorch CPU-only + chronos-forecasting
  uv pip install torch chronos-forecasting
  # Takes 2-3 minutes first time
  # Uses cached packages from volume on subsequent runs
fi
```

**Where cached:**
- PyTorch packages: `/home/appuser/.cache/pip` (Docker volume: `ml_pip_cache`)
- HuggingFace models: `/home/appuser/.cache/huggingface` (Docker volume: `ml_models_cache`)

#### 3.4 First-Time Setup (if needed)
```bash
# Check if users table has any records
if [ "$FIRST_TIME_SETUP" = "true" ]; then
  # Run setup.sh to create admin/test users
  bash /app/setup.sh
fi
```

#### 3.5 Start Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Timing Breakdown

### First Deployment (No Cache)

| Step | Time | Description |
|------|------|-------------|
| Build image | 39s | Fast (no ML deps) |
| Pull image | 10s | Download from GHCR |
| Container start | 30s | Wait for DB, migrations |
| **ML deps install** | **2-3 min** | Download PyTorch + models |
| Setup (if first-time) | 10s | Create users |
| **Total** | **~4-5 min** | First deployment |

### Subsequent Deployments (Cached)

| Step | Time | Description |
|------|------|-------------|
| Build image | 39s | Fast (no ML deps) |
| Pull image | 10s | Download from GHCR |
| Container start | 30s | Wait for DB, migrations |
| **ML deps check** | **~10s** | Uses cached packages |
| **Total** | **~1-2 min** | Subsequent deployments |

---

## Key Points

### ✅ ML Dependencies Are NOT in Docker Image

**Why?**
- Reduces image size from ~2.5GB to ~200MB
- Faster CI/CD builds (39s vs 10-15 min)
- Avoids GitHub Actions disk space issues

**How?**
- Installed at runtime in `docker-entrypoint.sh`
- Cached in Docker volumes (persist across releases)
- Only downloads on first run or if cache is cleared

### ✅ Volumes Persist Across Deployments

**Volumes:**
- `ml_models_cache` → HuggingFace models (~500MB)
- `ml_pip_cache` → PyTorch packages (~500MB)

**Result:** ML deps only download once per server, reused forever

### ✅ Health Check Handles ML Install Time

**docker-compose.yml:**
```yaml
healthcheck:
  start_period: 300s  # 5 minutes for first-time ML install
```

**deploy-stage.yml:**
- Waits up to 6 minutes for `/ready` endpoint
- Accounts for ML deps installation time

---

## Deployment Commands

### Build & Push Image
```bash
# Create and push tag
git tag v0.0.1
git push origin v0.0.1

# Triggers: release-images.yml
# Result: Image in GHCR
```

### Deploy to Stage
```bash
# Via GitHub Actions UI:
# 1. Go to Actions → "Deploy Stage"
# 2. Click "Run workflow"
# 3. Enter image_tag: v0.0.1
# 4. Click "Run workflow"

# Or manually on server:
cd /opt/forecaster
docker pull ghcr.io/USER/forecaster-enterprise/backend:v0.0.1
docker compose up -d
```

---

## Troubleshooting

### ML Dependencies Not Installing

**Check logs:**
```bash
docker compose logs backend | grep -i "torch\|chronos"
```

**Verify volumes:**
```bash
docker volume ls | grep ml_
docker exec forecast-backend ls -la /home/appuser/.cache/pip
```

### Health Check Timeout

**First deployment:** Normal if ML deps are downloading (up to 5 min)

**Subsequent deployments:** Should be fast (~30 sec). If slow:
```bash
# Check if ML deps are cached
docker exec forecast-backend python -c "import torch; import chronos_forecasting"
# Should succeed immediately
```

### Deployment Fails After 6 Minutes

**Check:**
1. Backend logs: `docker compose logs backend`
2. Database connection: `docker compose ps db`
3. ML deps installation: Look for "Installing PyTorch" in logs

---

## Related Documentation

- [Best Practices Assessment](./DEPLOYMENT_BEST_PRACTICES_ASSESSMENT.md) - **Evaluation against industry standards**
- [First Release Checklist](./FIRST_RELEASE_CHECKLIST.md)
- [CI/CD Approaches](../system/DEPLOYMENT_CICD_APPROACHES.md)
- [ML Dependencies Architecture](../system/ML_DEPENDENCIES_ARCHITECTURE.md)
- [CI/CD Audit](../system/CICD_AUDIT.md)

---

**Last Updated:** 2025-12-30
