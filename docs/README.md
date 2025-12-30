# Forecaster Enterprise Documentation

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Quick Start](setup/QUICK_START.md) | One-command setup guide |
| [Next Steps](roadmap/NEXT_STEPS.md) | Current development priorities |
| [API Reference](backend/API_REFERENCE.md) | All API endpoints |
| [System Contracts](system/CONTRACTS.md) | Auth, naming conventions, patterns |
| [Data Model](DATA_MODEL.md) | Database schema |

---

## Documentation by Role

| Role | Key Documents |
|------|---------------|
| **Developer** | [Quick Start](setup/QUICK_START.md) → [API Reference](backend/API_REFERENCE.md) → [Architecture](backend/ARCHITECTURE.md) → [Contracts](system/CONTRACTS.md) |
| **Product Manager** | [Next Steps](roadmap/NEXT_STEPS.md) → [User Stories](roadmap/product/USER_STORIES.md) → [Workflows](roadmap/product/WORKFLOWS.md) |
| **DevOps** | [First Release Checklist](setup/FIRST_RELEASE_CHECKLIST.md) → [CI/CD Approaches](system/DEPLOYMENT_CICD_APPROACHES.md) → [ENV Management](setup/ENV_MANAGEMENT.md) |

---

## Documentation Structure

```
docs/
├── README.md                     # This file
├── DATA_MODEL.md                 # Database schema
├── DATA_REQUIREMENTS.md          # User-facing data requirements
├── STOCK_AGGREGATION.md          # How stock is aggregated
├── QUICK_TEST_GUIDE.md           # Quick test guide
│
├── setup/                        # Setup & deployment
│   ├── QUICK_START.md            # One-command setup
│   ├── DEVELOPMENT_SETUP.md      # Docker & local development
│   ├── ENV_MANAGEMENT.md         # Environment variables guide
│   ├── FIRST_RELEASE_CHECKLIST.md # Release & deployment guide
│   └── SHARED_TEST_DATA_SUPABASE.md # Seed data sharing
│
├── backend/                      # Backend technical docs
│   ├── README.md                 # Backend quick reference
│   ├── API_REFERENCE.md          # API endpoints
│   ├── ARCHITECTURE.md           # System architecture
│   ├── STRUCTURE_ANALYSIS.md     # Codebase map
│   ├── SUPPLIER_MANAGEMENT_GUIDE.md
│   └── forecasting/              # Forecasting module docs
│       ├── README.md
│       ├── METHODS.md
│       └── METRICS_BEST_PRACTICES.md
│
├── system/                       # System contracts & integration
│   ├── CONTRACTS.md              # API contracts, naming conventions
│   ├── INTEGRATION.md            # Frontend ↔ Backend integration rules
│   ├── DEPLOYMENT_CICD_APPROACHES.md # CI/CD strategies
│   ├── ML_DEPENDENCIES_ARCHITECTURE.md # ML deps handling
│   ├── CICD_AUDIT.md             # CI/CD audit & status
│   ├── SIMULATION_SYSTEM.md      # Simulation system docs
│   └── LOGGING_STRATEGY.md       # Logging implementation
│
├── roadmap/                      # Planning & roadmaps
│   ├── README.md                 # Roadmap rules
│   ├── NEXT_STEPS.md             # Current priorities
│   ├── DEMO_WOW_FEATURES.md      # High-impact demo features
│   ├── backend/                  # Backend roadmaps
│   ├── features/                 # Feature plans
│   └── product/                  # User stories, workflows
│
├── reference/                    # Reference docs
│   ├── M5_DATA_MAPPING.md
│   └── SECURITY_AUDIT_REPORT.md
│
├── standards/
│   └── STANDARDS.md              # Project standards
│
└── archive/                      # Historical docs
    └── README.md                 # Archive index
```

---

## Setup

### Quick Setup (Recommended)

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

See [DEVELOPMENT_SETUP.md](setup/DEVELOPMENT_SETUP.md) for Docker and local development options.

---

## Key Topics

### Backend
- [API Reference](backend/API_REFERENCE.md) - All endpoints
- [Architecture](backend/ARCHITECTURE.md) - System design
- [Structure Analysis](backend/STRUCTURE_ANALYSIS.md) - Where things live

### Forecasting
- [Forecasting README](backend/forecasting/README.md) - Module status
- [Methods](backend/forecasting/METHODS.md) - Implementation details
- [Forecasting Roadmap](roadmap/backend/FORECASTING_ROADMAP.md) - Roadmap

### System
- [Contracts](system/CONTRACTS.md) - Naming conventions, auth patterns
- [Integration](system/INTEGRATION.md) - Frontend ↔ Backend rules

### Data
- [Data Model](DATA_MODEL.md) - Schema and relationships
- [M5 Data Mapping](reference/M5_DATA_MAPPING.md) - Dataset mapping

---

## Running

### Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

### Tests

```bash
cd backend
uv run pytest tests/ -v
```

---

**Note:** Frontend documentation is maintained in the [frontend repository](https://github.com/Suko/forecaster-enterprise-frontend).
