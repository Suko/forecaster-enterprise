# Multi-Location On-Premise Deployment Guide

**Remote Docker Updates Across Multiple On-Premise Locations**

---

## Overview

Deploying to **multiple on-premise Docker locations** requires a different approach than single-server deployments. Key challenges:

- Network segmentation between locations
- Secure remote access
- Coordinated updates across sites
- Rollback capabilities
- Monitoring distributed deployments

---

## Architecture Options

### **Option 1: Pull-Based Deployment (Recommended)**
**Locations pull updates from central registry**

```
Central Registry (GHCR/GitLab)
          │
          ├── Location A (Pulls automatically)
          ├── Location B (Pulls on schedule)
          └── Location C (Pulls on demand)
```

**Pros:** Simple, resilient, locations can update independently
**Cons:** Less control over exact timing

---

### **Option 2: Push-Based Deployment**
**CI/CD pushes directly to each location**

```
CI/CD Pipeline
     │
     ├── SSH → Location A
     ├── SSH → Location B
     └── SSH → Location C
```

**Pros:** Full control, immediate updates
**Cons:** Requires network access, more complex

---

### **Option 3: Hybrid Approach**
**Registry + Orchestration**

```
Registry → Deployment Server → Locations
```

---

## Implementation Strategies

### **Strategy 1: Registry + Watchtower (Pull-Based)**

#### **Setup on Each Location:**
```bash
# Run Watchtower to auto-update containers
docker run -d \
  --name watchtower \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e WATCHTOWER_POLL_INTERVAL=300 \
  -e WATCHTOWER_NOTIFICATIONS=email \
  -e WATCHTOWER_NOTIFICATION_EMAIL_FROM=deploy@yourcompany.com \
  -e WATCHTOWER_NOTIFICATION_EMAIL_TO=ops@yourcompany.com \
  -e WATCHTOWER_NOTIFICATION_EMAIL_SERVER=smtp.yourcompany.com \
  containrrr/watchtower
```

#### **How It Works:**
1. **CI/CD** pushes new image to registry with tag `latest`
2. **Watchtower** checks registry every 5 minutes
3. **Automatically updates** running containers
4. **Sends notifications** on successful/failed updates

#### **Pros:**
- ✅ Zero-touch updates
- ✅ Works with network restrictions
- ✅ Automatic rollback on failure
- ✅ Email notifications

#### **Cons:**
- ❌ Update timing not guaranteed
- ❌ Requires Watchtower on each location

---

### **Strategy 2: Ansible + SSH (Push-Based)**

#### **Ansible Inventory:**
```yaml
# inventory.yml
all:
  children:
    locations:
      hosts:
        location_a:
          ansible_host: 10.1.1.100
          location_name: "New York Office"
        location_b:
          ansible_host: 10.2.1.100
          location_name: "London Office"
        location_c:
          ansible_host: 10.3.1.100
          location_name: "Tokyo Office"
```

#### **Ansible Playbook:**
```yaml
# deploy.yml
---
- name: Deploy to all locations
  hosts: locations
  serial: 1  # Update one location at a time

  vars:
    image_tag: "{{ lookup('env', 'CI_COMMIT_TAG') | default('latest') }}"

  tasks:
    - name: Login to registry
      docker_login:
        registry: ghcr.io
        username: "{{ github_actor }}"
        password: "{{ github_token }}"

    - name: Pull new image
      docker_image:
        name: "ghcr.io/your-org/forecaster-backend:{{ image_tag }}"
        source: pull

    - name: Stop old container
      docker_container:
        name: forecaster-backend
        state: stopped
        ignore_missing: yes

    - name: Start new container
      docker_container:
        name: forecaster-backend
        image: "ghcr.io/your-org/forecaster-backend:{{ image_tag }}"
        state: started
        ports:
          - "8000:8000"
        env:
          DATABASE_URL: "{{ database_url }}"
        healthcheck:
          test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
          interval: 30s
          timeout: 10s
          retries: 3

    - name: Wait for health check
      uri:
        url: http://localhost:8000/health
        status_code: 200
      register: health_check
      until: health_check.status == 200
      retries: 10
      delay: 5

    - name: Notify success
      slack:
        token: "{{ slack_token }}"
        msg: "✅ Deployment successful to {{ location_name }}"
      when: health_check.status == 200
```

