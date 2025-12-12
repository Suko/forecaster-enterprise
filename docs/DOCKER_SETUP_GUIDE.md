# Docker Setup Guide - High Level Flow

## 🚀 Complete Startup Sequence

```
1. Database (PostgreSQL) → 2. Backend Setup → 3. Backend Server → 4. Frontend → 5. License Watcher
```

---

## 📋 Step-by-Step Flow

### **1. Database Container (`db`)**

**What happens:**
- PostgreSQL 16 starts in a container
- Uses Docker volume `postgres_data` for persistence (data survives container restarts)
- Health check: `pg_isready` every 10s
- **No manual setup needed** - PostgreSQL initializes automatically

**Environment Variables (from `.env`):**
```bash
DB_USER=postgres              # Default: postgres
DB_PASSWORD=postgres          # Default: postgres  
DB_NAME=forecaster_enterprise # Default: forecaster_enterprise
```

**Port:** `5432` (exposed to host)

**Dependencies:** None (starts first)

---

### **2. Backend Container (`backend`)**

**What happens:**

#### **Phase 1: Wait for Database**
- Backend waits until database health check passes
- Polls every 2 seconds: `psql -h db -U $DB_USER -d $DB_NAME`

#### **Phase 2: Database Migrations**
- Always runs: `alembic upgrade head`
- Updates schema to latest version
- Idempotent (safe to run multiple times)

#### **Phase 3: First-Time Setup Detection**
- Checks if `users` table has any records
- **If empty** → First-time setup → runs `setup.sh`
- **If has data** → Skips setup → goes straight to server

#### **Phase 4: Setup Script (if first-time)**
Runs `/app/setup.sh` with arguments from environment variables:

**What setup.sh does:**
1. Creates admin user (`admin@example.com` / `admin123`)
2. Creates test user (`test@example.com` / `testpassword123`)
3. Creates client organization
4. Imports sales data (CSV or M5 dataset)
5. Sets up test data (products, locations, suppliers, stock)
6. Shifts dates to recent
7. Populates historical stock

#### **Phase 5: Start Uvicorn Server**
- Runs: `uvicorn main:app --host 0.0.0.0 --port 8000`
- Health endpoint: `http://localhost:8000/health`

**Port:** `8000` (exposed to host)

**Dependencies:** `db` (must be healthy)

---

### **3. Frontend Container (`nuxt-frontend`)**

**What happens:**
- Builds Nuxt 3 application (during `docker-compose build`)
- Runs production server: `node .output/server/index.mjs`
- Connects to backend at `http://backend:8000` (internal Docker network)
- Exposes API to browser at `http://localhost:8000` (from `NUXT_PUBLIC_API_BASE_URL`)

**Port:** `3000` (exposed to host)

**Dependencies:** 
- `backend` (must be healthy)
- `license-watcher` (must be started)

---

### **4. License Watcher (`licence-watcher`)**

**What happens:**
- Monitors license validity
- Watches Docker containers with label `com.forecasting.license: "true"`
- Runs in background

**Dependencies:** None (starts independently)

---

## 🔧 Environment Variables

### **📍 Where to Set Environment Variables:**

**For Docker (docker-compose):**
- **Location:** `.env` file in **project root** (same directory as `docker-compose.yml`)
- **Path:** `/Users/mihapro/Development/ecommerce/forecaster_enterprise/.env`
- **Why:** `docker-compose.yml` line 28-29 reads: `env_file: - .env` (relative to compose file)

**For Local Development (without Docker):**
- **Backend:** `.env` in project root OR `backend/.env` (backend checks both)
- **Frontend:** `.env` in project root OR `frontend/.env`

**Quick Setup:**
```bash
# From project root
cp .env.example .env
# Edit .env with your values
nano .env  # or use your preferred editor
```

### **Required in `.env` file:**

