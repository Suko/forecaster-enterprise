# Forecaster Enterprise Documentation

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Quick Start](QUICK_START.md) | One-command setup guide |
| [Development Setup](DEVELOPMENT_SETUP.md) | Docker & local development |
| [Data Model](DATA_MODEL.md) | Database schema and sync strategy |
| [System Contracts](system/CONTRACTS.md) | Auth, security, naming conventions |

---

## Documentation Structure

```
docs/
├── README.md                     # This file
├── QUICK_START.md                # One-command setup
├── DEVELOPMENT_SETUP.md          # Docker & local development (consolidated)
├── SETUP_SCRIPT_GUIDE.md         # Detailed setup options
├── ENV_MANAGEMENT.md             # Environment variables guide
├── DATA_MODEL.md                 # Database schema
├── M5_DATA_MAPPING.md            # M5 dataset mapping
├── SHARED_TEST_DATA_SUPABASE.md  # Shared test data workflow
├── SECURITY_AUDIT_REPORT.md      # Security audit findings
├── USER_STORIES.md               # Feature requirements
├── WORKFLOWS.md                  # System workflows
│
├── backend/
│   ├── README.md                 # Backend quick reference
│   ├── ARCHITECTURE.md           # Backend architecture
│   ├── API_REFERENCE.md          # API endpoints
│   ├── BACKEND_ROADMAP.md        # Backend development roadmap
│   ├── FORECASTING_ROADMAP.md    # Forecasting module roadmap
│   ├── SUPPLIER_MANAGEMENT_GUIDE.md  # Supplier & MOQ management
│   ├── TEST_PLAN.md              # Testing strategy
│   └── forecasting/
│       ├── README.md             # Forecasting module status
│       └── METHODS.md            # Method implementations
│
├── frontend/
│   ├── AUTH_BEST_PRACTICES.md    # Auth implementation guide
│   └── FRONTEND_ROADMAP.md       # Frontend development roadmap
│
├── standards/
│   └── STANDARDS.md              # Project standards
│
└── system/
    └── CONTRACTS.md              # System contracts
```

---

## Setup

### Quick Setup (Test/Demo)

```bash
cd backend
./setup.sh
```

Creates users, imports demo data, sets up everything.

### With M5 Dataset

```bash
./setup.sh --use-m5-data
```

Uses real M5 forecasting competition data.

### Development Setup

See [DEVELOPMENT_SETUP.md](DEVELOPMENT_SETUP.md) for:
- Hybrid development (Docker DB + Local backend)
- Full Docker setup
- Environment configuration
- Troubleshooting

---

## Key Topics

### Backend
- [Architecture](backend/ARCHITECTURE.md) - System design
- [API Reference](backend/API_REFERENCE.md) - Endpoints
- [Backend Roadmap](backend/BACKEND_ROADMAP.md) - Implementation status

### Forecasting
- [Module README](backend/forecasting/README.md) - Status and progress
- [Methods](backend/forecasting/METHODS.md) - Implementation details
- [Forecasting Roadmap](backend/FORECASTING_ROADMAP.md) - Forecasting module roadmap

### Supplier Management
- [Supplier Management Guide](backend/SUPPLIER_MANAGEMENT_GUIDE.md) - MOQ, Lead Time, Primary suppliers

### Data
- [Data Model](DATA_MODEL.md) - Schema and relationships
- [M5 Data Mapping](M5_DATA_MAPPING.md) - How M5 dataset is mapped
- [System Contracts](system/CONTRACTS.md) - Naming conventions (`item_id`, not `sku`)

### Frontend
- [Frontend Roadmap](frontend/FRONTEND_ROADMAP.md) - UI development status
- [Auth Best Practices](frontend/AUTH_BEST_PRACTICES.md) - Authentication patterns

---

## Development

### Running Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

### Running Frontend

```bash
cd frontend
npm run dev
```

### Running Tests

```bash
cd backend
uv run pytest tests/ -v
```

---

*Last updated: 2025-01-27*
