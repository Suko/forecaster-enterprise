# Test Data Import Flow

**Status:** 📋 Design Phase  
**Last Updated:** 2025-01-XX

---

## Overview

This document defines the flow for importing test data from CSV sources into the `ts_demand_daily` table, covering all use cases: development, testing, and manual imports.

---

## Test Data Source

### Location
`/Users/mihapro/Development/ecommerce/forecaster_enterprise/data/sintetic_data/synthetic_ecom_chronos2_demo.csv`

### Format
```csv
date, store_id, sku, category, sales_qty, price, base_price, 
inventory_level, promo_flag, holiday_flag, marketing_index, 
is_weekend, lead_time_days
```

### Characteristics
- **14,621 rows** (2 years of daily data)
- **Multiple SKUs**: SKU001, SKU002, etc.
- **Multiple stores**: STORE001, etc.
- **Date range**: 2023-01-01 to 2024-12-31
- **Covariates included**: promo_flag, holiday_flag, is_weekend, marketing_index

---

## Use Cases & Flows

### 1. **Automated Test Execution (pytest)**

**When:** Running unit/integration tests  
**Trigger:** `pytest tests/`  
**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Test Execution Starts                                     │
│    pytest tests/test_forecasting/test_forecast_service.py   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Test Fixtures Load                                        │
│    - db_session fixture (SQLite in-memory or PostgreSQL)     │
│    - test_client fixture (creates test client)                │
│    - test_data_loader fixture (loads CSV)                    │
│    - populate_test_data fixture (runs import)                 │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. populate_test_data Fixture Executes                       │
│    a) Check if ts_demand_daily table exists                  │
│    b) Create table if missing (simplified schema)            │
│    c) Load CSV via TestDataLoader                             │
│    d) Transform CSV columns → ts_demand_daily columns        │
│    e) Insert rows with test_client.client_id                 │
│    f) Commit transaction                                      │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Test Runs                                                 │
│    - ForecastService queries ts_demand_daily                  │
│    - Data is isolated by client_id                            │
│    - Tests verify forecast generation, accuracy, etc.         │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Test Cleanup                                              │
│    - SQLite: In-memory DB destroyed (automatic)              │
│    - PostgreSQL: Transaction rollback (automatic)             │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation:**
- ✅ `tests/conftest.py` - `populate_test_data` fixture
- ✅ `tests/fixtures/test_data_loader.py` - CSV loader
- ✅ Works with both SQLite and PostgreSQL

**No Action Needed** - This is already working.

---

### 2. **Development Environment Setup**

**When:** Setting up local development environment  
**Trigger:** Manual execution or setup script  
**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Developer Sets Up Environment                             │
│    - Creates/connects to local PostgreSQL                    │
│    - Runs migrations (creates ts_demand_daily table)          │
│    - Creates test client in clients table                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Developer Runs Import Script                               │
│    python backend/scripts/import_csv_to_ts_demand_daily.py  │
│         --csv data/sintetic_data/synthetic_ecom_chronos2... │
│         --client-id <test_client_id>                         │
│         [--clear-existing]                                   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Import Script Executes                                    │
│    a) Load CSV file                                          │
│    b) Validate data (dates, SKUs, values)                   │
│    c) Transform columns:                                    │
│       - sku → item_id                                        │
│       - date → date_local                                    │
│       - sales_qty → units_sold                              │
│       - promo_flag → promotion_flag                          │
│       - holiday_flag → holiday_flag                         │
│       - is_weekend → is_weekend                              │
│       - marketing_index → marketing_spend (if needed)        │
│    d) Create full daily series (fill gaps)                  │
│    e) Insert into ts_demand_daily with client_id             │
│    f) Report: rows imported, errors, warnings                │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Developer Can Now Test                                    │
│    - Run API locally: POST /api/v1/forecast                  │
│    - Query database directly                                 │
│    - Test forecast accuracy                                  │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation:**
- ✅ **Complete** - `backend/scripts/import_csv_to_ts_demand_daily.py`
- ✅ **Complete** - `backend/scripts/setup_demo_client.py` (one-command demo setup)

**Usage:**
```bash
# Quick demo setup (creates client + imports data)
python backend/scripts/setup_demo_client.py

# Or import only (if client exists)
python backend/scripts/import_csv_to_ts_demand_daily.py \
    --csv data/sintetic_data/synthetic_ecom_chronos2_demo.csv \
    --client-id <uuid>
```

See `backend/scripts/README.md` for full documentation.

---

### 3. **Manual Data Import (Production-Like)**

