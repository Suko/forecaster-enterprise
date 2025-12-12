#!/usr/bin/env bash
set -euo pipefail

# Push a local, data-only seed dump to Supabase.
# Preferred workflow:
#   1) Build locally: ./scripts/build_local_seed.sh
#   2) Push to Supabase: ./scripts/push_seed_to_supabase.sh --wipe-mode all
#
# Prereqs:
#   - pg_restore, psql installed.
#   - SUPABASE_PG_URL set (sync URL, sslmode=require).
#   - Local dump file exists (default ../data/seed/demo_seed.dump).
#
# Usage:
#   export SUPABASE_PG_URL="postgresql://postgres:pass@db.<ref>.supabase.co:5432/postgres?sslmode=require"
#   ./backend/scripts/push_seed_to_supabase.sh --wipe-mode all
#
# Args:
#   --wipe-mode none|client|all   (default: all)
#   --client-name NAME           (default: Demo Client; used for wipe-mode client)
#   --dump-path PATH             (default: ../data/seed/demo_seed.dump)
#   --skip-migrations            (skip alembic upgrade on Supabase)

WIPE_MODE="all"
CLIENT_NAME="Demo Client"
DUMP_PATH="../data/seed/demo_seed.dump"
SKIP_MIGRATIONS="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --wipe-mode)
      WIPE_MODE="$2"; shift 2;;
    --client-name)
      CLIENT_NAME="$2"; shift 2;;
    --dump-path)
      DUMP_PATH="$2"; shift 2;;
    --skip-migrations)
      SKIP_MIGRATIONS="true"; shift 1;;
    *)
      echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "${SUPABASE_PG_URL:-}" ]]; then
  echo "ERROR: SUPABASE_PG_URL is not set."
  exit 1
fi

if [[ ! -f "${DUMP_PATH}" ]]; then
  echo "ERROR: Dump file not found at ${DUMP_PATH}."
  exit 1
fi

echo "Pushing dump to Supabase (wipe-mode=${WIPE_MODE}, client='${CLIENT_NAME}')"
python3 - <<'PY'
import os
from urllib.parse import urlparse, parse_qs
u = os.environ["SUPABASE_PG_URL"]
p = urlparse(u)
qs = parse_qs(p.query)
print(f"Target host: {p.hostname}")
print(f"Target db:   {p.path.lstrip('/') or 'postgres'}")
print(f"SSL mode:    {qs.get('sslmode', ['(default)'])[0]}")
PY

# 1) Ensure schema is up to date on Supabase
if [[ "${SKIP_MIGRATIONS}" != "true" ]]; then
  echo "Running migrations on Supabase..."
  DATABASE_URL="${SUPABASE_PG_URL}" uv run alembic upgrade heads
fi

# 2) Wipe Supabase data if requested
if [[ "${WIPE_MODE}" == "client" ]]; then
  echo "Wiping data for client '${CLIENT_NAME}' on Supabase..."
  psql "${SUPABASE_PG_URL}" -v ON_ERROR_STOP=1 <<SQL
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM clients WHERE name='${CLIENT_NAME}') THEN
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM order_cart_items WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM purchase_order_items WHERE po_id IN (SELECT id FROM purchase_orders WHERE client_id IN (SELECT client_id FROM c));
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM purchase_orders WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM inventory_metrics WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM product_supplier_conditions WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM stock_levels WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM products WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM suppliers WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM locations WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM client_settings WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM ts_demand_daily WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM forecast_results WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM forecast_runs WHERE client_id IN (SELECT client_id FROM c);
    WITH c AS (SELECT client_id FROM clients WHERE name='${CLIENT_NAME}')
    DELETE FROM sku_classifications WHERE client_id IN (SELECT client_id FROM c);
    DELETE FROM clients WHERE name='${CLIENT_NAME}';
  END IF;
END $$;
SQL
elif [[ "${WIPE_MODE}" == "all" ]]; then
  echo "Wiping ALL app data on Supabase..."
  psql "${SUPABASE_PG_URL}" -v ON_ERROR_STOP=1 <<'SQL'
TRUNCATE TABLE
  order_cart_items,
  purchase_order_items,
  purchase_orders,
  inventory_metrics,
  product_supplier_conditions,
  stock_levels,
  products,
  suppliers,
  locations,
  client_settings,
  ts_demand_daily,
  forecast_results,
  forecast_runs,
  sku_classifications,
  users,
  clients
RESTART IDENTITY CASCADE;
SQL
elif [[ "${WIPE_MODE}" == "none" ]]; then
  echo "Skipping wipe."
else
  echo "ERROR: Invalid wipe-mode '${WIPE_MODE}'. Use none|client|all."
  exit 1
fi

# 3) Restore data-only dump.
# Supabase roles are not superusers, so --disable-triggers fails on system triggers.
# The local dump already contains only app tables, ordered safely by pg_dump.
echo "Restoring data from ${DUMP_PATH}..."
pg_restore --no-owner --no-privileges --data-only --exit-on-error --single-transaction \
  -d "${SUPABASE_PG_URL}" \
  "${DUMP_PATH}"

echo "Post-restore sanity counts:"
psql "${SUPABASE_PG_URL}" -t -A -c "select count(*) from clients;" | sed 's/^/  clients: /'
psql "${SUPABASE_PG_URL}" -t -A -c "select count(*) from ts_demand_daily;" | sed 's/^/  ts_demand_daily: /'

echo "✅ Supabase restore complete."
