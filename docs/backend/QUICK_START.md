# Quick Start Guide

**Using `uv` for package management**

## Step 1: Run Migrations

```bash
cd forecaster_enterprise/backend
uv run alembic upgrade head
```

This will create all the database tables.

## Step 2: Set Up Test Data

### Option A: One-Command Setup (Recommended)

This creates a demo client and imports test data in one step:

```bash
cd forecaster_enterprise/backend
uv run python scripts/setup_demo_client.py \
  --name "Demo Client" \
  --csv ../data/synthetic_data/synthetic_ecom_chronos2_demo.csv
```

This will:
1. Create a "Demo Client" (or use existing)
2. Import sales data from CSV to `ts_demand_daily`
3. Return the `client_id` you'll need for next steps

### Option B: Manual Setup (Two Steps)

**Step 2a: Create Client and Import Sales Data**

First, you need a client. You can either:
- Use an existing client (check database)
- Create one manually
- Or use `setup_demo_client.py` which creates one

Then import sales data:
```bash
cd forecaster_enterprise/backend
uv run python scripts/import_csv_to_ts_demand_daily.py \
  --csv ../data/synthetic_data/synthetic_ecom_chronos2_demo.csv \
  --client-id <your-client-uuid>
```

**Step 2b: Create Inventory Test Data**

After sales data is imported, create inventory data:
```bash
uv run python scripts/setup_test_data.py \
  --client-id <your-client-uuid>
```

This creates:
- Products (from item_ids in ts_demand_daily)
- Locations
- Suppliers
- Product-supplier conditions
- Stock levels
- Client settings

## Step 3: Start the Server

```bash
cd forecaster_enterprise/backend
uv run uvicorn main:app --reload
```

Server will start at `http://localhost:8000`

## Step 4: Test the APIs

### Get API Documentation
Visit: `http://localhost:8000/docs` (Swagger UI)

### Quick Health Check
```bash
curl http://localhost:8000/health
```

### Login to Get Token
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "your-password"}'
```

Save the token:
```bash
export TOKEN="<your-token-here>"
```

### Test Dashboard
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/dashboard
```

### Test Products
```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/products
```

## Troubleshooting

### "Client ID does not exist"
- Make sure you've created a client first
- Use `setup_demo_client.py` to create one automatically

### "Table does not exist"
- Run migrations: `uv run alembic upgrade head`

### "No item_ids found in ts_demand_daily"
- Import sales data first using `import_csv_to_ts_demand_daily.py`
- The `setup_test_data.py` script needs existing item_ids to create products

### Finding Your Client ID

After running `setup_demo_client.py`, it will print the client_id. You can also query the database:

```sql
SELECT client_id, name FROM clients;
```

Or use the API (if you have admin access):
```bash
# This would require an admin endpoint (not yet implemented)
```

## Complete Workflow Example

```bash
# 1. Migrations
cd forecaster_enterprise/backend
uv run alembic upgrade head

# 2. Setup (creates client + imports data)
uv run python scripts/setup_demo_client.py \
  --csv ../data/synthetic_data/synthetic_ecom_chronos2_demo.csv

# Note the client_id from output, then:
uv run python scripts/setup_test_data.py --client-id <client-id-from-above>

# 3. Start server
uv run uvicorn main:app --reload

# 4. Test
curl http://localhost:8000/health
```

