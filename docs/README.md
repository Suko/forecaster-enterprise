# Forecaster Enterprise Documentation

**Status:** Phase 2B Complete ✅ | Production Readiness: 85%

---

## Quick Start

| Document | Purpose |
|----------|---------|
| [Backend Architecture](backend/ARCHITECTURE.md) | System architecture |
| [Forecasting Module](backend/forecasting/README.md) | 🎯 **Module status & progress** |
| [Standards](standards/STANDARDS.md) | Project standards |
| [System Contracts](system/CONTRACTS.md) | Auth, security, data contracts |

---

## Documentation Structure

```
docs/
├── README.md                    # This file
├── SECURITY_AUDIT_REPORT.md     # Security audit results
│
├── backend/
│   ├── ARCHITECTURE.md          # Backend architecture
│   ├── STRUCTURE_ANALYSIS.md    # Code structure
│   ├── ROADMAP.md               # Development roadmap & todos
│   └── forecasting/             # Forecasting module
│       ├── README.md            # Module status & progress
│       └── METHODS.md           # Method implementations
│
├── standards/
│   └── STANDARDS.md             # Consolidated standards
│
├── system/
│   └── CONTRACTS.md             # System contracts (auth, security)
│
└── reports/                     # Validation reports (keep)
```

---

## By Topic

### Forecasting

| Document | Purpose |
|----------|---------|
| [Module README](backend/forecasting/README.md) | Status, progress, routing |
| [Methods](backend/forecasting/METHODS.md) | Method implementations |

### Backend

| Document | Purpose |
|----------|---------|
| [Architecture](backend/ARCHITECTURE.md) | System architecture |
| [Structure](backend/STRUCTURE_ANALYSIS.md) | Code structure analysis |
| [Roadmap](backend/ROADMAP.md) | Development roadmap & todos |
| [Roadmap](backend/ROADMAP.md) | Development roadmap & todos |

### Standards & Contracts

| Document | Purpose |
|----------|---------|
| [Standards](standards/STANDARDS.md) | Forecasting, testing, evaluation |
| [Contracts](system/CONTRACTS.md) | Auth, security, data |

---

## Development

### Running Backend

```bash
cd backend
uv run uvicorn main:app --reload --port 8000
```

### Running Tests

```bash
cd backend && uv run pytest tests/
```

### Key Scripts

```bash
# Setup demo client
python backend/scripts/setup_demo_client.py

# Import CSV data
python backend/scripts/import_csv_to_ts_demand_daily.py --csv <path> --client-id <uuid>

# Validate method routing
python backend/scripts/validate_method_routing.py
```

---

## Current Status

| Component | Status |
|-----------|--------|
| Chronos-2 | ✅ Active |
| SBA (Lumpy) | ✅ Active |
| Croston (Intermittent) | ✅ Ready |
| Min/Max (C-Z) | ✅ Ready |
| Method Routing | ✅ 100% correct |
| Security | ✅ 100% audit passed |
| Integration Tests | ✅ 100% passing |

---

*Last updated: 2025-12-09*