**When:** Importing real client data or test data for demos  
**Trigger:** Manual execution or scheduled job  
**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User/Admin Prepares CSV                                   │
│    - CSV matches expected format (or uses mapping)           │
│    - Validates CSV structure locally (optional)              │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. User Runs Import Script                                   │
│    python backend/scripts/import_csv_to_ts_demand_daily.py  │
│         --csv /path/to/client_data.csv                       │
│         --client-id <real_client_id>                         │
│         --format standard|shopify|custom                     │
│         [--column-mapping json_file]                         │
│         [--clear-existing]                                   │
│         [--dry-run]                                          │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Import Script Executes                                    │
│    a) Validate client_id exists in clients table            │
│    b) Load and parse CSV                                     │
│    c) Apply column mapping (if custom format)                │
│    d) Validate data quality:                                 │
│       - Date format and range                                │
│       - SKU format                                           │
│       - Numeric values (non-negative, reasonable ranges)    │
│       - Missing values handling                              │
│    e) Transform to ts_demand_daily format                    │
│    f) Create full daily series (fill gaps with zeros)       │
│    g) Check for duplicates (item_id, date_local, client_id) │
│    h) Insert/update with conflict resolution                │
│    i) Log import results to data_quality_event (future)     │
│    j) Report summary: rows imported, errors, warnings       │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Data Available for Forecasting                            │
│    - ForecastService can query ts_demand_daily              │
│    - Data isolated by client_id                              │
│    - Ready for forecast generation                           │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation:**
- ✅ **Basic script available** - `backend/scripts/import_csv_to_ts_demand_daily.py`
- ⚠️ **Phase 2 features pending** - Enhanced features for production use

**Phase 1 (Current):**
- ✅ Standard CSV format support
- ✅ Basic validation
- ✅ Conflict resolution (upsert)

**Phase 2 (Future - Production ETL):**
- Multiple CSV formats (Shopify, custom)
- Column mapping configuration
- Dry-run mode
- Advanced data quality validation
- Full daily series generation

---

### 4. **CI/CD Pipeline**

**When:** Automated testing in CI/CD  
**Trigger:** Git push, PR, scheduled build  
**Flow:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CI/CD Pipeline Starts                                    │
│    - GitHub Actions / GitLab CI / Jenkins                    │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Setup Test Database                                       │
│    - Create PostgreSQL test database                        │
│    - Run migrations                                          │
│    - Create test client                                      │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Import Test Data (Optional)                               │
│    - If needed: run import script                            │
│    - OR: Use populate_test_data fixture (preferred)          │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Run Tests                                                 │
│    pytest tests/ --cov=backend/forecasting                   │
└─────────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Cleanup                                                   │
│    - Drop test database                                      │
│    - Clean up resources                                      │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation:**
- ✅ Tests work with `populate_test_data` fixture
- ⚠️ **Optional Enhancement**: Standalone import script for CI setup

**Action Required:**
- Optional: Add import script to CI setup if needed
- Current approach (fixture-based) is sufficient

---

## Column Mapping: CSV → ts_demand_daily

### Standard Mapping (synthetic_ecom_chronos2_demo.csv)

| CSV Column | ts_demand_daily Column | Transformation |
|------------|------------------------|----------------|
| `sku` | `item_id` | Direct mapping |
| `date` | `date_local` | Parse to date |
| `sales_qty` | `units_sold` | Direct mapping |
| `promo_flag` | `promotion_flag` | Convert to boolean |
| `holiday_flag` | `holiday_flag` | Convert to boolean |
| `is_weekend` | `is_weekend` | Convert to boolean |
| `marketing_index` | `marketing_spend` | Optional: scale/index → spend |
| `store_id` | *(ignored)* | Not in ts_demand_daily (single location) |
| `category` | *(ignored)* | Not in ts_demand_daily |
| `price` | *(ignored)* | Not in ts_demand_daily |
| `base_price` | *(ignored)* | Not in ts_demand_daily |
| `inventory_level` | *(ignored)* | Not in ts_demand_daily |
| `lead_time_days` | *(ignored)* | Not in ts_demand_daily |

### Required Fields in ts_demand_daily

- `item_id` (VARCHAR) - **Required**
- `date_local` (DATE) - **Required**
- `units_sold` (NUMERIC) - **Required** (default: 0)
- `client_id` (UUID) - **Required** (from import script argument)

### Optional Fields in ts_demand_daily

- `promotion_flag` (BOOLEAN) - Default: FALSE
- `holiday_flag` (BOOLEAN) - Default: FALSE
- `is_weekend` (BOOLEAN) - Default: FALSE
- `marketing_spend` (NUMERIC) - Default: 0
- All other fields from full schema (future expansion)

---

## Data Transformation Rules

