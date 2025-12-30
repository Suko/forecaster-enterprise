# ML Dependencies Architecture - Best Practices

**Last Updated:** 2025-12-30  
**Purpose:** Document best practices for handling large ML dependencies (PyTorch, models) in containerized deployments.

---

## Problem Statement

ML dependencies are large:
- **PyTorch + CUDA:** ~2GB
- **Chronos-2 model:** ~500MB (downloaded from HuggingFace)
- **Total:** ~2.5GB per container

This causes:
- Slow Docker builds
- CI/CD disk space issues
- Slow deployments (every release downloads models)

---

## Solution: Runtime Installation + Shared Cache

### Current Implementation (Recommended for v0.0.1)

**Architecture:**
```
┌─────────────────┐
│  Backend Image  │  ← Small (~200MB), fast builds
│  (Code only)    │
└────────┬────────┘
         │
         │ Uses shared volumes
         ▼
┌─────────────────┐
│  ml_models_cache │  ← Persists across releases
│  (HuggingFace)  │
└─────────────────┘
┌─────────────────┐
│  ml_pip_cache   │  ← PyTorch packages cached
│  (pip cache)    │
└─────────────────┘
```

**How it works:**
1. **Backend image:** Contains only application code (no PyTorch)
2. **First run:** Downloads PyTorch CPU-only + models to shared volume
3. **Subsequent releases:** Reuses cached models from volume
4. **Result:** Fast builds, models persist across releases

**Benefits:**
- ✅ Small Docker image (~200MB vs ~2.5GB)
- ✅ Fast CI/CD builds (no PyTorch download)
- ✅ Models cached (not re-downloaded on every release)
- ✅ Simple architecture (no separate services)

**Trade-offs:**
- ⚠️ First startup takes 2-3 minutes (downloads PyTorch)
- ⚠️ Models stored on host disk (manage disk space)

---

## Alternative: Separate ML Service (Future)

For larger scale, consider separating ML into its own service:

```
┌──────────────┐      ┌──────────────┐
│   Backend    │─────▶│  ML Service  │
│  (FastAPI)   │ HTTP │  (PyTorch)   │
└──────────────┘      └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │ Model Cache  │
                       │  (Volume)    │
                       └──────────────┘
```

**When to use:**
- Multiple backend instances (scale independently)
- GPU acceleration needed (dedicated GPU container)
- Model versioning required
- A/B testing different models

**Implementation:**
- ML service exposes REST API for predictions
- Backend calls ML service via HTTP
- Models loaded once in ML service, shared across requests

---

## Volume Configuration

### docker-compose.yml

```yaml
services:
  backend:
    volumes:
      # Model cache - persists across releases
      - ml_models_cache:/root/.cache/huggingface
      - ml_pip_cache:/root/.cache/pip

volumes:
  ml_models_cache:  # HuggingFace models
  ml_pip_cache:     # PyTorch packages
```

### What Gets Cached

1. **HuggingFace Models** (`/root/.cache/huggingface`)
   - Chronos-2 model weights
   - Other pretrained models
   - Downloaded once, reused forever

2. **Python Packages** (`/root/.cache/pip`)
   - PyTorch wheels
   - Other ML dependencies
   - Speeds up reinstallations

---

## Deployment Scenarios

### Scenario 1: First Deployment
```
1. Build backend image (fast, no PyTorch)
2. Deploy container
3. Container starts → Downloads PyTorch (2-3 min)
4. Downloads Chronos-2 model (30 sec)
5. Ready to serve requests
```

### Scenario 2: Subsequent Releases
```
1. Build backend image (fast, no PyTorch)
2. Deploy new container
3. Container starts → PyTorch already in pip cache
4. Chronos-2 model already in HuggingFace cache
5. Ready in ~10 seconds (no downloads)
```

### Scenario 3: Fresh Server (No Cache)
```
1. Build backend image
2. Deploy to new server
3. First run downloads everything (one-time cost)
4. Future releases reuse cache
```

---

## Disk Space Management

### Cache Sizes
- **PyTorch CPU-only:** ~500MB
- **Chronos-2 model:** ~500MB
- **Total cache:** ~1GB per deployment

### Cleanup (if needed)
```bash
# Remove old models
docker volume rm ml_models_cache

# Or prune unused volumes
docker volume prune
```

### Monitoring
```bash
# Check cache size
docker volume inspect ml_models_cache

# Check disk usage
df -h
```

---

## Environment Variables

Control ML dependency installation:

```bash
# Skip ML dependencies (statistical models only)
SKIP_ML_DEPS=true

# Use GPU PyTorch (if GPU available)
PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu121
```

---

## Comparison: Approaches

| Approach | Image Size | Build Time | First Start | Subsequent Starts | Complexity |
|----------|-----------|------------|-------------|-------------------|------------|
| **All in image** | 2.5GB | 10-15 min | 10 sec | 10 sec | Low |
| **Runtime + Cache** ✅ | 200MB | 2-3 min | 2-3 min | 10 sec | Low |
| **Separate ML service** | 200MB | 2-3 min | 10 sec | 10 sec | Medium |

**Recommendation:** Use "Runtime + Cache" for v0.0.1, consider separate service for scale.

---

## Migration Path

### Current (v0.0.1)
- ✅ Runtime installation with shared cache
- ✅ Models persist across releases
- ✅ Fast CI/CD builds

### Future (v1.0+)
- Consider separate ML service if:
  - Multiple backend instances
  - GPU acceleration needed
  - Model versioning required

---

## Troubleshooting

### Models Not Cached
**Symptom:** Models re-download on every release

**Fix:** Check volume mount:
```bash
docker exec forecast-backend ls -la /root/.cache/huggingface
```

### Disk Space Issues
**Symptom:** Server running out of space

**Fix:** Clean old models or increase disk:
```bash
docker volume prune
```

### PyTorch Installation Fails
**Symptom:** `uv pip install` fails

**Fix:** Check network, try CPU-only index:
```bash
uv pip install --index-url https://download.pytorch.org/whl/cpu torch
```

---

**Document Owner:** Development Team  
**Last Updated:** 2025-12-30
