# First Release Checklist (v0.0.1)

**Last Updated:** 2025-12-29
**Status:** Pre-release
**Goal:** Safely deploy v0.0.1 to stage, then production

---

## Executive Summary

The codebase is feature-complete for v1 (per `docs/roadmap/NEXT_STEPS.md`). The CI/CD pipelines are configured but deployments are placeholders. This checklist ensures safe first deployment.

**Estimated Time:** 2-4 hours
**Risk Level:** Medium (first-time deployment)

---

## Pre-Release Verification ✅

### 1. Backend Health Checks
- [ ] `/health` endpoint returns 200 (no DB dependency)
- [ ] `/ready` endpoint returns 200 (DB reachable + migrations applied)
- [ ] Basic API calls work: `GET /api/v1/products` returns data
- [ ] Forecasting endpoints functional: `GET /api/v1/forecast/results`

### 2. Local Deployment Test
- [ ] `docker compose up -d` succeeds
- [ ] Health checks pass locally
- [ ] Basic smoke tests pass (curl `/ready`, sample API calls)
- [ ] Database migrations apply cleanly
- [ ] `docker compose down` cleans up properly

### 3. CI/CD Gates Pass
- [ ] `backend-ci.yml` passes on PR (lint + tests)
- [ ] `docker-build.yml` builds successfully on Dockerfile changes
- [ ] No linter errors or test failures
- [ ] **Test Suite Status**: 264 test functions discovered, no skipped tests
- [ ] **Lint Status**: Minor issues present (import sorting, deprecated typing) - acceptable for v0.0.1

---

## Deployment Infrastructure Setup 🚀

### 1. GitHub Environments
**Required for approval gating and secrets management**

- [ ] Create `stage` environment
- [ ] Create `production` environment with required reviewers
- [ ] Configure environment protection rules

### 2. Deployment Secrets
**Per environment (stage/prod) - store in GitHub Environment secrets**

- [ ] `DEPLOY_HOST` - Server hostname/IP (e.g., `stage.example.com`)
- [ ] `DEPLOY_USER` - SSH username (e.g., `ubuntu`)
- [ ] `DEPLOY_SSH_KEY` - Private SSH key for deploy user
- [ ] `DEPLOY_PATH` - Remote directory (e.g., `/opt/forecaster`)
- [ ] `DATABASE_URL` - Production database connection string
- [ ] `SECRET_KEY` - Application secret key
- [ ] Other runtime secrets (API keys, external service URLs)

### 3. Server Prerequisites
**On target servers (stage/prod)**

- [ ] Docker + Docker Compose installed
- [ ] SSH access configured for deploy user
- [ ] Deploy directory exists: `/opt/forecaster` (or configured path)
- [ ] `docker-compose.yml` present in deploy directory
- [ ] Environment file (`.env`) with runtime configuration
- [ ] Database accessible from server
- [ ] SSL certificates configured (if needed)

---

## Deployment Workflow Implementation 📋

### 1. Stage Deploy Workflow
**File:** `.github/workflows/deploy-stage.yml`

Current status: Placeholder only

**Required implementation:**
```yaml
# Replace the placeholder with actual deployment steps:
- SSH into DEPLOY_HOST
- cd $DEPLOY_PATH
- docker compose pull ghcr.io/YOUR_REPO/backend:v0.0.1
- docker compose up -d
- Wait for /ready endpoint (curl with timeout)
- Run basic smoke tests
- Log success/failure
```

### 2. Production Deploy Workflow
**File:** `.github/workflows/deploy-production.yml`

Current status: Placeholder only

**Required implementation:**
- Same as stage, plus:
- Pre-deployment backup (if applicable)
- Post-deployment verification
- Alert notifications
- Rollback procedure documentation

### 3. Rollback Plan
- [ ] Document rollback procedure: deploy previous tag
- [ ] Test rollback process (deploy → rollback → verify)
- [ ] Know which tag to rollback to (likely none for v0.0.1)

---

## Release Process 🔄

### Phase 1: Build & Test
1. [ ] Push code changes to main via PR
2. [ ] Verify CI passes
3. [ ] Create and push tag: `git tag v0.0.1 && git push origin v0.0.1`
4. [ ] Monitor "Release Images" workflow - should build and push to GHCR

### Phase 2: Stage Deployment
1. [ ] Go to GitHub Actions → "Deploy Stage"
2. [ ] Click "Run workflow"
3. [ ] Enter `image_tag: v0.0.1`
4. [ ] Monitor deployment logs
5. [ ] Verify stage deployment:
   - [ ] Health checks pass
   - [ ] Basic functionality works
   - [ ] No errors in logs

### Phase 3: Production Deployment
1. [ ] Go to GitHub Actions → "Deploy Production"
2. [ ] Click "Run workflow" (requires approval)
3. [ ] Enter `image_tag: v0.0.1`
4. [ ] Monitor deployment logs
5. [ ] Verify production deployment
6. [ ] Monitor for 24 hours post-deployment

---

## Post-Release Validation 📊

### 1. Functional Tests
- [ ] All API endpoints respond correctly
- [ ] Database connections stable
- [ ] External integrations working (if any)
- [ ] Performance acceptable (response times < 2s)

### 2. Monitoring & Alerts
- [ ] Application logs accessible
- [ ] Error tracking configured
- [ ] Health check monitoring (uptime monitoring)
- [ ] Database monitoring (connection pool, query performance)

### 3. Rollback Readiness
- [ ] Previous deployment artifacts preserved
- [ ] Rollback procedure tested
- [ ] Emergency contacts documented

---

## Risk Mitigation 🛡️

### High-Risk Items
- **Database migrations**: Test locally first, backup before prod
- **External dependencies**: Verify all integrations work
- **SSL/Network config**: Test connectivity before deploy
- **Resource limits**: Monitor memory/CPU usage

### Rollback Triggers
- API endpoints return 5xx errors > 5 minutes
- Database connection failures
- Memory/CPU usage > 90%
- External service outages affecting functionality

### Emergency Contacts
- [ ] Primary: [Contact info]
- [ ] Secondary: [Contact info]
- [ ] On-call schedule: [Details]

---

## Success Criteria ✅

**Stage Success:**
- Deployment completes without errors
- `/ready` endpoint returns 200
- Basic API calls succeed
- No application crashes in 1 hour

**Production Success:**
- All stage success criteria met
- 24-hour stability period
- No customer-impacting issues
- Rollback procedure validated

---

## Related Documentation

- [Deployment & CI/CD Approaches](../system/DEPLOYMENT_CICD_APPROACHES.md)
- [Environment Management](../setup/ENV_MANAGEMENT.md)
- [Development Setup](../setup/DEVELOPMENT_SETUP.md)
- [System Integration](../system/INTEGRATION.md)

---

**Document Owner:** Development Team
**Last Updated:** 2025-12-29
**Next Review:** After v0.0.1 deployment