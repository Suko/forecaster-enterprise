# Test Data Research for Phase 2A (SKU Classification)

**Date:** 2025-12-08  
**Status:** 🔍 **Research Phase**  
**Goal:** Find/analyze test data that demonstrates different demand patterns for ABC-XYZ classification

---

## Current Test Data Analysis

### What We Have

**Location:** `data/sintetic_data/synthetic_ecom_chronos2_demo.csv`

**Characteristics:**
- ✅ **20 SKUs** (SKU001 - SKU020)
- ✅ **731 days** of data per SKU (2023-01-01 to 2024-12-31)
- ✅ **Multiple stores** (STORE001, etc.)
- ✅ **Covariates included**: promo_flag, holiday_flag, is_weekend, marketing_index

**What We Need to Analyze:**
- [ ] Volume distribution (ABC classification)
- [ ] Variability (XYZ classification)
- [ ] Demand patterns (regular, intermittent, lumpy, seasonal)
- [ ] Coefficient of Variation (CV) per SKU
- [ ] Average Demand Interval (ADI) per SKU

---

## Required Test Data Characteristics

### For ABC-XYZ Classification Testing

| Pattern Type | What We Need | Why |
|--------------|--------------|-----|
| **A-Class (High Volume)** | SKUs with 80% of revenue | Test high-value routing |
| **B-Class (Medium Volume)** | SKUs with 15% of revenue | Test medium-value routing |
| **C-Class (Low Volume)** | SKUs with 5% of revenue | Test low-value routing |
| **X-Class (Low Variability)** | CV < 0.5 | Test regular demand |
| **Y-Class (Medium Variability)** | 0.5 ≤ CV < 1.0 | Test moderate variation |
| **Z-Class (High Variability)** | CV ≥ 1.0 | Test high variation |
| **Intermittent** | ADI > 1.32 | Test Croston's method |
| **Lumpy** | ADI > 1.32 AND CV² > 0.49 | Test SBA method |
| **Seasonal** | Clear seasonal patterns | Test seasonal models |
| **New Products** | < 90 days history | Test analogy-based |

---

## Public Datasets for Testing

### 1. **FreshRetailNet-50K** ⭐ RECOMMENDED

