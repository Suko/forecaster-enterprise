# Next Steps: Deployment Implementation

**Action plan to get a tagged release deployed to stage via GitHub Actions + GHCR**

---

## 🎯 Immediate Next Steps (Deploy to Stage)

### Step 1: Prepare the Stage Server

**1.1 Provision Stage Server**
- [ ] Get a server (VPS, AWS EC2, DigitalOcean, etc.)
- [ ] Minimum specs: 2 CPU, 4GB RAM, 20GB disk
- [ ] Install Docker: `curl -fsSL https://get.docker.com | sh`
- [ ] Ensure Docker Compose v2 is available: `docker compose version`

**Hetzner Cloud (recommended defaults):**
- Image: Ubuntu 22.04/24.04
- Attach your SSH key in Hetzner Console (avoid password SSH)
- Enable Hetzner Firewall rules:
  - Inbound `22/tcp` from your IP (SSH)
  - Inbound `8000/tcp` from your IP (stage only) OR keep closed and use a tunnel/reverse proxy
  - Inbound `80/tcp` + `443/tcp` if you put Nginx/Caddy in front
  - No inbound `5432/tcp` (Postgres stays internal)

**1.2 Create Deploy Directory**
```bash
sudo mkdir -p /opt/forecaster
sudo chown $USER:$USER /opt/forecaster
cd /opt/forecaster
```

**1.3 Copy Deployment Compose**
- Choose one of:
  - `docker-compose.stage.with-db.yml` (Postgres runs as a container on the same VM)
  - `docker-compose.stage.yml` (Postgres is NOT in Docker; you point at an existing Postgres)
- Copy the chosen file to the server at `/opt/forecaster/docker-compose.stage.yml`
- Create `/opt/forecaster/.env` based on `.env.example` (do not commit this file)

**Required in `/opt/forecaster/.env` (minimum):**
- `DB_USER`, `DB_PASSWORD`, `DB_NAME`
- `DB_HOST` and `DB_PORT`
  - If using `docker-compose.stage.with-db.yml`: set `DB_HOST=db` (default)
  - If Postgres runs on the VM host: set `DB_HOST=host.docker.internal` and ensure Docker supports `host-gateway`
  - If Postgres is on another server: set `DB_HOST=<hostname>` and `DB_PORT=5432`
- `JWT_SECRET_KEY` (required in production/stage)

---

### Step 2: Configure GitHub Environment (`stage`)

**Create `stage` environment:**
- [ ] GitHub → Repo → Settings → Environments → New environment → `stage`

**Add these secrets to the `stage` environment (required):**
- [ ] `DEPLOY_HOST` - Stage server IP/hostname
- [ ] `DEPLOY_USER` - SSH username (e.g., `ubuntu`)
- [ ] `DEPLOY_SSH_KEY` - Private SSH key
- [ ] `DEPLOY_PATH` - `/opt/forecaster`

**Optional (to select compose file on the server):**
- [ ] `DEPLOY_COMPOSE_FILE` - Defaults to `docker-compose.stage.yml`

**Optional (recommended for private repos / private GHCR packages):**
- [ ] `GHCR_USERNAME` - GitHub username or org name
- [ ] `GHCR_TOKEN` - PAT with `read:packages`

---

### Step 3: Verify Deploy Workflow

**Workflow:** `.github/workflows/deploy-stage.yml`

Expected behavior:
- SSH to the stage host
- Pull `ghcr.io/<owner>/<repo>/backend:<image_tag>`
- Run `docker compose -f docker-compose.stage.yml up -d --no-deps --force-recreate backend`
- Wait for `GET /ready` to be 200
- Run smoke checks: `GET /api/v1/health`

---

### Step 4: Test Deployment End-to-End

**4.1 Create Test Tag**
```bash
git tag v0.0.1-test
git push origin v0.0.1-test
```

**4.2 Wait for Image Build**
- [ ] GitHub Actions → `Release Images (vX.Y.Z)` should push to GHCR

**4.3 Deploy to Stage**
- [ ] GitHub Actions → `Deploy Stage` → Run workflow
- [ ] Input: `image_tag: v0.0.1-test`

**4.4 Verify on Stage Host**
```bash
ssh ubuntu@YOUR_STAGE_IP
cd /opt/forecaster
docker compose -f docker-compose.stage.yml ps
curl -sf http://localhost:8000/ready
curl -sf http://localhost:8000/api/v1/health
```

---

## 🔴 Before Production (Recommended)

1. **Document rollback**
   - Deploy previous known-good tag (same workflow, older `image_tag`)
2. **Add notifications**
   - Slack/email on deploy success/failure (optional)
3. **Add deeper smoke checks**
   - Keep them unauthenticated (or use a short-lived service token)

---

## Related Docs

- [Deployment Flow](./DEPLOYMENT_FLOW.md)
- [First Release Checklist](./FIRST_RELEASE_CHECKLIST.md)
- [Best Practices Assessment](./DEPLOYMENT_BEST_PRACTICES_ASSESSMENT.md)
- [Environment Management](./ENV_MANAGEMENT.md)

---

**Last Updated:** 2026-01-03
