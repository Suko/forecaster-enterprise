# Environment Variables Reference

**Status:** ✅ Complete  
**Date:** 2025-12-06

---

## Overview

This document lists all environment variables used by the forecasting system and backend.

---

## Quick Reference: Your Current .env

**You currently have:**
- ✅ `ENVIRONMENT`
- ✅ `DEBUG`
- ✅ `DATABASE_URL`
- ✅ `JWT_SECRET_KEY`
- ✅ `SERVICE_API_KEY`

**Optional but recommended:**
- `CORS_ORIGINS` - If running a frontend (default: localhost origins)
- `RATE_LIMIT_ENABLED` - Rate limiting (default: true)
- `RATE_LIMIT_PER_MINUTE` - Requests per minute (default: 5)
- `RATE_LIMIT_PER_HOUR` - Requests per hour (default: 20)

**Optional (have defaults):**
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiry (default: 30)
- `API_HOST` - API host (default: 0.0.0.0)
- `API_PORT` - API port (default: 8000)
- `APP_NAME` - App name (default: "Forecaster Enterprise")

---

## Required Variables

### `JWT_SECRET_KEY`
- **Purpose:** Secret key for JWT token signing and validation
- **Type:** String (minimum 32 characters)
- **Location:** `backend/config.py` → `settings.secret_key`
- **Generation:** `openssl rand -hex 32`
- **Production:** Required (application will fail to start if not set)
- **Development:** Auto-generated with warning if not set
- **Security:** Never commit to version control

**Example:**
```bash
JWT_SECRET_KEY=your-secret-key-here-minimum-32-characters-long
```

### `DATABASE_URL`
- **Purpose:** PostgreSQL connection string
- **Type:** String (PostgreSQL connection URI)
- **Location:** `backend/config.py` → `settings.database_url`
- **Format:** `postgresql://user:password@host:port/database`
- **Production:** Required
- **Development:** Defaults to `postgresql://postgres:postgres@localhost:5432/forecaster_enterprise`

**Example:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/forecaster_enterprise
```

---

## Optional Variables

### `SERVICE_API_KEY`
- **Purpose:** Service API key for automated/system forecasts
- **Type:** String (minimum 32 characters recommended)
- **Location:** `backend/config.py` → `settings.service_api_key` or `os.getenv("SERVICE_API_KEY")`
- **Generation:** `openssl rand -hex 32`
- **Usage:** Used in `X-API-Key` header for automated forecast calls
- **Behavior:** If not set, service API key authentication is disabled
- **Security:** Never commit to version control

**Example:**
```bash
SERVICE_API_KEY=your-service-api-key-here-minimum-32-characters-long
```

**When to Use:**
- Scheduled/automated forecast generation (cron jobs)
- System-to-system API calls
- Background workers that generate forecasts

**See:** [SYSTEM_AUTHENTICATION.md](SYSTEM_AUTHENTICATION.md) for usage details

---

## Application Configuration

### `ENVIRONMENT`
- **Purpose:** Application environment (development/production)
- **Type:** String
- **Values:** `development`, `production`, `staging`
- **Default:** `development`
- **Location:** `backend/config.py` → `settings.environment`

**Example:**
```bash
ENVIRONMENT=production
```

### `DEBUG`
- **Purpose:** Enable debug mode
- **Type:** Boolean
- **Values:** `true`, `false`, `1`, `0`
- **Default:** `false`
- **Location:** `backend/config.py` → `settings.debug`
- **Note:** Cannot be enabled in production

**Example:**
```bash
DEBUG=false
```

### `APP_NAME`
- **Purpose:** Application name
- **Type:** String
- **Default:** `Forecaster Enterprise`
- **Location:** `backend/config.py` → `settings.app_name`

---

## API Configuration

### `API_HOST`
- **Purpose:** Host to bind API server
- **Type:** String
- **Default:** `0.0.0.0`
- **Location:** `backend/config.py` → `settings.api_host`
- **Note:** Not recommended in production (use reverse proxy)

### `API_PORT`
- **Purpose:** Port for API server
- **Type:** Integer
- **Default:** `8000`
- **Location:** `backend/config.py` → `settings.api_port`

---

## JWT Configuration

### `JWT_ALGORITHM`
- **Purpose:** JWT signing algorithm
- **Type:** String
- **Default:** `HS256`
- **Location:** `backend/config.py` → `settings.algorithm`
- **Values:** `HS256`, `HS384`, `HS512`, `RS256`, etc.

### `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- **Purpose:** JWT token expiration time
- **Type:** Integer
- **Default:** `30`
- **Location:** `backend/config.py` → `settings.access_token_expire_minutes`

