# Test Data Quick Start Guide

**Goal:** Set up complete test data with M5 historical data + synthetic recent data from today backwards.

---

## Strategy

1. **M5 Historical Data (2015-2024):** Preserved for forecasting
2. **Synthetic Recent Data (Today backwards):** Generated automatically for metrics
3. **Every SKU:** Always populated from today backwards when setting up test data

---

## Quick Setup

### Option 1: Full Setup (Recommended)

```bash
# This will:
# 1. Create products, locations, suppliers, stock levels
# 2. Generate recent sales data from today backwards (last 30 days)
# 3. Preserve all existing M5/synthetic historical data

uv run python backend/scripts/setup_test_data.py \
    --client-id <your-client-uuid> \
    --days-back 30
```

### Option 2: Generate Recent Data Only

If you already have products but need recent sales data:

```bash
# Generate last 30 days (minimum for DIR calculation)
uv run python backend/scripts/generate_recent_sales_data.py \
    --client-id <your-client-uuid> \
    --days-back 30

# Generate last 365 days (for full forecasting)
uv run python backend/scripts/generate_recent_sales_data.py \
    --client-id <your-client-uuid> \
    --days-back 365
```

---

## What Gets Generated

### Sales Data (`ts_demand_daily`)
- ✅ **Last 30-365 days** from today backwards
- ✅ **Pattern-based:** Uses historical averages from M5 data
- ✅ **Realistic:** Weekend effects, promotions, holidays
- ✅ **No overwrites:** Only fills missing dates

### Product Patterns
- **70% Normal:** 10-50 units/day
- **20% High-volume:** 50-200 units/day  
- **10% Low-volume:** 1-10 units/day
- **5% Dead-stock:** 0 sales for 60+ days (for testing)

### Effects Applied
- **Weekend:** -30% sales
- **Holidays:** +20% sales
- **Promotions:** 1-2 per month, +50% sales
- **Weekly pattern:** Higher mid-week, lower Monday

---

## Data Flow

```
┌─────────────────────────────────────────┐
│  M5 Dataset (2015-2024)                 │
│  ✅ Preserved - Used for forecasting    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Synthetic Data (2024 backwards)        │
│  ✅ Preserved - Historical context      │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│  Recent Synthetic Data (Today backwards)│
│  ✅ Generated - Enables metrics         │
│  - Last 30 days (minimum)               │
│  - Last 365 days (recommended)         │
└─────────────────────────────────────────┘
```

---

## Verification

After setup, verify:

```bash
# Check recent data exists
psql -d your_db -c "
SELECT 
    item_id,
    MIN(date_local) as first_date,
    MAX(date_local) as last_date,
    COUNT(*) as records
FROM ts_demand_daily
WHERE client_id = '<your-client-uuid>'
  AND date_local >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY item_id
LIMIT 10;
"

# Should show:
# - last_date = today (or very recent)
# - records >= 30 per item
```

---

## Troubleshooting

### DIR Still Shows 0
- Check if recent data exists: `SELECT MAX(date_local) FROM ts_demand_daily WHERE client_id = '...'`
- Should be today or yesterday
- If not, run: `generate_recent_sales_data.py --days-back 30`

### No Historical Data
- Import M5 dataset first: `python backend/scripts/download_m5_data.py`
- Or import CSV: `python backend/scripts/import_csv_to_ts_demand_daily.py`

### Want More Days
- Increase `--days-back` parameter (30-365)
- More days = better forecasting, but slower generation

---

## Next Steps

1. ✅ Run `setup_test_data.py` with your client ID
2. ✅ Verify recent data exists (last 30 days)
3. ✅ Test DIR calculation (should not be 0)
4. ✅ Test status classification (should not be "unknown")
5. ✅ Test recommendations (should generate)

---

**Status:** ✅ Ready to use - Run `setup_test_data.py` and you're done!
