# Test Data Reset Guide

**Complete guide for deleting and repopulating test data**

---

## Quick Reset (Recommended)

### Option 1: Reset Everything (Keeps Sales Data) ✅ RECOMMENDED

```bash
# Delete all test data BUT keep sales data (M5/synthetic)
# Then repopulate products, locations, suppliers, stock, etc.

uv run python backend/scripts/reset_test_data.py \
    --client-id <uuid> \
    --keep-sales-data
```

**What this does:**
1. ✅ Deletes: products, locations, suppliers, stock_levels, conditions, settings
2. ✅ **Keeps:** `ts_demand_daily` (ALL sales data):
   - M5 dataset (2015-2024) if imported
   - Synthetic CSV data if imported
   - Generated recent data
   - All historical sales records
3. ✅ Re-creates: All test data structures
4. ✅ Shifts dates to recent (if needed)
5. ✅ Populates historical stock

**Use when:** You want fresh test data but keep valuable M5/synthetic sales history

**Why keep sales data?**
- M5 dataset is valuable real historical patterns
- Synthetic data may have been carefully curated
- Re-importing takes time
- Setup script needs existing sales data to get item_ids

---

### Option 2: Complete Reset (Deletes Everything) ⚠️ Requires Re-import

```bash
# Delete EVERYTHING including sales data
# Then you need to re-import sales data first

uv run python backend/scripts/reset_test_data.py \
    --client-id <uuid>
```

**What this does:**
1. ✅ Deletes: **Everything** including `ts_demand_daily`:
   - ❌ M5 dataset (if imported) - **DELETED**
   - ❌ Synthetic CSV data (if imported) - **DELETED**
   - ❌ All historical sales records - **DELETED**
2. ⚠️ **You must re-import sales data** before running setup
3. Then run: `setup_test_data.py` to create test data

**Use when:** You want a completely fresh start (loses all sales history)

**⚠️ Warning:** This deletes valuable M5/synthetic data. Only use if you're sure!

---

## Step-by-Step Complete Reset

### 1. Delete Everything

```bash
uv run python backend/scripts/reset_test_data.py \
    --client-id <uuid>
```

### 2. Re-import Sales Data

**Option A: Import M5 Dataset**
```bash
uv run python backend/scripts/download_m5_data.py \
    --client-id <uuid>
```

**Option B: Import CSV**
```bash
uv run python backend/scripts/import_csv_to_ts_demand_daily.py \
    --csv data/synthetic_data/synthetic_ecom_chronos2_demo.csv \
    --client-id <uuid>
```

### 3. Re-create Test Data

```bash
uv run python backend/scripts/setup_test_data.py \
    --client-id <uuid> \
    --days-back 30
```

---

## What Gets Deleted

### With `--keep-sales-data` (Recommended)

| Table | Deleted? | Reason |
|-------|----------|--------|
| `products` | ✅ Yes | Re-created |
| `locations` | ✅ Yes | Re-created |
| `suppliers` | ✅ Yes | Re-created |
| `product_supplier_conditions` | ✅ Yes | Re-created |
| `stock_levels` | ✅ Yes | Re-created |
| `client_settings` | ✅ Yes | Re-created |
| `purchase_orders` | ✅ Yes | Clean slate |
| `order_cart_items` | ✅ Yes | Clean slate |
| `ts_demand_daily` | ❌ **No** | **Preserved** |

### Without `--keep-sales-data` (Complete Reset)

| Table | Deleted? | Reason |
|-------|----------|--------|
| All above | ✅ Yes | Complete reset |
| `ts_demand_daily` | ✅ **Yes** | **Must re-import** |

---

## Reset Workflow