---

## CORS Configuration

### `CORS_ORIGINS`
- **Purpose:** Allowed CORS origins
- **Type:** Comma-separated string
- **Default:** `http://localhost:3000,http://localhost:5173`
- **Location:** `backend/config.py` → `settings.cors_origins`
- **Format:** `origin1,origin2,origin3`

**Example:**
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,https://app.example.com
```

---

## Rate Limiting Configuration

### `RATE_LIMIT_ENABLED`
- **Purpose:** Enable rate limiting
- **Type:** Boolean
- **Default:** `true`
- **Location:** `backend/config.py` → `settings.rate_limit_enabled`

### `RATE_LIMIT_PER_MINUTE`
- **Purpose:** Requests allowed per minute
- **Type:** Integer
- **Default:** `5`
- **Location:** `backend/config.py` → `settings.rate_limit_per_minute`

### `RATE_LIMIT_PER_HOUR`
- **Purpose:** Requests allowed per hour
- **Type:** Integer
- **Default:** `20`
- **Location:** `backend/config.py` → `settings.rate_limit_per_hour`

---

## Configuration File

### `.env` File

All environment variables are loaded from `.env` file:

**Locations (checked in order):**
1. `backend/.env` (primary)
2. Project root `.env` (fallback)
3. Current working directory `.env` (fallback)

**Template:**
See `.env.example` for complete template with all variables.

**Loading:**
- Loaded automatically by `backend/config.py` using `python-dotenv`
- Runtime environment variables take precedence over `.env` file
- Uses `override=False` to prevent `.env` from overwriting runtime vars

---

## Code Access

### In Python Code

```python
from config import settings

# JWT Secret Key
secret_key = settings.secret_key

# Service API Key
service_api_key = settings.service_api_key or os.getenv("SERVICE_API_KEY")

# Database URL
database_url = settings.database_url
```

### Direct Environment Access

```python
import os

# Direct access (not recommended, use settings instead)
jwt_secret = os.getenv("JWT_SECRET_KEY")
service_key = os.getenv("SERVICE_API_KEY")
```

---

## Security Best Practices

### ✅ Do:
- Store secrets in environment variables
- Use strong, random keys (32+ characters)
- Rotate keys periodically
- Use different keys per environment
- Store `.env` files securely (never commit)
- Use secrets manager in production (AWS Secrets Manager, HashiCorp Vault, etc.)

### ❌ Don't:
- Commit `.env` files to version control
- Use weak or predictable keys
- Share keys between environments
- Hardcode secrets in code
- Log secrets in application logs

---

## Production Checklist

- [ ] `JWT_SECRET_KEY` set (32+ characters)
- [ ] `SERVICE_API_KEY` set (if using automated forecasts)
- [ ] `DATABASE_URL` configured
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` restricted (no wildcards, no localhost)
- [ ] `.env` file not committed to version control
- [ ] Secrets stored in secure secrets manager
- [ ] Keys rotated periodically

---

## Testing

### Test Environment Variables

**Optional:**
- `TEST_POSTGRES=true` - Use PostgreSQL instead of SQLite for tests
- `TEST_DATABASE_URL` - PostgreSQL connection string for tests
- `TEST_SERVICE_API_KEY` - Service API key for tests (default: "test-service-api-key-12345")

**See:** [TEST_UPDATE_SUMMARY.md](TEST_UPDATE_SUMMARY.md) for test configuration

---

## References

- [SYSTEM_AUTHENTICATION.md](SYSTEM_AUTHENTICATION.md) - Service API key usage
- [AUTH_SETUP.md](../AUTH_SETUP.md) - Authentication setup
- [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md) - Multi-tenant configuration
- `.env.example` - Complete environment variable template

---

**Status:** ✅ Complete - All environment variables documented

