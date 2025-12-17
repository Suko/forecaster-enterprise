# Quick Start Guide

**One-command setup for first-time users**

---

## 🚀 Just Run This

```bash
cd backend
./setup.sh
```

**That's it!** The script does everything automatically.

---

## What It Does

The `setup.sh` script automatically:

1. ✅ **Checks prerequisites** (uv, Python, PostgreSQL)
2. ✅ **Creates .env file** from `.env.example` (if missing)
3. ✅ **Generates secure JWT secret** (if needed)
4. ✅ **Installs all dependencies** (via `uv sync`)
5. ✅ **Checks database connection**
6. ✅ **Runs database migrations**
7. ✅ **Creates admin user** (`admin@example.com` / `admin123`)
8. ✅ **Creates test user** (`test@example.com` / `testpassword123`)
9. ✅ **Imports sales data** (CSV or M5 dataset)
10. ✅ **Sets up test data** (products, locations, suppliers, stock)
11. ✅ **Shifts dates to recent** (makes all data relative to today)
12. ✅ **Populates historical stock** (calculates stock_on_date)
13. ✅ **Verifies setup** (checks that data was created)

---

## Prerequisites

**Before running `setup.sh`, make sure you have:**

1. **PostgreSQL running**
   ```bash
   # macOS
   brew services start postgresql
   
   # Linux
   sudo systemctl start postgresql
   
   # Or use Docker
   docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15
   ```

2. **uv installed** (Python package manager)
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Python 3.12+** (uv will handle this if not installed)

---

## Options

### Use M5 Dataset Instead of CSV

```bash
./setup.sh --use-m5-data
```

Downloads real M5 forecasting dataset from Zenodo (no API needed).

### Custom Client Name

```bash
./setup.sh --client-name "My Company"
```

### Skip Steps

```bash
./setup.sh --skip-admin          # Skip admin user creation
./setup.sh --skip-test-user      # Skip test user creation
./setup.sh --skip-csv-import     # Skip data import
./setup.sh --skip-test-data      # Skip test data setup
```

---

## After Setup

### Start the Server

```bash
uv run uvicorn main:app --reload
```

### Access the API

- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Login Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: `admin123`

**Test User:**
- Email: `test@example.com`
- Password: `testpassword123`

---

## Troubleshooting

### "uv is not installed"

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Database connection failed"

1. **Check PostgreSQL is running:**
   ```bash
   # macOS
   brew services list
   
   # Linux
   sudo systemctl status postgresql
   ```

2. **Check DATABASE_URL in `.env`:**
   ```bash
   cat backend/.env
   ```
   
   Default: `postgresql://postgres:postgres@localhost:5432/forecaster_enterprise`

3. **Create database if needed:**
   ```bash
   createdb forecaster_enterprise
   ```

### "CSV file not found"

The script looks for CSV in:
1. `../data/synthetic_data/synthetic_ecom_chronos2_demo.csv`
2. `backend/../data/synthetic_data/synthetic_ecom_chronos2_demo.csv`

**Solution:** Use `--csv-path` to specify location:
```bash
./setup.sh --csv-path /path/to/your/data.csv
```

Or use M5 data instead:
```bash
./setup.sh --use-m5-data
```

### "Dependencies installation failed"

Make sure you have:
- Python 3.12+ installed
- Internet connection (for downloading packages)
- Sufficient disk space

---

## What Gets Created

### Database Tables
- `users` - Admin and test users
- `clients` - Demo client
- `products` - Test products (from CSV/M5)
- `locations` - Warehouse locations
- `suppliers` - Supplier data
- `stock_levels` - Current stock per location
- `ts_demand_daily` - Sales history (with recent dates)
- `purchase_orders` - Order planning data
- And more...

### Files
- `.env` - Environment configuration (created from `.env.example`)
- `backend/data/m5/` - M5 dataset (if using `--use-m5-data`)

---

## Next Steps

1. **Start the server:**
   ```bash
   uv run uvicorn main:app --reload
   ```

2. **Test the API:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Run tests:**
   ```bash
   uv run pytest tests/test_api/test_inventory_api.py -v
   ```

4. **Reset test data** (if needed):
   ```bash
   uv run python scripts/reset_test_data.py --client-name "Demo Client"
   ```

---

## Summary

**For first-time users:**

1. ✅ Install PostgreSQL and start it
2. ✅ Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. ✅ Run: `cd backend && ./setup.sh`
4. ✅ Start server: `uv run uvicorn main:app --reload`
5. ✅ Open: http://localhost:8000/docs

**That's it!** 🎉

---

**Need help?** Check the full documentation in `docs/` directory.
