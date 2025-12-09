# Phase 2 Kickoff - SKU Classification & Forecasting Strategy

**Date:** 2025-12-08  
**Status:** 🎯 **Ready to Start**  
**Prerequisite:** Phase 1 Complete ✅

---

## The Problem We Solve

> "Customer uploads data, many SKUs have 50%+ MAPE. What do we do?"

**Reality:** Not all SKUs are forecastable with the same method or accuracy.

---

## Phase 2A: SKU Classification (ABC-XYZ)

### Industry Standard Approach

**ABC-XYZ Classification** is used by:
- ✅ SAP IBP
- ✅ Oracle Demand Planning  
- ✅ Blue Yonder
- ✅ o9 Solutions
- ✅ Amazon, Walmart, Target

### The Classification Matrix

```
            Volume (ABC Analysis)
            A (High)     B (Medium)    C (Low)
          ┌────────────┬────────────┬────────────┐
X (Low    │    A-X     │    B-X     │    C-X     │  Forecastable
Variab.)  │  ML Model  │  ML Model  │  ML Model  │  MAPE < 30%
          ├────────────┼────────────┼────────────┤
Y (Medium │    A-Y     │    B-Y     │    C-Y     │  Medium
Variab.)  │  ML Model  │  ML Model  │  Safety+   │  MAPE 30-50%
          ├────────────┼────────────┼────────────┤
Z (High   │    A-Z     │    B-Z     │    C-Z     │  Hard to forecast
Variab.)  │  Attention │  Rules     │  Min/Max   │  MAPE > 50%
          └────────────┴────────────┴────────────┘
```

### Classification Criteria

| Class | Volume (ABC) | Criteria |
|-------|--------------|----------|
| **A** | Top 80% of revenue | ~20% of SKUs |
| **B** | Next 15% of revenue | ~30% of SKUs |
| **C** | Bottom 5% of revenue | ~50% of SKUs |

| Class | Variability (XYZ) | Criteria (CV = CoeffVar) |
|-------|-------------------|--------------------------|
| **X** | Low variability | CV < 0.5 |
| **Y** | Medium variability | 0.5 ≤ CV < 1.0 |
| **Z** | High variability | CV ≥ 1.0 |

### Additional Classifications

| Pattern | Detection | Method |
|---------|-----------|--------|
| **Intermittent** | ADI > 1.32 | Croston's method |
| **Lumpy** | ADI > 1.32 AND CV² > 0.49 | SBA (Syntetos-Boylan) |
| **Seasonal** | Seasonal decomposition | Seasonal models |
| **New Product** | < 90 days history | Analogy-based |

> **ADI** = Average Demand Interval (days between sales)  
> **CV** = Coefficient of Variation (std/mean)

---

## Implementation Plan

### Step 1: SKU Classifier Service

```python
# New service: forecasting/services/sku_classifier.py

class SKUClassifier:
    """
    Classifies SKUs using ABC-XYZ analysis.
    Industry standard for demand planning.
    """
    
    def classify_sku(self, history_df: pd.DataFrame) -> SKUClassification:
        """Returns classification with recommended method."""
        return SKUClassification(
            abc_class="A",      # Volume class
            xyz_class="X",      # Variability class
            demand_pattern="regular",  # regular/intermittent/lumpy/seasonal
            forecastability_score=0.85,
            recommended_method="chronos2",
            expected_mape_range=(15, 25),
            warnings=[]
        )
```

### Step 2: Method Router

```python
# Routing logic based on classification

ROUTING_RULES = {
    # High value, low variability → Best model
    ("A", "X"): {"method": "chronos2", "safety_factor": 1.0},
    ("B", "X"): {"method": "chronos2", "safety_factor": 1.0},
    ("C", "X"): {"method": "chronos2", "safety_factor": 1.1},
    
    # Medium variability → ML with higher safety
    ("A", "Y"): {"method": "chronos2", "safety_factor": 1.2},
    ("B", "Y"): {"method": "chronos2", "safety_factor": 1.3},
    ("C", "Y"): {"method": "ma7", "safety_factor": 1.5},
    
    # High variability → Rules-based or attention
    ("A", "Z"): {"method": "chronos2", "safety_factor": 1.5, "flag": "attention"},
    ("B", "Z"): {"method": "ma7", "safety_factor": 2.0},
    ("C", "Z"): {"method": "min_max", "safety_factor": 2.0},
}

INTERMITTENT_ROUTING = {
    "intermittent": {"method": "croston", "safety_factor": 1.5},
    "lumpy": {"method": "sba", "safety_factor": 2.0},
}
```

### Step 3: Database Schema Addition