```bash
# Database
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=forecaster_enterprise

# Backend Setup (optional - has defaults)
ADMIN_EMAIL=admin@example.com          # Default: admin@example.com
ADMIN_PASSWORD=admin123                 # Default: admin123
ADMIN_NAME="Admin User"                 # Default: Admin User
CLIENT_NAME="Demo Client"               # Default: Demo Client
TEST_EMAIL=test@example.com             # Default: test@example.com
TEST_PASSWORD=testpassword123           # Default: testpassword123
TEST_NAME="Test User"                   # Default: Test User

# Data Import
CSV_PATH=../data/synthetic_data/synthetic_ecom_chronos2_demo.csv
USE_M5_DATA=false                       # Use M5 dataset instead of CSV

# Skip Options
SKIP_TEST_DATA=false                    # Skip test data creation
SKIP_CSV_IMPORT=false                   # Skip CSV import
SETUP_TEST_DATA=false                   # Alias for setup flag

# Application
ENVIRONMENT=production                   # Default: production
DEBUG=false                              # Default: false

# Frontend
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
NUXT_SESSION_PASSWORD=your-secret-key   # Required for sessions

# License (optional)
LICENSE_URL=
LICENSE_KEY=
CHECK_INTERVAL=3600                      # Default: 3600 seconds
GRACE_PERIOD=172800                      # Default: 172800 seconds
```

### **How Environment Variables Flow:**

1. **`.env` file** → Read by `docker-compose.yml` (line 28-29)
2. **`docker-compose.yml`** → Sets defaults, passes to containers
3. **Container environment** → Available to `docker-entrypoint.sh`
4. **`docker-entrypoint.sh`** → Builds arguments for `setup.sh`
5. **`setup.sh`** → Uses values to create users/data

---

## 🎯 Quick Start Commands

### **First Time Setup:**
```bash
# 1. Create .env file (if not exists)
cp .env.example .env

# 2. Edit .env with your values (optional - defaults work)
# nano .env

# 3. Start everything
docker-compose up -d

# 4. Watch backend logs (to see setup progress)
docker-compose logs -f backend

# 5. Check health
curl http://localhost:8000/health
```

### **Stop Everything:**
```bash
docker-compose down
```

### **Stop and Remove Data (Fresh Start):**
```bash
docker-compose down -v  # Removes volumes (deletes database!)
```

### **Rebuild After Code Changes:**
```bash
docker-compose build backend
docker-compose up -d backend
```

---

## 🔍 Key Points

### **Database Persistence:**
- **Data survives** container restarts (stored in Docker volume)
- **To reset:** `docker-compose down -v` (deletes all data)
- **First-time setup** only runs when `users` table is empty

### **Setup Script Execution:**
- **Runs automatically** on first container start
- **Skips** if database already has users
- **Can be forced** by deleting database volume

### **Health Checks:**
- **Database:** `pg_isready` (checks PostgreSQL is accepting connections)
- **Backend:** `curl http://localhost:8000/health` (checks API is responding)
- **Frontend:** HTTP request to `/api/health` (checks Nuxt is responding)

### **Dependencies Chain:**
```
db (no deps)
  ↓
backend (waits for db healthy)
  ↓
frontend (waits for backend healthy)
  ↓
license-watcher (independent)
```

---

## 🐛 Troubleshooting

### **"Unknown option: User" Error:**
- **Fixed!** Now uses bash arrays to handle spaces in names
- If you see this, rebuild: `docker-compose build backend`

### **Database Connection Issues:**
- Check database is healthy: `docker-compose ps db`
- Check logs: `docker-compose logs db`
- Verify `.env` has correct `DB_USER`, `DB_PASSWORD`, `DB_NAME`

### **Backend Won't Start:**
- Check database is ready: `docker-compose logs db | tail -20`
- Check backend logs: `docker-compose logs backend | tail -50`
- Verify port 8000 is free: `lsof -i :8000`

### **Frontend Can't Connect to Backend:**
- Verify backend health: `curl http://localhost:8000/health`
- Check `NUXT_PUBLIC_API_BASE_URL` in `.env`
- Check frontend logs: `docker-compose logs frontend`

---

## 📝 Summary

**The Complete Flow:**
1. ✅ **Database starts** → PostgreSQL initializes
2. ✅ **Backend waits** → Database health check passes
3. ✅ **Migrations run** → Schema updated
4. ✅ **Setup check** → If first-time, runs `setup.sh`
5. ✅ **Backend starts** → Uvicorn server on port 8000
6. ✅ **Frontend waits** → Backend health check passes
7. ✅ **Frontend starts** → Nuxt server on port 3000
8. ✅ **License watcher** → Runs in background

**All managed automatically by Docker Compose!** 🎉
