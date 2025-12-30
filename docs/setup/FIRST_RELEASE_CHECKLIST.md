# First Release Checklist (v0.0.1)

**Last Updated:** 2025-12-30
**Status:** ✅ CI/CD operational, ready for deployment
**Goal:** Safely deploy v0.0.1 to stage, then production

---

## Executive Summary

**Simplified Stage Deployment Plan** - Get v0.0.1 working on stage using GitHub Actions + GHCR.

**Goal:** Working deployment in 1-2 hours, then expand to production.

**Current Status:** ✅ CI/CD operational (39s builds). Ready for stage deployment.

**Estimated Time:** 1-2 hours for stage
**Risk Level:** Low (GitHub-managed, proven tools)

---

## Pre-Release Verification ✅

**Note:** If switching to self-hosted GitLab, verify your server has sufficient resources:
- **CPU:** 2+ cores for GitLab + runners
- **RAM:** 4GB+ for GitLab instance
- **Storage:** 50GB+ for container images and git repos
- **Docker:** Latest version installed

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
- [x] `backend-ci.yml` passes on PR (lint + tests)
- [x] `docker-build.yml` builds successfully on Dockerfile changes
- [x] `release-images.yml` builds and pushes to GHCR (✅ 39s build time)
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

### 2. GitHub Container Registry (GHCR)
**Using:** `ghcr.io` (automatic with GitHub Actions)

**Image URL:** `ghcr.io/YOUR_USERNAME/forecaster-enterprise/backend:v0.0.1`

**Setup:** Automatic - no configuration needed
**Cost:** Included in GitHub Pro ($4/month for private repos)

### 2. Stage Environment Secrets
**Add to GitHub `stage` environment:**

- [ ] `DEPLOY_HOST` - Your stage server IP/hostname
- [ ] `DEPLOY_USER` - SSH username (e.g., `ubuntu`)
- [ ] `DEPLOY_SSH_KEY` - Private SSH key (generate with `ssh-keygen`)
- [ ] `DEPLOY_PATH` - Directory on server (e.g., `/opt/forecaster`)
- [ ] `DATABASE_URL` - Stage database connection
- [ ] `SECRET_KEY` - Random secret key for the app

### 3. Stage Server Setup
**On your stage server:**

**3.1 Provision Server**
- [ ] Get a server (VPS, AWS EC2, DigitalOcean, etc.)
- [ ] Minimum specs: 2 CPU, 4GB RAM, 20GB disk
- [ ] Install Docker: `curl -fsSL https://get.docker.com | sh`
- [ ] Create deploy directory: `mkdir -p /opt/forecaster && chown $USER:$USER /opt/forecaster`

**3.2 Set Up Database**
- [ ] Option A: Use existing PostgreSQL (if available)
- [ ] Option B: Run PostgreSQL in Docker on same server
- [ ] Option C: Use managed database (AWS RDS, DigitalOcean DB, etc.)
- [ ] Note connection details for `.env` file

**3.3 Prepare Server**
```bash
# On stage server
cd /opt/forecaster
# Copy docker-compose.yml from repo
# Create .env file with stage credentials
```

**3.4 SSH Key Setup**
```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "deploy@forecaster" -f ~/.ssh/forecaster_deploy -N ""

# Copy PRIVATE key to GitHub secret DEPLOY_SSH_KEY
cat ~/.ssh/forecaster_deploy

# Copy PUBLIC key to stage server
ssh-copy-id -i ~/.ssh/forecaster_deploy.pub ubuntu@YOUR_STAGE_IP

# Test connection
ssh ubuntu@YOUR_STAGE_IP "docker --version"
```

---

## Stage Deployment Implementation 📋

### 1. Deploy Stage Workflow
**Status:** ✅ Already configured in `.github/workflows/deploy-stage.yml`

**Features:**
- SSH key setup from secret
- Image pull from GHCR
- Health check wait (up to 6 min for ML deps)
- Log output on success/failure

### 2. Test Deployment

**2.1 Create Test Tag**
```bash
git tag v0.0.1-test
git push origin v0.0.1-test
```

**2.2 Trigger Build**
- [ ] Wait for `release-images.yml` to complete
- [ ] Verify image in GHCR: `ghcr.io/USER/forecaster-enterprise/backend:v0.0.1-test`

