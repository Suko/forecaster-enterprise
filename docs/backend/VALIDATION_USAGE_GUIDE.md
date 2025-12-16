# Data Validation Usage Guide

**Last Updated:** 2025-12-16  
**Purpose:** Understand when, why, and how to use the data validation service

---

## When to Use Validation

### 1. **After ETL Sync** (Most Common)
**When:** After importing or syncing data from external sources

**Why:** 
- Verify data was imported correctly
- Catch data quality issues before they affect forecasts
- Ensure all required relationships exist

**Example:**
```bash
# After syncing sales data
curl -X POST "http://localhost:8000/api/v1/etl/validate" \
  -H "Authorization: Bearer <token>" \
  -d '{"include_computed_metrics": true}'
```

### 2. **Before Running Forecasts**
**When:** Before generating forecasts for the first time or after major data changes

**Why:**
- Ensure minimum 3 weeks of history exists
- Verify no orphaned records that would cause forecast errors
- Validate computed metrics are accurate

**Example:**
```python
# Before forecast generation
response = requests.post(
    f"{API_URL}/api/v1/etl/validate",
    headers={"Authorization": f"Bearer {token}"},
    json={"include_computed_metrics": True}
)
if not response.json()["summary"]["is_valid"]:
    print("❌ Data validation failed - fix issues before forecasting")
    return
```

### 3. **After Data Migration or Updates**
**When:** After bulk data updates, migrations, or manual data corrections

**Why:**
- Verify data integrity after changes
- Catch any broken relationships
- Ensure computed metrics still calculate correctly

### 4. **Scheduled Health Checks** (Future)
**When:** Daily/weekly automated checks (when ETL scheduling is implemented)

**Why:**
- Proactive monitoring of data quality
- Early detection of data issues
- Track data quality trends over time

### 5. **Troubleshooting Issues**
**When:** When forecasts are inaccurate, metrics look wrong, or frontend displays incorrect values

**Why:**
- Identify root cause of display issues
- Verify calculations are correct
- Check for data inconsistencies

**Example:**
```python
# Debugging why DIR looks wrong
report = validate_data(include_computed_metrics=True)
for validation in report["computed_metrics"]["sample_validations"]:
    if validation["validation_errors"]:
        print(f"❌ {validation['item_id']}: {validation['validation_errors']}")
```

### 6. **Onboarding New Clients**
**When:** When setting up a new client's data

**Why:**
- Verify all required data is present
- Check data quality meets minimum standards
- Ensure system is ready for production use

---

## Use Cases by Role

### **Data Engineer / ETL Developer**
**Primary Use:** After ETL syncs, before production deployment

**Focus:**
- Raw data quality (dates, formats, ranges)
- Data completeness (orphaned records)
- Missing relationships

**Example:**
```python
# After ETL sync
report = await validation_service.validate_all(
    client_id=client_id,
    include_computed_metrics=False,  # Skip if just checking raw data
    include_frontend_consistency=False
)

if report["summary"]["total_errors"] > 0:
    # Fix data quality issues
    for error in report["raw_data_quality"]["errors"]:
        logger.error(f"Data quality issue: {error}")
```

### **Backend Developer**
**Primary Use:** When developing features that use computed metrics

**Focus:**
- Computed metrics validation (DIR, stockout risk, status)
- Frontend-backend consistency
- Calculation accuracy

**Example:**
```python
# Validate metrics are calculated correctly
report = await validation_service.validate_all(
    client_id=client_id,
    include_computed_metrics=True,
    include_frontend_consistency=True
)

# Check for calculation errors
for validation in report["computed_metrics"]["sample_validations"]:
    if validation["validation_errors"]:
        print(f"Calculation error: {validation['item_id']}")
        print(f"  Errors: {validation['validation_errors']}")
```

### **QA / Testing**
**Primary Use:** Before releases, after data changes, regression testing

**Focus:**
- All validation checks
- Regression testing
- Integration testing

**Example:**
```python
# Full validation suite
def test_data_quality():
    report = validate_data(
        include_computed_metrics=True,
        include_frontend_consistency=True
    )
    
    assert report["summary"]["is_valid"], "Data validation failed"
    assert report["summary"]["total_errors"] == 0, "Found data errors"
```

### **Operations / DevOps**
**Primary Use:** System health monitoring, production readiness checks

**Focus:**
- System status endpoint
- Data quality trends
- Automated health checks

