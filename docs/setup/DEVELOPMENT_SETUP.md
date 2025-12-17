# Development Setup Guide

**Complete guide for local and Docker-based development**

---

## Quick Start

### Option 1: Hybrid Development (Recommended)

**Best for active development:** Database in Docker, Backend + Frontend run locally with hot reload.

**Terminal 1: Database**
```bash
docker-compose -f docker-compose.dev.yml up -d db
```

**Terminal 2: Backend**
```bash
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3: Frontend**
```bash
cd frontend
npm install  # First time only
npm run dev
```

### Option 2: Full Docker

**Best for testing production-like setup:**

```bash
docker-compose up -d
docker-compose logs -f backend  # Watch setup progress
```

---

## Access Points

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/health |

**Default Credentials:**
- Email: `admin@example.com`
- Password: `admin123`

---

## Environment Configuration

### Required `.env` File

Create `.env` in project root:

```bash
# Database
DB_USER=postgres
DB_PASSWORD=postgres123
DB_NAME=forecaster_enterprise

# Application
ENVIRONMENT=development
DEBUG=true

# JWT (generate: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key-here

# Frontend
NUXT_SESSION_PASSWORD=your-session-key-here
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Admin User (created on first startup)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=Admin User
```

---

## Docker vs Local PostgreSQL

### Key Difference

**They are COMPLETELY SEPARATE databases!**

| Aspect | Docker PostgreSQL | Local PostgreSQL |
|--------|------------------|------------------|
| Data Storage | Docker volume | `/usr/local/var/postgres` |
| Connection From Host | `localhost:5432` | `localhost:5432` |
| Connection From Docker | `db:5432` | `host.docker.internal:5432` |

### Port Conflict Resolution

Both use port 5432. If you have local PostgreSQL:

```bash
# Stop local PostgreSQL
brew services stop postgresql@16

# Or change Docker port in docker-compose.yml
ports:
  - "5433:5432"
```

---

## Docker Startup Flow

```
1. Database (PostgreSQL) starts
   ↓
2. Backend waits for DB health check
   ↓
3. Migrations run (alembic upgrade head)
   ↓
4. First-time setup detection (if users table empty → runs setup.sh)
   ↓
5. Backend server starts (port 8000)
   ↓
6. Frontend waits for backend health
   ↓
7. Frontend starts (port 3000)
```

---

## Common Tasks

### Database Operations

```bash
# Connect to Docker database
docker-compose exec db psql -U postgres -d forecaster_enterprise

# Or from host
PGPASSWORD=postgres123 psql -h localhost -U postgres -d forecaster_enterprise

# Reset database (deletes all data!)
docker-compose down -v
docker-compose up -d
```

### Run Migrations

```bash
# Local backend
cd backend
uv run alembic upgrade head

# Docker backend
docker-compose exec backend alembic upgrade head
```

### Run Tests

```bash
cd backend
uv run pytest tests/ -v
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f db
```

---

## Hybrid Development Benefits

| Feature | Hybrid | Full Docker |
|---------|--------|-------------|
| Hot Reload | ✅ Both | ❌ Rebuild needed |
| Debugger Support | ✅ Full | ⚠️ Limited |
| Iteration Speed | ✅ Fast | ⚠️ Slower |
| Database Isolation | ✅ Docker | ✅ Docker |
| Production-Like | ⚠️ Partial | ✅ Full |

---

## Troubleshooting

### Port Conflicts

```bash
# Check what's using a port
lsof -i :5432  # Database
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
```

### Database Connection Issues

```bash
# Verify database is running
docker-compose ps db

# Test connection
PGPASSWORD=postgres123 psql -h localhost -U postgres -d forecaster_enterprise -c "SELECT 1;"
```

### Frontend Can't Connect to Backend

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend .env
cat frontend/.env
# Should have: NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### "JWT_SECRET_KEY must be set" Error

```bash
# Generate and add to .env
echo "JWT_SECRET_KEY=$(openssl rand -hex 32)" >> .env
```

---

## First-Time Setup

```bash
# 1. Create .env file
cp .env.example .env
# Edit with your values

# 2. Start database
docker-compose -f docker-compose.dev.yml up -d db

# 3. Run backend setup
cd backend
./setup.sh

# 4. Start backend
uv run uvicorn main:app --reload

# 5. Start frontend
cd ../frontend
npm install
npm run dev
```

---

## VS Code / Cursor Integration

The **Container Tools** extension (formerly Docker extension) provides:
- Container management in sidebar
- Log viewing (right-click container → "View Logs")
- Terminal access to containers

Access via:
- Container icon in sidebar
- Command Palette: `Cmd+Shift+P` → "Docker"

---

*Last updated: 2025-01-27*
