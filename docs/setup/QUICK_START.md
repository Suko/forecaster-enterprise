# Quick Start Guide

**One-command setup for first-time users**

---

## 🚀 Just Run This

```bash
cd backend
./setup.sh --client-name "My Company"
```

**That's it!** Creates a client with admin/test users, ready for data import via API.

---

## What It Does

The `setup.sh` script automatically:

1. ✅ **Checks prerequisites** (uv, Python, PostgreSQL)
2. ✅ **Creates .env file** from `.env.example` (if missing)
3. ✅ **Generates secure JWT secret** (if needed)
4. ✅ **Installs all dependencies** (via `uv sync`)
5. ✅ **Checks database connection**
6. ✅ **Runs database migrations**
7. ✅ **Creates client** (your company)
8. ✅ **Creates admin user** (`admin@example.com` / `admin123`)
9. ✅ **Creates test user** (`test@example.com` / `testpassword123`)

### With Demo Data (for development)

```bash
./setup.sh --with-demo-data
```

Also does:
- ✅ **Imports sales data** (CSV + M5 dataset)
- ✅ **Sets up test data** (products, locations, suppliers, stock)
- ✅ **Shifts dates to recent** (makes all data relative to today)
- ✅ **Populates historical stock** (calculates stock_on_date)

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

### Production Setup (Default)

```bash
./setup.sh --client-name "My Company"
```

Creates client + users only. Import your real data via API.

### Development Setup (With Demo Data)

```bash
./setup.sh --with-demo-data                    # CSV + M5 datasets
./setup.sh --with-demo-data --csv-only         # CSV only
./setup.sh --with-demo-data --m5-only          # M5 only (downloads from Zenodo)
```

### Skip Users

```bash
./setup.sh --skip-admin          # Skip admin user creation
./setup.sh --skip-test-user      # Skip test user creation
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

### "CSV file not found" (when using --with-demo-data)

The script looks for CSV in:
1. `../data/synthetic_data/synthetic_ecom_chronos2_demo.csv`
2. `backend/../data/synthetic_data/synthetic_ecom_chronos2_demo.csv`

**Solution:** Use `--csv-path` to specify location:
```bash
./setup.sh --with-demo-data --csv-path /path/to/your/data.csv
```

Or use M5 data only (downloads from Zenodo):
```bash
./setup.sh --with-demo-data --m5-only
```

### "Dependencies installation failed"

Make sure you have:
- Python 3.12+ installed
- Internet connection (for downloading packages)
- Sufficient disk space

---

## What Gets Created

### Default Setup (client-only)
- `clients` - Your client
- `users` - Admin and test users

### With Demo Data (`--with-demo-data`)
Also creates:
- `products` - Test products (from CSV/M5)
- `locations` - Warehouse locations
- `suppliers` - Supplier data
- `stock_levels` - Current stock per location
- `ts_demand_daily` - Sales history (with recent dates)
- `purchase_orders` - Order planning data

### Files
- `.env` - Environment configuration (created from `.env.example`)
- `backend/data/m5/` - M5 dataset (if using `--with-demo-data --m5-only`)

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

3. **Import your data** (production):
   - Use the ETL API endpoints to import sales data
   - See `docs/backend/API_REFERENCE.md` for details

4. **Run tests** (development with demo data):
   ```bash
   uv run pytest tests/test_api/test_inventory_api.py -v
   ```

---

## Summary

**For production (new client):**

1. ✅ Install PostgreSQL and start it
2. ✅ Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. ✅ Run: `cd backend && ./setup.sh --client-name "My Company"`
4. ✅ Start server: `uv run uvicorn main:app --reload`
5. ✅ Import your data via API

**For development (with demo data):**

```bash
cd backend && ./setup.sh --with-demo-data
```

**That's it!** 🎉

---

**Need help?** Check the full documentation in `docs/` directory.