```
┌─────────────────────────────────────────┐
│  Option 1: Keep Sales Data (Recommended)│
└─────────────────────────────────────────┘
                    │
                    ▼
    reset_test_data.py --keep-sales-data
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Delete test data      Keep ts_demand_daily
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
        setup_test_data.py (auto-called)
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Create test data      Shift dates + stock
                    │
                    ▼
            ✅ Complete!


┌─────────────────────────────────────────┐
│  Option 2: Complete Reset              │
└─────────────────────────────────────────┘
                    │
                    ▼
    reset_test_data.py (no --keep-sales-data)
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
  Delete EVERYTHING      ⚠️ Must re-import
        │                       │
        ▼                       ▼
  Import M5/CSV data
        │
        ▼
  setup_test_data.py
        │
        ▼
    ✅ Complete!
```

---

## Examples

### Example 1: Quick Reset (Keep Sales)

```bash
# Reset test data but keep M5 sales history
uv run python backend/scripts/reset_test_data.py \
    --client-id 85e0001b-1ecc-4e8a-86fe-3104f3393a0d \
    --keep-sales-data

# Output:
# 🗑️  Step 1: Clearing all existing test data...
#    Deleted 40 Products
#    Deleted 3 Locations
#    Deleted 4 Suppliers
#    Deleted 66 Product-supplier conditions
#    Deleted 120 Stock levels
#    Kept sales data (ts_demand_daily) - 53440 records preserved
# 
# 🔄 Step 2: Re-populating test data...
# [setup_test_data.py runs automatically]
# 
# ✅ RESET COMPLETE!
```

### Example 2: Complete Reset

```bash
# Step 1: Delete everything
uv run python backend/scripts/reset_test_data.py \
    --client-id 85e0001b-1ecc-4e8a-86fe-3104f3393a0d

# Output:
# ⚠️  WARNING: Sales data was deleted.
#    You need to re-import M5 or synthetic data

# Step 2: Re-import sales data
uv run python backend/scripts/download_m5_data.py \
    --client-id 85e0001b-1ecc-4e8a-86fe-3104f3393a0d

# Step 3: Re-create test data
uv run python backend/scripts/setup_test_data.py \
    --client-id 85e0001b-1ecc-4e8a-86fe-3104f3393a0d
```

---

## Verification

After reset, verify data:

```sql
-- Check products
SELECT COUNT(*) FROM products WHERE client_id = '<uuid>';

-- Check stock levels
SELECT COUNT(*) FROM stock_levels WHERE client_id = '<uuid>';

-- Check sales data
SELECT 
    COUNT(*) as total_records,
    MIN(date_local) as first_date,
    MAX(date_local) as last_date
FROM ts_demand_daily
WHERE client_id = '<uuid>';

-- Check historical stock
SELECT 
    COUNT(*) as records_with_stock,
    COUNT(stock_on_date) as records_with_stock_populated
FROM ts_demand_daily
WHERE client_id = '<uuid>'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days';
```

---

## Troubleshooting

### Error: "No item_ids found in ts_demand_daily"

**Cause:** Sales data was deleted but not re-imported

**Solution:**
```bash
# Re-import sales data first
uv run python backend/scripts/import_csv_to_ts_demand_daily.py \
    --csv <your-csv-file> \
    --client-id <uuid>

# Then run setup
uv run python backend/scripts/setup_test_data.py --client-id <uuid>
```

### Error: "Client not found"

**Cause:** Client ID doesn't exist

**Solution:**
```bash
# Use --client-name to create new client
uv run python backend/scripts/reset_test_data.py \
    --client-name "New Test Client" \
    --keep-sales-data
```

### Dates Still Old After Reset

**Cause:** Date shifting didn't run

**Solution:**
```bash
# Manually shift dates
uv run python backend/scripts/shift_dates_to_recent.py \
    --client-id <uuid>
```

---

## Summary

| Command | What It Does | When to Use |
|---------|--------------|-------------|
| `reset_test_data.py --keep-sales-data` | Delete test data, keep sales, repopulate | ✅ **Most common** - Quick reset |
| `reset_test_data.py` | Delete everything | Complete fresh start |
| `setup_test_data.py --clear-existing` | Clear and recreate (keeps sales) | Alternative to reset |

**Recommended:** Use `reset_test_data.py --keep-sales-data` for quick resets!

---

**Status:** ✅ **READY** - You can now completely delete and repopulate test data!
