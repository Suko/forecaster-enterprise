# Forecaster Enterprise Documentation

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Quick Start](QUICK_START.md) | One-command setup guide |
| [Setup Script Guide](SETUP_SCRIPT_GUIDE.md) | Detailed setup options (test data, M5, reset) |
| [Data Model](DATA_MODEL.md) | Database schema and sync strategy |
| [System Contracts](system/CONTRACTS.md) | Auth, security, naming conventions |

---

## Documentation Structure

```
docs/
├── README.md                 # This file
├── QUICK_START.md            # One-command setup
├── SETUP_SCRIPT_GUIDE.md     # Detailed setup options
├── DATA_MODEL.md             # Database schema
├── M5_DATA_MAPPING.md        # M5 dataset mapping to daily records
│
├── backend/
│   ├── ARCHITECTURE.md       # Backend architecture
│   ├── API_REFERENCE.md      # API endpoints
│   ├── ROADMAP.md            # Development roadmap
│   └── forecasting/
│       ├── README.md         # Forecasting module status
│       └── METHODS.md        # Method implementations
│
├── frontend/
│   ├── AUTH_BEST_PRACTICES.md
│   └── FRONTEND_ROADMAP.md
│
├── standards/
│   └── STANDARDS.md          # Project standards
│
├── system/
│   └── CONTRACTS.md          # System contracts
│
├── USER_STORIES.md           # Feature requirements
└── WORKFLOWS.md              # System workflows
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

### Production Setup

See [QUICK_START.md](QUICK_START.md) for manual setup steps.

---

## Key Topics

### Forecasting
- [Module README](backend/forecasting/README.md) - Status and progress
- [Methods](backend/forecasting/METHODS.md) - Implementation details

### Backend
- [Architecture](backend/ARCHITECTURE.md) - System design
- [API Reference](backend/API_REFERENCE.md) - Endpoints

### Data
- [Data Model](DATA_MODEL.md) - Schema and relationships
- [M5 Data Mapping](M5_DATA_MAPPING.md) - How M5 dataset is mapped to daily records
- [System Contracts](system/CONTRACTS.md) - Naming conventions (`item_id`, not `sku`)

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

*Last updated: 2025-12-10*
