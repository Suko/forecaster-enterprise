# Forecaster Enterprise Documentation

---

## 📋 Documentation View Selector

**Quick Filter:** Jump to docs by your role or interest

| View | Key Documents |
|------|---------------|
| **👨‍💻 Developer** | [Quick Start](setup/QUICK_START.md) → [Next Steps](NEXT_STEPS.md) → [API Reference](backend/API_REFERENCE.md) → [Architecture](backend/ARCHITECTURE.md) |
| **📊 Product Manager** | [Next Steps](NEXT_STEPS.md) → [User Stories](USER_STORIES.md) → [Workflows](WORKFLOWS.md) → [Roadmaps (Archive)](archive/backend/BACKEND_ROADMAP.md) |
| **🔧 DevOps** | [Quick Start](setup/QUICK_START.md) → [Development Setup](setup/DEVELOPMENT_SETUP.md) → [ENV Management](setup/ENV_MANAGEMENT.md) → [Security Audit](reference/SECURITY_AUDIT_REPORT.md) |
| **📚 Reference** | [API Reference](backend/API_REFERENCE.md) → [Data Model](DATA_MODEL.md) → [System Contracts](system/CONTRACTS.md) → [Compatibility Audit](system/BACKEND_FRONTEND_COMPATIBILITY.md) → [Standards](standards/STANDARDS.md) |
| **🎯 Current Work** | [Next Steps](NEXT_STEPS.md) - 4-week development plan |

**Detailed View (Expandable Sections):**

<details>
<summary><strong>👨‍💻 For Developers</strong> - Setup, APIs, Architecture</summary>

**Getting Started:**
- [Quick Start](setup/QUICK_START.md) - One-command setup
- [Development Setup](setup/DEVELOPMENT_SETUP.md) - Docker & local development
- [Next Steps](NEXT_STEPS.md) - Current development priorities

**Backend:**
- [Backend Roadmap (Archive)](archive/backend/BACKEND_ROADMAP.md) - Historical implementation snapshot
- [API Reference](backend/API_REFERENCE.md) - All endpoints
- [Architecture](backend/ARCHITECTURE.md) - System design
- [System Contracts](system/CONTRACTS.md) - Naming conventions, patterns
- [Compatibility Audit](system/BACKEND_FRONTEND_COMPATIBILITY.md) - Current mismatches + decisions

**Frontend:**
- [Frontend Roadmap (Archive)](archive/frontend/FRONTEND_ROADMAP.md) - Historical MVP plan snapshot
- [Auth Best Practices](frontend/AUTH_BEST_PRACTICES.md) - Authentication patterns

**Data & Models:**
- [Data Model](DATA_MODEL.md) - Database schema
- [M5 Data Mapping](reference/M5_DATA_MAPPING.md) - Dataset mapping

</details>

<details>
<summary><strong>📊 For Product/Project Managers</strong> - Roadmaps, User Stories, Workflows</summary>

**Planning & Status:**
- [Next Steps](NEXT_STEPS.md) - Current development priorities (4-week plan)
- [Backend Roadmap (Archive)](archive/backend/BACKEND_ROADMAP.md) - Historical implementation snapshot
- [Frontend Roadmap (Archive)](archive/frontend/FRONTEND_ROADMAP.md) - Historical MVP plan snapshot

**Requirements:**
- [User Stories](USER_STORIES.md) - Feature requirements by stakeholder
- [Workflows](WORKFLOWS.md) - System workflows and decision loops

**Forecasting:**
- [Forecasting Roadmap](backend/FORECASTING_ROADMAP.md) - Forecasting module roadmap
- [Forecasting Methods](backend/forecasting/METHODS.md) - Method implementations

</details>

<details>
<summary><strong>🔧 For DevOps/Setup</strong> - Environment, Deployment, Configuration</summary>

