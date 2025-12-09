# Data Validator vs Data Audit - Key Differences

## Overview

Both `DataValidator` and `DataAuditLogger` are important for data quality, but they serve **different purposes**:

- **DataValidator**: ✅ **Validates and cleans data** (ensures correctness)
- **DataAuditLogger**: 📝 **Logs data flow** (tracks what happened for investigation)

---

## DataValidator

### Purpose
**Ensures data correctness before sending to models**

### What It Does
1. ✅ **Validates** data structure and quality
2. ✅ **Cleans** data (fills missing dates, handles NaN)
3. ✅ **Checks** for issues (duplicates, gaps, negative values)
4. ✅ **Returns** cleaned DataFrame ready for models

### Key Features
- **Time frequency validation** (Darts-inspired)
- **Missing date detection and filling**
- **NaN value handling** (multiple strategies)
- **Duplicate timestamp removal**
- **Data type conversion** (Decimal → float)

### When It Runs
- **Always** - Before sending data to models
- **Required** - Models won't receive data if validation fails

### Example
```python
# Validates and cleans data
is_valid, report, error, cleaned_df = DataValidator.validate_context_data(
    df,
    item_id="SKU001",
    fill_missing_dates=True,  # Fill gaps
    fillna_strategy="zero",   # Fill NaN with 0
)

if is_valid:
    # Use cleaned_df for forecasting
    predictions = await model.predict(context_df=cleaned_df)
```

### Output
- ✅ **Cleaned DataFrame** (ready for models)
- ✅ **Validation report** (what was checked/fixed)
- ✅ **Error message** (if validation fails)

---

## DataAuditLogger

### Purpose
**Tracks data flow for investigation and debugging**

### What It Does
1. 📝 **Logs** data sent to models (INPUT)
2. 📝 **Logs** predictions from models (OUTPUT)
3. 📝 **Logs** comparison with actuals (COMPARISON)
4. 📝 **Stores** audit trail in database

### Key Features
- **Data flow tracking** (IN → Model → OUT → Comparison)
- **Statistics logging** (mean, std, min, max)
- **Timestamp tracking** (when each stage happened)
- **Stored in database** (for later investigation)

### When It Runs
- **Conditionally** - Only if `ENABLE_AUDIT_LOGGING=true`
- **Optional** - Can be disabled in production for performance
- **Testing/Development** - Enabled by default

### Example
```python
# Only if audit logging enabled
if settings.enable_audit_logging:
    audit_logger = DataAuditLogger(db, forecast_run_id)
    
    # Log input data
    audit_logger.log_data_input(item_id, context_df, method, validation_report)
    
    # Log model output
    audit_logger.log_model_output(item_id, predictions_df, method, validation_report)
    
    # Store in database
    forecast_run.audit_metadata = audit_logger.get_audit_trail()
```

### Output
- 📝 **Audit trail** (JSON structure)
- 📝 **Stored in database** (`forecast_run.audit_metadata`)
- 📝 **Can be saved to file** (for investigation)

---

## Comparison Table

| Aspect | DataValidator | DataAuditLogger |
|--------|---------------|-----------------|
| **Purpose** | Validate & clean data | Track data flow |
| **When** | Always (required) | Optional (configurable) |
| **What** | Checks data quality | Logs what happened |
| **Output** | Cleaned DataFrame | Audit trail (JSON) |
| **Required** | ✅ Yes - Models need clean data | ⚠️ No - For investigation only |
| **Performance** | Fast (data cleaning) | Minimal overhead |
| **Storage** | No (in-memory) | Yes (database/file) |

---

## How They Work Together

### Data Flow

