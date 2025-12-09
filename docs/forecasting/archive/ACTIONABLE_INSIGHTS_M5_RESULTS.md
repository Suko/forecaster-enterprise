# Actionable Insights from M5 Test Results

**Date:** 2025-12-08  
**Status:** 🔍 **Analysis Complete - Action Items Identified**

---

## What the Results Mean

### Current Situation

1. **Classification System is Working** ✅
   - Correctly identifies A-Y, A-Z, lumpy patterns
   - Sets appropriate MAPE expectations
   - Recommends appropriate methods

2. **But We're Not Using the Recommendations** ⚠️
   - System recommends: `sba`, `croston`, `min_max`, `ma7`, `chronos2`
   - We only implement: `chronos-2`, `statistical_ma7`
   - **We're using chronos-2 for ALL SKUs, ignoring recommendations**

3. **Results Show the Problem**
   - Lumpy demand SKUs: 143.5% average MAPE (expected: 50-90%)
   - High-variability (Z-class): 116.3% average MAPE (expected: 60.6%)
   - **Chronos-2 is not optimal for these patterns**

---

## Actionable Points

### 🎯 Priority 1: Implement Method Routing (CRITICAL)

**Problem:** Classification recommends methods, but we ignore them.

**Solution:** Use `recommended_method` from classification instead of always using `primary_model`.

**Current Code:**
```python
# forecast_service.py - line ~100
recommended_method = primary_model  # Always uses primary_model!
```

**Should Be:**
```python
# After classification, use recommended method
if classification and classification.recommended_method:
    method_to_use = classification.recommended_method
else:
    method_to_use = primary_model
```

**Impact:** 
- ✅ Use MA7 for C-Y, C-Z SKUs (better than Chronos-2)
- ✅ Route to appropriate methods when available
- ✅ Improve accuracy for high-variability SKUs

---

### 🎯 Priority 2: Implement Missing Methods

**Methods Recommended But Not Implemented:**

| Method | Recommended For | Status | Priority |
|--------|----------------|--------|----------|
| **sba** | Lumpy demand | ❌ Not implemented | **HIGH** |
| **croston** | Intermittent demand | ❌ Not implemented | **HIGH** |
| **min_max** | C-Z (low value, high variability) | ❌ Not implemented | **MEDIUM** |
| **ma7** | C-Y, B-Z | ✅ Implemented | ✅ |
| **chronos2** | A-X, B-X, C-X, A-Y, B-Y, A-Z | ✅ Implemented | ✅ |

**Action Items:**

#### 2A. Implement SBA (Syntetos-Boylan Approximation)
**For:** Lumpy demand (4 M5 SKUs showing 143.5% MAPE with Chronos-2)

**What it does:**
- Handles sporadic, high-variability demand
- Better than Chronos-2 for lumpy patterns
- Industry standard for intermittent/lumpy demand

**Implementation:**
```python
# forecasting/modes/statistical/sba.py
class SBAModel(BaseForecastModel):
    """Syntetos-Boylan Approximation for lumpy demand"""
    async def predict(self, context_df, prediction_length, ...):
        # Calculate average demand interval
        # Calculate average demand size
        # Apply SBA formula
```

#### 2B. Implement Croston's Method
**For:** Intermittent demand (ADI > 1.32)

**What it does:**
- Separates demand size and demand interval
- Better for products with many zero-demand days
- Industry standard for intermittent demand

**Implementation:**
```python
# forecasting/modes/statistical/croston.py
class CrostonModel(BaseForecastModel):
    """Croston's method for intermittent demand"""
    async def predict(self, context_df, prediction_length, ...):
        # Separate demand size and interval
        # Forecast each separately
        # Combine forecasts
```

#### 2C. Implement Min/Max Rules
**For:** C-Z SKUs (low value, high variability)

**What it does:**
- Simple rules: min = safety stock, max = reorder point
- No complex forecasting needed
- Cost-effective for low-value items

**Implementation:**
```python
# forecasting/modes/statistical/min_max.py
class MinMaxModel(BaseForecastModel):
    """Min/Max rules for low-value, high-variability SKUs"""
    async def predict(self, context_df, prediction_length, ...):
        # Calculate min (safety stock)
        # Calculate max (reorder point)
        # Return constant forecast
```

---

### 🎯 Priority 3: Update Model Factory

**Current:** Only `chronos-2` and `statistical_ma7` registered

**Action:** Register new methods:
```python
# forecasting/modes/factory.py
_models = {
    "chronos-2": Chronos2Model,
    "statistical_ma7": MovingAverageModel,
    "sba": SBAModel,  # NEW
    "croston": CrostonModel,  # NEW
    "min_max": MinMaxModel,  # NEW
}
```

---

## Implementation Roadmap

### Phase 1: Quick Win (This Week)
**Goal:** Use existing methods better

