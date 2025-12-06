# Testing Strategy for Forecasting Module

**Status:** ✅ Test Infrastructure Ready  
**Last Updated:** 2025-12-06

---

## Overview

We have synthetic test data that's perfect for testing, even though the structure differs slightly from production. This document outlines our testing strategy.

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
- In-memory SQLite database (fast tests)
- Automatic table creation/cleanup
- Async session fixtures

**Usage:**
```python
@pytest.mark.asyncio
async def test_forecast_service(db_session):
    service = ForecastService(db_session)
    # Test with in-memory database
```

### 3. Test Fixtures

**Available Fixtures:**
- `db_session`: Async database session
- `test_data_loader`: TestDataLoader instance
- `sample_item_data`: Pre-loaded SKU001 data
- `sample_item_ids`: List of available item IDs

---

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   ├── __init__.py
│   └── test_data_loader.py        # CSV data loader
├── test_forecasting/
│   ├── __init__.py
│   ├── test_models.py            # Model unit tests
│   ├── test_inventory_calculator.py
│   ├── test_quality_calculator.py
│   └── test_data_loader.py
└── test_api/
    └── test_forecast_api.py      # API integration tests
```

---

## Testing Levels

### 1. Unit Tests (Fast, Isolated)

**What to Test:**
- ✅ Model calculations (MovingAverageModel)
- ✅ Inventory formulas (InventoryCalculator)
- ✅ Quality metrics (QualityCalculator)
- ✅ Data transformation (TestDataLoader)

**Example:**
```python
def test_calculate_dir():
    dir_value = InventoryCalculator.calculate_days_of_inventory_remaining(
        current_stock=500,
        avg_daily_demand=100,
    )
    assert dir_value == 5.0
```

### 2. Integration Tests (Service Layer)

**What to Test:**
- ✅ ForecastService with real models
- ✅ Database storage and retrieval
- ✅ Model factory
- ✅ End-to-end forecast generation

**Example:**
```python
@pytest.mark.asyncio
async def test_forecast_service_generation(db_session, sample_item_data):
    service = ForecastService(db_session)
    forecast_run = await service.generate_forecast(
        client_id="test_client",
        user_id="test_user",
        item_ids=["SKU001"],
        prediction_length=7,
    )
    assert forecast_run.status == "completed"
```

### 3. API Integration Tests (Full Stack)

**What to Test:**
- ✅ API endpoint structure
- ✅ Request/response validation
- ✅ Authentication
- ✅ Error handling

**Example:**
```python
def test_forecast_endpoint(client, auth_token):
    response = client.post(
        "/api/v1/forecast",
        json={"item_ids": ["SKU001"], "prediction_length": 30},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
```

---

## Test Data Transformation

### CSV Format → Chronos-2 Format

**Input (CSV):**
```
date, sku, sales_qty, promo_flag, holiday_flag, is_weekend
2023-01-01, SKU001, 245, 0, 1, 1
```

**Output (Chronos-2):**
```
id, timestamp, target, promo_flag, holiday_flag, is_weekend
SKU001, 2023-01-01, 245, 0, 1, 1
```

**Transformation Logic:**
```python
# In TestDataLoader.get_item_data()
result_df['id'] = item_id
result_df['timestamp'] = item_df['date']
result_df['target'] = item_df['sales_qty']  # or 'units_sold' in production
result_df['promo_flag'] = item_df['promo_flag'].astype(int)
# ... other covariates
```

---

## Running Tests

### Run All Tests
```bash
cd backend
pytest
```

### Run Specific Test File
```bash
pytest tests/test_forecasting/test_models.py
```

### Run with Coverage
```bash
pytest --cov=forecasting --cov-report=html
```

### Run Fast Tests Only (Unit Tests)
```bash
pytest -m "not integration"
```

---

## Test Data Coverage

### What the Test Data Provides

| Feature | Test Data | Production |
|---------|-----------|------------|
| **Historical Data** | ✅ 2 years daily | ✅ From ETL |
| **Multiple Items** | ✅ SKU001-SKU020 | ✅ All items |
| **Covariates** | ✅ promo, holiday, weekend | ✅ From ETL |
| **Date Range** | ✅ 2023-2024 | ✅ Current |
| **Store/Location** | ✅ store_id | ✅ location_id |

### What's Different (But OK for Testing)

| Aspect | Test Data | Production | Impact |
|--------|-----------|------------|--------|
| **Column Names** | `sku`, `sales_qty` | `item_id`, `units_sold` | ✅ Handled by loader |
| **Store vs Location** | `store_id` | `location_id` | ✅ Optional in MVP |
| **Client ID** | Not in CSV | `client_id` | ✅ Can mock for tests |

---

## Mocking Strategy

### For Unit Tests

**Mock External Dependencies:**
- Chronos-2 model (don't load real model in unit tests)
- Database queries (use fixtures)
- External APIs

**Example:**
```python
@pytest.fixture
def mock_chronos_model():
    # Mock Chronos2Model to avoid loading real model
    pass
```

### For Integration Tests

**Use Real Components:**
- Real database (in-memory SQLite)
- Real models (if fast enough)
- Real data transformations

---

## Test Scenarios

### 1. Happy Path
- ✅ Generate forecast for item with good history
- ✅ Calculate inventory metrics
- ✅ Backfill actuals and view quality

### 2. Edge Cases
- ⚠️ Item with insufficient history (< 7 days)
- ⚠️ Item with no sales (all zeros)
- ⚠️ Item with missing data
- ⚠️ Invalid input parameters

### 3. Error Handling
- ⚠️ Model initialization failure
- ⚠️ Database connection errors
- ⚠️ Invalid item IDs
- ⚠️ Missing required fields

---

## Continuous Testing

### Pre-Commit Hooks
```bash
# Run fast tests before commit
pytest tests/test_forecasting/test_models.py -v
```

### CI/CD Pipeline
```yaml
# Run all tests
pytest --cov=forecasting --cov-report=xml
```

---

## Test Data Maintenance

### Adding New Test Data

1. Add CSV file to `data/sintetic_data/`
2. Update `TestDataLoader` if format changes
3. Add tests for new data format

### Updating Test Data

- Keep test data in sync with expected schema
- Document any format changes
- Update transformation logic if needed

---

## Best Practices

1. **Fast Tests First**: Unit tests should run in < 1 second
2. **Isolated Tests**: Each test should be independent
3. **Use Fixtures**: Reuse test data and setup
4. **Mock External**: Don't load real ML models in unit tests
5. **Real Data**: Use real test data for integration tests
6. **Clear Names**: Test names should describe what they test

---

## Next Steps

1. ✅ Test infrastructure created
2. ✅ TestDataLoader implemented
3. ⏳ Complete unit tests for all calculators
4. ⏳ Add integration tests for ForecastService
5. ⏳ Add API integration tests with authentication
6. ⏳ Add performance tests (if needed)

---

## References

- Test Data: `data/sintetic_data/synthetic_ecom_chronos2_demo.csv`
- Test Loader: `tests/fixtures/test_data_loader.py`
- Pytest Docs: https://docs.pytest.org/

