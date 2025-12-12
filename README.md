# Forecaster Enterprise: Forecasting & Inventory Management Platform

**Status:** ✅ Phase 1 (MVP) Complete - Forecasting System Ready

## Quick Start

### Option 1: Full Setup with Test Data (Recommended for Demo/Development)

```bash
cd backend
./setup.sh
```

This single command:
- ✅ Installs dependencies
- ✅ Runs database migrations
- ✅ Creates admin user (`admin@example.com` / `admin123`)
- ✅ Creates test user (`test@example.com` / `testpassword123`)
- ✅ **Imports both CSV and M5 datasets** (synthetic + real patterns)
- ✅ Creates products, locations, suppliers, stock levels
- ✅ Shifts dates to recent (so metrics work)
- ✅ Populates historical stock data

**Options:**
```bash
# Import only CSV (skip M5)
./setup.sh --csv-only

# Import only M5 (skip CSV)
./setup.sh --m5-only
# or (deprecated): ./setup.sh --use-m5-data

# Custom client name
./setup.sh --client-name "My Company"

# Skip test data (users and migrations only)
./setup.sh --skip-test-data
```

### Option 2: Manual Setup (Production/Custom)

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials and JWT secret
   ```

2. **Install dependencies and run migrations:**
   ```bash
   cd backend
   uv sync
   uv run alembic upgrade head
   ```

3. **Create users (optional):**
   ```bash
   uv run python create_user.py --email admin@example.com --password yourpassword --admin
   ```

4. **Start backend:**
   ```bash
   uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### Start Frontend

```bash
cd frontend
bun install
bun run dev
```

