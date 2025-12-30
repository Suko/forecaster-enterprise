# Blue-Green Deployment Guide

**Zero-downtime deployment strategy for Forecaster Enterprise**

---

## ⚠️ Recommendation: Do You Need This?

**For low traffic (current state):**
- ✅ **Stick with rolling deployment** - Simple, works fine
- ✅ **Brief downtime acceptable** - 10-30 seconds is fine
- ✅ **Lower complexity** - Easier to maintain
- ✅ **Resource efficient** - No 2x container overhead

**Consider blue-green when:**
- Traffic grows significantly (1000+ concurrent users)
- Zero downtime becomes critical
- You need instant rollback capability
- You want to test new version before switching

**Current recommendation:** Keep rolling deployment for v0.0.1, consider blue-green for v1.0+ when traffic increases.

---

## Overview

**Blue-Green Deployment:**
- **Blue:** Current production environment (receiving traffic)
- **Green:** New version environment (being tested)
- **Switch:** Route traffic from blue → green after validation
- **Rollback:** Route traffic back to blue if issues detected

**Benefits:**
- ✅ Zero downtime deployments
- ✅ Instant rollback capability
- ✅ Safe testing of new version
- ✅ No service interruption

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Blue-Green Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Internet                                                       │
│     │                                                            │
│     ▼                                                            │
│  ┌──────────────┐                                               │
│  │   Nginx      │  ← Load balancer (routes traffic)            │
│  │  (Port 80)   │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ├─────────────────┬─────────────────┐                 │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐              │
│  │  Blue    │      │  Green   │      │   DB     │              │
│  │ :8001    │      │ :8002    │      │ :5432    │              │
│  │ (active) │      │ (standby)│      │ (shared) │              │
│  └──────────┘      └──────────┘      └──────────┘              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Points:**
- Both environments share the same database
- Nginx routes traffic to active environment
- Only one environment receives traffic at a time
- Both environments can run simultaneously

---

## Implementation

### Step 1: Create Blue-Green Docker Compose Files

#### `docker-compose.blue.yml`
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: forecast-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-forecaster_enterprise}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend-blue:
    image: ghcr.io/${GITHUB_REPOSITORY}/backend:${BACKEND_TAG:-latest}
    container_name: forecast-backend-blue
    restart: unless-stopped
    ports:
      - "8001:8000"  # Blue on port 8001
    volumes:
      - ./data:/data:ro
      - ml_models_cache:/home/appuser/.cache/huggingface
      - ml_pip_cache:/home/appuser/.cache/pip
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}?sslmode=disable
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - DEBUG=${DEBUG:-false}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s

volumes:
  postgres_data:
  ml_models_cache:
  ml_pip_cache:
```

#### `docker-compose.green.yml`
```yaml
services:
  # DB is shared, but we reference it
  backend-green:
    image: ghcr.io/${GITHUB_REPOSITORY}/backend:${BACKEND_TAG:-latest}
    container_name: forecast-backend-green
    restart: unless-stopped
    network_mode: "service:db"  # Share network with blue's db
    ports:
      - "8002:8000"  # Green on port 8002
    volumes:
      - ./data:/data:ro
      - ml_models_cache:/home/appuser/.cache/huggingface
      - ml_pip_cache:/home/appuser/.cache/pip
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}?sslmode=disable
      - ENVIRONMENT=${ENVIRONMENT:-production}
      - DEBUG=${DEBUG:-false}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s
```

**Note:** Green shares the same database via Docker network. For simplicity, you can run both on the same compose file with different ports.

### Step 2: Simplified Approach (Single Compose File)

**Better approach:** Use one compose file with both environments:

#### `docker-compose.bg.yml`
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: forecast-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-forecaster_enterprise}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend-blue:
    image: ${BACKEND_IMAGE:-ghcr.io/USER/forecaster-enterprise/backend:latest}
    container_name: forecast-backend-blue
    restart: unless-stopped
    ports:
      - "8001:8000"
    volumes:
      - ./data:/data:ro
      - ml_models_cache:/home/appuser/.cache/huggingface
      - ml_pip_cache:/home/appuser/.cache/pip
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}?sslmode=disable
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s

  backend-green:
    image: ${BACKEND_IMAGE:-ghcr.io/USER/forecaster-enterprise/backend:latest}
    container_name: forecast-backend-green
    restart: unless-stopped
    ports:
      - "8002:8000"
    volumes:
      - ./data:/data:ro
      - ml_models_cache:/home/appuser/.cache/huggingface
      - ml_pip_cache:/home/appuser/.cache/pip
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}?sslmode=disable
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ready"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 300s

  nginx:
    image: nginx:alpine
    container_name: forecast-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx-active.conf:/etc/nginx/conf.d/active.conf:ro
    depends_on:
      - backend-blue
      - backend-green

volumes:
  postgres_data:
  ml_models_cache:
  ml_pip_cache:
```

