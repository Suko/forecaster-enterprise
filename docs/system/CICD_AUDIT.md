# CI/CD and Deployment Audit

**Date:** 2025-12-30  
**Status:** Issues identified, fixes proposed

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CI/CD Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Tag Push (v0.0.1)                                          │
│     └─▶ release-images.yml                                      │
│         ├─▶ Build backend Docker image (no ML deps)            │
│         └─▶ Push to GHCR                                        │
│                                                                 │
│  2. Deploy Stage (manual)                                       │
│     └─▶ deploy-stage.yml                                        │
│         ├─▶ Pull image from GHCR                                │
│         ├─▶ docker-compose up                                   │
│         └─▶ Health check                                        │
│                                                                 │
│  3. Deploy Production (manual, approval required)               │
│     └─▶ deploy-production.yml                                   │
│         └─▶ Same as stage (placeholder)                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Container Startup Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Container Startup Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. docker-entrypoint.sh                                        │
│     ├─▶ Wait for DB                                             │
│     ├─▶ Run migrations (alembic upgrade head)                   │
│     ├─▶ Check if first-time (users table empty?)                │
│     ├─▶ Install ML deps (if not cached)                         │
│     ├─▶ Run setup.sh (if first-time)                            │
│     └─▶ Start uvicorn                                           │
│                                                                 │
│  2. setup.sh (first-time only)                                  │
│     ├─▶ Create admin user                                       │
│     ├─▶ Create test user (optional)                             │
│     ├─▶ Import demo data (optional)                             │
│     └─▶ Set up products/stock (optional)                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Issues Identified

### 🔴 Critical Issues

#### 1. uv.lock Out of Sync
**Problem:** Lock file still references chronos-forecasting and darts, even though removed from pyproject.toml  
**Impact:** `uv sync --frozen` will still try to install them  
**Fix:** Regenerate lock file with `uv lock`

#### 2. Container User Mismatch
**Problem:** Container runs as `appuser`, but:
- Volume mounts use `/root/.cache/` (wrong user home)
- `uv pip install --system` may fail without root

**Impact:** ML dependencies won't install, forecasting won't work  
**Fix:** 
- Change volume mounts to `/home/appuser/.cache/`
- Or keep container as root for runtime installs

#### 3. ML Deps Install Before App Starts
**Problem:** PyTorch download blocks app startup (2-3 min)  
**Impact:** Health checks may timeout on first run  
**Fix:** 
- Increase start_period in health check
- Or install in background

### 🟡 Medium Issues

#### 4. First-Time Detection Fragile
**Problem:** Checks `users` table existence after migrations  
**Scenarios not handled:**
- Migration fails but DB exists
- Users table exists but empty
- Partial setup failure

**Fix:** Use a dedicated `setup_completed` flag table

#### 5. No Rollback on Setup Failure
**Problem:** If setup.sh fails partially, no cleanup  
**Impact:** Inconsistent state  
**Fix:** Add transactional setup with rollback

#### 6. Deploy Workflows Are Placeholders
**Problem:** deploy-stage.yml and deploy-production.yml don't actually deploy  
**Impact:** Manual SSH required  
**Fix:** Implement actual deployment logic

### 🟢 Minor Issues

#### 7. Disk Cleanup Too Aggressive
**Problem:** Workflow deletes ALL Docker images/cache  
**Impact:** May affect other workflows  
**Fix:** More targeted cleanup

#### 8. No Smoke Tests After Deploy
**Problem:** Only health check, no API verification  
**Fix:** Add basic API smoke tests

---

## Proposed Fixes

### Fix 1: Regenerate uv.lock (Required)

```bash
cd backend
uv lock
```

### Fix 2: Fix Volume Mounts

```yaml
# docker-compose.yml
volumes:
  - ml_models_cache:/home/appuser/.cache/huggingface
  - ml_pip_cache:/home/appuser/.cache/pip
```

### Fix 3: Fix ML Install Command

```bash
# docker-entrypoint.sh - run as appuser, use pip (not uv pip --system)
pip install --quiet \
  --index-url https://download.pytorch.org/whl/cpu \
  torch torchvision torchaudio \
  chronos-forecasting darts
```

### Fix 4: Increase Health Check Start Period

```yaml
# docker-compose.yml
healthcheck:
  start_period: 300s  # 5 minutes for first-time ML install
```

### Fix 5: Add Setup Completion Flag

```python
# Check setup_status table instead of users
SELECT completed FROM setup_status WHERE id = 1;
```

---

## Recommended Order of Changes

1. **Regenerate uv.lock** (removes old deps)
2. **Fix volume mounts** (correct user path)
3. **Fix ML install command** (use pip, not uv pip --system)
4. **Test Docker build** locally
5. **Push and test CI/CD**
6. **Implement deploy workflows** (after build works)

---

## Testing Checklist

- [ ] `uv lock` regenerates without errors
- [ ] `docker build ./backend` succeeds
- [ ] `docker-compose up` starts successfully
- [ ] First-time setup creates admin user
- [ ] ML dependencies install from cache on restart
- [ ] Forecasting API works after ML install
- [ ] Health check passes within timeout

---

## Files to Modify

1. `backend/uv.lock` - Regenerate
2. `backend/docker-entrypoint.sh` - Fix ML install
3. `docker-compose.yml` - Fix volume mounts, health check
4. `.github/workflows/deploy-stage.yml` - Implement deployment
5. `.github/workflows/deploy-production.yml` - Implement deployment

---

**Next Steps:** Fix issues in order, test locally, then push to trigger CI/CD.
