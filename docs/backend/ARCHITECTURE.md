# Backend Architecture

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Overview

The backend follows a clean layered architecture with clear separation of concerns.

---

## Directory Structure

```
backend/
├── api/                    # Route handlers (thin layer)
│   ├── auth.py            # Authentication routes
│   ├── forecast.py        # Forecasting API routes
│   └── monitoring.py      # Health check routes
├── schemas/                # Pydantic models
│   ├── auth.py            # Auth schemas
│   └── forecast.py        # Forecast schemas
├── services/               # Application services
│   ├── auth_service.py    # Auth business logic
│   └── user_service.py    # User management
├── forecasting/            # Domain module (see forecasting/README.md)
├── core/                   # Shared utilities
│   ├── rate_limit.py      # Rate limiting
│   └── monitoring.py      # Application monitoring
├── auth/                   # Authentication module
│   ├── dependencies.py    # FastAPI dependencies
│   ├── jwt.py             # JWT utilities
│   ├── security.py        # Password hashing
│   └── service_auth.py    # Service-to-service auth
├── models/                 # SQLAlchemy models
│   ├── database.py        # Database setup
│   ├── user.py            # User model
│   ├── client.py          # Client/tenant model
│   └── forecast.py        # Forecast storage
├── config.py               # Configuration
├── main.py                 # FastAPI entry point
└── migrations/             # Alembic migrations
```

---

## Architecture Layers

### 1. API Layer (`api/`)
Thin route handlers that delegate to services. No business logic.

### 2. Schema Layer (`schemas/`)
Pydantic models for request/response validation.

### 3. Service Layer (`services/`)
Application-level business logic orchestration.

### 4. Domain Layer (`forecasting/`)
Domain-specific forecasting logic with its own layered structure.

### 5. Model Layer (`models/`)
SQLAlchemy database models and ORM definitions.

### 6. Core Utilities (`core/`)
Shared utilities like rate limiting and monitoring.

### 7. Auth Module (`auth/`)
Authentication and authorization utilities.

---

## Data Flow

```
Request → API Route → Service → Domain Logic → Data Access → Database
                                     ↓
                              Response ← Schema Validation
```

---

## Multi-Tenant Architecture

### Tenant Isolation

| Layer | Isolation Method |
|-------|------------------|
| Database | `client_id` filter on all queries |
| API | Token-based client extraction |
| Cache | Client-scoped keys |

### Client Model

```python
class Client(Base):
    id: UUID
    name: str
    created_at: datetime
    is_active: bool
```

---

## API Endpoints

| Prefix | Module | Purpose |
|--------|--------|---------|
| `/api/auth/*` | auth.py | Authentication |
| `/api/v1/forecast/*` | forecast.py | Forecasting operations |
| `/api/monitoring/*` | monitoring.py | Health checks |

---

## Key Design Patterns

### Factory Pattern
Used in forecasting to select appropriate methods based on SKU classification.

### Dependency Injection
FastAPI dependencies for authentication, database sessions, and tenant context.

### Repository Pattern
Data access layer abstracts database operations.

---

## Database Schema

### Core Tables

| Table | Purpose |
|-------|---------|
| `users` | User authentication |
| `clients` | Multi-tenant clients |
| `forecast_runs` | Forecast job tracking |
| `forecast_results` | Forecast output storage |
| `sku_classifications` | SKU pattern data |
| `ts_demand_daily` | Historical demand data |

### Migrations

Using Alembic for database versioning:

```bash
cd backend
alembic upgrade head        # Apply migrations
alembic revision -m "desc"  # Create new migration
```

---

## Configuration

Environment-based configuration using Pydantic Settings:

```python
# config.py
class Settings(BaseSettings):
    database_url: str
    secret_key: str
    service_api_key: Optional[str]
    
    class Config:
        env_file = ".env"
```

---

## Running the Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

---

## Related Documentation

- [STRUCTURE_ANALYSIS.md](./STRUCTURE_ANALYSIS.md) - Detailed structure
- [forecasting/README.md](./forecasting/README.md) - Forecasting module
- [../system/CONTRACTS.md](../system/CONTRACTS.md) - System contracts

---

*Backend architecture reference*


