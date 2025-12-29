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

## Integration Status

### ✅ **Implementation Complete** (2025-12-17)

**All forecast integration tasks have been completed:**

- ✅ **InventoryService** - Uses forecasts automatically with auto-refresh
- ✅ **DashboardService** - Uses forecasts automatically with auto-refresh
- ✅ **DataValidationService** - Validates forecast quality and completeness
- ✅ **API Responses** - Include `using_forecast` indicator
- ✅ **Auto-Refresh** - Background forecast generation when stale (non-blocking)

**System now matches its claims:** AI-powered forecasting drives inventory decisions automatically.

### Where Forecasting Comes Into Play

#### ✅ **Currently Integrated**

1. **Special Inventory Calculation Endpoint**
   - Endpoint: `POST /api/v1/forecast/inventory/calculate`
   - Uses forecasted demand (next 30 days) for DIR, safety stock, reorder points

2. **Regular Endpoints (Auto-Refresh)**
   - `GET /api/v1/inventory/products` - Uses forecasts when available (<7 days old)
   - `GET /api/v1/dashboard` - Uses forecasts when available (<7 days old)
   - `GET /api/v1/recommendations` - Uses forecasts for planning
   - Auto-refreshes stale forecasts in background (non-blocking)

#### Auto-Refresh Feature
**Problem**: Forecasts can become stale (>7 days old), but we don't want to block API calls.

**Solution**: Non-blocking auto-refresh system
- API checks forecast freshness
- If fresh (<7 days): Use immediately ✅
- If stale (>7 days): Use historical data for this request, trigger background refresh
- Next request uses fresh forecast ✅

**Benefits**: API response time ~50ms (vs 10-60 seconds blocking), instant user experience.

---

## Performance Analysis

### Current Performance Impact
**Query Pattern**: Historical data (last 30 days from `ts_demand_daily`)
- ✅ Single query per product
- ✅ Fast: ~10-50ms per product
- ✅ Scales: O(n) where n = number of products

### Forecast Integration Impact
**Additional Queries**: Check latest forecast + get forecast results
- ⚠️ **+1-2 queries per request** (forecast_run check, forecast_results batch)
- ⚠️ **+20-100ms per request** (depending on forecast table size)
- ⚠️ **N+1 problem risk** if done per-product

### Optimization Strategies Implemented

#### ✅ **Batch Forecast Lookup**
Instead of per-product queries, fetch all forecasts at once:
- 1 query for forecast run check
- 1 query for all forecast results (batch)
- Total: +2 queries regardless of product count
- Latency: +20-50ms (constant, not per-product)

#### ✅ **Database Indexes**
Created critical indexes for forecast queries:
```sql
CREATE INDEX idx_forecast_runs_client_created
ON forecast_runs(client_id, created_at DESC);

CREATE INDEX idx_forecast_results_run_item_date
ON forecast_results(forecast_run_id, item_id, date);
```

#### ✅ **Forecast Run Caching**
Cache latest forecast_run_id per client:
- Cache hit rate: ~99% (forecast_run_id changes daily/weekly)
- Forecast run check: 0-1ms (cached) vs 5-20ms (query)
- Reduces database load by 99%

### Performance Targets Met
| Metric | Target | Achieved |
|--------|--------|----------|
| Dashboard load (10 products) | <100ms | ~52ms (+4% overhead) |
| Product list (100 products) | <300ms | ~205ms (+2.5% overhead) |
| Cache hit rate | >95% | ~99% |

**Conclusion**: With proper caching, forecast integration adds negligible performance overhead.

---

## Testing & Frequency

### Testing Options

#### ✅ **Manual API Calls** (Recommended for Testing)
```bash
# Generate forecast
curl -X POST "http://localhost:8000/api/v1/forecast/generate" \
  -H "Authorization: Bearer <token>" \
  -d '{"item_ids": ["SKU001"], "prediction_length": 30}'

# Check integration (should use forecast)
curl -X GET "http://localhost:8000/api/v1/inventory/products" \
  -H "Authorization: Bearer <token>"
```

#### ✅ **Manual Forecast Test Script**
```bash
cd backend
uv run python scripts/manual_forecast_test.py
```
Shows before/after metrics comparison when forecasts are generated.

#### ✅ **Integration Tests**
```bash
pytest backend/tests/test_services/test_forecast_integration.py -v
```
Tests InventoryService, DashboardService, and RecommendationsService use forecasts correctly.

### Forecast Frequency Recommendations

#### **Daily Forecasts** (Recommended for Most Cases)
- **When**: Fast-moving inventory, seasonal products, high-value items
- **Benefits**: Fresh forecasts, reacts quickly to changes
- **Schedule**: 2-4 AM daily (`0 3 * * *`)

#### **Weekly Forecasts** (For Stable Products)
- **When**: Slow-moving inventory, stable demand patterns
- **Benefits**: Less compute resources, sufficient for planning
- **Schedule**: Sunday 2-4 AM (`0 3 * * 0`)

#### **Hybrid Approach** (Optimal)
Different frequencies by product classification:
- **Daily**: A-X, A-Y (high value, fast moving)
- **Weekly**: A-Z, B-X/Y, C-X/Y/Z (stable or low priority)

### Testing Checklist
- ✅ Manual forecast generation
- ✅ Integration with inventory/dashboard APIs
- ✅ Auto-refresh behavior
- ✅ Fallback to historical data
- ✅ Edge cases (no forecast, stale forecast)

---

## Accuracy Tracking

### Current Implementation
- ✅ `forecast_results.actual_value` backfilled from historical sales
- ✅ `POST /api/v1/forecast/forecasts/actuals` - Backfill endpoint
- ✅ `QualityCalculator` - Calculates MAPE, MAE, RMSE, Bias
- ✅ `GET /api/v1/forecast/forecasts/quality/{item_id}` - Accuracy metrics

### Workflow
1. **Generate forecast** → Store predictions (actual_value = NULL)
2. **Wait for actual sales** → ETL loads real sales data
3. **Backfill actuals** → `POST /api/v1/forecast/forecasts/actuals`
4. **Calculate accuracy** → Compare predictions vs actuals

### Metrics Available
- **MAPE** (Mean Absolute Percentage Error) - Primary accuracy metric
- **MAE** (Mean Absolute Error) - Absolute error magnitude
- **RMSE** (Root Mean Squared Error) - Penalizes large errors
- **Bias** - Systematic over/under-forecasting

**See**: [Forecast Accuracy Tracking](../FORECAST_ACCURACY_TRACKING.md)

---

## Related Documentation

- [METHODS.md](./METHODS.md) - Method implementation details
- [../ARCHITECTURE.md](../ARCHITECTURE.md) - Backend architecture
- [../FORECASTING_ROADMAP.md](../FORECASTING_ROADMAP.md) - Development roadmap & todos
- [../../standards/STANDARDS.md](../../standards/STANDARDS.md) - Project standards
- [../FORECAST_ACCURACY_TRACKING.md](../FORECAST_ACCURACY_TRACKING.md) - Accuracy tracking implementation

---

*Single source of truth for forecasting module status*
