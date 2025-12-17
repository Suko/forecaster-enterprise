# Development Scripts

**Purpose:** Development and demo setup only. Production will use proper ETL pipelines.

---

## Active Scripts

| Script | Purpose |
|--------|---------|
| **Setup & Data** | |
| `setup_test_data.py` | Create products, locations, suppliers, stock for testing |
| `setup_demo_client.py` | Create demo client + import CSV data |
| `reset_test_data.py` | Reset test data for a client |
| `download_m5_data.py` | Download M5 forecasting competition data |
| `import_csv_to_ts_demand_daily.py` | Import sales history from CSV |
| `shift_dates_to_recent.py` | Shift historical dates to recent |
| `populate_historical_stock.py` | Backfill stock_on_date column |
| `generate_recent_sales_data.py` | Generate synthetic recent sales |
| **Supabase Seed** | |
| `build_local_seed.sh` | Build local seed dump for Supabase |
| `push_seed_to_supabase.sh` | Push seed to Supabase |
| `seed_supabase_demo.sh` | Seed Supabase demo data |
| `setup_kaggle_token.sh` | Configure Kaggle API token |
| **Testing** | |
| `test_all_apis.py` | Test all API endpoints |
| `test_integration.py` | Integration test suite |
| `test_production_readiness.py` | Production readiness checks |
| `test_m5_forecast_accuracy.py` | Forecast accuracy testing |
| `test_classification_endpoint.py` | Classification API test |
| `manual_forecast_test.py` | **NEW:** Run forecast and compare metrics before/after |
| `validate_forecast_results.py` | **NEW:** Validate forecast run and results integrity |
| **Utilities** | |
| `check_data_completeness.py` | Verify data completeness |
| `check_inventory_data.py` | Check inventory data |
| `security_audit.py` | Security audit checks |
| `comprehensive_model_comparison_all_skus.py` | Model comparison across SKUs |
| `setup_multi_client_test.py` | Multi-client testing setup |

**Archived scripts:** See `archive/` folder for old diagnostic/investigation scripts.

---

## Quick Start: Setup Demo Client

The easiest way to get started:

```bash
# From project root
python backend/scripts/setup_demo_client.py
```

This will:
1. Create a "Demo Client" in the database
2. Import test data from `data/sintetic_data/synthetic_ecom_chronos2_demo.csv`
3. Print the `client_id` for use in API calls

**Custom options:**
```bash
# Custom client name
python backend/scripts/setup_demo_client.py --name "My Test Client"

# Custom CSV file
python backend/scripts/setup_demo_client.py --csv /path/to/data.csv

# Clear existing data if client exists
python backend/scripts/setup_demo_client.py --clear-existing
```

---

## Import CSV to Database

If you already have a client and just want to import data:

```bash
python backend/scripts/import_csv_to_ts_demand_daily.py \
    --csv data/sintetic_data/synthetic_ecom_chronos2_demo.csv \
    --client-id <your-client-uuid> \
    [--clear-existing]
```

**Requirements:**
- Client must exist in `clients` table
- `ts_demand_daily` table must exist (run migrations first)
- CSV must have columns: `date`, `sku`, `sales_qty`
- Optional columns: `promo_flag`, `holiday_flag`, `is_weekend`, `marketing_index`

---

## Prerequisites

1. **Database migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

2. **Environment variables:**
   - `DATABASE_URL` must be set in `.env` file

3. **CSV format:**
   - Standard format: `date`, `sku`, `sales_qty`, `promo_flag`, `holiday_flag`, `is_weekend`, `marketing_index`
   - See `data/sintetic_data/synthetic_ecom_chronos2_demo.csv` for example

---

## Scripts Overview

| Script | Purpose | When to Use |
|--------|---------|-------------|
| `setup_demo_client.py` | Create client + import data | **Start here** - Quick demo setup |
| `import_csv_to_ts_demand_daily.py` | Import CSV only | When client already exists |
| `build_local_seed.sh` | Build curated local seed + dump | Preparing shared demo dataset |
| `push_seed_to_supabase.sh` | Overwrite Supabase from local dump | Share demo dataset across devs |

