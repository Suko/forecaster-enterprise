# Forecaster Enterprise: Forecasting & Inventory Management Platform

**Status:** Phase 1 (MVP) Complete - Forecasting System Ready

## Quick Start

### Option 1: Full Setup with Test Data (Recommended)

```bash
cd backend
./setup.sh
```

This single command:
- ✅ Installs dependencies
- ✅ Runs database migrations
- ✅ Creates admin user (`admin@example.com` / `admin123`)
- ✅ Creates test user (`test@example.com` / `testpassword123`)
- ✅ Imports both CSV and M5 datasets (synthetic + real patterns)
- ✅ Creates products, locations, suppliers, stock levels
- ✅ Shifts dates to recent (so metrics work)
- ✅ Populates historical stock data

**Options:**
```bash
# Import only CSV (skip M5)
./setup.sh --csv-only

# Import only M5 (skip CSV)
./setup.sh --m5-only

# Custom client name
./setup.sh --client-name "My Company"

# Skip test data (users and migrations only)
./setup.sh --skip-test-data
```

### Option 2: Manual Setup

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

**Access:**
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Environment Configuration

All configuration is managed through `.env` file in the project root. See `.env.example` for all available options.

**Key environment variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `SERVICE_API_KEY` - Service API key for automated/system forecasts (optional)
- `ENVIRONMENT` - development/production
- `CORS_ORIGINS` - Comma-separated list of allowed origins
- `CHRONOS_MODEL_ID` - Chronos-2 model ID (default: "amazon/chronos-2")
- `CHRONOS_DEVICE` - Device for Chronos-2 (default: "cpu")

## Project Structure

```
forecaster_enterprise/
├── backend/                    # FastAPI backend
│   ├── api/                    # API routes (thin layer)
│   ├── schemas/                # Pydantic request/response models
│   ├── services/               # Business logic layer
│   ├── forecasting/            # Forecasting module
│   │   ├── core/               # Core abstractions
│   │   ├── modes/              # Models (Chronos-2, MA7, Croston)
│   │   ├── services/           # Forecast orchestration
│   │   └── applications/       # Business logic (inventory)
│   ├── models/                 # SQLAlchemy ORM models
│   ├── auth/                   # Authentication module
│   ├── migrations/             # Alembic migrations
│   ├── tests/                  # Test suite
│   └── scripts/                # Utility scripts
├── docs/                       # Documentation
│   ├── backend/                # Backend docs (API, architecture)
│   ├── setup/                  # Setup guides
│   ├── system/                 # System contracts & integration
│   └── roadmap/                # Feature roadmaps
├── data/                       # Data files (large files gitignored)
└── scripts/                    # Project-level scripts
```

**Note:** Frontend is maintained in a [separate repository](https://github.com/Suko/forecaster-enterprise-frontend).

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI)                           │
├─────────────────────────────────────────────────────────────┤
│  API Layer (api/) - Thin route handlers                     │
│  - /api/v1/auth, /api/v1/forecast, /api/v1/inventory        │
│  - /api/v1/products, /api/v1/dashboard, /api/v1/simulation  │
├─────────────────────────────────────────────────────────────┤
│  Services Layer - Business logic                            │
│  - Auth, Inventory, Dashboard, Simulation services          │
│  - ForecastService, QualityCalculator, InventoryCalculator  │
├─────────────────────────────────────────────────────────────┤
│  Forecasting Models                                         │
│  - Chronos-2 (AI-based, primary)                            │
│  - MA7, Croston, MinMax (statistical)                       │
├─────────────────────────────────────────────────────────────┤
│  Models Layer - SQLAlchemy ORM                              │
│  - User, Client (multi-tenant), Product, Supplier           │
│  - ForecastRun, ForecastResult, ts_demand_daily             │
└─────────────────────────────────────────────────────────────┘
│  PostgreSQL (async with asyncpg) | Package manager: uv      │
```

## Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Server** | FastAPI | Async API server with OpenAPI docs |
| **Package Manager** | uv | Python dependency management |
| **Database** | PostgreSQL | Async with asyncpg |
| **Migrations** | Alembic | Database schema management |
| **Forecasting** | Chronos-2 | AI-based time series forecasting |
| **Forecasting** | MA7, Croston | Statistical baselines |

## Key Features

### Phase 1 - Complete
- **Forecasting**: Chronos-2 + statistical models
- **Inventory**: APICS-standard calculations (DIR, ROP, Safety Stock)
- **Accuracy Tracking**: MAPE, MAE, RMSE, Bias metrics
- **Simulation**: What-if scenario testing
- **Multi-Tenant**: Full client isolation
- **Authentication**: JWT + Service API Key

### 🔜 Phase 2 - Planned
- Covariates (promotions, holidays)
- Advanced analytics & drift detection
- Production ETL pipelines

## Documentation

| Doc | Purpose |
|-----|---------|
| **[docs/backend/README.md](docs/backend/README.md)** | Backend quick reference |
| **[docs/backend/API_REFERENCE.md](docs/backend/API_REFERENCE.md)** | Complete API documentation |
| **[docs/backend/ARCHITECTURE.md](docs/backend/ARCHITECTURE.md)** | System architecture |
| **[docs/setup/QUICK_START.md](docs/setup/QUICK_START.md)** | Setup guide |
| **[docs/system/CONTRACTS.md](docs/system/CONTRACTS.md)** | System contracts |
| **[docs/backend/forecasting/](docs/backend/forecasting/)** | Forecasting documentation |
