# Expected MAPE Ranges

**Version:** 1.1  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the **industry-standard** MAPE ranges for each SKU classification. These ranges represent what is achievable with good forecasting practices - **not adjusted to match our current results**.

---

## 1. Industry-Standard MAPE Ranges

### ABC-XYZ Matrix

| Classification | Min MAPE | Target MAPE | Max MAPE | Forecastability |
|----------------|----------|-------------|----------|-----------------|
| **A-X** | 10% | 15% | 25% | Excellent |
| **A-Y** | 20% | 30% | 40% | Good |
| **A-Z** | 30% | 45% | 60% | Moderate |
| **B-X** | 15% | 20% | 30% | Good |
| **B-Y** | 25% | 35% | 45% | Moderate |
| **B-Z** | 40% | 55% | 70% | Challenging |
| **C-X** | 20% | 30% | 35% | Good |
| **C-Y** | 30% | 40% | 50% | Moderate |
| **C-Z** | 50% | 75% | 100% | Acceptable |

### By Demand Pattern

| Pattern | Min MAPE | Target MAPE | Max MAPE | Method |
|---------|----------|-------------|----------|--------|
| **Regular** | 10% | 25% | 50% | Chronos-2 |
| **Intermittent** | 40% | 60% | 80% | Croston |
| **Lumpy** | 50% | 70% | 90% | SBA |

---

## 2. Our Current Performance vs Standards

### Validation Results (2025-12-09)

| Classification | Industry Standard | Our Actual | Status | Action |
|----------------|-------------------|------------|--------|--------|
| **A-X** | 10-25% | 17.1% | ✅ **Meets** | Use forecasts confidently |
| **A-Y** | 20-40% | 111.9% | ❌ **Below** | Flag for review, increase safety stock |
| **A-Z (regular)** | 30-60% | 86.6% | ⚠️ **Partial** | Monitor closely |
| **A-Z (lumpy)** | 50-90% | 79.1% | ✅ **Meets** | Use with SBA method |

### Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Meets standard | 24/40 | 60% |
| ⚠️ Partial | 14/40 | 35% |
| ❌ Below standard | 2/40 | 5% |

---

## 3. Status Definitions

### ✅ Meets Standard
- MAPE within expected range
- **Action:** Use forecasts with confidence
- **Client message:** "High confidence forecasts"

### ⚠️ Partial (Within 1.5× max)
- MAPE exceeds range but < 1.5× maximum
- **Action:** Use with caution, consider safety stock
- **Client message:** "Forecasts available but monitor closely"

### ❌ Below Standard (Exceeds 1.5× max)
- MAPE significantly exceeds expected range
- **Action:** Flag for manual review, high safety stock
- **Client message:** "This SKU is challenging to forecast - recommend manual review"

---

## 4. Why We Don't Adjust Ranges

### The Wrong Approach ❌

```
Original A-Y range: 20-40% (industry standard)
Our actual MAPE: 111.9%
Adjusted range: 60-120% ← Makes us "pass" artificially
```

**Problem:** This is circular reasoning. We're lowering the bar to match our performance.

### The Right Approach ✅

```
Industry standard: 20-40%
Our actual: 111.9%
Status: ❌ Below standard
Action: Investigate, improve, or flag for manual handling
```

**Benefit:** Honest assessment → correct business decisions

---

## 5. Actions for Below-Standard SKUs

### A-Y SKUs (Below Standard)

**Current Status:**
- Both Chronos-2 (111.9%) and MA7 (155.1%) struggle
- Root cause unknown

**Recommended Actions:**
1. **Short-term:** Flag for manual review, increase safety stock
2. **Medium-term:** Investigate root cause (data quality? missing covariates?)
3. **Long-term:** Consider alternative methods or accept limitation

### Client Communication

> "These SKUs show higher forecast uncertainty than industry benchmarks. We recommend:
> - Using higher safety stock levels
> - Manual review of forecasts before ordering
> - Monitoring actual vs forecast closely"

---

## 6. Implementation

### SKU Classification Output

```python
class SKUClassification:
    # ... existing fields ...
    
    # Performance status (new)
    meets_standard: bool  # True if MAPE within expected range
    performance_status: str  # "meets", "partial", "below"
    recommended_action: str  # Business guidance
```

### API Response Enhancement

```json
{
  "classification": {
    "abc_class": "A",
    "xyz_class": "Y",
    "expected_mape_range": [20, 40],
    "performance_status": "below_standard",
    "recommended_action": "Flag for manual review, increase safety stock",
    "warning": "This SKU type historically exceeds industry benchmarks"
  }
}
```

---

## 7. Industry Benchmarks Source

These ranges are based on:
- SAP IBP forecasting guidelines
- Oracle Demand Management best practices
- Academic research on demand forecasting
- Industry surveys (Gartner, IBF)

### Typical Industry Performance

| Industry | Average MAPE | Top Quartile |
|----------|--------------|--------------|
| Consumer goods | 25-35% | < 20% |
| Retail | 30-40% | < 25% |
| Fashion | 40-60% | < 35% |
| Industrial | 20-30% | < 15% |

---

## 8. Continuous Improvement

### Track Over Time

| Metric | Current | Target (6 mo) | Target (12 mo) |
|--------|---------|---------------|----------------|
| Meets standard | 60% | 70% | 80% |
| A-Y MAPE | 111.9% | < 60% | < 40% |
| Overall MAPE | 40.4% | < 35% | < 30% |

### Improvement Opportunities

1. **Covariates** - Add promotions, holidays (Phase 3)
2. **More data** - Longer history improves accuracy
3. **Method tuning** - Optimize hyperparameters
4. **Data quality** - Clean outliers, fill gaps

---

## 9. Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2025-12-09 | Initial industry-standard ranges | Phase 2B completion |
| 2025-12-09 | Reverted adjusted ranges | Maintain honest benchmarks |
| 2025-12-09 | Added performance status system | Honest reporting to clients |

---

*Industry standards should not be adjusted to match results. If we don't meet standards, we improve or flag - not change the goalpost.*