**Source:** [arXiv:2505.16319](https://arxiv.org/abs/2505.16319)

**Characteristics:**
- ✅ **50,000 store-product time series**
- ✅ **898 stores** across 18 cities
- ✅ **863 perishable SKUs**
- ✅ **Hourly sales data** (can aggregate to daily)
- ✅ **Stockout annotations** (perfect for intermittent demand)
- ✅ **Promotional discounts** (covariates)
- ✅ **Weather data** (covariates)

**Why It's Good:**
- Large scale (50K series)
- Real-world data (not synthetic)
- Includes stockouts (intermittent demand)
- Multiple stores (hierarchical forecasting)
- Covariates included

**How to Use:**
- Download from arXiv
- Aggregate hourly → daily
- Extract SKUs with different patterns
- Use for ABC-XYZ classification testing

---

### 2. **Store Sales Dataset**

**Source:** [GitHub: skforecast-datasets](https://github.com/skforecast/skforecast-datasets)

**Characteristics:**
- ✅ **913,000 transactions** (2013-2017)
- ✅ **50 products** across 10 stores
- ✅ **Time series format**

**Why It's Good:**
- Multiple products (different volumes)
- Multiple stores (hierarchical)
- Real transaction data

**Limitation:**
- May need aggregation/transformation

---

### 3. **M5 Forecasting Competition Dataset** ⭐ RECOMMENDED

**Source:** [Kaggle M5 Forecasting](https://www.kaggle.com/c/m5-forecasting-accuracy)

**Characteristics:**
- ✅ **42,840 time series** (products × stores)
- ✅ **3,049 products** across 10 stores
- ✅ **Daily sales** (2011-2016)
- ✅ **Hierarchical structure** (product → category → department)
- ✅ **Promotional calendar** (covariates)
- ✅ **Calendar events** (holidays, etc.)

**Why It's Perfect:**
- ✅ **Industry standard** (used by researchers worldwide)
- ✅ **Hierarchical** (perfect for our Phase 3)
- ✅ **Multiple demand patterns** (regular, intermittent, seasonal)
- ✅ **Covariates included**
- ✅ **Well-documented**

**How to Use:**
1. Download from Kaggle (free, requires account)
2. Extract diverse SKUs:
   - High volume (A-class)
   - Low volume (C-class)
   - High variability (Z-class)
   - Intermittent demand
   - Seasonal patterns
3. Use for classification algorithm testing

---

### 4. **Multi-Product Sales Dataset**

**Source:** [OpenDataBay](https://www.opendatabay.com/data/consumer/e728abfe-2b94-4ec6-8270-9838c21f1da0)

**Characteristics:**
- ✅ **10 years** of data
- ✅ **4 products** (small business)
- ✅ **Sales trends**

**Limitation:**
- Only 4 products (limited diversity)
- May not have all patterns we need

---

## Synthetic Data Generation

### Option: Generate Test Data with Specific Patterns

**Approach:** Create synthetic SKUs with known characteristics

```python
# Example: Generate test SKUs with specific patterns

patterns = {
    "A-X": {  # High volume, low variability
        "mean": 100,
        "std": 20,  # CV = 0.2
        "pattern": "regular"
    },
    "A-Z": {  # High volume, high variability
        "mean": 100,
        "std": 150,  # CV = 1.5
        "pattern": "lumpy"
    },
    "C-X": {  # Low volume, low variability
        "mean": 5,
        "std": 1,  # CV = 0.2
        "pattern": "regular"
    },
    "C-Z": {  # Low volume, high variability
        "mean": 5,
        "std": 10,  # CV = 2.0
        "pattern": "intermittent"
    },
    "intermittent": {
        "mean": 10,
        "std": 15,
        "pattern": "intermittent",  # ADI > 1.32
        "zero_probability": 0.6  # 60% zero days
    },
    "seasonal": {
        "mean": 50,
        "std": 20,
        "pattern": "seasonal",
        "seasonal_amplitude": 0.3
    }
}
```

**Pros:**
- ✅ Full control over patterns
- ✅ Known ground truth (we know the classification)
- ✅ Can test edge cases

**Cons:**
- ⚠️ Not real-world data
- ⚠️ May miss real-world complexities

---

## Recommended Approach

### Phase 1: Analyze Current Data

**Action:** Analyze our 20 SKUs to see what patterns we already have

```python
# Script to analyze current SKUs
# backend/scripts/analyze_sku_patterns.py

# For each SKU, calculate:
# 1. Total revenue (for ABC)
# 2. Coefficient of Variation (for XYZ)
# 3. Average Demand Interval (for intermittent)
# 4. Seasonal patterns
# 5. Demand pattern classification
```

**Questions:**
- Do we have A/B/C classes?
- Do we have X/Y/Z classes?
- Do we have intermittent demand?
- Do we have seasonal patterns?

### Phase 2: Supplement with M5 Dataset

**Action:** Download M5 dataset and extract diverse SKUs

**Why M5:**
- ✅ Industry standard
- ✅ Well-documented
- ✅ Multiple patterns
- ✅ Hierarchical (good for Phase 3)

**Extract:**
- 10-20 SKUs with different patterns
- Mix of A/B/C and X/Y/Z
- Some intermittent, some seasonal

### Phase 3: Generate Synthetic (If Needed)

**Action:** Generate specific edge cases we can't find in real data

**Use for:**
- Extreme cases (CV > 2.0)
- Very intermittent (ADI > 3.0)
- New products (< 90 days)

---

## Implementation Plan

### Step 1: Analyze Current Data (This Week)

**Script:** `backend/scripts/analyze_sku_patterns.py`

**Output:**
- Classification report for all 20 SKUs
- Which patterns we have
- Which patterns we're missing

### Step 2: Download M5 Dataset (Next Week)

**Action:**
1. Download from Kaggle
2. Extract diverse SKUs (10-20)
3. Import to our test database
4. Verify patterns match our needs

### Step 3: Generate Synthetic (If Needed)

**Action:**
1. Identify missing patterns
2. Generate synthetic SKUs
3. Add to test database

---

## Test Data Requirements Summary

| Pattern | Current Data | M5 Dataset | Synthetic | Priority |
|---------|--------------|------------|-----------|----------|
| A-X (High, Low Var) | ❓ Unknown | ✅ Yes | ✅ Yes | High |
| A-Z (High, High Var) | ❓ Unknown | ✅ Yes | ✅ Yes | High |
| B-Y (Medium, Med Var) | ❓ Unknown | ✅ Yes | ✅ Yes | Medium |
| C-X (Low, Low Var) | ❓ Unknown | ✅ Yes | ✅ Yes | Medium |
| C-Z (Low, High Var) | ❓ Unknown | ✅ Yes | ✅ Yes | High |
| Intermittent | ❓ Unknown | ✅ Yes | ✅ Yes | High |
| Lumpy | ❓ Unknown | ✅ Yes | ✅ Yes | Medium |
| Seasonal | ❓ Unknown | ✅ Yes | ✅ Yes | Medium |
| New Product | ❌ No | ❌ No | ✅ Yes | Low |

---

## Next Steps

1. **✅ Create analysis script** - Analyze current 20 SKUs
2. **⏳ Download M5 dataset** - Get diverse patterns
3. **⏳ Generate synthetic** - Fill missing patterns
4. **⏳ Import to test DB** - Ready for Phase 2A testing

---

## Resources

- **M5 Dataset:** https://www.kaggle.com/c/m5-forecasting-accuracy
- **FreshRetailNet:** https://arxiv.org/abs/2505.16319
- **Store Sales:** https://github.com/skforecast/skforecast-datasets
- **Syntetos & Boylan (2005):** Intermittent demand classification
- **APICS CPIM:** ABC-XYZ classification standards

---

*Research document - Next: Create analysis script*

