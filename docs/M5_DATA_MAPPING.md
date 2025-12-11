# M5 Dataset Mapping Documentation

## 📊 Overview

The M5 Forecasting Competition dataset contains real-world retail sales data from Walmart. This document explains how we download, process, and map M5 data into our `ts_demand_daily` table format.

---

## 📥 Dataset Source

**Download Location:**
- **URL:** `https://zenodo.org/record/12636070/files/m5-forecasting-accuracy.zip`
- **Source:** Zenodo (no API credentials needed)
- **Size:** ~500MB
- **Script:** `backend/scripts/download_m5_data.py`

**Storage Locations (checked in order):**
1. `data/m5/` (project root) - **Preferred**
2. `backend/data/m5/` (backend directory) - Fallback

---

## 📋 M5 Dataset Structure

### **Files in M5 Dataset:**

1. **`sales_train_evaluation.csv`** - Main sales data file
2. **`calendar.csv`** - Maps day numbers to actual dates
3. Other files (prices, events, etc.) - Not currently used

### **sales_train_evaluation.csv Format:**

**Wide Format (One row per product×store combination):**

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Product×Store identifier | `HOBBIES_1_001_CA_1_evaluation` |
| `item_id` | Product ID | `HOBBIES_1_001` |
| `dept_id` | Department ID | `HOBBIES_1` |
| `cat_id` | Category ID | `HOBBIES` |
| `store_id` | Store ID | `CA_1` |
| `state_id` | State ID | `CA` |
| `d_1` | Sales on day 1 | `0` |
| `d_2` | Sales on day 2 | `0` |
| `d_3` | Sales on day 3 | `1` |
| `...` | ... | ... |
| `d_1913` | Sales on day 1913 | `5` |

**Total:** 1,913 daily sales columns (`d_1` through `d_1913`)

### **calendar.csv Format:**

Maps day numbers to actual dates:

| d | date | wm_yr_wk | weekday | wday | month | year | ... |
|---|------|-----------|---------|------|-------|------|-----|
| 1 | 2011-01-29 | 11104 | Saturday | 1 | 1 | 2011 | ... |
| 2 | 2011-01-30 | 11104 | Sunday | 2 | 1 | 2011 | ... |
| 3 | 2011-01-31 | 11105 | Monday | 3 | 1 | 2011 | ... |
| ... | ... | ... | ... | ... | ... | ... | ... |
| 1913 | 2016-04-24 | 16117 | Sunday | 2 | 4 | 2016 | ... |

**Date Range:** 2011-01-29 to 2016-04-24 (1,913 days)

---

## 🔄 Mapping Process: Wide Format → Daily Records

### **Step 1: Load Files**

```python
# Load sales data
sales_df = pd.read_csv("sales_train_evaluation.csv")

# Load calendar for date mapping
calendar_df = pd.read_csv("calendar.csv")
dates = pd.to_datetime(calendar_df['date']).tolist()
# dates = [2011-01-29, 2011-01-30, 2011-01-31, ..., 2016-04-24]
```

### **Step 2: Extract Daily Sales**

For each row (product×store combination):

```python
# Get all daily sales columns (d_1, d_2, ..., d_1913)
sales_cols = [col for col in row.index if col.startswith('d_')]
sales_values = row[sales_cols].values.astype(float)
# sales_values = [0, 0, 1, 2, 0, 3, ..., 5]  (1913 values)
```

### **Step 3: Convert to Daily Records**

Transform from wide format to long format:

```python
for day_idx, sales_qty in enumerate(sales_values):
    sale_date = dates[day_idx].date()  # Get actual date from calendar
    
    # Insert into ts_demand_daily
    INSERT INTO ts_demand_daily (
        client_id,
        item_id,           # M5_<original_id>
        date_local,        # 2011-01-29, 2011-01-30, ...
        units_sold         # Sales quantity for that day
    ) VALUES (...)
```

### **Step 4: Result**

**Before (Wide Format):**
```
One row: id, item_id, dept_id, ..., d_1, d_2, d_3, ..., d_1913
```

**After (Daily Records):**
```
1,913 rows in ts_demand_daily:
- item_id: M5_HOBBIES_1_001_CA_1_evaluation, date_local: 2011-01-29, units_sold: 0
- item_id: M5_HOBBIES_1_001_CA_1_evaluation, date_local: 2011-01-30, units_sold: 0
- item_id: M5_HOBBIES_1_001_CA_1_evaluation, date_local: 2011-01-31, units_sold: 1
- ...
- item_id: M5_HOBBIES_1_001_CA_1_evaluation, date_local: 2016-04-24, units_sold: 5
```

---

## 📊 Data Mapping Details

### **M5 ID Structure:**

M5 uses hierarchical IDs: `{cat_id}_{dept_id}_{item_id}_{state_id}_{store_id}_evaluation`

**Example:** `HOBBIES_1_001_CA_1_evaluation`
- Category: `HOBBIES`
- Department: `HOBBIES_1`
- Item: `HOBBIES_1_001`
- State: `CA`
- Store: `CA_1`
- Type: `evaluation` (vs `validation`)

### **Our Mapping:**

| M5 Field | Our Field | Transformation |
|----------|-----------|----------------|
| `id` | `item_id` | Prefixed with `M5_` → `M5_{id}` |
| `d_1, d_2, ..., d_1913` | `units_sold` | Direct value (one per day) |
| Calendar `date` | `date_local` | Direct mapping (d_1 → first date, etc.) |
| N/A | `client_id` | From import parameters |

### **Item ID Format:**

```
M5_{original_m5_id}
```

