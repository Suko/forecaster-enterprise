# Testing Strategy for Forecasting Module

**Status:** ✅ Test Infrastructure Ready  
**Last Updated:** 2025-12-06

---

## Overview

We have synthetic test data that's perfect for testing, even though the structure differs slightly from production. This document outlines our testing strategy.

---

## Test Database Strategy

### Two Testing Modes

We support **two database backends** for testing:

#### 1. **SQLite (Default)** - Fast Unit Tests
- **When:** Default for all tests
- **Speed:** Very fast (in-memory)
- **Setup:** No setup required
- **Use Case:** Unit tests, fast iteration

#### 2. **PostgreSQL** - Production-Like Integration Tests
- **When:** Set `TEST_POSTGRES=true` environment variable
- **Speed:** Slower (real database)
- **Setup:** Requires PostgreSQL running
- **Use Case:** Integration tests, catching PostgreSQL-specific issues

### How to Use

**Default (SQLite):**
```bash
# Fast tests with SQLite (default)
pytest tests/
```

**PostgreSQL:**
```bash
# Integration tests with PostgreSQL
TEST_POSTGRES=true pytest tests/

# Or with custom database URL
TEST_POSTGRES=true TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test_db pytest tests/
```

### When to Use Each

| Test Type | Database | Why |
|-----------|----------|-----|
| **Unit Tests** | SQLite | Fast, no setup, tests logic |
| **Integration Tests** | PostgreSQL | Real database, catches DB-specific issues |
| **CI/CD** | Both | SQLite for speed, PostgreSQL for accuracy |

### PostgreSQL Test Setup

**Prerequisites:**
```bash
# Create test database
createdb forecaster_enterprise_test

# Or via psql
psql -U postgres -c "CREATE DATABASE forecaster_enterprise_test;"
```

**Environment Variables:**
```bash
export TEST_POSTGRES=true
export TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/forecaster_enterprise_test
```

---

## Test Data

### Source: `synthetic_ecom_chronos2_demo.csv`

**Location:** `/Users/mihapro/Development/ecommerce/forecaster_enterprise/data/sintetic_data/`

**Structure:**
```
date, store_id, sku, category, sales_qty, price, base_price, 
inventory_level, promo_flag, holiday_flag, marketing_index, 
is_weekend, lead_time_days
```

**Characteristics:**
- ✅ **14,621 rows** (about 2 years of daily data)
- ✅ **Multiple SKUs** (SKU001, SKU002, etc.)
- ✅ **Multiple stores** (STORE001, etc.)
- ✅ **Covariates included**: promo_flag, holiday_flag, is_weekend, marketing_index
- ✅ **Date range**: 2023-01-01 to 2024-12-31

**Differences from Production:**
- Production: `ts_demand_daily` table with `client_id`, `item_id`, `date_local`, `units_sold`
- Test data: CSV with `store_id`, `sku`, `date`, `sales_qty`
- **Solution**: Use `TestDataLoader` to transform test data to expected format

---

## Test Infrastructure

### 1. Test Data Loader

**Location:** `tests/fixtures/test_data_loader.py`

**Purpose:** Load and transform CSV test data to Chronos-2 format

**Features:**
- Loads CSV file
- Filters by item_id, date range, store
- Transforms to format: `id`, `timestamp`, `target`, [covariates]
- Provides helper methods for test data access

**Usage:**
```python
from tests.fixtures.test_data_loader import TestDataLoader

loader = TestDataLoader()
item_data = loader.get_item_data("SKU001")
# Returns DataFrame with: id, timestamp, target, promo_flag, holiday_flag, etc.
```

### 2. Test Database

**Location:** `tests/conftest.py`

**Features:**
- **Auto-detects** database backend (SQLite or PostgreSQL)
- Automatic table creation/cleanup
- Async session fixtures
- Works with both SQLite and PostgreSQL

**Usage:**
```python
@pytest.mark.asyncio
async def test_forecast_service(db_session):
    service = ForecastService(db_session)
    # Works with both SQLite and PostgreSQL
```

### 3. Test Fixtures

