# Next Steps: Deployment Implementation

**Action plan to get v0.0.1 deployed to stage**

---

## 🎯 Immediate Next Steps (To Deploy)

### Step 1: Set Up Stage Infrastructure

**1.1 Provision Stage Server**
- [ ] Get a server (VPS, AWS EC2, DigitalOcean, etc.)
- [ ] Minimum specs: 2 CPU, 4GB RAM, 20GB disk
- [ ] Install Docker: `curl -fsSL https://get.docker.com | sh`
- [ ] Create deploy directory: `mkdir -p /opt/forecaster`

**1.2 Set Up Database**
- [ ] Option A: Use existing PostgreSQL (if available)
- [ ] Option B: Run PostgreSQL in Docker on same server
- [ ] Option C: Use managed database (AWS RDS, DigitalOcean DB, etc.)
- [ ] Note connection details for `.env` file

**1.3 Prepare Server**
```bash
# On stage server
sudo mkdir -p /opt/forecaster
sudo chown $USER:$USER /opt/forecaster
cd /opt/forecaster

# Copy docker-compose.yml from repo
# Create .env file with stage credentials
```

---

### Step 2: Configure GitHub Environments

**2.1 Create Stage Environment**
- [ ] Go to GitHub → Repo → Settings → Environments
- [ ] Click "New environment"
- [ ] Name: `stage`
- [ ] No required reviewers (for now)

**2.2 Add Environment Secrets**
- [ ] `DEPLOY_HOST` - Stage server IP/hostname
- [ ] `DEPLOY_USER` - SSH username (e.g., `ubuntu`)
- [ ] `DEPLOY_SSH_KEY` - Private SSH key (see below)
- [ ] `DEPLOY_PATH` - `/opt/forecaster`
- [ ] `GITHUB_REPOSITORY` - Your repo (e.g., `USER/forecaster-enterprise`)

**2.3 Generate SSH Key**
```bash
# On your local machine
ssh-keygen -t rsa -b 4096 -C "deploy@forecaster" -f ~/.ssh/forecaster_deploy -N ""

# Copy PRIVATE key to GitHub secret DEPLOY_SSH_KEY
cat ~/.ssh/forecaster_deploy

# Copy PUBLIC key to stage server
ssh-copy-id -i ~/.ssh/forecaster_deploy.pub ubuntu@YOUR_STAGE_IP
```

---

### Step 3: Fix Deploy Workflow SSH Key

**Current issue:** Workflow references `~/.ssh/deploy_key` but we created `forecaster_deploy`

**Fix:** Update `.github/workflows/deploy-stage.yml`:
```yaml
# Add step to set up SSH key
- name: Set up SSH key
  run: |
    mkdir -p ~/.ssh
    echo "$DEPLOY_SSH_KEY" > ~/.ssh/deploy_key
    chmod 600 ~/.ssh/deploy_key
    ssh-keyscan -H $DEPLOY_HOST >> ~/.ssh/known_hosts

- name: Deploy to stage
  run: |
    # ... rest of deployment
```

---

### Step 4: Test Deployment

**4.1 Create Test Tag**
```bash
git tag v0.0.1-test
git push origin v0.0.1-test
```

**4.2 Trigger Build**
- [ ] Wait for `release-images.yml` to complete
- [ ] Verify image in GHCR: `ghcr.io/USER/forecaster-enterprise/backend:v0.0.1-test`

**4.3 Deploy to Stage**
- [ ] Go to GitHub Actions → "Deploy Stage"
- [ ] Click "Run workflow"
- [ ] Enter `image_tag: v0.0.1-test`
- [ ] Monitor deployment logs

**4.4 Verify Deployment**
```bash
# SSH to stage server
ssh ubuntu@YOUR_STAGE_IP

# Check containers
docker ps

# Check logs
docker compose -f /opt/forecaster/docker-compose.yml logs backend

# Test health
curl http://localhost:8000/ready
```

---

## 🔴 High Priority Improvements (Before Production)

### 1. Add Smoke Tests to Deployment

**Update `.github/workflows/deploy-stage.yml`:**
```yaml
- name: Run smoke tests
  run: |
    ssh -o StrictHostKeyChecking=no -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
      # Wait for backend to be ready
      sleep 30
      
      # Smoke tests
      curl -f http://localhost:8000/ready || exit 1
      curl -f http://localhost:8000/api/v1/health || exit 1
      curl -f http://localhost:8000/api/v1/products || exit 1
      
      echo "✅ Smoke tests passed"
    EOF
```

### 2. Document Rollback Procedure

**Create `docs/setup/ROLLBACK_PROCEDURE.md`:**
- How to identify which tag to rollback to
- Steps to rollback (deploy previous tag)
- How to verify rollback succeeded
- When to rollback (error thresholds)

### 3. Add Deployment Notifications

**Option A: GitHub Actions Notifications**
- Use GitHub's built-in notifications
- Configure in repo settings

**Option B: Slack/Email Integration**
```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'Deployment failed!'
```

---

## 🟡 Medium Priority (v0.5+)

### 1. Improve Health Check Monitoring
- Add uptime monitoring (UptimeRobot, Pingdom)
- Set up alerts for health check failures
- Monitor response times

### 2. Add Log Aggregation
- Send logs to centralized location (CloudWatch, ELK, etc.)
- Enable log retention
- Set up log alerts

### 3. Database Backup Strategy
- Automated daily backups
- Test restore procedure
- Document backup retention policy

---

## ✅ Checklist: Ready to Deploy?

Before deploying to stage, verify:

- [ ] Stage server provisioned and accessible
- [ ] Docker installed on stage server
- [ ] Database accessible from stage server
- [ ] GitHub `stage` environment created
- [ ] All environment secrets configured
- [ ] SSH key set up and tested
- [ ] `docker-compose.yml` copied to stage server
- [ ] `.env` file created on stage server
- [ ] Image built and pushed to GHCR (`v0.0.1-test`)
- [ ] Deploy workflow updated with SSH key setup

---

## 🚀 Deployment Sequence

Once ready:

1. **Build Image**
   ```bash
   git tag v0.0.1
   git push origin v0.0.1
   # Wait for release-images.yml to complete
   ```

2. **Deploy to Stage**
   - GitHub Actions → "Deploy Stage" → Run workflow
   - Enter `image_tag: v0.0.1`
   - Monitor logs

3. **Verify**
   - Check health: `curl http://STAGE_IP:8000/ready`
   - Test API: `curl http://STAGE_IP:8000/api/v1/products`
   - Check logs: `docker compose logs backend`

4. **If Issues**
   - Check logs: `docker compose logs backend`
   - Verify ML deps: `docker exec forecast-backend python -c "import torch"`
   - Check database connection
   - Rollback if needed (deploy previous tag)

---

## 📋 Post-Deployment Tasks

After successful stage deployment:

- [ ] Document any issues encountered
- [ ] Update deployment docs with lessons learned
- [ ] Test rollback procedure
- [ ] Set up monitoring/alerting
- [ ] Plan production deployment (after stage validation)

---

## Related Documentation

- [Deployment Flow](./DEPLOYMENT_FLOW.md)
- [First Release Checklist](./FIRST_RELEASE_CHECKLIST.md)
- [Best Practices Assessment](./DEPLOYMENT_BEST_PRACTICES_ASSESSMENT.md)
- [Environment Management](./ENV_MANAGEMENT.md)

---

**Last Updated:** 2025-12-30
