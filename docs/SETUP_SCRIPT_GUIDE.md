# Setup Script Guide

**How `setup.sh` handles test data and recent sales data**

---

## What `setup.sh` Does

### Complete Workflow

```
Step 1: Run migrations
  ↓
Step 2: Create admin user
  ↓
Step 3: Create test user
  ↓
Step 4: Import sales data (Default: Both CSV + M5)
  → Creates client
  → Imports CSV sales data to ts_demand_daily
  → Imports M5 dataset to ts_demand_daily
  ↓
Step 5: Setup test data
  → Creates products, locations, suppliers, stock
  → Shifts sales data dates to recent (Step 9)
  → Populates historical stock (Step 10)
  ↓
Step 6: Done!
```

---

## Step 4: Sales Data Import

**Default behavior:** Imports **both** CSV and M5 datasets

**What it does:**
- Creates or finds client
- Imports CSV sales data to `ts_demand_daily` table (synthetic data)
- Imports M5 dataset to `ts_demand_daily` table (real historical patterns)
- Sales data may have old dates (e.g., 2024-12-31) - will be shifted in Step 5

**Scripts used:**
- `setup_demo_client.py` (CSV import)
- `download_m5_data.py` (M5 import)

**Result:** Both datasets coexist with different item_id prefixes:
- CSV: `SKU-001`, `SKU-002`, etc.
- M5: `M5_HOBBIES_1_008_CA_1_evaluation`, etc.

**Options:**
- `--csv-only`: Import only CSV (skip M5)
- `--m5-only`: Import only M5 (skip CSV)
- Default: Import both

---

## Step 5: Test Data Setup

**What it does:**
- Creates products, locations, suppliers, stock levels
- **Step 9:** Shifts sales data dates to recent (makes max date = today)
- **Step 10:** Populates historical stock (`stock_on_date`)

**Script used:** `setup_test_data.py`

**Key Features:**
- ✅ Automatically shifts dates to recent (no manual step needed)
- ✅ Preserves all sales data (M5, synthetic, etc.)
- ✅ Populates historical stock for analysis

---

## How Recent Sales Data Works

### Automatic Date Shifting

When you run `setup.sh`, Step 5 automatically:

1. **Shifts all sales data dates** so max date = today
   - Example: If data ends at 2024-12-31 and today is 2025-01-27
   - All dates shifted forward by 27 days
   - Now data ends at 2025-01-27 ✅

2. **Preserves all sales data**
   - M5 dataset: ✅ Preserved
   - Synthetic CSV: ✅ Preserved
   - All patterns: ✅ Preserved

3. **Populates historical stock**
   - Calculates `stock_on_date` for each date
   - Works backwards from current stock
   - Enables stockout detection

---

## Usage

### Standard Setup (Recommended)

```bash
cd backend
./setup.sh
```

**What happens:**
1. ✅ Migrations run
2. ✅ Admin & test users created
3. ✅ **Both CSV and M5 sales data imported** (default)
4. ✅ Test data created
5. ✅ **Sales dates shifted to recent** (automatic)
6. ✅ **Historical stock populated** (automatic)

### Custom Options

```bash
# Import only CSV (skip M5)
./setup.sh --csv-only

# Import only M5 (skip CSV)
./setup.sh --m5-only

# Skip all data import
./setup.sh --skip-csv-import

# Skip test data setup (if already done)
./setup.sh --skip-test-data

# Custom CSV file
./setup.sh --csv-path /path/to/your/data.csv

# Custom client name
./setup.sh --client-name "My Test Client"
```

---

## After Setup

### Verify Recent Data

```sql
-- Check if dates are recent
SELECT 
    MAX(date_local) as max_date,
    MIN(date_local) as min_date,
    COUNT(*) as total_records
FROM ts_demand_daily
WHERE client_id = '<your-client-id>';

-- Should show:
-- max_date = today (or very recent)
-- total_records > 0
```

### Verify Historical Stock

```sql
-- Check if stock_on_date is populated
SELECT 
    COUNT(*) as total_records,
    COUNT(stock_on_date) as records_with_stock
FROM ts_demand_daily
WHERE client_id = '<your-client-id>'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days';

-- Should show:
-- records_with_stock > 0
```

---

## Reset Test Data

### Quick Reset (Keeps Sales Data)

```bash
# Delete test data but keep sales data
uv run python scripts/reset_test_data.py \
    --client-id <uuid> \
    --keep-sales-data
```

**What this does:**
- Deletes: products, locations, suppliers, stock
- **Keeps:** All sales data in `ts_demand_daily`
- Re-creates: All test data
- **Re-shifts dates:** Makes data recent again
- **Re-populates stock:** Historical stock data

### Complete Reset

```bash
# Delete everything including sales data
uv run python scripts/reset_test_data.py --client-id <uuid>

# Then re-import sales data
uv run python scripts/import_csv_to_ts_demand_daily.py \
    --csv <file> \
    --client-id <uuid>

# Then re-run setup
uv run python scripts/setup_test_data.py --client-id <uuid>
```

---

## Summary

| Step | What It Does | Recent Data? |
|------|--------------|--------------|
| **Step 4** | Import CSV sales data | ❌ Dates may be old |
| **Step 5** | Create test data | ✅ **Shifts dates to recent** |
| **Step 5** | Populate stock | ✅ **Historical stock added** |

**Key Point:**
- ✅ `setup.sh` automatically ensures recent sales data
- ✅ No manual date shifting needed
- ✅ All sales data preserved (M5, synthetic)
- ✅ Historical stock populated automatically

---

## Troubleshooting

### Dates Still Old After Setup

**Check:** Did Step 5 complete successfully?

**Solution:**
```bash
# Manually shift dates
uv run python scripts/shift_dates_to_recent.py --client-id <uuid>
```

### No Historical Stock

**Check:** Did Step 10 complete?

**Solution:**
```bash
# Manually populate stock
uv run python scripts/populate_historical_stock.py --client-id <uuid>
```

### DIR Still Shows 0

**Check:** Is there sales data for last 30 days?

**Solution:**
```bash
# Verify recent data exists
# If not, dates may not have shifted - run shift_dates_to_recent.py
```

---

**Status:** ✅ **setup.sh automatically handles recent sales data** - No manual steps needed!