**Examples:**
- `M5_HOBBIES_1_001_CA_1_evaluation`
- `M5_HOUSEHOLD_1_118_CA_1_evaluation`
- `M5_FOODS_1_001_TX_1_evaluation`

---

## 🔍 Code Flow

### **Import Function: `import_m5_skus_to_database()`**

**Location:** `backend/scripts/download_m5_data.py`

**Process:**

1. **Load Data:**
   ```python
   sales_df = pd.read_csv("sales_train_evaluation.csv")
   calendar_df = pd.read_csv("calendar.csv")
   dates = pd.to_datetime(calendar_df['date']).tolist()
   ```

2. **For Each Selected SKU:**
   ```python
   for sku_info in selected_skus:
       sku_id = sku_info['id']  # e.g., "HOBBIES_1_001_CA_1_evaluation"
       row = sales_dict[sku_id]
       
       # Get daily sales columns
       sales_cols = [col for col in row.index if col.startswith('d_')]
       sales_values = row[sales_cols].values.astype(float)
   ```

3. **Insert Daily Records:**
   ```python
   for day_idx, sales_qty in enumerate(sales_values):
       sale_date = dates[day_idx].date()
       
       await db.execute(
           text("""
               INSERT INTO ts_demand_daily (
                   client_id, item_id, date_local, units_sold
               ) VALUES (
                   :client_id, :item_id, :date_local, :units_sold
               )
           """),
           {
               "client_id": client_id,
               "item_id": f"M5_{sku_id}",
               "date_local": sale_date,
               "units_sold": int(sales_qty) if not np.isnan(sales_qty) else 0,
           }
       )
   ```

---

## 📈 Example: Complete Mapping

### **Input (M5 Format):**

**sales_train_evaluation.csv:**
```csv
id,item_id,dept_id,cat_id,store_id,state_id,d_1,d_2,d_3,d_4,d_5,...,d_1913
HOBBIES_1_001_CA_1_evaluation,HOBBIES_1_001,HOBBIES_1,HOBBIES,CA_1,CA,0,0,1,2,0,...,5
```

**calendar.csv:**
```csv
d,date,...
1,2011-01-29,...
2,2011-01-30,...
3,2011-01-31,...
4,2011-02-01,...
5,2011-02-02,...
...
1913,2016-04-24,...
```

### **Output (ts_demand_daily Table):**

| client_id | item_id | date_local | units_sold |
|-----------|---------|------------|------------|
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2011-01-29 | 0 |
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2011-01-30 | 0 |
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2011-01-31 | 1 |
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2011-02-01 | 2 |
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2011-02-02 | 0 |
| ... | ... | ... | ... |
| `{uuid}` | `M5_HOBBIES_1_001_CA_1_evaluation` | 2016-04-24 | 5 |

**Result:** 1,913 daily records for this one SKU

---

## 🎯 Key Points

### **1. Wide to Long Transformation:**
- **Input:** 1 row with 1,913 columns
- **Output:** 1,913 rows with 1 date + 1 sales value each

### **2. Date Mapping:**
- `d_1` → First date in calendar.csv (2011-01-29)
- `d_2` → Second date in calendar.csv (2011-01-30)
- `d_1913` → Last date in calendar.csv (2016-04-24)

### **3. Item ID Prefix:**
- All M5 items prefixed with `M5_` to distinguish from other data sources
- Format: `M5_{original_m5_id}`

### **4. Data Quality:**
- Missing values (`NaN`) converted to `0`
- Sales quantities converted to integers
- Dates validated against calendar.csv

---

## 🚀 Usage

### **Download and Import:**

```bash
# Download M5 dataset and import selected SKUs
cd backend
python scripts/download_m5_data.py --client-name "Demo Client" --n-skus 40
```

### **What Happens:**

1. ✅ Downloads M5 dataset from Zenodo (if not exists)
2. ✅ Analyzes patterns (regular, intermittent, lumpy)
3. ✅ Selects diverse SKUs (different patterns)
4. ✅ Converts wide format → daily records
5. ✅ Imports to `ts_demand_daily` table

### **Result:**

- ~40 SKUs × 1,913 days = ~76,520 daily sales records
- All stored in `ts_demand_daily` table
- Ready for forecasting

---

## 📚 References

- **M5 Competition:** https://www.kaggle.com/c/m5-forecasting-accuracy
- **Zenodo Dataset:** https://zenodo.org/record/12636070
- **Script:** `backend/scripts/download_m5_data.py`
- **Import Function:** `import_m5_skus_to_database()`

---

## 🔧 Technical Details

### **Date Range:**
- **Start:** 2011-01-29
- **End:** 2016-04-24
- **Duration:** 1,913 days (~5.2 years)

### **Data Volume:**
- **Total Products:** 3,049
- **Total Stores:** 10
- **Total Combinations:** 42,840 (products × stores)
- **Daily Records per SKU:** 1,913

### **Pattern Analysis:**
The script analyzes each SKU to determine:
- **Pattern:** regular, intermittent, or lumpy
- **XYZ Classification:** X (low variance), Y (medium), Z (high variance)
- **Selection:** Chooses diverse SKUs across patterns

---

## ✅ Summary

**M5 Data Mapping:**
1. **Source:** `sales_train_evaluation.csv` (wide format)
2. **Date Mapping:** `calendar.csv` (day numbers → dates)
3. **Transformation:** Wide format (1 row, 1913 cols) → Daily records (1913 rows)
4. **Storage:** `ts_demand_daily` table
5. **Item IDs:** Prefixed with `M5_` for identification

**Result:** Real-world daily sales data ready for forecasting! 🎉
