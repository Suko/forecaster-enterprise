# Data Validation API

**Last Updated:** 2025-12-16  
**Status:** ✅ Implemented

## Overview

The Data Validation API provides comprehensive validation of:
- Raw data quality (dates, formats, ranges)
- Data completeness (orphaned records, missing relationships)
- Computed metrics accuracy (DIR, stockout risk, status, inventory value)
- Frontend-backend consistency (formatting, thresholds)

## Endpoints

### 1. Validate Data

**Endpoint:** `POST /api/v1/etl/validate`

**Authentication:** Required (JWT token)

**Request Body:**
```json
{
  "include_computed_metrics": true,
  "include_frontend_consistency": true
}
```

**Response:**
```json
{
  "client_id": "uuid",
  "validation_timestamp": "2025-01-27",
  "raw_data_quality": {
    "errors": [],
    "warnings": [],
    "info": []
  },
  "data_completeness": {
    "errors": [],
    "warnings": [],
    "info": []
  },
  "computed_metrics": {
    "errors": [],
    "warnings": [],
    "info": [],
    "sample_validations": [
      {
        "item_id": "SKU-001",
        "current_stock": 100,
        "calculated_metrics": {
          "dir": 45.5,
          "stockout_risk": 25.0,
          "status": "normal",
          "inventory_value": 5000.00
        },
        "validation_errors": [],
        "validation_warnings": []
      }
    ],
    "samples_checked": 10
  },
  "frontend_consistency": {
    "errors": [],
    "warnings": [],
    "info": []
  },
  "summary": {
    "total_errors": 0,
    "total_warnings": 0,
    "total_info": 0,
    "is_valid": true
  }
}
```

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/etl/validate" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "include_computed_metrics": true,
    "include_frontend_consistency": true
  }'
```

---

### 2. System Status

**Endpoint:** `GET /api/v1/system/status`

**Authentication:** Required (JWT token)

**Response:**
```json
{
  "initialized": true,
  "has_products": true,
  "has_locations": true,
  "has_suppliers": false,
  "has_sales_data": true,
  "has_stock_levels": true,
  "setup_instructions": null,
  "data_quality": {
    "products_count": 150,
    "locations_count": 3,
    "suppliers_count": 0,
    "sales_records_count": 45000,
    "stock_levels_count": 450
  },
  "metrics_validation": null
}
```

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/system/status" \
  -H "Authorization: Bearer <token>"
```

---

## Validation Checks

### Raw Data Quality

- ✅ Date ranges (min 3 weeks, max 2 years)
- ✅ SKU/item_id format (alphanumeric + underscores, 1-255 chars)
- ✅ Location_id format (1-50 chars, not null)
- ✅ Numeric ranges (quantity >= 0, cost >= 0)
- ✅ Future dates detection
- ✅ Negative values detection

### Data Completeness

- ✅ Orphaned item_ids in `ts_demand_daily` (not in products)
- ✅ Orphaned location_ids in `ts_demand_daily` (not in locations)
- ✅ Products without stock levels
- ✅ Products with sales but no stock
- ✅ Missing dates (gaps in time series)

### Computed Metrics Validation

- ✅ **DIR (Days of Inventory Remaining)**
  - Formula: `DIR = current_stock / average_daily_demand`
  - Validates: DIR >= 0, NULL when no demand, 0 when stock = 0
  
- ✅ **Stockout Risk**
  - Formula: `risk = 1 - DIR / (lead_time + safety_buffer)` when DIR < required_days
  - Validates: Risk 0-1 (decimal), 1.0 (100%) when stock = 0
  - Frontend multiplies by 100 to display as percentage
  
- ✅ **Status**
  - Validates: `out_of_stock`, `understocked`, `overstocked`, `normal`, `unknown`
  - Matches DIR thresholds from `client_settings`
  
- ✅ **Inventory Value**
  - Formula: `inventory_value = current_stock * unit_cost`
  - Validates calculation accuracy

### Frontend-Backend Consistency

- ✅ DIR formatting (1 decimal place precision)
- ✅ Stockout risk range validation
  - Backend returns: 0-1 (decimal, where 1.0 = 100%)
  - Frontend multiplies by 100: `(value * 100).toFixed(1)%`
  - **✅ Fixed: Now correctly displays 0-100%**
- ✅ Status values match frontend expectations
- ✅ DIR thresholds match frontend cell styling (14 days red, 90 days green)

---

## Known Issues Detected

### ✅ Fixed: Stockout Risk Range Mismatch

**Status:** ✅ FIXED (2025-01-27)

**Previous Issue:** Backend returned stockout risk as 0-100 (percentage), but frontend expected 0-1 (decimal) and multiplied by 100.

**Fix Applied:**
- Changed `MetricsService.calculate_stockout_risk()` to return 0-1 (decimal) instead of 0-100
- Updated `DashboardService` to use 0-1 range
- Updated `RecommendationsService` to compare against 0.70 instead of 70
- Updated validation service to check 0-1 range

**Current Behavior:**
- Backend returns: 0-1 (decimal, where 1.0 = 100%)
- Frontend multiplies by 100: `(value * 100).toFixed(1)%`
- Result: Correct display of 0-100%

**Files Updated:**
- `backend/services/metrics_service.py`
- `backend/services/dashboard_service.py`
- `backend/services/recommendations_service.py`
- `backend/services/data_validation_service.py`

---

## Usage Examples

### Python Client

```python
import requests

# Validate data
response = requests.post(
    "http://localhost:8000/api/v1/etl/validate",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "include_computed_metrics": True,
        "include_frontend_consistency": True
    }
)

report = response.json()
if report["summary"]["is_valid"]:
    print("✅ All validations passed")
else:
    print(f"❌ Found {report['summary']['total_errors']} errors")
    print(f"⚠️  Found {report['summary']['total_warnings']} warnings")
```

### Check System Status

```python
response = requests.get(
    "http://localhost:8000/api/v1/system/status",
    headers={"Authorization": f"Bearer {token}"}
)

status = response.json()
if not status["initialized"]:
    print("⚠️  System not initialized")
    print(f"Setup: {status['setup_instructions']}")
```

---

## Integration with Existing Scripts

The validation service consolidates logic from:
- `scripts/check_data_completeness.py` - Date range validation
- `scripts/check_inventory_data.py` - DIR prerequisites
- `forecasting/services/data_validator.py` - Time series validation

All validation logic is now available via API endpoint.

---

## Next Steps

1. ✅ Data validation service implemented
2. ✅ API endpoints created
3. ✅ Fix stockout risk range mismatch (backend updated to return 0-1)
4. ⏳ Add validation to CI/CD pipeline
5. ⏳ Create development UI for validation results (optional)

---

**Related Documentation:**
- [Validation Usage Guide](./VALIDATION_USAGE_GUIDE.md) - **When and how to use validation**
- [Data Requirements](../DATA_REQUIREMENTS.md)
- [Data Model](../DATA_MODEL.md)
- [Next Steps](../NEXT_STEPS.md)