#### **CI/CD Pipeline Integration:**
```yaml
# .gitlab-ci.yml or GitHub Actions
deploy_multi_location:
  stage: deploy
  script:
    - ansible-playbook -i inventory.yml deploy.yml
  environment:
    name: production
  when: manual
```

#### **Pros:**
- ✅ Precise control over deployment timing
- ✅ Health checks before marking success
- ✅ Notifications (Slack, email)
- ✅ Serial deployment (one location at a time)

#### **Cons:**
- ❌ Requires SSH access to all locations
- ❌ More complex setup

---

### **Strategy 3: Kubernetes + ArgoCD (Advanced)**

#### **For locations with Kubernetes:**
```yaml
# Application manifest
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: forecaster-backend
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/forecaster-deploy
    targetRevision: HEAD
    path: manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: forecaster
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

#### **Pros:**
- ✅ GitOps approach
- ✅ Automatic drift correction
- ✅ Rollback to any git commit
- ✅ Multi-cluster support

#### **Cons:**
- ❌ Requires Kubernetes at each location
- ❌ Complex setup

---

## Security Considerations

### **Network Security:**
- **VPN:** Required for remote access
- **Firewall rules:** Restrict SSH/HTTPS to CI/CD servers
- **Certificates:** Use TLS for all communications

### **Authentication:**
- **SSH keys:** Deploy keys for each location
- **Registry tokens:** Read-only tokens for pulling images
- **API keys:** Encrypted in CI/CD variables

### **Access Control:**
```yaml
# GitHub Environments with required reviewers
production:
  required_reviewers:
    - admin-team
    - security-team
```

---

## Rollback Strategies

### **Automated Rollback:**
```yaml
# In deployment script
- name: Check deployment health
  uri:
    url: http://localhost:8000/health
    status_code: 200
  register: health_result
  failed_when: health_result.status != 200

- name: Rollback on failure
  docker_container:
    name: forecaster-backend
    image: "ghcr.io/your-org/forecaster-backend:previous-tag"
    state: started
  when: health_result.status != 200
```

### **Manual Rollback:**
```bash
# Rollback specific location
ansible-playbook -i inventory.yml rollback.yml \
  --extra-vars "target_location=location_a"
```

---

## Monitoring & Observability

### **Central Dashboard:**
- **Prometheus + Grafana:** Aggregate metrics from all locations
- **AlertManager:** Deployment failure alerts
- **Status page:** Public visibility of location health

### **Per-Location Monitoring:**
```yaml
# Health check endpoint
GET /health/locations

# Returns:
{
  "locations": {
    "location_a": {
      "status": "healthy",
      "version": "v0.0.1",
      "last_updated": "2025-01-15T10:30:00Z"
    },
    "location_b": {
      "status": "updating",
      "version": "v0.0.1",
      "last_updated": "2025-01-15T10:25:00Z"
    }
  }
}
```

---

## Deployment Phases

### **Phase 1: Pilot Deployment**
1. Deploy to one location first
2. Monitor for 24 hours
3. Verify all functionality
4. Get user feedback

### **Phase 2: Staged Rollout**
1. Deploy to 25% of locations
2. Monitor and validate
3. Deploy to 50%, then 100%

### **Phase 3: Automated Updates**
1. Enable automatic updates for stable releases
2. Manual approval for major version changes

---

## Cost & Resource Considerations

### **Infrastructure Requirements:**
- **CI/CD server:** 2-4 CPU, 4GB RAM
- **Registry storage:** 50-200GB depending on image count
- **Monitoring:** Additional 1-2 CPU, 2GB RAM

### **Network Requirements:**
- **Bandwidth:** 100-500MB per deployment per location
- **Latency:** <100ms for real-time monitoring
- **VPN:** Site-to-site or client VPN for access

---

## Implementation Checklist

- [ ] Choose deployment strategy (Pull/Push/Hybrid)
- [ ] Set up central container registry
- [ ] Configure network access between CI/CD and locations
- [ ] Implement health checks and monitoring
- [ ] Set up rollback procedures
- [ ] Test deployment with non-production data
- [ ] Plan phased rollout approach
- [ ] Document emergency procedures

---

## Recommended Approach

**Start with:** Watchtower (pull-based) for simplicity
**Scale to:** Ansible (push-based) for control
**Enterprise:** Kubernetes + ArgoCD for full automation

This gives you **reliable, secure, remote updates** across all your on-premise Docker locations! 🏢🌍