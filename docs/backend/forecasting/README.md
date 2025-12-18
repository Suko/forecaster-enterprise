# Forecasting Module

**Status:** Production Ready (85%)  
**Last Updated:** 2025-12-17

---

## Quick Status

| Phase | Status |
|-------|--------|
| Phase 1: Core Forecasting | ✅ Complete |
| Phase 2A: SKU Classification | ✅ Complete |
| Phase 2B: Specialized Methods | ✅ Complete |
| Production Readiness | 🚧 85% |
| Phase 3: Covariates | ⏳ Planned |

---

## Implemented Methods

| Method | Type | Use Case | Status |
|--------|------|----------|--------|
| **Chronos-2** | ML | Regular demand, high-value SKUs | ✅ Active |
| **SBA** | Statistical | Lumpy demand | ✅ Active |
| **Croston** | Statistical | Intermittent demand | ✅ Ready |
| **Min/Max** | Rules | C-Z SKUs (low value) | ✅ Ready |
| **MA7** | Statistical | Baseline, simple patterns | ✅ Active |

---

## Performance Metrics

### By Classification

| Classification | MAPE | Status |
|----------------|------|--------|
| A-X (Stable) | 17.1% | ✅ Within range (10-25%) |
| A-Y (Medium) | 111.9% | ⚠️ Below standard (20-40%) |
| A-Z (Variable) | 86.6% | ⚠️ Partial (30-60%) |
| Lumpy | 79.1% | ✅ Within range (50-90%) |

### Key Results

- **SBA Improvement:** 113.8% → 79.1% MAPE (34.7 point improvement)
- **Routing Correctness:** 100% (40/40 SKUs)
- **Overall Within Range:** 60% (24/40 SKUs)

---

## Method Routing

| Classification | Pattern | Routes To |
|----------------|---------|-----------|
| A-X, A-Y, A-Z | Regular | chronos-2 |
| Any | Lumpy | sba |
| Any | Intermittent | croston |
| C-Z | Any | min_max |
| C-X, C-Y | Regular | statistical_ma7 |

---

## Code Structure

```
backend/forecasting/
├── applications/           # Application layer
│   └── inventory/         # Inventory forecasting
├── core/                   # Core utilities
│   ├── models/            # Base model classes
│   └── tenant_manager.py  # Multi-tenant management
├── modes/                  # Forecasting methods
│   ├── factory.py         # Method factory
│   ├── ml/                # ML methods (chronos2)
│   └── statistical/       # Statistical methods
├── services/               # Domain services
│   ├── forecast_service.py
│   ├── data_access.py
│   ├── quality_calculator.py
│   └── sku_classifier.py
└── validation/             # Data validation
```

---

## End-to-End Flow (Current Implementation)

### 1) Forecast generation (API)
- Endpoint: `POST /api/v1/forecast` (`backend/api/forecast.py`)
- Auth intent: JWT (user calls) or `X-API-Key` + body `client_id` (system calls)
- Orchestrator: `ForecastService.generate_forecast()` (`backend/forecasting/services/forecast_service.py`)

### 2) Data loading (training data)
- Source of truth: `ts_demand_daily` (filtered by `client_id`)
- Loader: `DataAccess.fetch_historical_data()` (`backend/forecasting/services/data_access.py`)
- Output schema (DataFrame): `id`, `timestamp`, `target` (+ optional covariates)

### 3) Validation + method routing
- Input validation/cleanup: `DataValidator.validate_context_data()` (`backend/forecasting/services/data_validator.py`)
  - Fills missing dates (daily frequency) and fills NaNs (0 for demand)
- SKU classification: `SKUClassifier.classify_sku()` (`backend/forecasting/services/sku_classifier.py`)
  - Persists to `sku_classifications` for later retrieval (`backend/models/forecast.py`)
- Method selection:
  - Uses classification’s `recommended_method`, mapped to implemented model IDs
  - Executes the selected method and (optionally) `statistical_ma7` baseline

### 4) Model execution
- Model instantiation: `ModelFactory.create_model()` (`backend/forecasting/modes/factory.py`)
- Per-item prediction: `BaseForecastModel.predict()` implementations under `backend/forecasting/modes/`
- Output validation: `DataValidator.validate_predictions()` (`backend/forecasting/services/data_validator.py`)

### 5) Persistence + response
- Run metadata: `forecast_runs`
- Daily predictions: `forecast_results`
- API response: `ForecastService.get_forecast_results()` formats DB rows for `ForecastResponse`

### 6) Downstream usage (inventory & dashboard)
- Product list and dashboard prefer forecasts if “fresh” (<7 days), otherwise fall back to historical demand and trigger a non-blocking background refresh:
  - `backend/services/inventory_service.py`
  - `backend/services/dashboard_service.py`

---

## P0 Hotfixes (Completed)

### 1) Forecast persistence/return path
`ForecastService.generate_forecast()` now commits and returns on the success path, so `forecast_runs`/`forecast_results` persist reliably.

### 2) Forecast endpoint auth/tenant isolation
`get_client_id_from_request_or_token()` now ignores request-body `client_id` for JWT calls and only accepts it when a valid `X-API-Key` is present.

---

## Next Actions

### Production Readiness
- ✅ Integration Testing (100%)
- ✅ Multi-Client Testing (100%)
- ✅ Performance Monitoring (100%)
- ✅ Security Audit (100%)
- ⏳ Deployment Preparation

### Future (Phase 3)
- Covariates (promotions, holidays)
- Hierarchical forecasting
- Advanced ML models (TimesFM, Moirai)

---

## Known Issues

### A-Y Performance
- **Problem:** 111.9% MAPE (expected: 20-40%)
- **Investigation:** Chronos-2 is 43.2 points better than MA7 but both struggle
- **Conclusion:** These SKUs are inherently difficult; covariates may help

### Blocking Implementation Issues
- ✅ Forecast persistence/return path: fixed
- ✅ Auth/tenant isolation: fixed

---

## Related Documentation

- [METHODS.md](./METHODS.md) - Method implementation details
- [../ARCHITECTURE.md](../ARCHITECTURE.md) - Backend architecture
- [../FORECASTING_ROADMAP.md](../FORECASTING_ROADMAP.md) - Development roadmap & todos
- [../../standards/STANDARDS.md](../../standards/STANDARDS.md) - Project standards

---

*Single source of truth for forecasting module status*