**2.3 Deploy to Stage**
- [ ] Go to GitHub Actions → "Deploy Stage"
- [ ] Click "Run workflow"
- [ ] Enter `image_tag: v0.0.1-test`
- [ ] Monitor deployment logs

**2.4 Verify Deployment**
```bash
# SSH to stage server
ssh ubuntu@YOUR_STAGE_IP

# Check containers
docker ps

# Check logs
docker compose -f /opt/forecaster/docker-compose.yml logs backend

# Test health
curl http://localhost:8000/ready
curl http://localhost:8000/api/v1/health
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

## Production Deployment (Phase 2)

**After stage proves stable, set up production:**

1. [ ] Create `production` environment with required reviewers
2. [ ] Add production secrets (separate database, etc.)
3. [ ] Set up production server with same prerequisites
4. [ ] Update `deploy-production.yml` with production workflow
5. [ ] Test production deployment process

---

## Alternative Approaches (Future)

**If using GitLab locally hosted instead of GitHub Actions:**

### Key Differences:
- **CI/CD File**: `.gitlab-ci.yml` instead of `.github/workflows/`
- **Container Registry**: GitLab registry instead of GHCR
- **Secrets**: GitLab CI/CD variables instead of GitHub secrets
- **Environments**: GitLab environments instead of GitHub environments
- **Cost**: No monthly costs vs GitHub Actions limits

### Required Changes:
1. **Install GitLab** on your existing server
2. **Replace GitHub workflows** with `.gitlab-ci.yml`
3. **Update container image references** to use GitLab registry
4. **Configure GitLab runners** on your server
5. **Set up GitLab environments** with deployment approvals
6. **Migrate secrets** to GitLab CI/CD variables

### GitLab CI/CD Structure:
```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_IMAGE: $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_TAG

build:
  stage: build
  script:
    - docker build -t $DOCKER_IMAGE ./backend
    - docker push $DOCKER_IMAGE

deploy_staging:
  stage: deploy
  environment:
    name: staging
    url: https://staging.your-domain.com
  script:
    - docker pull $DOCKER_IMAGE
    - docker-compose up -d
    - curl -f http://localhost:8000/ready
```

**Cost Comparison:**
- **GitHub Actions**: 2,000 minutes/month free, then $0.008/minute (≈$4.80/month for 600 extra minutes)
- **GitLab Self-Hosted**: $0 - runs on your existing server

**Pros:** Zero cost, full control, runs on existing infrastructure
**Cons:** Setup time (1-2 days), maintenance overhead

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

## High Priority Improvements (Before Production) 🔴

### 1. Add Smoke Tests to Deployment
**Update `.github/workflows/deploy-stage.yml` to include:**
```yaml
- name: Run smoke tests
  run: |
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
      curl -f http://localhost:8000/ready || exit 1
      curl -f http://localhost:8000/api/v1/health || exit 1
      curl -f http://localhost:8000/api/v1/products || exit 1
      echo "✅ Smoke tests passed"
    EOF
```

### 2. Document Rollback Procedure
- [ ] Create rollback documentation
- [ ] Test rollback process (deploy previous tag)
- [ ] Document which tag to rollback to
- [ ] Define rollback triggers (error thresholds)

### 3. Add Deployment Notifications
- [ ] Configure Slack/email notifications
- [ ] Alert on deployment success/failure
- [ ] Include deployment logs in notifications

---

## Related Documentation

- [Deployment Flow](./DEPLOYMENT_FLOW.md) - **Complete build → deploy → startup flow**
- [Deployment & CI/CD Approaches](../system/DEPLOYMENT_CICD_APPROACHES.md)
- [ML Dependencies Architecture](../system/ML_DEPENDENCIES_ARCHITECTURE.md)
- [CI/CD Audit](../system/CICD_AUDIT.md)
- [Environment Management](./ENV_MANAGEMENT.md)
- [Development Setup](./DEVELOPMENT_SETUP.md)
- [System Integration](../system/INTEGRATION.md)

---

**Document Owner:** Development Team
**Last Updated:** 2025-12-29
**Next Review:** After v0.0.1 deployment