**Example:**
```python
# Health check
status = get_system_status()
if not status["initialized"]:
    alert("System not initialized")
    
# Data quality check
report = validate_data()
if report["summary"]["total_errors"] > 10:
    alert(f"High error count: {report['summary']['total_errors']}")
```

---

## Common Validation Scenarios

### Scenario 1: First-Time Setup
**Goal:** Verify system is ready for use

```python
# 1. Check system status
status = requests.get(f"{API_URL}/api/v1/system/status", 
                     headers={"Authorization": f"Bearer {token}"}).json()

if not status["initialized"]:
    print("⚠️  System not initialized")
    print(f"Setup: {status['setup_instructions']}")
    return

# 2. Run full validation
report = requests.post(f"{API_URL}/api/v1/etl/validate",
                      headers={"Authorization": f"Bearer {token}"},
                      json={"include_computed_metrics": True,
                            "include_frontend_consistency": True}).json()

# 3. Check results
if report["summary"]["is_valid"]:
    print("✅ System ready for use")
else:
    print(f"❌ Found {report['summary']['total_errors']} errors")
    print("Fix issues before proceeding")
```

### Scenario 2: After ETL Sync
**Goal:** Verify data was imported correctly

```python
# After syncing sales data
report = validate_data(include_computed_metrics=False)

# Check for import issues
errors = report["raw_data_quality"]["errors"]
warnings = report["raw_data_quality"]["warnings"]

if errors:
    print("❌ Data quality errors:")
    for error in errors:
        print(f"  - {error}")

if warnings:
    print("⚠️  Data quality warnings:")
    for warning in warnings:
        print(f"  - {warning}")

# Check completeness
orphaned = report["data_completeness"]["errors"]
if orphaned:
    print("❌ Orphaned records found:")
    for error in orphaned:
        print(f"  - {error}")
```

### Scenario 3: Debugging Metric Calculations
**Goal:** Find why DIR or stockout risk looks wrong

```python
# Validate computed metrics
report = validate_data(include_computed_metrics=True)

# Check sample validations
for validation in report["computed_metrics"]["sample_validations"]:
    item_id = validation["item_id"]
    metrics = validation["calculated_metrics"]
    
    print(f"\n{item_id}:")
    print(f"  DIR: {metrics['dir']}")
    print(f"  Stockout Risk: {metrics['stockout_risk']}")
    print(f"  Status: {metrics['status']}")
    
    if validation["validation_errors"]:
        print(f"  ❌ Errors: {validation['validation_errors']}")
    if validation["validation_warnings"]:
        print(f"  ⚠️  Warnings: {validation['validation_warnings']}")
```

### Scenario 4: Frontend Display Issues
**Goal:** Verify backend returns correct format for frontend

```python
# Check frontend-backend consistency
report = validate_data(include_frontend_consistency=True)

consistency = report["frontend_consistency"]

if consistency["errors"]:
    print("❌ Frontend-backend mismatches:")
    for error in consistency["errors"]:
        print(f"  - {error}")

if consistency["warnings"]:
    print("⚠️  Frontend-backend warnings:")
    for warning in consistency["warnings"]:
        print(f"  - {warning}")
```

---

## Validation Options

### Quick Validation (Raw Data Only)
**Use:** Fast check after ETL sync

```python
report = validate_data(
    include_computed_metrics=False,
    include_frontend_consistency=False
)
# Only checks raw data quality and completeness
```

### Full Validation (All Checks)
**Use:** Comprehensive validation before production

```python
report = validate_data(
    include_computed_metrics=True,
    include_frontend_consistency=True
)
# Checks everything
```

### Metrics-Only Validation
**Use:** When you only care about calculation accuracy

```python
report = validate_data(
    include_computed_metrics=True,
    include_frontend_consistency=False
)
# Skips frontend checks, focuses on calculations
```

---

## Interpreting Results

### Summary Section
```json
{
  "summary": {
    "total_errors": 5,
    "total_warnings": 12,
    "total_info": 3,
    "is_valid": false
  }
}
```

**Interpretation:**
- `is_valid: false` = Has errors (must fix)
- `total_errors > 0` = Critical issues (blocks functionality)
- `total_warnings > 0` = Non-critical issues (may affect accuracy)
- `total_info` = Informational messages (no action needed)

### Error Types

**Raw Data Quality Errors:**
- Invalid date ranges (too short/long)
- Future dates in history
- Negative values
- Invalid formats