**Setup:**
- [Quick Start](setup/QUICK_START.md) - One-command setup guide
- [Development Setup](setup/DEVELOPMENT_SETUP.md) - Docker & local development
- [Setup Script Guide](setup/SETUP_SCRIPT_GUIDE.md) - Detailed setup options
- [Environment Management](setup/ENV_MANAGEMENT.md) - Environment variables guide

**Data:**
- [Shared Test Data](setup/SHARED_TEST_DATA_SUPABASE.md) - Test data workflow
- [M5 Data Mapping](reference/M5_DATA_MAPPING.md) - Dataset mapping

**Security:**
- [Security Audit Report](reference/SECURITY_AUDIT_REPORT.md) - Security findings

</details>

<details>
<summary><strong>📚 Reference Documentation</strong> - APIs, Contracts, Standards</summary>

**APIs:**
- [API Reference](backend/API_REFERENCE.md) - All API endpoints
- [Backend Architecture](backend/ARCHITECTURE.md) - System design

**Standards:**
- [System Contracts](system/CONTRACTS.md) - Naming conventions, patterns
- [Standards](standards/STANDARDS.md) - Project standards

**Data:**
- [Data Model](DATA_MODEL.md) - Database schema and relationships
- [M5 Data Mapping](reference/M5_DATA_MAPPING.md) - How M5 dataset is mapped

**Guides:**
- [Supplier Management Guide](backend/SUPPLIER_MANAGEMENT_GUIDE.md) - MOQ, Lead Time
- [Forecasting Methods](backend/forecasting/METHODS.md) - Method implementations

</details>

<details>
<summary><strong>🎯 Current Work (Active Development)</strong> - What's being worked on now</summary>

**Active Priorities:**
- [Next Steps](NEXT_STEPS.md) - **Current 4-week development plan**
  - Week 1: Forecasting Hardening + Contract Alignment
  - Week 2: Empty State Handling
  - Week 3: Frontend Polish (optional)
  - Week 4: ETL Scheduling

**Status:**
- Backend MVP: ✅ Complete (Phases 1-4)
- Frontend MVP: ✅ ~87% Complete
- **Test Bed Feature:** ✅ Complete & Validated (2025-12-22)
- Next: Forecasting hardening + contract alignment

</details>

---

## Quick Links

| Document | Purpose |
|----------|---------|
| [Quick Start](setup/QUICK_START.md) | One-command setup guide |
| [Next Steps](NEXT_STEPS.md) | **Current development priorities** |
| [Demo Wow Features](DEMO_WOW_FEATURES.md) | **UI features for impressive demos** |
| [Development Setup](setup/DEVELOPMENT_SETUP.md) | Docker & local development |
| [Data Model](DATA_MODEL.md) | Database schema and sync strategy |
| [System Contracts](system/CONTRACTS.md) | Auth, security, naming conventions |
| [Logging Strategy](system/LOGGING_STRATEGY.md) | Logging implementation & monitoring |

---

## Documentation Structure

