#!/usr/bin/env bash
set -euo pipefail

# Build demo/test seed data on LOCAL Postgres.
# This is the fast, local-first step before pushing to Supabase.
#
# Prereqs:
#   - Local Postgres running and DATABASE_URL points to it (non-async URL).
#   - uv + backend deps installed.
#   - M5 dataset already downloaded locally (data/m5).
#
# Usage:
#   cd backend
#   ./scripts/build_local_seed.sh
#
# Optional env:
#   CLIENT_NAME="Demo Client"
#   M5_SKUS=200
#   M5_HISTORY_DAYS=1095          # 3 years; omit/empty for full M5 range
#   STOCK_HISTORY_DAYS=1095
#   INCLUDE_SYNTHETIC=false
#   SYNTHETIC_CSV=../data/synthetic_data/synthetic_ecom_chronos2_demo.csv
#   WIPE_LOCAL=true              # delete existing client data first
#   DUMP_PATH=../data/seed/demo_seed.dump
#   LOCAL_PG_URL=postgresql://...  # used for pg_dump if DATABASE_URL is async

CLIENT_NAME=${CLIENT_NAME:-"Demo Client"}
M5_SKUS=${M5_SKUS:-200}
M5_HISTORY_DAYS=${M5_HISTORY_DAYS:-1095}
STOCK_HISTORY_DAYS=${STOCK_HISTORY_DAYS:-1095}
INCLUDE_SYNTHETIC=${INCLUDE_SYNTHETIC:-false}
SYNTHETIC_CSV=${SYNTHETIC_CSV:-"../data/synthetic_data/synthetic_ecom_chronos2_demo.csv"}
WIPE_LOCAL=${WIPE_LOCAL:-true}
DUMP_PATH=${DUMP_PATH:-"../data/seed/demo_seed.dump"}

echo "Local seed build for '${CLIENT_NAME}'"

# Ensure local build never uses Supabase async override
unset SUPABASE_PG_URL || true
if [[ -z "${ASYNC_DATABASE_URL:-}" ]]; then
  # Prefer local sync DB URL from env or .env for async scripts
  local_db_url=${LOCAL_PG_URL:-${DATABASE_URL:-}}
  if [[ -z "${local_db_url}" ]]; then
    for env_file in ".env" "../.env"; do
      if [[ -f "${env_file}" ]]; then
        val=$(grep -E "^DATABASE_URL=" "${env_file}" | tail -n1 | cut -d= -f2- || true)
        if [[ -n "${val}" ]]; then
          local_db_url="${val}"
          break
        fi
      fi
    done
  fi
  if [[ -n "${local_db_url}" ]]; then
    local_db_url="${local_db_url/postgresql+asyncpg/postgresql}"
    if [[ "${local_db_url}" == postgres://* ]]; then
      export ASYNC_DATABASE_URL="${local_db_url/postgres:\/\//postgresql+asyncpg://}"
    else
      export ASYNC_DATABASE_URL="${local_db_url/postgresql:\/\//postgresql+asyncpg://}"
    fi
  fi
fi

# 1) Migrations on local DB
echo "Running local migrations..."
uv run alembic upgrade heads

# 2) Wipe local Demo Client data (including sales) if requested
if [[ "${WIPE_LOCAL}" == "true" ]]; then
  echo "Wiping local data for client '${CLIENT_NAME}'..."
  uv run python scripts/reset_test_data.py --client-name "${CLIENT_NAME}" || true
fi

# 3) Import M5 sales (curated subset, last N days)
echo "Importing M5 sales (${M5_SKUS} SKUs)..."
history_arg=()
if [[ -n "${M5_HISTORY_DAYS}" ]]; then
  history_arg=(--history-days "${M5_HISTORY_DAYS}")
fi

uv run python scripts/download_m5_data.py \
  --client-name "${CLIENT_NAME}" \
  --n-skus "${M5_SKUS}" \
  "${history_arg[@]}"

# 4) Optional synthetic CSV import (requires location_id or defaults to UNSPECIFIED)
if [[ "${INCLUDE_SYNTHETIC}" == "true" ]]; then
  echo "Importing synthetic CSV: ${SYNTHETIC_CSV}"
  client_id=$(
    uv run python - <<PY
import asyncio
from sqlalchemy import text
from models.database import get_async_session_local

async def main():
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as s:
        r = await s.execute(text("SELECT client_id FROM clients WHERE name = :n"), {"n": "${CLIENT_NAME}"})
        row = r.fetchone()
        print(row[0] if row else "")

asyncio.run(main())
PY
  )
  if [[ -z "${client_id}" ]]; then
    echo "ERROR: Could not resolve client_id for '${CLIENT_NAME}'"
    exit 1
  fi
  uv run python scripts/import_csv_to_ts_demand_daily.py \
    --csv "${SYNTHETIC_CSV}" \
    --client-id "${client_id}"
fi

# 5) Create supporting data + shift dates + backfill stock_on_date
echo "Running setup_test_data..."
uv run python scripts/setup_test_data.py \
  --client-name "${CLIENT_NAME}" \
  --clear-existing \
  --use-m5-locations \
  --stock-history-days "${STOCK_HISTORY_DAYS}"

# 6) Export a data-only dump of app tables
echo "Creating local dump at ${DUMP_PATH}..."
mkdir -p "$(dirname "${DUMP_PATH}")"

dump_db_url=${LOCAL_PG_URL:-${DATABASE_URL:-}}
if [[ -z "${dump_db_url}" ]]; then
  # Fallback: read DATABASE_URL from backend/.env or root .env
  for env_file in ".env" "../.env"; do
    if [[ -f "${env_file}" ]]; then
      val=$(grep -E "^DATABASE_URL=" "${env_file}" | tail -n1 | cut -d= -f2- || true)
      if [[ -n "${val}" ]]; then
        dump_db_url="${val}"
        break
      fi
    fi
  done
fi
if [[ -z "${dump_db_url}" ]]; then
  echo "ERROR: DATABASE_URL or LOCAL_PG_URL must be set for pg_dump."
  exit 1
fi
# Strip surrounding quotes if present
dump_db_url="${dump_db_url%\"}"; dump_db_url="${dump_db_url#\"}"
dump_db_url="${dump_db_url%\'}"; dump_db_url="${dump_db_url#\'}"
# Normalize async URL to sync URL for pg_dump
dump_db_url="${dump_db_url/postgresql+asyncpg/postgresql}"

pg_dump -Fc --data-only --no-owner --no-privileges \
  --table=clients \
  --table=users \
  --table=products \
  --table=locations \
  --table=suppliers \
  --table=product_supplier_conditions \
  --table=stock_levels \
  --table=client_settings \
  --table=ts_demand_daily \
  "${dump_db_url}" \
  > "${DUMP_PATH}"

echo "✅ Local seed build complete."
echo "Dump: ${DUMP_PATH}"