```sql
-- Add classification to ts_demand_daily or create separate table
ALTER TABLE ts_demand_daily ADD COLUMN IF NOT EXISTS
    sku_classification JSONB;

-- Or separate classification table (recommended)
CREATE TABLE sku_classifications (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    
    -- ABC-XYZ
    abc_class CHAR(1),  -- A, B, C
    xyz_class CHAR(1),  -- X, Y, Z
    
    -- Demand Pattern
    demand_pattern VARCHAR(50),  -- regular, intermittent, lumpy, seasonal, new
    
    -- Metrics
    coefficient_of_variation DECIMAL(10,4),
    average_demand_interval DECIMAL(10,4),
    revenue_contribution DECIMAL(10,4),
    
    -- Forecasting
    forecastability_score DECIMAL(5,4),  -- 0.0 to 1.0
    recommended_method VARCHAR(50),
    expected_mape_min DECIMAL(5,2),
    expected_mape_max DECIMAL(5,2),
    
    -- Metadata
    classification_date TIMESTAMP,
    history_days_used INTEGER,
    
    UNIQUE(client_id, item_id)
);
```

### Step 4: API Response Enhancement

```json
{
  "forecast_run_id": "abc123",
  "item_id": "SKU001",
  "classification": {
    "abc_class": "A",
    "xyz_class": "Y",
    "demand_pattern": "regular",
    "forecastability_score": 0.72,
    "expected_accuracy": "MAPE 25-40%"
  },
  "method_used": "chronos2",
  "predictions": [...],
  "confidence": {
    "level": "medium",
    "reason": "Medium variability SKU"
  },
  "recommendations": [
    "Consider higher safety stock for this SKU",
    "Review for promotional patterns"
  ]
}
```

---

## Phase 2B: Covariates (After Classification)

Once SKU classification is working, covariates become more valuable:

| Covariate | Applies To | Impact |
|-----------|-----------|--------|
| **Promotions** | A-Z, B-Z SKUs | Explains spikes |
| **Holidays** | All SKUs | Calendar patterns |
| **Marketing** | A-class SKUs | High-value items |
| **Seasonality** | Seasonal SKUs | Pattern modeling |

---

## Phase 3: Hierarchical Forecasting (Future)

**Multi-location aggregation and reconciliation** - See `HIERARCHICAL_FORECASTING_STRATEGY.md`

**Why Phase 3?**
- ✅ Phase 2A (Classification) solves the immediate problem (high MAPE)
- ✅ Phase 2B (Covariates) improves accuracy for existing forecasts
- ⏳ Phase 3 (Hierarchical) is advanced optimization for multi-location clients

**When to prioritize Phase 3:**
- Multiple clients with multi-location needs
- After Phase 2A & 2B are stable
- When aggregation would significantly improve accuracy

---

## Success Metrics

### Phase 2A Goals

| Metric | Target |
|--------|--------|
| SKU classification accuracy | > 90% correct |
| Method routing working | All 9 categories |
| API returns classification | ✅ |
| User can filter by class | ✅ |

### Business Value

| Outcome | Measurement |
|---------|-------------|
| Reduced "bad" forecasts | Fewer MAPE > 100% |
| Right method per SKU | Method diversification |
| Clear expectations | Users understand accuracy |
| Actionable recommendations | "Use min/max for C-Z" |

---

## Implementation Order

### Phase 2A: SKU Classification (4-5 weeks)

```
Week 1-2: SKU Classifier
├── ABC analysis (revenue-based)
├── XYZ analysis (variability-based)
├── Demand pattern detection
└── Unit tests

Week 3: Method Router
├── Routing rules
├── Integration with ForecastService
└── Integration tests

Week 4: API & UI
├── Classification endpoint
├── Enhanced forecast response
└── Recommendations system

Week 5: Testing & Validation
├── Test on all 20 SKUs
├── Validate classification accuracy
└── Performance benchmarks
```

### Phase 2B: Covariates (2-3 weeks)

```
Week 6-7: Covariate Integration
├── Covariate data model
├── Integration with Chronos-2
└── Accuracy improvement validation

Week 8: Testing
├── Test with real covariate data
└── Compare accuracy with/without covariates
```

### Phase 3: Hierarchical Forecasting (Future)

See `HIERARCHICAL_FORECASTING_STRATEGY.md` for details.

---

## References

### Academic
- Silver, E.A. (1998) - Inventory Management
- Syntetos & Boylan (2005) - Intermittent demand classification

### Industry
- SAP IBP Documentation
- APICS CPIM Certification Materials
- Gartner Supply Chain Research

---

## Files to Create

```
forecasting/services/
├── sku_classifier.py      # New: Classification logic
├── method_router.py       # New: Routing logic
└── croston.py             # New: Intermittent demand model

models/
└── sku_classification.py  # New: SQLAlchemy model

tests/test_forecasting/
├── test_sku_classifier.py
└── test_method_router.py
```

---

*Phase 2 Ready to Start: 2025-12-08*
