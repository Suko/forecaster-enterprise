# M5 Data Setup Guide

**How to download and use M5 dataset with setup.sh**

---

## Current Status

**Answer:** ❌ **NO** - `setup.sh` does NOT automatically download M5 data by default.

**Default behavior:**
- Uses CSV import (`synthetic_ecom_chronos2_demo.csv`)
- Does NOT download M5 dataset

---

## Option 1: Use M5 Data (New!)

**Added:** `--use-m5-data` flag to `setup.sh`

```bash
# Download and import M5 dataset instead of CSV
./setup.sh --use-m5-data
```

**What this does:**
1. ✅ Downloads M5 dataset from Kaggle (if not already downloaded)
2. ✅ Imports 40 diverse SKUs to `ts_demand_daily`
3. ✅ Creates client if needed
4. ✅ Then runs `setup_test_data.py` to create test data
5. ✅ Shifts dates to recent
6. ✅ Populates historical stock

**Requirements:**
- `requests` package: `pip install requests`
- No API credentials needed - downloads directly from Zenodo

---

## Option 2: Use CSV Data (Default)

```bash
# Uses CSV import (default)
./setup.sh
```

**What this does:**
1. ✅ Imports CSV file (`synthetic_ecom_chronos2_demo.csv`)
2. ✅ Creates client
3. ✅ Imports sales data
4. ✅ Then runs `setup_test_data.py`
5. ✅ Shifts dates to recent
6. ✅ Populates historical stock

---

## Comparison

| Data Source | Command | Pros | Cons |
|-------------|---------|------|------|
| **M5 Dataset** | `./setup.sh --use-m5-data` | ✅ Real historical patterns<br>✅ Diverse SKU types<br>✅ Large dataset<br>✅ No API needed | ⚠️ Large download (~500MB)<br>⚠️ Slower import |
| **CSV (Default)** | `./setup.sh` | ✅ Fast<br>✅ No API needed<br>✅ Small file | ⚠️ Synthetic data<br>⚠️ Limited patterns |

---

## M5 Dataset Details

### What is M5?
- M5 Forecasting Competition dataset
- 42,840 time series (products × stores)
- 3,049 products across 10 stores
- Daily sales from 2011-2016
- Real retail sales patterns

### Import Process

1. **Download** (if not already downloaded):
   - From Zenodo (no credentials needed)
   - Direct download: https://zenodo.org/records/12636070
   - Extracts to: `backend/data/m5/`

2. **Analyze Patterns:**
   - Analyzes all SKUs for diversity
   - Identifies different demand patterns

3. **Select SKUs:**
   - Selects 40 diverse SKUs (default)
   - Ensures variety: high-volume, low-volume, seasonal, etc.

4. **Import to Database:**
   - Imports to `ts_demand_daily` table
   - Item IDs prefixed with `M5_` (e.g., `M5_HOBBIES_1_008_CA_1_evaluation`)

---

## Setup Workflow with M5

```
./setup.sh --use-m5-data
    ↓
Step 1: Migrations
    ↓
Step 2: Create admin user
    ↓
Step 3: Create test user
    ↓
Step 4: Download & Import M5
    ├─ Download from Kaggle (if needed)
    ├─ Analyze patterns
    ├─ Select 40 diverse SKUs
    └─ Import to ts_demand_daily
    ↓
Step 5: Setup test data
    ├─ Create products, locations, suppliers, stock
    ├─ Shift dates to recent (Step 9)
    └─ Populate historical stock (Step 10)
    ↓
Done! ✅
```

---

## Manual M5 Import

If you want to import M5 separately:

```bash
# Download and import M5
uv run python scripts/download_m5_data.py \
    --client-name "Demo Client" \
    --n-skus 40

# Then run setup_test_data.py
uv run python scripts/setup_test_data.py \
    --client-name "Demo Client"
```

---

## Requirements

To use `--use-m5-data`, you only need:

1. **Install requests package:**
   ```bash
   pip install requests
   # Or
   uv add requests
   ```

2. **That's it!** No API credentials needed - downloads directly from Zenodo.

---

## Troubleshooting

### Error: "requests package not installed"

**Solution:**
```bash
pip install requests
# Or
uv add requests
```

### Error: "Dataset files not found"

**Solution:**
1. Download manually from: https://zenodo.org/records/12636070
2. Extract to: `backend/data/m5/`
3. Or: `project_root/data/m5/`

### M5 Import Takes Too Long

**Solution:**
- Reduce number of SKUs: `--n-skus 20` (instead of 40)
- Or use CSV import instead: `./setup.sh` (without `--use-m5-data`)

---

## Summary

| Question | Answer |
|----------|--------|
| **Does setup.sh auto-download M5?** | ❌ No (by default) |
| **Can setup.sh use M5 data?** | ✅ Yes (with `--use-m5-data` flag) |
| **Default data source?** | CSV file (`synthetic_ecom_chronos2_demo.csv`) |
| **M5 requirements?** | `requests` package (no API credentials needed) |

**Recommendation:**
- **Quick setup:** Use default CSV (`./setup.sh`)
- **Real patterns:** Use M5 (`./setup.sh --use-m5-data`)

---

**Status:** ✅ **M5 support added to setup.sh** - Use `--use-m5-data` flag!