```
docs/
├── README.md                     # This file
├── NEXT_STEPS.md                 # Current development priorities
├── DATA_MODEL.md                 # Database schema
├── STOCK_AGGREGATION.md          # How stock is aggregated
├── DATA_REQUIREMENTS.md          # User-facing data requirements
├── DEMO_WOW_FEATURES.md          # High-impact demo features
├── USER_STORIES.md               # Feature requirements
├── WORKFLOWS.md                  # System workflows
│
├── setup/                        # Setup & development
│   ├── QUICK_START.md            # One-command setup
│   ├── DEVELOPMENT_SETUP.md      # Docker & local development
│   ├── SETUP_SCRIPT_GUIDE.md     # Detailed setup options
│   ├── ENV_MANAGEMENT.md         # Environment variables guide
│   └── SHARED_TEST_DATA_SUPABASE.md  # Shared test data workflow
│
├── features/                     # Feature planning
│   ├── EXPERIMENTS_PAGE_MIGRATION_PLAN.md # Test Bed & ROI Calculator (✅ Complete)
│   ├── TEST_BED_SYSTEM_VALIDATION.md # System validation explanation
│   ├── FORECAST_METHOD_COMPARISON_ANALYSIS.md # Design decisions
│   ├── WORKING_ORDERS_FEATURE.md # Working Orders feature plan
│   ├── INVENTORY_IMPROVEMENTS.md # Inventory page enhancements
│   ├── PURCHASE_ORDER_IMPROVEMENTS.md # Purchase Order UI/UX improvements
│   └── DASHBOARD_IMPROVEMENTS.md # Dashboard enhancements
│
├── reference/                    # Reference docs
│   ├── M5_DATA_MAPPING.md        # M5 dataset mapping
│   └── SECURITY_AUDIT_REPORT.md  # Security audit findings
│
├── backend/
│   ├── README.md                 # Backend quick reference
│   ├── ARCHITECTURE.md           # Backend architecture
│   ├── STRUCTURE_ANALYSIS.md     # Codebase map
│   ├── API_REFERENCE.md          # API endpoints
│   ├── BACKEND_ROADMAP.md        # (stub) archived snapshot
│   ├── FORECASTING_ROADMAP.md    # Forecasting module roadmap
│   ├── SUPPLIER_MANAGEMENT_GUIDE.md  # Supplier & MOQ management
│   ├── TEST_PLAN.md              # (stub) archived checklist
│   └── forecasting/
│       ├── README.md             # Forecasting module status
│       ├── METHODS.md            # Method implementations
│       ├── METRICS_BEST_PRACTICES.md # MAPE calculation guide
│       └── INVENTORY_ORDERING_GUIDE.md # Metric selection guide
│
├── frontend/
│   ├── AUTH_BEST_PRACTICES.md    # Auth implementation guide
│   └── FRONTEND_ROADMAP.md       # (stub) archived snapshot
│
├── standards/
│   └── STANDARDS.md              # Project standards
│
├── system/
│   ├── LOGGING_STRATEGY.md       # Logging strategy & implementation
│   ├── BACKEND_FRONTEND_COMPATIBILITY.md # Compatibility audit
│   └── CONTRACTS.md              # System contracts
│
└── archive/
    └── README.md                 # Archive policy + index
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

See [DEVELOPMENT_SETUP.md](setup/DEVELOPMENT_SETUP.md) for:
- Hybrid development (Docker DB + Local backend)
- Full Docker setup
- Environment configuration
- Troubleshooting

---

## Key Topics

### Backend
- [Architecture](backend/ARCHITECTURE.md) - System design
- [API Reference](backend/API_REFERENCE.md) - Endpoints
- [Backend Roadmap (Archive)](archive/backend/BACKEND_ROADMAP.md) - Historical implementation snapshot

### Forecasting
- [Module README](backend/forecasting/README.md) - Status and progress
- [Methods](backend/forecasting/METHODS.md) - Implementation details
- [Forecasting Roadmap](backend/FORECASTING_ROADMAP.md) - Forecasting module roadmap

### Supplier Management
- [Supplier Management Guide](backend/SUPPLIER_MANAGEMENT_GUIDE.md) - MOQ, Lead Time, Primary suppliers

### Data
- [Data Model](DATA_MODEL.md) - Schema and relationships
- [M5 Data Mapping](reference/M5_DATA_MAPPING.md) - How M5 dataset is mapped
- [System Contracts](system/CONTRACTS.md) - Naming conventions (`item_id`, not `sku`)

### Frontend
- [Frontend Roadmap (Archive)](archive/frontend/FRONTEND_ROADMAP.md) - Historical MVP plan snapshot
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
bun run dev
```

### Running Tests

```bash
cd backend
uv run pytest tests/ -v
uv run ruff check .
```

```bash
cd frontend
bun run lint
bun run format:check
```

---

*Last updated: 2025-12-22*
