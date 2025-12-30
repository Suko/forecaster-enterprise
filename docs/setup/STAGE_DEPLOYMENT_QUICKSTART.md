# Stage Deployment Quickstart

**Get v0.0.1 running on stage in 1-2 hours**

---

## Overview

**Goal:** Deploy working application to stage server using GitHub Actions + GHCR.

**Time:** 1-2 hours
**Tools:** GitHub Actions (CI/CD) + GHCR (registry)
**Cost:** ~$4/month (GitHub Pro for private repos)

---

## Step 1: GitHub Environment Setup (5 minutes)

### Create Stage Environment
1. Go to **GitHub → Your Repo → Settings → Environments**
2. Click **"New environment"**
3. Name: `stage`
4. **No required reviewers** (for now)
5. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `DEPLOY_HOST` | Your stage server IP (e.g., `192.168.1.100`) |
| `DEPLOY_USER` | SSH username (e.g., `ubuntu`) |
| `DEPLOY_SSH_KEY` | Private SSH key (see below) |
| `DEPLOY_PATH` | `/opt/forecaster` |
| `DATABASE_URL` | Your stage database URL |
| `SECRET_KEY` | Random string (e.g., `openssl rand -hex 32`) |

### Generate SSH Key
```bash
# Generate deploy key
ssh-keygen -t rsa -b 4096 -C "deploy@forecaster" -f ~/.ssh/stage_deploy -N ""

# Copy PRIVATE key to GitHub secret DEPLOY_SSH_KEY
cat ~/.ssh/stage_deploy

# Copy PUBLIC key to your stage server
ssh-copy-id -i ~/.ssh/stage_deploy ubuntu@YOUR_STAGE_IP
```

---

## Step 2: Stage Server Setup (10 minutes)

### Install Docker
```bash
# SSH to your stage server
ssh ubuntu@YOUR_STAGE_IP

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker ubuntu

# Logout and login again
exit
ssh ubuntu@YOUR_STAGE_IP
```

### Create Deploy Directory
```bash
# Create directory
sudo mkdir -p /opt/forecaster
sudo chown ubuntu:ubuntu /opt/forecaster

# Copy docker-compose.yml from your repo
# (Edit paths and environment variables as needed)
```

### Test Connection
```bash
# Test Docker works
docker --version

# Test database connection (if needed)
# Test any other connectivity
```

---

## Step 3: Deploy Workflow (5 minutes)

**Update `.github/workflows/deploy-stage.yml`:**

```yaml
name: Deploy Stage

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: "Release tag to deploy (e.g., v0.0.1)"
        required: true

permissions:
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: stage
    steps:
      - name: Deploy to stage
        run: |
          echo "🚀 Deploying ${{ inputs.image_tag }} to stage"

          # SSH and deploy
          ssh -o StrictHostKeyChecking=no -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
            cd $DEPLOY_PATH
            echo "Pulling: ghcr.io/$GITHUB_REPOSITORY/backend:${{ inputs.image_tag }}"
            docker pull ghcr.io/$GITHUB_REPOSITORY/backend:${{ inputs.image_tag }}
            docker tag ghcr.io/$GITHUB_REPOSITORY/backend:${{ inputs.image_tag }} forecaster-backend:latest
            docker compose down || true
            docker compose up -d
            sleep 15
            curl -f http://localhost:8000/ready || (echo "❌ Health check failed" && exit 1)
            echo "✅ Stage deployment successful!"
          EOF
```

---

## Step 4: Deploy! (2 minutes)

### Create Release
```bash
# Create and push tag
git tag v0.0.1
git push origin v0.0.1
```

### Deploy to Stage
1. **Go to GitHub Actions** → "Deploy Stage" workflow
2. **Click "Run workflow"**
3. **Enter:** `image_tag: v0.0.1`
4. **Watch logs** for success

### Verify Deployment
```bash
# Test health
curl http://YOUR_STAGE_IP:8000/ready

# Test API
curl http://YOUR_STAGE_IP:8000/api/v1/products
```

---

## Troubleshooting

### SSH Issues
```bash
# Test SSH connection
ssh -i ~/.ssh/stage_deploy ubuntu@YOUR_STAGE_IP

# Check SSH key permissions
chmod 600 ~/.ssh/stage_deploy
```

### Docker Issues
```bash
# Check Docker on server
ssh ubuntu@YOUR_STAGE_IP "docker ps"

# Check logs
ssh ubuntu@YOUR_STAGE_IP "cd /opt/forecaster && docker compose logs"
```

### Health Check Issues
```bash
# Manual health check
ssh ubuntu@YOUR_STAGE_IP "curl http://localhost:8000/ready"

# Check if app is running
ssh ubuntu@YOUR_STAGE_IP "docker ps"
```

---

## Success Criteria

✅ **Deployment logs show success**  
✅ **curl http://stage-server:8000/ready returns 200**  
✅ **API endpoints work** (products, forecasts, etc.)  
✅ **No errors in Docker logs**

---

## Next Steps

1. **Test thoroughly** on stage
2. **Fix any issues** found
3. **Set up production** environment when ready
4. **Add monitoring** and alerts

**Total time: 30-60 minutes for first deployment!** 🚀