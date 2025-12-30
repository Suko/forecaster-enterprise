# Container Registry Guide

**Understanding Docker Registries for Deployment**

---

## What is a Container Registry?

A **container registry** is a storage and distribution system for Docker images. Think of it like:

- **Git for source code** → **Registry for container images**
- **NPM for JavaScript packages** → **Registry for Docker containers**

**Key Purpose:** Store built container images so they can be pulled and run on any server.

---

## How Container Registries Work

### 1. **Build Phase** (CI/CD Pipeline)
```bash
# Build your application into a container
docker build -t myapp:v1.0.0 ./backend

# Tag with registry information
docker tag myapp:v1.0.0 registry.example.com/myproject/backend:v1.0.0

# Push to registry
docker push registry.example.com/myproject/backend:v1.0.0
```

### 2. **Storage Phase** (Registry)
- Registry stores the layered filesystem
- Images are versioned by tags (`v1.0.0`, `latest`, `commit-sha`)
- Access controlled by authentication

### 3. **Deployment Phase** (Your Server)
```bash
# Pull the exact same image on any server
docker pull registry.example.com/myproject/backend:v1.0.0

# Run it
docker run registry.example.com/myproject/backend:v1.0.0
```

---

## Registry Options for Your Setup

### **Option 1: GitHub Container Registry (GHCR)**
**Best for: GitHub Actions users**

```bash
# Login (automatic in GitHub Actions)
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_ACTOR --password-stdin

# Build and push
docker build -t ghcr.io/YOUR_USERNAME/forecaster-enterprise/backend:v0.0.1 ./backend
docker push ghcr.io/YOUR_USERNAME/forecaster-enterprise/backend:v0.0.1

# On deployment server
docker pull ghcr.io/YOUR_USERNAME/forecaster-enterprise/backend:v0.0.1
```

**Pros:** Free, integrated with GitHub, automatic auth
**Cons:** Requires internet access to GitHub

---

### **Option 2: GitLab Container Registry**
**Best for: Self-hosted GitLab users**

```bash
# Login with deploy token
docker login gitlab.yourdomain.com:5050 -u deploy-token -p $DEPLOY_TOKEN

# Build and push
docker build -t gitlab.yourdomain.com:5050/YOUR_PROJECT/backend:v0.0.1 ./backend
docker push gitlab.yourdomain.com:5050/YOUR_PROJECT/backend:v0.0.1

# On deployment server
docker pull gitlab.yourdomain.com:5050/YOUR_PROJECT/backend:v0.0.1
```

**Pros:** Runs on your server, no external dependencies, free
**Cons:** Requires GitLab setup and maintenance

---

### **Option 3: Docker Hub**
**Best for: Simple setups**

```bash
# Login
docker login -u YOUR_USERNAME -p YOUR_PASSWORD

# Build and push
docker build -t yourusername/forecaster-backend:v0.0.1 ./backend
docker push yourusername/forecaster-backend:v0.0.1

# On deployment server
docker pull yourusername/forecaster-backend:v0.0.1
```

**Pros:** Simple, established, free public repos
**Cons:** Rate limits, potential vendor lock-in

---

### **Option 4: Self-Hosted Registry (Advanced)**
**Best for: Air-gapped or custom requirements**

```bash
# Run registry on your server
docker run -d -p 5000:5000 --name registry registry:2

# Build and push
docker build -t localhost:5000/backend:v0.0.1 ./backend
docker push localhost:5000/backend:v0.0.1

# On deployment server
docker pull your-server.com:5000/backend:v0.0.1
```

**Pros:** Complete control, no external dependencies
**Cons:** More complex setup, backup/monitoring required

---

## Image Naming Convention

**Standard format:** `REGISTRY/ORGANIZATION/REPOSITORY:TAG`

```
ghcr.io/YOUR_USERNAME/forecaster-enterprise/backend:v0.0.1
├───┘    └────────────┘ └────────────────────┘ └─────┘
Registry   Organization         Repository         Tag
```

### Common Tags:
- **Version tags:** `v1.0.0`, `v0.0.1`
- **Latest:** `latest` (auto-updates)
- **Commit-based:** `abc1234` (commit SHA)
- **Branch-based:** `main`, `develop`

---

## Security & Access Control

### Authentication Methods:

1. **Username/Password** (Docker Hub, some private registries)
2. **Deploy Tokens** (GitLab, some custom registries)
3. **Registry Tokens** (AWS ECR, Google GCR)
4. **Kubernetes Secrets** (for K8s deployments)