**Available Fixtures:**
- `db_session`: Async database session (SQLite or PostgreSQL)
- `test_data_loader`: TestDataLoader instance
- `sample_item_data`: Pre-loaded SKU001 data
- `sample_item_ids`: List of available item IDs

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (supports both DBs)
├── fixtures/
│   ├── __init__.py
│   └── test_data_loader.py        # CSV data loader
├── test_forecasting/
│   ├── __init__.py
│   ├── test_data_loader.py        # Test data loader tests
│   ├── test_models.py             # Model tests
│   ├── test_inventory_calculator.py  # Inventory formula tests
│   ├── test_quality_calculator.py    # Quality metric tests
│   └── test_forecast_service.py    # Service integration tests
└── test_api/
    └── test_forecast_api.py        # API endpoint tests
```

---

## Running Tests

### Quick Tests (SQLite - Default)
```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_forecasting/test_models.py

# With verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=forecasting --cov-report=html
```

### Integration Tests (PostgreSQL)
```bash
# Run all tests with PostgreSQL
TEST_POSTGRES=true pytest tests/

# Run specific test with PostgreSQL
TEST_POSTGRES=true pytest tests/test_forecasting/test_forecast_service.py -v

# With custom database
TEST_POSTGRES=true TEST_DATABASE_URL=postgresql://user:pass@localhost:5432/test_db pytest tests/
```

### CI/CD Strategy

**Recommended approach:**
1. **Fast feedback:** Run SQLite tests first (unit tests)
2. **Accuracy check:** Run PostgreSQL tests (integration tests)
3. **Both in CI:** Run both in parallel or sequentially

**Example CI config:**
```yaml
# .github/workflows/test.yml
- name: Run SQLite tests
  run: pytest tests/ -v

- name: Run PostgreSQL tests
  run: |
    TEST_POSTGRES=true pytest tests/ -v
  env:
    TEST_DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
```

---

## Test Coverage

### Current Coverage

- ✅ **Unit Tests:** Models, calculators, data loader
- ✅ **Integration Tests:** ForecastService end-to-end
- ✅ **API Tests:** Endpoint integration (in progress)

### What's Tested

1. **Data Loading**
   - CSV loading and transformation
   - Data filtering and formatting

2. **Forecasting Models**
   - MovingAverageModel (7-day)
   - ModelFactory
   - BaseForecastModel interface

3. **Inventory Calculations**
   - Days of Inventory Remaining (DIR)
   - Safety Stock
   - Reorder Point (ROP)
   - Recommended Order Quantity
   - Stockout Risk

4. **Quality Metrics**
   - MAPE (Mean Absolute Percentage Error)
   - MAE (Mean Absolute Error)
   - RMSE (Root Mean Squared Error)
   - Forecast Bias

5. **Service Integration**
   - ForecastService orchestration
   - Data access (database and test data)
   - Result storage and retrieval

---

## Best Practices

### 1. Use SQLite for Unit Tests
- Fast iteration
- No external dependencies
- Tests business logic

### 2. Use PostgreSQL for Integration Tests
- Before committing major changes
- In CI/CD pipeline
- When testing database-specific features

### 3. Test Data Isolation
- Each test gets a fresh database session
- Tables are created/dropped per test
- No data leakage between tests

### 4. Test Both Databases
- Run SQLite tests frequently (fast feedback)
- Run PostgreSQL tests before releases (accuracy)

---

## Troubleshooting

### PostgreSQL Tests Failing

**Issue:** Cannot connect to PostgreSQL
```bash
# Check PostgreSQL is running
pg_isready

# Check database exists
psql -U postgres -l | grep forecaster_enterprise_test

# Create database if missing
createdb forecaster_enterprise_test
```

**Issue:** Permission errors
```bash
# Grant permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE forecaster_enterprise_test TO postgres;"
```

### SQLite Tests Failing

**Issue:** Usually indicates a code problem (not database issue)
- Check test data is loading correctly
- Verify model definitions match database schema

---

## Summary

- ✅ **Default:** SQLite (fast, no setup)
- ✅ **Optional:** PostgreSQL (production-like, catches DB issues)
- ✅ **Best Practice:** Use both (SQLite for speed, PostgreSQL for accuracy)
- ✅ **CI/CD:** Run both in pipeline

**Quick Start:**
```bash
# Fast tests (SQLite)
pytest tests/

# Integration tests (PostgreSQL)
TEST_POSTGRES=true pytest tests/
```
