# Forecasting System - Quick Reference

**Status:** ✅ Phase 1 Complete  
**Last Updated:** 2025-12-08

---

## Quick Navigation

| Topic | Document |
|-------|----------|
| **Architecture** | [ARCHITECTURE.md](ARCHITECTURE.md) |
| **API Endpoints** | [API_DESIGN.md](API_DESIGN.md) |
| **Data Models** | [DATA_MODELS.md](DATA_MODELS.md) |
| **Multi-Tenant** | [MULTI_TENANT_ARCHITECTURE.md](MULTI_TENANT_ARCHITECTURE.md) |
| **Authentication** | [SYSTEM_AUTHENTICATION.md](SYSTEM_AUTHENTICATION.md) |
| **Business Overview** | [BUSINESS_GUARANTEES.md](BUSINESS_GUARANTEES.md) |
| **Setup** | [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) |

---

## What's Implemented (Phase 1)

### ✅ Core Features
- **Forecasting Models**: Chronos-2 (primary) + MA7 (baseline)
- **Inventory Calculations**: APICS formulas (DIR, ROP, Safety Stock, etc.)
- **Quality Metrics**: MAPE, MAE, RMSE, Bias
- **API Endpoints**: 4 endpoints (forecast, inventory, actuals, quality)
- **Tests**: 33 passing tests

### ✅ Infrastructure
- **Database**: PostgreSQL (prod) + SQLite (tests)
- **Multi-Tenant**: Unified SaaS + on-premise architecture
- **Authentication**: JWT + Service API key
- **Data Isolation**: All queries filtered by `client_id`

---

## Phase 2 Roadmap

| Feature | Document |
|---------|----------|
| **Covariates** | [COVARIATES_ROADMAP.md](COVARIATES_ROADMAP.md) |
| **Advanced Features** | [EXPERT_ANALYSIS.md](EXPERT_ANALYSIS.md) |
| **Covariate Management** | [COVARIATE_MANAGEMENT.md](COVARIATE_MANAGEMENT.md) |

---

## API Quick Start

```bash
# Generate forecast (with JWT)
curl -X POST /api/forecast \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -d '{"item_ids": ["SKU001"], "prediction_length": 7}'

# Generate forecast (with Service API Key)
curl -X POST /api/forecast \
  -H "X-API-Key: <SERVICE_API_KEY>" \
  -d '{"item_ids": ["SKU001"], "prediction_length": 7, "client_id": "uuid"}'
```

---

## Key Files

```
backend/
├── api/forecast.py              # API endpoints
├── forecasting/
│   ├── core/models/base.py      # Model interface
│   ├── modes/ml/chronos2.py     # Chronos-2 model
│   ├── modes/statistical/       # MA7 model
│   ├── services/                # Business logic
│   └── applications/            # Inventory calculator
├── models/                      # Database models
└── tests/test_forecasting/      # Tests
```

---

## For More Details

- **Technical Deep Dive**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [API_DESIGN.md](API_DESIGN.md)
- **Non-Technical Overview**: [BUSINESS_GUARANTEES.md](BUSINESS_GUARANTEES.md)
