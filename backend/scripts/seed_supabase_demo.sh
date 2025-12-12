#!/usr/bin/env bash
set -euo pipefail

# Seed a Supabase (or any remote Postgres) instance with demo data.
# Prereqs:
#   - DATABASE_URL set to the target Postgres connection string (service role recommended)
#   - Supabase schema empty or ready for migrations
#   - uv + Python deps available locally (same as backend requirements)
#
# Usage:
#   export DATABASE_URL="postgresql://user:pass@host:port/dbname"
#   ./backend/scripts/seed_supabase_demo.sh
#
# Optional env:
#   CLIENT_NAME="Demo Client"          # client name to create/use
#   M5_SKUS=40                         # number of M5 SKUs to import
#   STOCK_HISTORY_DAYS=1095            # stock_on_date backfill horizon (3 years)
#   INCLUDE_SYNTHETIC=false            # set to true to also import the synthetic CSV
#   SYNTHETIC_CSV=../data/synthetic_data/synthetic_ecom_chronos2_demo.csv

CLIENT_NAME=${CLIENT_NAME:-"Demo Client"}
M5_SKUS=${M5_SKUS:-40}
STOCK_HISTORY_DAYS=${STOCK_HISTORY_DAYS:-1095}
INCLUDE_SYNTHETIC=${INCLUDE_SYNTHETIC:-false}
SYNTHETIC_CSV=${SYNTHETIC_CSV:-"../data/synthetic_data/synthetic_ecom_chronos2_demo.csv"}

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "ERROR: DATABASE_URL is not set. Please export your Supabase/Postgres connection string."
  exit 1
fi

echo "Using DATABASE_URL (hidden), CLIENT_NAME='${CLIENT_NAME}', M5_SKUS=${M5_SKUS}, STOCK_HISTORY_DAYS=${STOCK_HISTORY_DAYS}"

# 1) Run migrations against the target DB
echo "Running migrations..."
uv run alembic upgrade heads

# 2) Import M5 data with per-location rows
echo "Importing M5 data (${M5_SKUS} SKUs)..."
uv run python scripts/download_m5_data.py \
  --client-name "${CLIENT_NAME}" \
  --n-skus "${M5_SKUS}"

# 3) Optionally import synthetic CSV
if [[ "${INCLUDE_SYNTHETIC}" == "true" ]]; then
  echo "Importing synthetic CSV: ${SYNTHETIC_CSV}"
  uv run python scripts/import_csv_to_ts_demand_daily.py \
    --csv "${SYNTHETIC_CSV}" \
    --client-name "${CLIENT_NAME}"
fi

# 4) Create products/locations/suppliers/stock and backfill stock_on_date for STOCK_HISTORY_DAYS
echo "Running setup_test_data..."
uv run python scripts/setup_test_data.py \
  --client-name "${CLIENT_NAME}" \
  --use-m5-locations \
  --stock-history-days "${STOCK_HISTORY_DAYS}"

echo "✅ Supabase demo seed complete for client '${CLIENT_NAME}'."
