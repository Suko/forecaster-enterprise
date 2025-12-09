# Data Validator Usage - When and Where

## Answer: **Data Validator is used when sending data TO the model, NOT when saving to ts_demand_daily table**

---

## Current Usage

### ✅ **Used: When Sending Data to Models**

**Location:** `forecast_service.py` (line 134)

**Flow:**
```
1. DataAccess.fetch_historical_data() 
   → Fetches from ts_demand_daily table
   
2. DataValidator.validate_context_data() 
   → ✅ VALIDATES HERE (before model)
   
3. Model.predict(context_df)
   → Sends validated data to model
```

**Code:**
```python
# In forecast_service.py
for item_id in item_ids:
    item_context = context_df[context_df["id"] == item_id].copy()
    
    # ✅ VALIDATE INPUT DATA (IN) - Always validate, even if audit logging is off
    is_valid, validation_report, error_msg = self.validator.validate_context_data(
        item_context, item_id, min_history_days=7
    )
    
    if not is_valid:
        logger.error(f"Data validation failed for {item_id}: {error_msg}")
        continue
    
    # Generate forecast for this item
    predictions_df = await model.predict(
        context_df=item_context,  # ✅ Validated data sent to model
        prediction_length=prediction_length,
    )
```

**Purpose:**
- ✅ Ensures data quality before model execution
- ✅ Prevents model errors from bad data
- ✅ Logs validation reports for audit trail
- ✅ Validates predictions after model returns

---

### ❌ **NOT Used: When Saving to ts_demand_daily Table**

**Location:** `scripts/import_csv_to_ts_demand_daily.py`

**Flow:**
```
1. CSV file → Load with pandas
2. Basic column validation (required columns exist)
3. Transform data (date parsing, type conversion)
4. Insert directly to ts_demand_daily table
   → ❌ NO DataValidator used here
```

**Code:**
```python
# In import_csv_to_ts_demand_daily.py
df = pd.read_csv(csv_path)

# Basic validation (NOT using DataValidator class)
required_columns = ['date', 'sku', 'sales_qty']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    raise ValueError(f"Missing required columns: {missing_columns}")

# Transform and insert directly
# ❌ No DataValidator.validate_context_data() call
rows_to_insert = [...]
await session.execute(insert_query, row_data)
```

**What happens:**
- ✅ Basic column checks (required columns exist)
- ✅ Type conversion (date parsing, float conversion)
- ❌ **NO** time frequency validation
- ❌ **NO** missing date detection
- ❌ **NO** NaN handling validation
- ❌ **NO** duplicate timestamp checks

---

## Why This Design?

### ✅ **Validation at Model Input (Current Design)**

**Advantages:**
1. **Flexible**: Raw data in database can have gaps, duplicates, etc.
2. **ETL Independence**: ETL doesn't need to be perfect
3. **Model Protection**: Models always receive clean data
4. **Audit Trail**: Validation reports logged for debugging

**Disadvantages:**
1. **Performance**: Validation runs every forecast (could cache)
2. **Data Quality**: Bad data stays in database

### ❌ **Validation at Database Insert (Alternative Design)**

**Advantages:**
1. **Data Quality**: Only clean data in database
2. **Performance**: Validate once, use many times

**Disadvantages:**
1. **Rigid**: ETL must produce perfect data
2. **ETL Complexity**: ETL must handle all edge cases
3. **Less Flexible**: Can't handle real-world messy data

---

## Recommendation: **Hybrid Approach**

### Phase 1 (Current): ✅ Keep validation at model input
- Works well for MVP
- Handles real-world data issues
- Good for testing/development

### Phase 2 (Future): Add validation at ETL level
- Use `EnhancedDataValidator` in import scripts
- Clean data before inserting to database
- Still validate at model input (defense in depth)

### Example: Enhanced Import Script

```python
# Future: import_csv_to_ts_demand_daily.py
from forecasting.services.data_validator_enhanced import EnhancedDataValidator

# After loading CSV
df = pd.read_csv(csv_path)

# Transform to our format
df['id'] = df['sku']
df['timestamp'] = pd.to_datetime(df['date'])
df['target'] = df['sales_qty']

# ✅ Validate and clean BEFORE inserting
for item_id in df['id'].unique():
    item_df = df[df['id'] == item_id].copy()
    
    is_valid, report, cleaned_df, error = EnhancedDataValidator.validate_complete(
        item_df,
        item_id=item_id,
        fill_missing_dates=True,  # Fill gaps
        fillna_strategy="zero",   # Fill NaN with 0
    )
    
    if not is_valid:
        logger.warning(f"Skipping {item_id}: {error}")
        continue
    
    # Insert cleaned_df to database
    # Now database has clean, complete data
```

---

## Current Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                 │
└─────────────────────────────────────────────────────────────┘

1. ETL/Import (import_csv_to_ts_demand_daily.py)
   ↓
   [Basic column check only]
   ↓
   INSERT INTO ts_demand_daily
   ↓
   [Database may have: gaps, duplicates, NaN, etc.]
   ↓

2. Forecast Request
   ↓
   DataAccess.fetch_historical_data()
   ↓
   [Fetches from ts_demand_daily - may have issues]
   ↓
   ✅ DataValidator.validate_context_data()
   ↓
   [Validates: columns, dates, gaps, NaN, etc.]
   ↓
   Model.predict(context_df)
   ↓
   ✅ DataValidator.validate_predictions()
   ↓
   Store results
```

---

## Summary

| Stage | Validation | Purpose |
|-------|-----------|---------|
| **ETL/Import** | ❌ Basic only | Just check required columns exist |
| **Model Input** | ✅ Full validation | Ensure clean data for models |
| **Model Output** | ✅ Validation | Ensure predictions are valid |

**Current Design:** ✅ Validation at model input (good for MVP)
**Future Enhancement:** Add validation at ETL level (Phase 2)

---
*Last updated: 2025-12-08*

