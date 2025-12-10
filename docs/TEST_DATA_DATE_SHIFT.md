# Test Data Date Shifting - Simple Solution

**Why Date Shifting?** Instead of generating synthetic data, just shift all existing dates forward so the most recent data is today. This is simpler and preserves real M5 patterns!

---

## Strategy

```
Before:
M5 Data: 2015-01-01 to 2024-12-31 ❌ (too old for DIR calculation)

After:
M5 Data: 2024-02-01 to 2025-01-27 ✅ (recent, DIR works!)
```

**Benefits:**
- ✅ **Simple:** One UPDATE query
- ✅ **Fast:** No data generation needed
- ✅ **Preserves Patterns:** Real M5 sales patterns maintained
- ✅ **No Data Loss:** All historical data preserved
- ✅ **Works Immediately:** DIR calculations work right away

---

## Usage

### Option 1: Automatic (Recommended)

```bash
# Setup test data - automatically shifts dates to recent
uv run python backend/scripts/setup_test_data.py \
    --client-id <uuid>
```

This will:
1. Create products, locations, suppliers, stock
2. **Shift all sales data dates** so max date = today
3. All data becomes "recent" relative to today

### Option 2: Manual Date Shifting

```bash
# Shift dates only (if you already have data)
uv run python backend/scripts/shift_dates_to_recent.py \
    --client-id <uuid>

# Shift to specific date
uv run python backend/scripts/shift_dates_to_recent.py \
    --client-id <uuid> \
    --target-date 2025-01-27

# Shift to N days back from today
uv run python backend/scripts/shift_dates_to_recent.py \
    --client-id <uuid> \
    --days-back 7  # Max date will be 7 days ago
```

---

## How It Works

1. **Find Max Date:** Get the most recent date in existing data
2. **Calculate Offset:** `offset = today - max_date`
3. **Update All Dates:** `date_local = date_local + offset`
4. **Done!** All data is now recent

**Example:**
```
Current max date: 2024-12-31
Today: 2025-01-27
Offset: 27 days

All dates shifted forward by 27 days:
- 2024-12-31 → 2025-01-27 ✅
- 2024-12-30 → 2025-01-26 ✅
- 2015-01-01 → 2015-01-28 ✅
```

---

## Comparison: Date Shift vs Synthetic Generation

| Approach | Date Shift | Synthetic Generation |
|----------|------------|---------------------|
| **Complexity** | ✅ Simple (1 UPDATE) | ❌ Complex (pattern generation) |
| **Speed** | ✅ Fast (< 1 second) | ❌ Slow (minutes) |
| **Pattern Quality** | ✅ Real M5 patterns | ⚠️ Synthetic patterns |
| **Data Volume** | ✅ All historical data | ⚠️ Only recent data |
| **Maintenance** | ✅ One-time shift | ❌ Regenerate each time |

**Winner:** Date shifting is simpler and better for testing!

---

## Verification

After shifting, verify:

```sql
-- Check date range
SELECT 
    MIN(date_local) as first_date,
    MAX(date_local) as last_date,
    COUNT(*) as records
FROM ts_demand_daily
WHERE client_id = '<your-client-uuid>';

-- Should show:
-- last_date = today (or very recent)
-- first_date = today - (original date range)
```

---

## When to Use Each Approach

### Use Date Shifting When:
- ✅ You have M5 or historical data
- ✅ You want to preserve real patterns
- ✅ You need quick setup
- ✅ Testing/Demo purposes

### Use Synthetic Generation When:
- ⚠️ You need specific date ranges
- ⚠️ You want to test edge cases
- ⚠️ You need data for future dates
- ⚠️ You want to control exact patterns

---

## Troubleshooting

### Dates Already Recent
```
ℹ️  Dates already up to date
   Current max date: 2025-01-27
   Target max date: 2025-01-27
```
**Solution:** Nothing to do - dates are already recent!

### No Data Found
```
❌ Error: No sales data found
```
**Solution:** Import M5 data first:
```bash
python backend/scripts/download_m5_data.py
```

### Want to Reset Dates
If you need to reset dates back:
```bash
# Shift backwards (negative offset)
# Or re-import original data
```

---

## Summary

**Date shifting is the simpler solution:**
- ✅ One command: `setup_test_data.py`
- ✅ Preserves all M5 patterns
- ✅ Makes all data "recent"
- ✅ DIR calculations work immediately
- ✅ No complex generation needed

**Status:** ✅ **IMPLEMENTED** - Use `setup_test_data.py` and dates are automatically shifted!
