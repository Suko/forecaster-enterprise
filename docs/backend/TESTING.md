# Testing Guide - Phase 1.6

## Prerequisites

1. **PostgreSQL must be running**
2. **Database must be created:**
   ```bash
   createdb forecaster_enterprise
   # OR using psql:
   psql -U postgres -c "CREATE DATABASE forecaster_enterprise;"
   ```

3. **Run migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

## Test the API

### 1. Start the server:
```bash
cd backend
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Test Health Endpoint:
```bash
curl http://localhost:8000/health
```

### 3. Test Root Endpoint:
```bash
curl http://localhost:8000/
```

### 4. Test User Registration:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "name": "Test User"
  }'
```

### 5. Test Login:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpassword123"
```

### 6. Test Protected Endpoint (/auth/me):
```bash
# First get token from login response, then:
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Expected Results

- ✅ Health endpoint returns `{"status": "healthy"}`
- ✅ Registration creates user and returns user data
- ✅ Login returns `{"access_token": "...", "token_type": "bearer"}`
- ✅ /auth/me returns user data when authenticated
- ✅ /auth/me returns 401 when not authenticated

