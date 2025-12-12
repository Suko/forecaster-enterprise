# Complete Development Setup Guide

## 🎯 Hybrid Development Setup

**Best for active development:** Database in Docker, Backend + Frontend run locally

---

## 🚀 Quick Start

### **Three Terminal Setup:**

**Terminal 1: Database (Docker)**
```bash
cd /Users/mihapro/Development/ecommerce/forecaster_enterprise
docker-compose -f docker-compose.dev.yml up -d db

# Watch logs (optional)
docker-compose -f docker-compose.dev.yml logs -f db
```

**Terminal 2: Backend (Local with Hot Reload)**
```bash
cd /Users/mihapro/Development/ecommerce/forecaster_enterprise/backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 3: Frontend (Local with Hot Reload)**
```bash
cd /Users/mihapro/Development/ecommerce/forecaster_enterprise/frontend
npm install  # First time only
npm run dev
```

---

## ✅ Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🔧 Configuration

### **Database (.env in project root):**
```bash
DB_USER=postgres
DB_PASSWORD=postgres123
DB_NAME=forecaster_enterprise
```

### **Backend (.env in project root):**
```bash
DATABASE_URL=postgresql://postgres:postgres123@localhost:5432/forecaster_enterprise
# Or backend will construct from DB_* variables
```

### **Frontend (.env in project root or frontend/.env):**
```bash
NUXT_SESSION_PASSWORD=398a0c4ad0515f8f1874cc97d64ee290a25ca8ec0f6f30ccad438af2a507845e
NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 🎨 Development Features

### **Backend:**
- ✅ Hot reload (`--reload` flag)
- ✅ Auto-restart on code changes
- ✅ Python debugger support
- ✅ Fast iteration

### **Frontend:**
- ✅ Hot Module Replacement (HMR)
- ✅ Instant updates in browser
- ✅ Vue DevTools support
- ✅ Fast refresh

### **Database:**
- ✅ Isolated in Docker
- ✅ Easy to reset (`docker-compose -f docker-compose.dev.yml down -v`)
- ✅ Data persists between restarts
- ✅ Same data as full Docker setup

---

## 🛠️ Common Tasks

### **Stop Everything:**
```bash
# Stop database
docker-compose -f docker-compose.dev.yml down

# Stop backend: Ctrl+C in Terminal 2
# Stop frontend: Ctrl+C in Terminal 3
```

### **Reset Database:**
```bash
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d db
```

### **View Database:**
```bash
# Connect via psql
PGPASSWORD=postgres123 psql -h localhost -U postgres -d forecaster_enterprise

# Or use Docker
docker-compose -f docker-compose.dev.yml exec db psql -U postgres -d forecaster_enterprise
```

### **Run Migrations:**
```bash
cd backend
uv run alembic upgrade head
```

### **Run Tests:**
```bash
cd backend
uv run pytest tests/ -v
```

---

## 📋 Troubleshooting

### **Port Conflicts:**

**Port 5432 (Database):**
```bash
# Check what's using it
lsof -i :5432

# Stop local PostgreSQL if needed
brew services stop postgresql@16
```

**Port 8000 (Backend):**
```bash
# Check what's using it
lsof -i :8000

# Stop if needed
```

**Port 3000 (Frontend):**
```bash
# Check what's using it
lsof -i :3000

# Stop if needed
```

### **Database Connection Issues:**

**Backend can't connect:**
```bash
# Verify database is running
docker-compose -f docker-compose.dev.yml ps

# Test connection
PGPASSWORD=postgres123 psql -h localhost -U postgres -d forecaster_enterprise -c "SELECT 1;"

# Check .env has correct DB_PASSWORD
cat .env | grep DB_PASSWORD
```

### **Frontend Can't Connect to Backend:**

**Check API URL:**
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check frontend .env
cat frontend/.env
# Should have: NUXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

---

## 🎯 Workflow Summary

1. **Start database** (Docker) - One time per session
2. **Start backend** (Local) - Hot reload enabled
3. **Start frontend** (Local) - Hot reload enabled
4. **Develop** - Changes reflect immediately
5. **Test** - Full stack available locally

---

## ✅ Benefits

- ✅ **Fastest iteration** - No rebuilds needed
- ✅ **Hot reload** - Both backend and frontend
- ✅ **Debugger support** - Python and JavaScript
- ✅ **Isolated database** - Easy to reset
- ✅ **Production-like** - Same database as production
- ✅ **Full control** - Can modify code on the fly

---

## 📝 Notes

**First Time Setup:**
```bash
# Install backend dependencies
cd backend
uv sync

# Install frontend dependencies
cd ../frontend
npm install
```

**Environment Variables:**
- Project root `.env` is used by both backend and frontend
- Frontend can also have its own `.env` file
- Nuxt reads from both locations

**Data Persistence:**
- Database data stored in Docker volume
- Survives container restarts
- Shared with full Docker setup (same volume name)

---

## 🎉 Ready to Develop!

Your complete development environment:
- ✅ Database: Docker (isolated, easy reset)
- ✅ Backend: Local (hot reload, debugger)
- ✅ Frontend: Local (hot reload, dev tools)

**Start coding and see changes instantly!** 🚀
