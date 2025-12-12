# Shared Test Data on Supabase

Goal: build a curated demo dataset locally (fast), then bulk‑load it into Supabase so all developers share the same seed.

## Why local‑first

Direct seeding to Supabase via Python is slow (network + per‑row inserts on small instances). `pg_dump/pg_restore` uses bulk COPY and is much faster.

## Workflow

### 1) Build seed locally

```bash
cd backend

# Typical settings: 200 M5 SKUs, last 3 years of sales, 3 years stock history
CLIENT_NAME="Demo Client" \
M5_SKUS=200 \
M5_HISTORY_DAYS=1095 \
STOCK_HISTORY_DAYS=1095 \
INCLUDE_SYNTHETIC=false \
./scripts/build_local_seed.sh
```

Outputs a data‑only dump at `data/seed/demo_seed.dump`.

Env options:
- `M5_SKUS`: how many M5 SKUs to import (50–300 recommended).
- `M5_HISTORY_DAYS`: truncate sales history (e.g., 1095 = 3 years).
- `STOCK_HISTORY_DAYS`: how far back to backfill `stock_on_date`.
- `INCLUDE_SYNTHETIC=true`: also import synthetic CSV after M5.
- `WIPE_LOCAL=true|false`: clear local Demo Client data first.
- `DUMP_PATH`: override dump output path.

### 2) Push seed to Supabase

```bash
export SUPABASE_PG_URL="postgresql://postgres:<pass>@db.<project-ref>.supabase.co:5432/postgres?sslmode=require"

cd backend
./scripts/push_seed_to_supabase.sh --wipe-mode all
```

Wipe modes:
- `all` (default): TRUNCATE all app tables in `public` before restore.
- `client`: delete only one client tenant (`--client-name`).
- `none`: restore on top of existing data (not recommended for refreshes).

Optional flags:
- `--dump-path PATH`: restore a different dump file.
- `--skip-migrations`: skip `alembic upgrade heads` on Supabase if already current.

## After restore

Run quick checks on Supabase:
- `SELECT COUNT(*) FROM ts_demand_daily;`
- `SELECT MIN(date_local), MAX(date_local) FROM ts_demand_daily WHERE client_id = (SELECT client_id FROM clients WHERE name='Demo Client');`
- Sample `stock_on_date` non‑null for last 90 days.

Rotate Supabase DB password/service key after seeding.