1. ✅ Implement method routing (use `recommended_method`)
2. ✅ Route C-Y, C-Z to MA7 (already implemented)
3. ✅ Test with M5 SKUs

**Expected Impact:**
- C-Y SKUs: Should improve (MA7 better than Chronos-2)
- C-Z SKUs: Should improve slightly

### Phase 2: Implement SBA (Next Week)
**Goal:** Handle lumpy demand

1. ✅ Implement SBA model
2. ✅ Register in factory
3. ✅ Route lumpy demand to SBA
4. ✅ Test with M5 lumpy SKUs

**Expected Impact:**
- Lumpy demand: 143.5% → ~70-90% MAPE (within expected range)

### Phase 3: Implement Croston (Following Week)
**Goal:** Handle intermittent demand

1. ✅ Implement Croston's method
2. ✅ Register in factory
3. ✅ Route intermittent demand to Croston
4. ✅ Test with intermittent SKUs

**Expected Impact:**
- Intermittent demand: Better accuracy for sporadic patterns

### Phase 4: Implement Min/Max (Optional)
**Goal:** Simple rules for low-value items

1. ✅ Implement min/max rules
2. ✅ Register in factory
3. ✅ Route C-Z to min/max
4. ✅ Test with C-Z SKUs

**Expected Impact:**
- C-Z SKUs: Simpler, cost-effective forecasting

---

## Expected Results After Implementation

### Current (Using Chronos-2 for All)
| Pattern | Current MAPE | Expected MAPE | Status |
|---------|--------------|--------------|--------|
| Lumpy | 143.5% | 50-90% | ❌ **WAY ABOVE** |
| A-Z Regular | 87.3% | 30-60% | ❌ Above |
| A-Y Regular | 111.9% | 20-40% | ❌ Above |

### After Method Routing (Phase 1)
| Pattern | Expected MAPE | Method |
|---------|--------------|--------|
| Lumpy | 70-90% | SBA (when implemented) or MA7 |
| A-Z Regular | 30-60% | Chronos-2 (keep) |
| A-Y Regular | 20-40% | Chronos-2 (keep) |
| C-Z | 50-100% | MA7 or Min/Max |

### After Full Implementation (Phase 2-4)
| Pattern | Expected MAPE | Method |
|---------|--------------|--------|
| Lumpy | 50-90% | SBA ✅ |
| Intermittent | 40-80% | Croston ✅ |
| C-Z | 50-100% | Min/Max ✅ |
| A-X, B-X, C-X | 10-35% | Chronos-2 ✅ |
| A-Y, B-Y | 20-45% | Chronos-2 ✅ |

---

## Key Insights

### 1. **One Model Doesn't Fit All** ❌
- Chronos-2 is excellent for regular, low-variability demand
- But performs poorly on lumpy/high-variability demand
- **Solution:** Use different models for different patterns

### 2. **Classification is Working** ✅
- System correctly identifies patterns
- Recommendations are appropriate
- **Problem:** We're not using them yet

### 3. **High MAPE is Expected for Some SKUs** ✅
- Z-class SKUs: High variability = inherently unpredictable
- Lumpy demand: Sporadic = difficult to forecast
- **Solution:** Use specialized methods + set realistic expectations

### 4. **Method Routing is Critical** 🎯
- Biggest impact: Route to appropriate methods
- Quick win: Use MA7 for C-Y, C-Z (already implemented)
- Long-term: Implement SBA, Croston, Min/Max

---

## Next Steps

### Immediate (Today)
1. ✅ **Implement method routing** - Use `recommended_method` from classification
2. ✅ **Test with M5 SKUs** - Verify routing works
3. ✅ **Compare results** - Should see improvement for C-Y, C-Z

### This Week
1. ✅ **Implement SBA model** - For lumpy demand
2. ✅ **Test with lumpy SKUs** - Should see significant improvement
3. ✅ **Update documentation** - Method routing guide

### Next Week
1. ✅ **Implement Croston's method** - For intermittent demand
2. ✅ **Test with intermittent SKUs**
3. ✅ **Full validation** - All patterns covered

---

## Summary

**The Problem:**
- We classify SKUs correctly ✅
- We recommend appropriate methods ✅
- **But we ignore the recommendations** ❌
- Result: Poor accuracy for lumpy/high-variability SKUs

**The Solution:**
1. **Route to recommended methods** (Priority 1 - Quick win)
2. **Implement missing methods** (Priority 2 - SBA, Croston, Min/Max)
3. **Test and validate** (Priority 3 - Verify improvements)

**Expected Impact:**
- Lumpy demand: 143.5% → 70-90% MAPE (within expected range)
- C-Z SKUs: Better accuracy with appropriate methods
- Overall: More accurate forecasts for all SKU types

---

*Analysis completed: 2025-12-08*