### Step 3: Nginx Configuration

#### `nginx.conf`
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        # This will be overridden by active.conf
        server backend-blue:8000;
    }

    server {
        listen 80;
        server_name _;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Health check endpoint
            proxy_connect_timeout 5s;
            proxy_send_timeout 5s;
            proxy_read_timeout 5s;
        }

        # Health check endpoint for nginx
        location /nginx-health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

#### `nginx-active.conf` (points to active environment)
```nginx
# Active environment: blue or green
# This file is symlinked or copied during deployment

upstream backend {
    server backend-blue:8000;  # Change to backend-green:8000 to switch
}
```

### Step 4: Deployment Script

#### `deploy-blue-green.sh`
```bash
#!/bin/bash
set -e

IMAGE_TAG=${1:-latest}
ACTIVE_ENV=${2:-blue}  # Current active environment

echo "🚀 Blue-Green Deployment"
echo "   Image: ${IMAGE_TAG}"
echo "   Active: ${ACTIVE_ENV}"

# Determine target environment
if [ "$ACTIVE_ENV" = "blue" ]; then
    TARGET_ENV="green"
    TARGET_PORT="8002"
else
    TARGET_ENV="blue"
    TARGET_PORT="8001"
fi

echo "📦 Deploying to ${TARGET_ENV} environment..."

# Pull new image
docker pull ghcr.io/${GITHUB_REPOSITORY}/backend:${IMAGE_TAG}

# Update target environment
export BACKEND_IMAGE=ghcr.io/${GITHUB_REPOSITORY}/backend:${IMAGE_TAG}
docker compose -f docker-compose.bg.yml up -d backend-${TARGET_ENV}

# Wait for health check
echo "⏳ Waiting for ${TARGET_ENV} to be ready..."
MAX_WAIT=360
ELAPSED=0
while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:${TARGET_PORT}/ready > /dev/null 2>&1; then
        echo "✅ ${TARGET_ENV} is ready!"
        break
    fi
    echo "   Still waiting... ($ELAPSED/$MAX_WAIT seconds)"
    sleep 10
    ELAPSED=$((ELAPSED + 10))
done

# Run smoke tests
echo "🧪 Running smoke tests on ${TARGET_ENV}..."
if curl -sf http://localhost:${TARGET_PORT}/ready > /dev/null 2>&1 && \
   curl -sf http://localhost:${TARGET_PORT}/api/v1/health > /dev/null 2>&1; then
    echo "✅ Smoke tests passed!"
else
    echo "❌ Smoke tests failed - aborting switch"
    exit 1
fi

# Switch traffic
echo "🔄 Switching traffic to ${TARGET_ENV}..."
if [ "$TARGET_ENV" = "green" ]; then
    cat > nginx-active.conf << 'EOF'
upstream backend {
    server backend-green:8000;
}
EOF
else
    cat > nginx-active.conf << 'EOF'
upstream backend {
    server backend-blue:8000;
}
EOF
fi

# Reload nginx
docker exec forecast-nginx nginx -s reload

# Verify switch
echo "✅ Traffic switched to ${TARGET_ENV}"
echo "📊 Active environment: ${TARGET_ENV}"
echo "📊 Standby environment: ${ACTIVE_ENV} (kept running for rollback)"

# Save current active environment
echo "${TARGET_ENV}" > .active-env
```

### Step 5: Rollback Script

#### `rollback-blue-green.sh`
```bash
#!/bin/bash
set -e

ACTIVE_ENV=$(cat .active-env 2>/dev/null || echo "blue")

if [ "$ACTIVE_ENV" = "blue" ]; then
    ROLLBACK_ENV="green"
else
    ROLLBACK_ENV="blue"
fi

echo "🔄 Rolling back to ${ROLLBACK_ENV}..."

# Switch nginx back
if [ "$ROLLBACK_ENV" = "green" ]; then
    cat > nginx-active.conf << 'EOF'
upstream backend {
    server backend-green:8000;
}
EOF
else
    cat > nginx-active.conf << 'EOF'
upstream backend {
    server backend-blue:8000;
}
EOF
fi

# Reload nginx
docker exec forecast-nginx nginx -s reload

echo "✅ Rolled back to ${ROLLBACK_ENV}"
echo "${ROLLBACK_ENV}" > .active-env
```

### Step 6: Update GitHub Actions Workflow

#### `.github/workflows/deploy-stage-blue-green.yml`
```yaml
name: Deploy Stage (Blue-Green)

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
    timeout-minutes: 20
    steps:
      - name: Deploy blue-green
        run: |
          echo "🚀 Deploying ${{ inputs.image_tag }} using blue-green"

          ssh -o StrictHostKeyChecking=no -i ~/.ssh/deploy_key $DEPLOY_USER@$DEPLOY_HOST << 'EOF'
            set -e
            cd $DEPLOY_PATH
            
            # Get current active environment
            ACTIVE_ENV=$(cat .active-env 2>/dev/null || echo "blue")
            
            # Run deployment script
            bash deploy-blue-green.sh ghcr.io/$GITHUB_REPOSITORY/backend:${{ inputs.image_tag }} $ACTIVE_ENV
          EOF
```