**Note:** This project uses [Bun](https://bun.sh) for package management. You can also use npm/pnpm/yarn if preferred.

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Configuration

All configuration is managed through `.env` file in the project root. See `.env.example` for all available options.

**Key environment variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `SERVICE_API_KEY` - Service API key for automated/system forecasts (optional, for scheduled forecasts)
- `ENVIRONMENT` - development/production
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `CHRONOS_MODEL_ID` - Chronos-2 model ID (default: "amazon/chronos-2")
- `CHRONOS_DEVICE` - Device for Chronos-2 (default: "cpu")

**Security Notes:**
- `JWT_SECRET_KEY`: Required in production, auto-generated in development (with warning)
- `SERVICE_API_KEY`: Optional, only needed for automated/system forecasts. If not set, service API key authentication is disabled.

## Project Structure

```
forecaster_enterprise/
├── backend/                    # FastAPI backend
│   ├── api/                    # API routes/endpoints (thin layer)
│   │   ├── auth.py            # Auth routes (delegates to services)
│   │   └── forecast.py         # Forecasting API endpoints
│   ├── schemas/                # Pydantic models (request/response)
│   │   ├── auth.py            # Token, UserResponse, UserCreate, UserUpdate
│   │   └── forecast.py        # Forecast request/response models
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py    # Authentication business logic
│   │   └── user_service.py    # User management business logic
│   ├── forecasting/            # Forecasting module (Phase 1 MVP)
│   │   ├── core/               # Core forecasting abstractions
│   │   │   ├── models/        # Base model interface
│   │   │   └── tenant_manager.py
│   │   ├── modes/             # Forecasting models
│   │   │   ├── ml/            # ML models (Chronos-2)
│   │   │   ├── statistical/   # Statistical models (MA7)
│   │   │   └── factory.py     # Model factory
│   │   ├── services/          # Forecasting services
│   │   │   ├── forecast_service.py    # Main forecast orchestration
│   │   │   ├── data_access.py        # Historical data access
│   │   │   └── quality_calculator.py  # Accuracy metrics
│   │   └── applications/      # Business applications
│   │       └── inventory/     # Inventory calculations (DIR, ROP, Safety Stock)
│   ├── core/                   # Core utilities
│   │   └── rate_limit.py     # Rate limiting and password validation
│   ├── auth/                   # Auth module
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing
│   │   ├── jwt.py              # JWT token creation/validation
│   │   ├── dependencies.py      # FastAPI auth dependencies
│   │   ├── service_auth.py     # Service API key authentication
│   │   └── security_logger.py  # Security event logging
│   ├── models/                 # Database models (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── database.py         # Database setup
│   │   ├── user.py             # User, Role models
│   │   ├── client.py           # Client (multi-tenant) model
│   │   └── forecast.py         # Forecast run and result models
│   ├── migrations/            # Alembic migrations
│   ├── scripts/               # Utility scripts
│   │   ├── setup_demo_client.py
│   │   ├── import_csv_to_ts_demand_daily.py
│   │   └── test_integration.py
│   ├── tests/                 # Test suite
│   │   ├── test_forecasting/  # Forecasting tests
│   │   ├── test_forecast_accuracy.py  # Real data accuracy test
│   │   └── ...
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration (loads from .env)
│   └── pyproject.toml          # Python dependencies (uv)
│
├── frontend/                   # Nuxt 4.x frontend
│   ├── app/                    # App directory (Nuxt 4.x structure)
│   │   ├── assets/             # Website assets (processed by build tool)
│   │   ├── components/         # Vue components
│   │   ├── composables/         # Vue composables (reusable state functions only)
│   │   ├── layouts/            # Layout components
│   │   ├── middleware/         # Nuxt middleware
│   │   ├── pages/              # Page views (file-based routing)
│   │   ├── utils/              # Utility functions (used across app)
│   │   └── app.vue             # Root component
│   ├── server/
│   │   └── api/                # Nuxt server API routes
│   └── public/                 # Static assets (served at root)
│
├── data/                       # Data files (large files gitignored)
│   ├── sintetic_data/         # Synthetic demo data
│   └── minibambini/           # Real client data (gitignored)
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Environment template
└── docs/                       # Documentation
    ├── forecasting/            # Forecasting system docs
    │   ├── CURRENT_STATUS.md  # Phase 1 status
    │   ├── ARCHITECTURE.md    # System architecture
    │   └── ...
    └── ...
```

## Frontend Structure Guidelines

**Note:** This project uses **Nuxt 4.x**, which requires the `app/` directory structure. All app-related code (components, composables, pages, layouts, middleware, assets, utils) is organized under the `app/` directory. See [Nuxt 4.x Directory Structure](https://nuxt.com/docs/4.x/directory-structure) for details.


## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Nuxt 4)                        │
│  - nuxt-auth-utils (JWT management, session handling)       │
│  - Nuxt UI (official Nuxt component library)              │
│  - Tailwind CSS 4 (styling)                                 │
│  - Dashboard layout with collapsible sidebar               │
│  - Settings management with tabs                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│                 Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API Layer (api/) - Thin route handlers             │  │
│  │  - /api/v1/auth (authentication)                     │  │
│  │  - /api/v1/forecast (forecast generation)             │  │
│  │  - /api/v1/inventory/calculate (inventory metrics)   │  │
│  │  - /api/v1/forecasts/actuals (backfill actuals)      │  │
│  │  - /api/v1/forecasts/quality (accuracy metrics)     │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │  Services Layer - Business logic                     │  │
│  │  - Auth & User services                              │  │
│  │  - ForecastService (orchestrates forecasting)       │  │
│  │  - QualityCalculator (accuracy metrics)             │  │
│  │  - InventoryCalculator (DIR, ROP, Safety Stock)     │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │  Forecasting Models Layer                           │  │
│  │  - Chronos-2 (AI-based, primary)                    │  │
│  │  - MA7 (Statistical baseline)                      │  │
│  │  - ModelFactory (extensible)                        │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │  Models Layer (models/) - SQLAlchemy ORM             │  │
│  │  - User, Client (multi-tenant)                      │  │
│  │  - ForecastRun, ForecastResult                      │  │
│  │  - ts_demand_daily (historical data)                │  │
│  └────────────────────────────────────────────────────┘  │
│  - Auth module (JWT, password hashing, security)           │
│  - Schemas (Pydantic models for validation)               │
│  - Core utilities (rate limiting, validation)             │
│  - Async/await throughout (async SQLAlchemy, asyncpg)     │
│  - Package manager: uv                                      │
│  - Database: PostgreSQL (async)                            │
└─────────────────────────────────────────────────────────────┘
```

### Backend Architecture (FastAPI Best Practices)

The backend follows FastAPI best practices with clear separation of concerns:

- **API Layer** (`api/`): Thin async route handlers that delegate to services
- **Schemas** (`schemas/`): Pydantic models for request/response validation
- **Services** (`services/`): Async business logic and data operations
- **Forecasting Module** (`forecasting/`): Complete forecasting system
  - **Models** (`modes/`): Forecasting algorithms (Chronos-2, MA7)
  - **Services** (`services/`): Forecast orchestration, data access, quality metrics
  - **Applications** (`applications/`): Business logic (inventory calculations)
- **Models** (`models/`): SQLAlchemy async database models
- **Core** (`core/`): Shared utilities (rate limiting, validation)
- **Auth** (`auth/`): Authentication and security utilities

**Async/Await**: The entire backend uses async/await for optimal performance:
- All routes are async functions
- All service functions are async
- Database operations use async SQLAlchemy with asyncpg
- This allows FastAPI to handle concurrent requests efficiently

### Forecasting System (Phase 1 MVP)

**Status:** ✅ Complete and tested

**Features:**
- **Models**: Chronos-2 (AI) + MA7 (statistical baseline)
- **Accuracy**: 18% MAPE verified on real data
- **Inventory**: APICS-standard calculations (DIR, ROP, Safety Stock)
- **Multi-tenant**: Full client isolation
- **Authentication**: JWT + Service API Key support

**API Endpoints:**
- `POST /api/v1/forecast` - Generate forecasts
- `POST /api/v1/inventory/calculate` - Calculate inventory metrics
- `POST /api/v1/forecasts/actuals` - Backfill actual sales
- `GET /api/v1/forecasts/quality/{item_id}` - Get accuracy metrics

See [docs/forecasting/CURRENT_STATUS.md](docs/forecasting/CURRENT_STATUS.md) for details.

## Stack Usage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI | API server, auth, forecasting, inventory (async) |
| **Package Manager** | uv | Python dependency management |
| **Database** | PostgreSQL | User data, forecasts, historical data (async with asyncpg) |
| **Migrations** | Alembic | Database schema management |
| **Forecasting** | Chronos-2 | AI-based time series forecasting (primary) |
| **Forecasting** | MA7 | Statistical baseline (7-day moving average) |
| **Frontend** | Nuxt 4 | SSR framework, routing, auth integration |
| **Frontend Package Manager** | Bun | Fast JavaScript runtime and package manager |
| **Auth Module** | nuxt-auth-utils | JWT token management, session handling |
| **UI Framework** | Nuxt UI | Official Nuxt component library |
| **Styling** | Tailwind CSS 4 | Utility-first CSS framework |
| **Icons** | Lucide Vue Next | Icon library |

## Key Features

### ✅ Phase 1 (MVP) - Complete
- **Forecasting**: Chronos-2 + MA7 models
- **Inventory**: APICS-standard calculations
- **Accuracy Tracking**: MAPE, MAE, RMSE, Bias metrics
- **Data Validation & Audit**: Input/output validation + audit trail (required for testing)
- **Multi-Tenant**: Full client isolation
- **Authentication**: JWT + Service API Key
- **Testing**: 41+ test functions, accuracy validation

### 🔜 Phase 2 - Planned
- **Covariates**: Promotions, holidays, marketing data
- **Advanced Analytics**: Model comparison, drift detection
- **Production ETL**: Airbyte, dbt pipelines

See [docs/forecasting/](docs/forecasting/) for detailed documentation.
