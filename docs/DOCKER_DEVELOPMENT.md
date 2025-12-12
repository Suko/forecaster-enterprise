# Docker Development Guide

## ✅ Yes! You Can Do Full Development with Docker

You have **3 options** for development with Docker:

1. **Full Docker** - Everything in containers (current setup)
2. **Hybrid** - Backend local, Database Docker (recommended for active development)
3. **Docker with Hot Reload** - Code mounted as volumes (best of both worlds)

---

## 🎯 Option 1: Full Docker Development (Current Setup)

### **What You Get:**
- ✅ Complete isolation
- ✅ Production-like environment
- ✅ Easy cleanup
- ✅ Consistent across team

### **Workflow:**
```bash
# 1. Stop local PostgreSQL
brew services stop postgresql@16

# 2. Start Docker
docker-compose up -d

# 3. Make code changes
# Edit files in your editor

# 4. Rebuild and restart after changes
docker-compose build backend
docker-compose restart backend

# 5. View logs
docker-compose logs -f backend

# 6. Access database
docker-compose exec db psql -U postgres -d forecaster_enterprise
```

### **Pros:**
- ✅ Production-like environment
- ✅ Isolated from system
- ✅ Easy to reset (delete volume)

### **Cons:**
- ⚠️ Need to rebuild after code changes
- ⚠️ Slower iteration cycle

---

## 🚀 Option 2: Hybrid Development (Recommended)

**Backend runs locally, Database in Docker**

### **Setup:**

**1. Keep Docker for database only:**
```yaml
# docker-compose.dev.yml (create this)
services:
  db:
    image: postgres:16-alpine
    container_name: forecast-db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres123}
      POSTGRES_DB: ${DB_NAME:-forecaster_enterprise}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**2. Stop local PostgreSQL:**
```bash
brew services stop postgresql@16
```

**3. Start Docker database:**
```bash
docker-compose -f docker-compose.dev.yml up -d db
```

**4. Run backend locally with hot reload:**
```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**5. Update .env for local backend:**
```bash
# In .env (or backend/.env)
DB_HOST=localhost
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/forecaster_enterprise
```

### **Workflow:**
```bash
# 1. Start database
docker-compose -f docker-compose.dev.yml up -d db

# 2. Run backend locally (with hot reload!)
cd backend
uv run uvicorn main:app --reload

# 3. Make code changes
# Backend auto-reloads! No rebuild needed!

# 4. Run tests
uv run pytest tests/ -v

# 5. Access database
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d forecaster_enterprise
```

### **Pros:**
- ✅ **Hot reload** - Changes reflect immediately
- ✅ Fast iteration
- ✅ Can use debugger
- ✅ Database isolated in Docker
- ✅ Easy database reset

### **Cons:**
- ⚠️ Need to manage two processes (Docker DB + local backend)

---

## 🔥 Option 3: Docker with Volume Mounts (Hot Reload in Docker)

**Mount code as volumes for live reload**

### **Setup:**

**1. Create `docker-compose.dev.yml`:**
```yaml
services:
  db:
    image: postgres:16-alpine
    container_name: forecast-db
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres123}
      POSTGRES_DB: ${DB_NAME:-forecaster_enterprise}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    container_name: forecaster-backend-dev
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - DB_HOST=db
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}?sslmode=disable
      - ENVIRONMENT=development
      - DEBUG=true
    volumes:
      # Mount code for hot reload
      - ./backend:/app
      # Keep .venv in container (don't mount)
      - backend_venv:/app/.venv
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
  backend_venv:
```

**2. Update `docker-entrypoint.sh` to support dev mode:**
```bash
# Add at the end of docker-entrypoint.sh
if [ "${ENVIRONMENT}" = "development" ] && [ "${DEBUG}" = "true" ]; then
  echo "Development mode: Starting with hot reload..."
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
  echo "Production mode: Starting uvicorn..."
  exec uvicorn main:app --host 0.0.0.0 --port 8000
fi
```

**3. Use it:**
```bash
# Start with dev compose
docker-compose -f docker-compose.dev.yml up

# Make code changes
# Backend auto-reloads in container!
```

### **Pros:**
- ✅ Hot reload in Docker
- ✅ Full Docker environment
- ✅ Fast iteration

### **Cons:**
- ⚠️ More complex setup
- ⚠️ Volume mounting can have permission issues

---

## 📋 Recommended Development Workflow

### **For Active Development (Writing Code):**

**Use Option 2 (Hybrid):**
```bash
# Terminal 1: Database
docker-compose -f docker-compose.dev.yml up -d db

# Terminal 2: Backend (with hot reload)
cd backend
uv run uvicorn main:app --reload

# Terminal 3: Frontend (if needed)
cd frontend
npm run dev
```

**Benefits:**
- ✅ Fastest iteration
- ✅ Hot reload
- ✅ Can use debugger
- ✅ Database isolated

### **For Testing Docker Setup:**

**Use Option 1 (Full Docker):**
```bash
docker-compose up -d
docker-compose logs -f backend
```

**Benefits:**
- ✅ Production-like
- ✅ Test complete setup
- ✅ Verify Docker config

---

## 🛠️ Common Development Tasks

### **1. Database Access:**
```bash
# Connect to Docker PostgreSQL
docker-compose exec db psql -U postgres -d forecaster_enterprise

# Or from Mac (if port exposed)
psql -h localhost -U postgres -d forecaster_enterprise
```

### **2. Run Migrations:**
```bash
# In Docker
docker-compose exec backend alembic upgrade head

# Or locally (if using hybrid)
cd backend
uv run alembic upgrade head
```

### **3. Run Tests:**
```bash
# In Docker
docker-compose exec backend uv run pytest tests/ -v

# Or locally (if using hybrid)
cd backend
uv run pytest tests/ -v
```

### **4. View Logs:**
```bash
# Backend logs
docker-compose logs -f backend

# Database logs
docker-compose logs -f db

# All logs
docker-compose logs -f
```

### **5. Reset Database:**
```bash
# Delete volume and restart
docker-compose down -v
docker-compose up -d
```

### **6. Access API Docs:**
```bash
# Open in browser
open http://localhost:8000/docs
```

---

## 🎯 Quick Start for Development

### **Step 1: Stop Local PostgreSQL**
```bash
brew services stop postgresql@16
```

### **Step 2: Choose Your Setup**

**Option A: Full Docker (Testing)**
```bash
docker-compose up -d
```

**Option B: Hybrid (Active Development)**
```bash
# Start database
docker-compose -f docker-compose.dev.yml up -d db

# Start backend locally
cd backend
uv run uvicorn main:app --reload
```

### **Step 3: Verify**
```bash
# Check health
curl http://localhost:8000/health

# Check database
docker-compose exec db psql -U postgres -d forecaster_enterprise -c "SELECT COUNT(*) FROM users;"
```

---

## 📝 Summary

**Yes, you can do full development with Docker!**

**Best Approach:**
- **Active Development:** Hybrid (Docker DB + Local Backend)
- **Testing Setup:** Full Docker
- **Production:** Full Docker

**Key Benefits:**
- ✅ Database isolated in Docker
- ✅ Easy to reset/cleanup
- ✅ Consistent environment
- ✅ Can use hot reload (with hybrid setup)

**Next Steps:**
1. Stop local PostgreSQL: `brew services stop postgresql@16`
2. Start Docker: `docker-compose up -d`
3. Or use hybrid for faster development