```
1. DataAccess.fetch_historical_data()
   ↓
2. DataValidator.validate_context_data()  ← VALIDATES & CLEANS
   ↓ (cleaned_df)
3. Model.predict(context_df=cleaned_df)
   ↓
4. DataAuditLogger.log_data_input()       ← LOGS INPUT (if enabled)
   ↓
5. Model generates predictions
   ↓
6. DataAuditLogger.log_model_output()     ← LOGS OUTPUT (if enabled)
   ↓
7. Store results in database
   ↓
8. DataAuditLogger.log_comparison()       ← LOGS COMPARISON (if enabled)
```

### In forecast_service.py

```python
# Step 1: Validate (ALWAYS)
is_valid, report, error, cleaned_df = self.validator.validate_context_data(
    item_context, item_id, min_history_days=7,
    fill_missing_dates=True,
    fillna_strategy="zero",
)

if not is_valid:
    logger.error(f"Validation failed: {error}")
    continue

# Step 2: Log input (OPTIONAL - if audit enabled)
if audit_logger:
    audit_logger.log_data_input(item_id, cleaned_df, method, report)

# Step 3: Generate forecast
predictions_df = await model.predict(context_df=cleaned_df)

# Step 4: Log output (OPTIONAL - if audit enabled)
if audit_logger:
    audit_logger.log_model_output(item_id, predictions_df, method, output_report)
```

---

## Key Differences Summary

### DataValidator
- ✅ **Active** - Changes data (cleans, fills, converts)
- ✅ **Required** - Models won't work without it
- ✅ **Fast** - In-memory operations
- ✅ **Purpose** - Ensure data quality

### DataAuditLogger
- 📝 **Passive** - Only logs, doesn't change data
- ⚠️ **Optional** - Can be disabled
- 📝 **Purpose** - Track what happened for debugging

---

## When to Use Each

### Use DataValidator When:
- ✅ Sending data to models (always)
- ✅ Need to clean/fix data issues
- ✅ Want to ensure data quality
- ✅ Need consistent time series

### Use DataAuditLogger When:
- 📝 Debugging forecast issues
- 📝 Investigating accuracy problems
- 📝 Need to track data transformations
- 📝 Production monitoring (optional)

---

## Configuration

### DataValidator
- **Always enabled** - No configuration needed
- **Parameters**: `fill_missing_dates`, `fillna_strategy`

### DataAuditLogger
- **Configurable**: `ENABLE_AUDIT_LOGGING=true/false`
- **Default**: Enabled in development, optional in production
- **Storage**: `forecast_run.audit_metadata` (JSONB column)

---

## Example: Both Working Together

```python
# 1. VALIDATE (always)
is_valid, validation_report, error, cleaned_df = DataValidator.validate_context_data(
    raw_data, "SKU001", fill_missing_dates=True
)

# 2. LOG INPUT (if audit enabled)
if audit_logger:
    audit_logger.log_data_input("SKU001", cleaned_df, "chronos-2", validation_report)

# 3. MODEL PREDICT
predictions = await model.predict(context_df=cleaned_df)

# 4. VALIDATE OUTPUT (always)
is_valid_out, output_report, error_out = DataValidator.validate_predictions(
    predictions, "SKU001", 30
)

# 5. LOG OUTPUT (if audit enabled)
if audit_logger:
    audit_logger.log_model_output("SKU001", predictions, "chronos-2", output_report)

# 6. STORE AUDIT TRAIL (if audit enabled)
if audit_logger:
    forecast_run.audit_metadata = audit_logger.get_audit_trail()
```

---

## Summary

| | DataValidator | DataAuditLogger |
|---|---------------|-----------------|
| **Role** | Data quality guard | Data flow tracker |
| **Action** | Validates & cleans | Logs & records |
| **Required** | ✅ Yes | ⚠️ Optional |
| **Output** | Cleaned DataFrame | Audit trail |
| **Purpose** | Ensure correctness | Enable investigation |

**Both are important but serve different purposes:**
- **DataValidator** = Quality control (required)
- **DataAuditLogger** = Observability (optional, for debugging)

---
*Last updated: 2025-12-08*

