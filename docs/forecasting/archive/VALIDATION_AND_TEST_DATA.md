# Validation and Test Data Guide

**Purpose:** Download test data and validate classification accuracy

---

## Overview

We've created scripts to:
1. **Download M5 dataset** (industry standard, 42K+ time series)
2. **Import diverse SKUs** (covering all ABC-XYZ patterns)
3. **Validate classification accuracy** (test against known patterns)

---

## Scripts Created

### 1. `download_m5_data.py`
**Purpose:** Download and import M5 dataset

**Features:**
- Downloads from Kaggle (requires API credentials)
- Analyzes patterns (ABC-XYZ, intermittent, lumpy)
- Selects 20 diverse SKUs
- Imports to `ts_demand_daily` table

**Usage:**
```bash
# 1. Install Kaggle
pip install kaggle

# 2. Set up credentials (~/.kaggle/kaggle.json)
# Get from: https://www.kaggle.com/account

# 3. Run script
cd backend
uv run python scripts/download_m5_data.py
```

**Output:**
- Downloads to `backend/data/m5/`
- Imports SKUs with prefix `M5_<original_id>`
- Creates diverse test set (A-X, A-Y, A-Z, B-X, etc.)

---

### 2. `validate_classification_accuracy.py`
**Purpose:** Validate classification accuracy

**Features:**
- Re-classifies all SKUs in database
- Compares with stored classifications
- Reports accuracy metrics
- Identifies mismatches

**Usage:**
```bash
cd backend
uv run python scripts/validate_classification_accuracy.py
```

**Output:**
- ABC classification accuracy
- XYZ classification accuracy
- Pattern detection accuracy
- Method recommendation accuracy
- Mismatch details

---

## Current Test Results

**Status:** ✅ Scripts working, but need more diverse data

**Current Database:**
- 1 classified SKU (SKU001)
- All X-class (low variability)
- All regular pattern

**Validation Results:**
- ✅ XYZ: 100% accuracy
- ✅ Pattern: 100% accuracy
- ✅ Method: 100% accuracy
- ⚠️ ABC: 0% (expected - only 1 SKU, so relative classification changes)

---

## Next Steps

### Option 1: Download M5 Dataset (Recommended)

**Why:**
- Industry standard (42K+ time series)
- Diverse patterns (regular, intermittent, lumpy, seasonal)
- Real-world data characteristics
- Well-documented

**Steps:**
1. Set up Kaggle API credentials
2. Run `download_m5_data.py`
3. Run validation script
4. Verify diverse patterns are classified correctly

---

### Option 2: Generate Synthetic Test Data

**Why:**
- No external dependencies
- Can create specific patterns
- Fast to generate

**Approach:**
- Create SKUs with known ABC-XYZ combinations
- Generate time series with specific CV, ADI
- Import to database
- Validate classification

---

### Option 3: Use Current Data + Manual Validation

**Why:**
- Already have 20 SKUs
- Can manually verify patterns
- Quick validation

**Limitation:**
- All current SKUs are X-class (low variability)
- Missing Y/Z classes
- Missing intermittent/lumpy patterns

---

## Expected Validation Results (After M5 Import)

### Pattern Distribution
- ✅ Regular: ~60-70%
- ✅ Intermittent: ~20-30%
- ✅ Lumpy: ~5-10%

### ABC Distribution
- ✅ A-class: ~20% (80% of revenue)
- ✅ B-class: ~30% (15% of revenue)
- ✅ C-class: ~50% (5% of revenue)

### XYZ Distribution
- ✅ X-class: ~40-50% (CV < 0.5)
- ✅ Y-class: ~30-40% (0.5 ≤ CV < 1.0)
- ✅ Z-class: ~10-20% (CV ≥ 1.0)

### Classification Accuracy Target
- ✅ ABC: >95%
- ✅ XYZ: >95%
- ✅ Pattern: >90%
- ✅ Method: >90%

---

## Validation Checklist

After importing M5 data:

- [ ] Run `validate_classification_accuracy.py`
- [ ] Check ABC distribution (should match 80/15/5 revenue split)
- [ ] Check XYZ distribution (should have X, Y, Z classes)
- [ ] Check pattern distribution (should have regular, intermittent, lumpy)
- [ ] Verify method recommendations (A-X → chronos2, C-Z → croston, etc.)
- [ ] Test forecast accuracy across SKU types
- [ ] Compare MAPE ranges with expected values

---

## Files Created

1. **`backend/scripts/download_m5_data.py`**
   - Downloads M5 dataset
   - Analyzes and imports diverse SKUs

2. **`backend/scripts/validate_classification_accuracy.py`**
   - Validates classification accuracy
   - Reports metrics and mismatches

3. **`docs/forecasting/M5_DATASET_GUIDE.md`**
   - Guide for downloading M5 dataset
   - Setup instructions
   - Usage examples

4. **`docs/forecasting/VALIDATION_AND_TEST_DATA.md`** (this file)
   - Overview of validation approach
   - Test results
   - Next steps

---

## Notes

### ABC Classification Relative Nature

**Important:** ABC classification is **relative** to all SKUs in the dataset.

- If you have 1 SKU → it will be classified as A (100% of revenue)
- If you have 100 SKUs → top 20% by revenue = A, next 30% = B, bottom 50% = C

**This is expected behavior** - ABC classification is always relative to the current dataset.

### Validation Approach

1. **Re-classify** all SKUs with current data
2. **Compare** with stored classifications
3. **Report** accuracy metrics
4. **Identify** mismatches (may be due to data changes or relative nature of ABC)

---

*Guide created: 2025-12-08*

