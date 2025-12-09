# M5 Dataset Download and Import Guide

**Purpose:** Download industry-standard M5 dataset to validate classification accuracy

---

## M5 Dataset Overview

**Source:** Kaggle M5 Forecasting Competition  
**URL:** https://www.kaggle.com/c/m5-forecasting-accuracy

**Characteristics:**
- ✅ **42,840 time series** (products × stores)
- ✅ **3,049 products** across 10 stores
- ✅ **Daily sales** (2011-2016, 1,913 days)
- ✅ **Hierarchical structure** (product → category → department)
- ✅ **Multiple demand patterns** (regular, intermittent, lumpy, seasonal)
- ✅ **Industry standard** (used by researchers worldwide)

---

## Setup

### 1. Install Kaggle Package

```bash
pip install kaggle
```

### 2. Set Up Kaggle API Credentials

1. Go to https://www.kaggle.com/account
2. Click "Create New API Token"
3. Download `kaggle.json`
4. Place it in `~/.kaggle/kaggle.json`
5. Set permissions: `chmod 600 ~/.kaggle/kaggle.json`

### 3. Run Download Script

```bash
cd backend
uv run python scripts/download_m5_data.py
```

---

## What the Script Does

1. **Downloads M5 Dataset**
   - Downloads from Kaggle
   - Extracts to `backend/data/m5/`

2. **Analyzes Patterns**
   - Calculates ABC classification (volume)
   - Calculates XYZ classification (variability)
   - Detects demand patterns (regular, intermittent, lumpy)

3. **Selects Diverse SKUs**
   - Selects 20 SKUs covering all patterns:
     - A-X, A-Y, A-Z
     - B-X, B-Y, B-Z
     - C-X, C-Y, C-Z
     - Intermittent demand
     - Lumpy demand

4. **Imports to Database**
   - Imports to `ts_demand_daily` table
   - Item IDs: `M5_<original_id>`
   - Under existing client_id

---

## Manual Download (Alternative)

If Kaggle API doesn't work:

1. Go to https://www.kaggle.com/c/m5-forecasting-accuracy/data
2. Download `sales_train_evaluation.csv` and `calendar.csv`
3. Extract to `backend/data/m5/`
4. Run script (it will skip download step)

---

## Validation After Import

### Test Classification Accuracy

```bash
# Test with M5 SKUs
cd backend
uv run python scripts/test_sku_classifier.py
```

**Expected:**
- Diverse ABC-XYZ combinations
- Intermittent and lumpy patterns detected
- Classification matches known patterns

### Test Forecast Accuracy

```bash
# Test forecast with diverse SKUs
cd backend
uv run python tests/test_forecast_accuracy.py
```

**Expected:**
- Different MAPE ranges for different SKU types
- A-X SKUs: Lower MAPE (10-25%)
- C-Z SKUs: Higher MAPE (50-100%)
- Intermittent SKUs: Higher MAPE (expected)

---

## Known Patterns in M5

| Pattern | Description | Expected Classification |
|---------|-------------|------------------------|
| **Regular** | Daily sales, low variability | A-X, B-X, C-X |
| **Intermittent** | Sporadic sales (ADI > 1.32) | Any ABC, pattern=intermittent |
| **Lumpy** | High variability, sporadic | A-Z, B-Z, C-Z, pattern=lumpy |
| **Seasonal** | Clear seasonal patterns | A-Y, B-Y (medium variability) |

---

## Benefits

1. **Validation**
   - Test classification on known patterns
   - Verify ABC-XYZ accuracy
   - Validate method recommendations

2. **Diversity**
   - More patterns than our 20 synthetic SKUs
   - Real-world data characteristics
   - Industry-standard test cases

3. **Accuracy Testing**
   - Test forecast accuracy across SKU types
   - Validate expected MAPE ranges
   - Compare with industry benchmarks

---

*Guide created: 2025-12-08*