### 1. **Full Daily Series**
- **Requirement**: `ts_demand_daily` must have a row for every day in the date range, even if `units_sold = 0`
- **Action**: Fill gaps with zero-demand days
- **Example**: If CSV has 2023-01-01 and 2023-01-03, insert 2023-01-02 with `units_sold = 0`

### 2. **Date Handling**
- Parse CSV dates to `date` objects (no time component)
- Validate date range (reasonable business dates)
- Handle timezone if needed (default: UTC or client timezone)

### 3. **Numeric Values**
- `units_sold`: Non-negative, round to 2 decimals
- `marketing_spend`: Non-negative, round to 2 decimals
- Handle missing values: Use 0 for `units_sold`, FALSE for flags

### 4. **Boolean Flags**
- Convert 0/1, "true"/"false", "yes"/"no" to boolean
- Default: FALSE if missing

### 5. **Duplicate Handling**
- Primary key: `(item_id, date_local, client_id)`
- Strategy: `ON CONFLICT DO UPDATE` or `ON CONFLICT DO NOTHING`
- Option: `--clear-existing` to delete existing data first

---

## Implementation Plan

### Phase 1: Basic Import Script (MVP)

**File:** `backend/scripts/import_csv_to_ts_demand_daily.py`

**Features:**
- ✅ Load CSV file
- ✅ Standard column mapping (synthetic_ecom_chronos2_demo.csv format)
- ✅ Transform to ts_demand_daily format
- ✅ Insert into database with client_id
- ✅ Basic validation (dates, SKUs, numeric values)
- ✅ Command-line arguments (CSV path, client_id)
- ✅ Error reporting

**Usage:**
```bash
python backend/scripts/import_csv_to_ts_demand_daily.py \
    --csv data/sintetic_data/synthetic_ecom_chronos2_demo.csv \
    --client-id <uuid>
```

### Phase 2: Enhanced Import Script (Future)

**Additional Features:**
- Support for multiple CSV formats (Shopify, custom)
- Column mapping configuration file (JSON)
- Dry-run mode (validate without importing)
- Full daily series generation (fill gaps)
- Data quality validation and reporting
- Conflict resolution options (upsert, skip, replace)
- Progress reporting for large files
- Logging to `data_quality_event` table

---

## Current State Summary

| Component | Status | Location |
|-----------|--------|----------|
| **Test Data CSV** | ✅ Exists | `data/sintetic_data/synthetic_ecom_chronos2_demo.csv` |
| **TestDataLoader** | ✅ Working | `backend/tests/fixtures/test_data_loader.py` |
| **populate_test_data fixture** | ✅ Working | `backend/tests/conftest.py` |
| **Import Script** | ✅ **Complete** | `backend/scripts/import_csv_to_ts_demand_daily.py` |
| **Demo Setup Script** | ✅ **Complete** | `backend/scripts/setup_demo_client.py` |

---

## Next Steps

1. ✅ **Import Script Created** - `backend/scripts/import_csv_to_ts_demand_daily.py`
2. ✅ **Demo Setup Script Created** - `backend/scripts/setup_demo_client.py`
3. ✅ **Documentation** - `backend/scripts/README.md`

**Ready to Use:**
- Run `python backend/scripts/setup_demo_client.py` to get started
- See `backend/scripts/README.md` for usage examples

**Future Enhancements** (Phase 2 - Production ETL):
- Multiple format support (Shopify, custom)
- Column mapping configuration
- Dry-run mode
- Full daily series generation
- Advanced data quality validation

---

## Questions & Decisions

### Q1: Should the import script create the `ts_demand_daily` table?
**A:** No. The table should be created by migrations. The script should fail if the table doesn't exist (with a helpful error message).

### Q2: Should the import script create the client?
**A:** No. The client should exist in the `clients` table. The script should validate `client_id` exists and fail if not.

### Q3: Should we support partial imports (date range)?
**A:** Phase 1: No. Import entire CSV. Phase 2: Yes, add `--start-date` and `--end-date` options.

### Q4: Should we support full daily series generation in Phase 1?
**A:** Phase 1: No. Import only dates present in CSV. Phase 2: Yes, add `--fill-gaps` option.

### Q5: Should we support multiple stores in Phase 1?
**A:** Phase 1: No. Aggregate or use first store. Phase 2: Yes, add `--store-id` filter or aggregation.

---

## Related Documents

- [TS_DEMAND_DAILY_SCHEMA.md](TS_DEMAND_DAILY_SCHEMA.md) - Full schema definition
- [TESTING_STRATEGY.md](TESTING_STRATEGY.md) - Testing approach
- [MVP_UNIFIED.md](MVP_UNIFIED.md) - MVP overview