---

## Example Workflow

```bash
# 1. Setup demo client (one command)
python backend/scripts/setup_demo_client.py

# Output:
# ============================================================
# Setting up Demo Client
# ============================================================
# 
# 1. Creating client: Demo Client
# Created client 'Demo Client' with ID: 123e4567-e89b-12d3-a456-426614174000
# 
# 2. Importing test data from: data/sintetic_data/synthetic_ecom_chronos2_demo.csv
# Loading CSV: data/sintetic_data/synthetic_ecom_chronos2_demo.csv
# Loaded 14,621 rows from CSV
# Inserting 14,621 rows...
#   Inserted 1,000 rows...
#   ...
# 
# ============================================================
# Demo Setup Complete!
# ============================================================
# Client ID: 123e4567-e89b-12d3-a456-426614174000
# Client Name: Demo Client
# 
# Data Import:
#   Rows inserted: 14,621
#   Unique items: 10
#   Date range: 2023-01-01 to 2024-12-31
# 
# You can now use this client_id to test forecasts!
# ============================================================

# 2. Use client_id in API calls
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001"],
    "horizon_days": 7,
    "client_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

---

## Shared Supabase Demo Dataset (Local‑First)

To avoid slow network inserts, build seed data locally, then push a data‑only dump to Supabase.

### 1) Build locally

```bash
cd backend
M5_SKUS=200 M5_HISTORY_DAYS=1095 STOCK_HISTORY_DAYS=1095 ./scripts/build_local_seed.sh
```

This creates `../data/seed/demo_seed.dump`.

### 2) Push to Supabase (overwrite)

```bash
export SUPABASE_PG_URL="postgresql://postgres:<pass>@db.<ref>.supabase.co:5432/postgres?sslmode=require"
cd backend
./scripts/push_seed_to_supabase.sh --wipe-mode all
```

Use `--wipe-mode client` to only delete/reseed one client, or `--wipe-mode none` to append.

---

## Notes

- **Development only:** These scripts are for development/demo purposes
- **Production:** Will use proper ETL pipelines (Airbyte, dbt, etc.)
- **Data isolation:** All data is isolated by `client_id` (multi-tenant safe)
- **Idempotent:** Running scripts multiple times is safe (uses `ON CONFLICT`)

---

## Troubleshooting

**Error: "Client ID does not exist"**
- Create client first using `setup_demo_client.py` or create manually in database

**Error: "ts_demand_daily table does not exist"**
- Run migrations: `cd backend && alembic upgrade head`

**Error: "Missing required columns"**
- Check CSV has: `date`, `sku`, `sales_qty`
- See example: `data/sintetic_data/synthetic_ecom_chronos2_demo.csv`

**Error: Database connection failed**
- Check `DATABASE_URL` in `.env` file
- Ensure database is running


---

## Testing Guide

### Quick Test: Integration

```bash
cd backend
uv run python3 scripts/test_integration.py
```

This tests:
- ✅ Database tables exist
- ✅ Client creation/finding
- ✅ Test data verification
- ✅ Forecast generation

### Full Test Workflow

1. **Run migrations:**
   ```bash
   cd backend
   uv run alembic upgrade head
   ```

2. **Setup demo client:**
   ```bash
   uv run python3 scripts/setup_demo_client.py
   ```

3. **Run integration tests:**
   ```bash
   uv run python3 scripts/test_integration.py
   ```

4. **Test API (manual):**
   ```bash
   # Start server
   uv run uvicorn main:app --reload --port 8000
   
   # Test forecast endpoint
   curl -X POST http://localhost:8000/api/v1/forecast \
     -H "X-API-Key: your-service-api-key" \
     -H "Content-Type: application/json" \
     -d '{"item_ids": ["SKU001"], "horizon_days": 7, "client_id": "your-client-id"}'
   ```

### Common Errors

| Error | Solution |
|-------|----------|
| `relation 'clients' does not exist` | Run `alembic upgrade head` |
| `ModuleNotFoundError: psycopg2` | Run `uv add psycopg2-binary` |
| `CSV file not found` | Check CSV path, use `--csv` option |
