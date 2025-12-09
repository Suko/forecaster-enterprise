# Brazilian Ecommerce Dataset Evaluation

**Dataset:** [Olist Brazilian Ecommerce](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)  
**Date:** 2025-12-08

---

## Dataset Overview

**Source:** Kaggle - Olist Brazilian Ecommerce  
**Size:** 100,000 orders (2016-2018)  
**Type:** Transaction-level data (not time series)

---

## What We Need vs. What This Dataset Provides

| Requirement | Brazilian Ecommerce | M5 Dataset |
|-------------|---------------------|------------|
| **Time Series Format** | ❌ Order-level (needs aggregation) | ✅ Already time series |
| **Daily Sales Data** | ⚠️ Need to aggregate | ✅ Daily sales ready |
| **Multiple SKUs** | ✅ Yes (many products) | ✅ Yes (3,049 products) |
| **Volume Distribution** | ✅ Likely diverse | ✅ Known to be diverse |
| **Variability Patterns** | ❓ Unknown | ✅ Known patterns |
| **Intermittent Demand** | ❓ Unknown | ✅ Yes |
| **Preprocessing Needed** | ⚠️ High (aggregation) | ✅ Low (ready to use) |

---

## Pros ✅

1. **Real-World E-Commerce Data**
   - Actual Brazilian e-commerce transactions
   - Real customer behavior
   - Multiple product categories

2. **Rich Metadata**
   - Product categories
   - Customer locations
   - Payment methods
   - Order status
   - Reviews/ratings

3. **Multiple Products**
   - Many SKUs to choose from
   - Different categories (electronics, furniture, etc.)
   - Likely diverse demand patterns

4. **Covariates Available**
   - Could extract promotional periods
   - Customer segments
   - Geographic patterns

---

## Cons ⚠️

1. **Not Time Series Format**
   - Order-level data (not daily sales)
   - Need to aggregate by product + date
   - More preprocessing required

2. **Unknown Patterns**
   - Don't know if it has Y/Z classes
   - Don't know if it has intermittent demand
   - Would need to analyze first

3. **More Work Required**
   - Need to write aggregation script
   - Need to handle missing dates
   - Need to create time series structure

4. **Less Documented**
   - M5 is industry standard
   - M5 has known patterns
   - M5 is well-researched

---

## Comparison: Brazilian Ecommerce vs. M5

### Brazilian Ecommerce
```
✅ Real e-commerce data
✅ Rich metadata
⚠️  Needs aggregation (order → daily sales)
⚠️  Unknown patterns
⚠️  More preprocessing
```

### M5 Dataset
```
✅ Industry standard
✅ Already time series format
✅ Known patterns (documented)
✅ Ready to use
✅ Well-researched
```

---

## Recommendation

### For Phase 2A (SKU Classification)

**M5 is Better Because:**
1. ✅ Already in time series format
2. ✅ Known to have diverse patterns (A/B/C, X/Y/Z)
3. ✅ Well-documented
4. ✅ Less preprocessing needed
5. ✅ Industry standard for validation

**Brazilian Ecommerce Could Work If:**
1. You want real e-commerce data (not retail)
2. You need rich metadata (categories, reviews)
3. You're willing to do aggregation work
4. You want to test with actual customer behavior

---

## If You Want to Use Brazilian Ecommerce

### Steps Required:

1. **Download Dataset**
   ```bash
   kaggle datasets download -d olistbr/brazilian-ecommerce
   ```

2. **Aggregate to Daily Sales**
   - Group by: product_id + date
   - Sum: quantity sold
   - Create time series structure

3. **Analyze Patterns**
   - Calculate ABC (volume)
   - Calculate XYZ (variability)
   - Detect intermittent/lumpy

4. **Select Diverse SKUs**
   - Pick 20-30 SKUs covering all patterns
   - Import to database

5. **Validate Classification**
   - Test ABC-XYZ classification
   - Verify patterns match expectations

---

## Final Recommendation

**For Phase 2A:** Use **M5 Dataset** (easier, known patterns)

**For Later Phases:** Consider **Brazilian Ecommerce** if you need:
- Real e-commerce customer behavior
- Rich metadata for advanced features
- Category-specific patterns

---

*Evaluation created: 2025-12-08*