**Data Completeness Errors:**
- Orphaned item_ids (sales data without product)
- Orphaned location_ids
- Missing required relationships

**Computed Metrics Errors:**
- DIR calculation incorrect
- Stockout risk out of range
- Status mismatch
- Inventory value calculation wrong

**Frontend Consistency Errors:**
- Formatting mismatches
- Range mismatches (like stockout risk)
- Invalid status values

---

## Best Practices

### 1. **Run Validation After Every ETL Sync**
```python
# In ETL sync script
async def sync_and_validate():
    # Sync data
    await sync_sales_history()
    await sync_products()
    await sync_stock_levels()
    
    # Validate
    report = await validate_data()
    if not report["summary"]["is_valid"]:
        raise Exception("Data validation failed after sync")
```

### 2. **Check Before Critical Operations**
```python
# Before generating forecasts
if not await is_data_valid():
    raise Exception("Cannot generate forecasts - data validation failed")
```

### 3. **Log Validation Results**
```python
report = await validate_data()
logger.info(f"Validation: {report['summary']['total_errors']} errors, "
           f"{report['summary']['total_warnings']} warnings")
```

### 4. **Use System Status for Quick Checks**
```python
# Quick health check
status = await get_system_status()
if not status["has_sales_data"]:
    print("⚠️  No sales data - run ETL sync")
```

### 5. **Validate Sample Products**
The validation service checks 10 sample products for computed metrics. If you need more:
- Run validation multiple times (different samples each time)
- Or extend the service to check all products (slower)

---

## Integration Examples

### Python Script
```python
import requests
from typing import Dict, Any

def validate_data(token: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run data validation"""
    response = requests.post(
        f"{api_url}/api/v1/etl/validate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "include_computed_metrics": True,
            "include_frontend_consistency": True
        }
    )
    response.raise_for_status()
    return response.json()

def get_system_status(token: str, api_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Get system status"""
    response = requests.get(
        f"{api_url}/api/v1/system/status",
        headers={"Authorization": f"Bearer {token}"}
    )
    response.raise_for_status()
    return response.json()

# Usage
token = "your-jwt-token"
report = validate_data(token)
print(f"Valid: {report['summary']['is_valid']}")
print(f"Errors: {report['summary']['total_errors']}")
```

### Shell Script
```bash
#!/bin/bash
# validate_data.sh

API_URL="http://localhost:8000"
TOKEN="your-jwt-token"

# Run validation
response=$(curl -s -X POST "${API_URL}/api/v1/etl/validate" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"include_computed_metrics": true}')

# Check if valid
is_valid=$(echo $response | jq -r '.summary.is_valid')
total_errors=$(echo $response | jq -r '.summary.total_errors')

if [ "$is_valid" = "true" ]; then
  echo "✅ Data validation passed"
  exit 0
else
  echo "❌ Data validation failed: $total_errors errors"
  echo "$response" | jq '.raw_data_quality.errors'
  exit 1
fi
```

### CI/CD Integration (Future)
```yaml
# .github/workflows/validate.yml
name: Data Validation

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Run Data Validation
        run: |
          response=$(curl -X POST "${API_URL}/api/v1/etl/validate" \
            -H "Authorization: Bearer ${TOKEN}")
          
          if [ $(echo $response | jq '.summary.is_valid') != "true" ]; then
            echo "❌ Validation failed"
            exit 1
          fi
```

---

## Troubleshooting

### Issue: Validation takes too long
**Solution:** Disable computed metrics validation for quick checks
```python
report = validate_data(include_computed_metrics=False)
```

### Issue: Too many errors to fix
**Solution:** Focus on errors first, warnings can wait
```python
report = validate_data()
errors = report["raw_data_quality"]["errors"]
# Fix errors first, warnings later
```

### Issue: Validation passes but metrics still wrong
**Solution:** Check sample_validations for specific products
```python
for validation in report["computed_metrics"]["sample_validations"]:
    if validation["validation_errors"]:
        # This product has calculation errors
        print(validation)
```

---

## Next Steps

1. ✅ Validation service implemented
2. ✅ API endpoints created
3. ⏳ Add validation to ETL sync workflow
4. ⏳ Create scheduled validation jobs
5. ⏳ Build development UI for validation results (optional)

---

**Related Documentation:**
- [Data Validation API](./DATA_VALIDATION_API.md) - API reference
- [Data Requirements](../DATA_REQUIREMENTS.md) - What data is required
- [Next Steps](../NEXT_STEPS.md) - Development priorities