### Best Practices:
- Use deploy tokens, not personal accounts
- Rotate tokens regularly
- Store credentials securely (CI/CD secrets)
- Use private repositories for production images

---

## Storage & Performance

### Image Layers:
- Docker images are built in layers
- Only changed layers are transferred
- Efficient for iterative deployments

### Storage Requirements:
- **Base images:** 100MB-1GB per image
- **Your app:** +50-200MB per version
- **Plan:** 10-50GB for registry storage

### Cleanup Strategy:
```bash
# Remove old images
docker image prune -a --filter "until=720h"  # Older than 30 days

# Registry cleanup (if supported)
# Most registries have automatic cleanup policies
```

---

## Cost Comparison

| Registry | Free Tier | Paid Plans | Best For |
|----------|-----------|------------|----------|
| **GHCR** | Unlimited | Included in GitHub | GitHub users |
| **GitLab** | Unlimited | Free | Self-hosted |
| **Docker Hub** | 1 private repo | $5/month | Simple projects |
| **AWS ECR** | 500MB | $0.10/GB | AWS users |
| **Google GCR** | 500MB | $0.026/GB | GCP users |

---

## Web UI Management

### **GitHub Container Registry (GHCR)**
**Location:** GitHub.com → Your Repository → Packages tab

**Features:**
- ✅ **Web UI:** Full browser interface
- ✅ **Image listing:** See all versions/tags
- ✅ **Delete images:** Click to remove old versions
- ✅ **Download manifests:** View image details
- ✅ **Public/Private:** Set visibility per image
- ✅ **Automated cleanup:** Set retention policies

**Access:** `https://github.com/YOUR_USERNAME/YOUR_REPO/packages`

### **GitLab Container Registry**
**Location:** GitLab → Your Project → Packages & Registries → Container Registry

**Features:**
- ✅ **Web UI:** Integrated GitLab interface
- ✅ **Image browser:** Navigate repositories/tags
- ✅ **Delete images:** Remove specific tags
- ✅ **Access tokens:** Manage deploy tokens
- ✅ **Storage usage:** Monitor disk usage
- ✅ **Cleanup policies:** Automatic old image removal

**Access:** `https://gitlab.yourdomain.com/YOUR_PROJECT/-/container_registry`

### **Docker Hub**
**Location:** hub.docker.com → Your Account → Repositories

**Features:**
- ✅ **Web UI:** Full-featured interface
- ✅ **Repository management:** Create/delete repos
- ✅ **Tag management:** Delete specific tags
- ✅ **Webhooks:** Trigger on new pushes
- ✅ **Organizations:** Team access control
- ✅ **Billing:** Usage monitoring

**Access:** `https://hub.docker.com/repositories/YOUR_USERNAME`

### **Self-Hosted Registry UIs**

#### **Option 1: Docker Registry UI**
```bash
docker run -d \
  --name registry-ui \
  -p 8080:80 \
  -e REGISTRY_URL=http://registry:5000 \
  -e DELETE_ENABLED=true \
  joxit/docker-registry-ui:latest
```

#### **Option 2: Harbor (Enterprise)**
- Full-featured registry with web UI
- User management, policies, scanning
- More complex setup but enterprise-grade

---

## Troubleshooting

### Common Issues:

1. **Authentication Failed**
   ```bash
   # Check credentials
   docker login registry.example.com
   # Verify token hasn't expired
   ```

2. **Push/Pull Timeout**
   ```bash
   # Check network connectivity
   curl -I registry.example.com/v2/
   # Verify firewall rules
   ```

3. **Disk Space Issues**
   ```bash
   # Check available space
   df -h
   # Clean up old images
   docker system prune -a
   ```

4. **Image Not Found**
   ```bash
   # Verify exact tag name
   docker images | grep your-image
   # Check registry permissions
   ```

---

## Migration Between Registries

**From GHCR to GitLab:**
```bash
# Pull from old registry
docker pull ghcr.io/old-org/project:v1.0.0

# Tag for new registry
docker tag ghcr.io/old-org/project:v1.0.0 gitlab.yourdomain.com/new-project:v1.0.0

# Push to new registry
docker push gitlab.yourdomain.com/new-project:v1.0.0
```

---

**Remember:** Container registries are the "delivery mechanism" for your deployments. Choose based on your infrastructure and cost preferences!