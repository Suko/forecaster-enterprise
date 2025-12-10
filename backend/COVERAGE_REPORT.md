# Test Coverage Report

**Generated:** $(date)  
**Coverage Tool:** pytest-cov with coverage.py

## Overall Coverage

**Total Coverage: 59%** (3913 total lines, 1620 missed)

## Coverage by Module

### API Layer (`api/`)
- `api/inventory.py`: Coverage needed
- `api/orders.py`: Coverage needed
- `api/purchase_orders.py`: Coverage needed
- `api/settings.py`: Coverage needed
- `api/etl.py`: 0% (not yet tested)

### Service Layer (`services/`)
- `services/metrics_service.py`: **84%** ✅
- `services/inventory_service.py`: **65%** ✅
- `services/cart_service.py`: **59%** ⚠️
- `services/recommendation_service.py`: **49%** ⚠️
- `services/purchase_order_service.py`: **28%** ⚠️
- `services/dashboard_service.py`: **31%** ⚠️
- `services/etl/etl_service.py`: **12%** ⚠️
- `services/etl/connectors.py`: **26%** ⚠️

### Model Layer (`models/`)
- `models/product.py`: **100%** ✅
- `models/stock.py`: **100%** ✅
- `models/supplier.py`: **100%** ✅
- `models/location.py`: **100%** ✅
- `models/product_supplier.py`: **100%** ✅
- `models/settings.py`: **100%** ✅
- `models/inventory_metrics.py`: **100%** ✅
- `models/purchase_order.py`: **100%** ✅
- `models/order_cart.py`: **100%** ✅
- `models/client.py`: **100%** ✅
- `models/user.py`: **100%** ✅
- `models/database.py`: **65%** ⚠️

### Schema Layer (`schemas/`)
- `schemas/inventory.py`: **100%** ✅
- `schemas/order.py`: **100%** ✅
- `schemas/settings.py`: **100%** ✅
- `schemas/etl.py`: **100%** ✅
- `schemas/auth.py`: **100%** ✅
- `schemas/forecast.py`: **100%** ✅

## Coverage Goals

### Current Status
- ✅ **Models**: 100% coverage (all new models fully tested)
- ✅ **Schemas**: 100% coverage (all new schemas fully tested)
- ⚠️ **Services**: 59% average (needs improvement)
- ⚠️ **APIs**: Coverage varies (needs improvement)

### Target Goals
- **Models**: 100% ✅ (Achieved)
- **Schemas**: 100% ✅ (Achieved)
- **Services**: >80% (Current: 59%)
- **APIs**: >80% (Current: varies)

## Areas Needing Improvement

### High Priority
1. **ETL Service** (12% coverage)
   - `services/etl/etl_service.py`: Only 12% covered
   - Needs comprehensive testing for sync operations

2. **Purchase Order Service** (28% coverage)
   - `services/purchase_order_service.py`: Only 28% covered
   - Needs tests for all PO operations

3. **Dashboard Service** (31% coverage)
   - `services/dashboard_service.py`: Only 31% covered
   - Needs tests for KPI calculations

### Medium Priority
1. **Cart Service** (59% coverage)
   - Some edge cases not covered
   - MOQ validation scenarios

2. **Recommendations Service** (49% coverage)
   - Recommendation generation logic
   - Role-based filtering

3. **API Endpoints**
   - Some endpoints have partial coverage
   - Error handling scenarios

## How to View Coverage Reports

### HTML Report (Recommended)
```bash
cd forecaster_enterprise/backend
open htmlcov/index.html
# Or on Linux:
# xdg-open htmlcov/index.html
```

### Terminal Report
```bash
cd forecaster_enterprise/backend
uv run pytest --cov=. --cov-report=term tests/
```

### XML Report (for CI/CD)
```bash
cd forecaster_enterprise/backend
uv run pytest --cov=. --cov-report=xml tests/
# Report saved to coverage.xml
```

## Running Coverage

### All Tests
```bash
uv run pytest --cov=. --cov-report=term --cov-report=html tests/
```

### Specific Test Files
```bash
uv run pytest --cov=. --cov-report=term tests/test_api/test_inventory_api.py
```

### With Missing Lines
```bash
uv run pytest --cov=. --cov-report=term-missing tests/
```

## Coverage Configuration

Coverage is configured in `pyproject.toml`:
- Excludes migrations, tests, and virtual environments
- Source directory: `.` (current directory)
- Reports: terminal, HTML, and XML

## Next Steps

1. ✅ Generate coverage reports
2. ⏳ Fix failing tests
3. ⏳ Increase service layer coverage to >80%
4. ⏳ Add ETL service tests
5. ⏳ Add API endpoint error handling tests
6. ⏳ Set up coverage thresholds in CI/CD