---

## Deployment Flow

### Initial Setup
```bash
# 1. Start both environments (blue active)
docker compose -f docker-compose.bg.yml up -d

# 2. Set blue as active
echo "blue" > .active-env

# 3. Configure nginx to point to blue
cat > nginx-active.conf << 'EOF'
upstream backend {
    server backend-blue:8000;
}
EOF

# 4. Start nginx
docker compose -f docker-compose.bg.yml up -d nginx
```

### Deploy New Version
```bash
# Deploy v0.0.2 to green (blue is active)
./deploy-blue-green.sh v0.0.2 blue

# Flow:
# 1. Pull v0.0.2 image
# 2. Deploy to green (port 8002)
# 3. Wait for health check
# 4. Run smoke tests
# 5. Switch nginx to green
# 6. Blue kept running for rollback
```

### Rollback
```bash
# If issues detected, rollback to blue
./rollback-blue-green.sh

# Flow:
# 1. Switch nginx back to blue
# 2. Green kept running (can investigate)
```

---

## Benefits

### ✅ Zero Downtime
- Traffic switches instantly via nginx reload
- No service interruption
- Users don't notice deployment

### ✅ Safe Testing
- New version tested before traffic switch
- Smoke tests validate functionality
- Can test green while blue serves traffic

### ✅ Instant Rollback
- Switch back in seconds
- No need to redeploy old version
- Old version already running

### ✅ Risk Reduction
- Both versions run simultaneously
- Easy comparison
- Gradual migration possible

---

## Considerations

### Database Migrations
- **Shared database** - Both environments use same DB
- **Migration safety** - Must be backward compatible
- **Best practice:** Run migrations before switching traffic

### Resource Usage
- **2x backend containers** - Double memory/CPU during deployment
- **Temporary** - Old environment can be stopped after validation
- **Cost:** Minimal (only during deployment window)

### ML Dependencies
- **Shared volumes** - Both environments share ML cache
- **First deployment:** Green downloads ML deps (2-3 min)
- **Subsequent:** Uses cached packages

---

## Monitoring

### Check Active Environment
```bash
# Check which environment is active
cat .active-env

# Check nginx config
docker exec forecast-nginx cat /etc/nginx/conf.d/active.conf

# Check both environments
curl http://localhost:8001/ready  # Blue
curl http://localhost:8002/ready  # Green
```

### Health Monitoring
```bash
# Monitor both environments
watch -n 5 'curl -s http://localhost:8001/health && curl -s http://localhost:8002/health'
```

---

## Cleanup

### Stop Standby Environment
```bash
# After validating new version, stop old environment
ACTIVE_ENV=$(cat .active-env)
if [ "$ACTIVE_ENV" = "blue" ]; then
    docker compose -f docker-compose.bg.yml stop backend-green
else
    docker compose -f docker-compose.bg.yml stop backend-blue
fi
```

---

## Comparison: Rolling vs Blue-Green

| Aspect | Rolling (Current) | Blue-Green |
|--------|-------------------|------------|
| **Downtime** | ~10-30 seconds | Zero |
| **Rollback** | Manual redeploy | Instant switch |
| **Testing** | No pre-testing | Test before switch |
| **Complexity** | Simple | Medium |
| **Resources** | Normal | 2x during deploy |
| **Risk** | Higher | Lower |
| **Best For** | **Low traffic (v0.0.1)** ✅ | High traffic (v1.0+) |

---

## When to Use

### ✅ Use Blue-Green When:
- **High traffic** (1000+ concurrent users, or revenue-critical)
- Zero downtime is critical (SLA requirements)
- Need instant rollback capability
- Want to test new version before switching traffic
- Have resources for 2x containers during deployment

### ⚠️ Use Rolling (Current) When:
- **Low to medium traffic** (< 1000 concurrent users)
- Brief downtime acceptable (10-30 seconds)
- Simple setup preferred
- Resource constraints (single server, limited RAM)
- **Current recommendation for v0.0.1**

### Migration Path:
1. **v0.0.1:** Rolling deployment (current) ✅
2. **v0.5+:** Monitor traffic, add smoke tests
3. **v1.0+:** Consider blue-green if traffic grows or zero-downtime becomes critical

---

## Related Documentation

- [Deployment Flow](./DEPLOYMENT_FLOW.md)
- [Best Practices Assessment](./DEPLOYMENT_BEST_PRACTICES_ASSESSMENT.md)
- [First Release Checklist](./FIRST_RELEASE_CHECKLIST.md)

---

**Last Updated:** 2025-12-30
