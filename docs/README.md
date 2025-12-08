# Forecaster Enterprise Documentation

## Quick Start

**Start here:**
- 🎯 [**Current Status**](forecasting/CURRENT_STATUS.md) - Phase 1 status and what works
- ⭐ [**MVP Guide**](forecasting/MVP_UNIFIED.md) - Implementation details

**For non-technical readers:**
- 💼 [**Business Guarantees**](forecasting/BUSINESS_GUARANTEES.md) - What the system guarantees

---

## Documentation Structure

```
docs/
├── README.md                    # This file
├── AUTH_SETUP.md                # Authentication setup
├── SECURITY_AUDIT_REPORT.md     # Security audit
│
├── backend/
│   ├── STRUCTURE_ANALYSIS.md    # Backend architecture
│   └── TESTING.md               # Testing guidelines
│
└── forecasting/                 # Forecasting module (17 files)
    │
    ├── Essential (7 files):
    │   ├── CURRENT_STATUS.md        # 🎯 START HERE
    │   ├── MVP_UNIFIED.md           # ⭐ Implementation guide
    │   ├── ARCHITECTURE.md          # System architecture
    │   ├── DATA_MODELS.md           # Database schemas
    │   ├── TS_DEMAND_DAILY_SCHEMA.md # Core data model
    │   ├── INTEGRATION.md           # Backend integration
    │   └── BUSINESS_GUARANTEES.md   # 💼 Non-technical summary
    │
    ├── Authentication (2 files):
    │   ├── MULTI_TENANT_ARCHITECTURE.md  # Multi-tenant design
    │   └── SYSTEM_AUTHENTICATION.md      # Service API key auth
    │
    └── Reference (5 files):
        ├── INDUSTRY_STANDARDS.md    # Formula reference
        ├── ENVIRONMENT_VARIABLES.md # Environment config
        ├── TESTING_STRATEGY.md      # Testing approach
        ├── TEST_DATA_IMPORT_FLOW.md # CSV import docs
        ├── API_DESIGN.md            # Phase 2+ API design
        ├── EXPERT_ANALYSIS.md       # Future roadmap
        └── COVARIATES_ROADMAP.md    # Phase 2 plan
```

---

## By Topic

### Forecasting

| Document | Purpose |
|----------|---------|
| [Current Status](forecasting/CURRENT_STATUS.md) | 🎯 What's done, what's next |
| [MVP Guide](forecasting/MVP_UNIFIED.md) | ⭐ Primary implementation reference |
| [Architecture](forecasting/ARCHITECTURE.md) | System design |
| [Data Models](forecasting/DATA_MODELS.md) | Database schemas |
| [ts_demand_daily Schema](forecasting/TS_DEMAND_DAILY_SCHEMA.md) | Core data model |
| [Integration](forecasting/INTEGRATION.md) | Backend integration |
| [Industry Standards](forecasting/INDUSTRY_STANDARDS.md) | MAPE, MAE, Safety Stock formulas |

### Authentication & Security

| Document | Purpose |
|----------|---------|
| [Auth Setup](AUTH_SETUP.md) | JWT authentication |
| [Multi-Tenant](forecasting/MULTI_TENANT_ARCHITECTURE.md) | SaaS + On-Premise design |
| [System Auth](forecasting/SYSTEM_AUTHENTICATION.md) | Service API key for automation |
| [Environment Variables](forecasting/ENVIRONMENT_VARIABLES.md) | Configuration reference |
| [Security Audit](SECURITY_AUDIT_REPORT.md) | Security review |

### Testing & Development

| Document | Purpose |
|----------|---------|
| [Testing Strategy](forecasting/TESTING_STRATEGY.md) | How to test |
| [Test Data Import](forecasting/TEST_DATA_IMPORT_FLOW.md) | CSV import for dev |
| [Backend Testing](backend/TESTING.md) | Backend test guide |

### Future / Phase 2+

| Document | Purpose |
|----------|---------|
| [Covariates Roadmap](forecasting/COVARIATES_ROADMAP.md) | Phase 2 plan |
| [Expert Analysis](forecasting/EXPERT_ANALYSIS.md) | Long-term roadmap |
| [API Design](forecasting/API_DESIGN.md) | Future API expansion |

### Non-Technical

| Document | Purpose |
|----------|---------|
| [Business Guarantees](forecasting/BUSINESS_GUARANTEES.md) | 💼 What system guarantees |

---

## Development Scripts

Located in `backend/scripts/`:

```bash
# Setup demo client with test data
python backend/scripts/setup_demo_client.py

# Import CSV to database
python backend/scripts/import_csv_to_ts_demand_daily.py --csv <path> --client-id <uuid>

# Run integration tests
python backend/scripts/test_integration.py
```

See [scripts/README.md](../backend/scripts/README.md) for details.

---

**Status:** Phase 1 Complete ✅ | Ready for Phase 2
