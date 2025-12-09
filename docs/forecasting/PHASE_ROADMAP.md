# Forecasting System - Phase Roadmap

**Last Updated:** 2025-12-08  
**Current Status:** Phase 1 Complete ✅

---

## Phase Overview

| Phase | Focus | Duration | Status |
|-------|-------|----------|--------|
| **Phase 1** | Core Forecasting | ✅ Complete | Basic models working |
| **Phase 2A** | SKU Classification | 4-5 weeks | 🎯 **Next** |
| **Phase 2B** | Covariates | 2-3 weeks | ⏳ After 2A |
| **Phase 3** | Hierarchical Forecasting | 4-6 weeks | 🔮 Future |

---

## Phase 1: Core Forecasting ✅

**Status:** ✅ **Complete**

**What we built:**
- ✅ Chronos-2 ML model
- ✅ MA7 statistical baseline
- ✅ Enhanced data validator
- ✅ API endpoints
- ✅ Multi-tenant architecture
- ✅ Comprehensive testing

**Results:**
- ✅ All 20 SKUs tested
- ✅ Chronos-2 best on 19/20 SKUs
- ✅ Average MAPE: 25-40% (acceptable for MVP)

---

## Phase 2A: SKU Classification 🎯

**Status:** 🎯 **Next Priority**

**Problem:** Many SKUs have high MAPE (50%+). What do we do?

**Solution:** ABC-XYZ Classification + Method Routing

**What we'll build:**
- SKU classifier (ABC-XYZ analysis)
- Method router (different models per SKU type)
- Forecastability scoring
- User recommendations

**Timeline:** 4-5 weeks

**See:** `PHASE_2_KICKOFF.md`

---

## Phase 2B: Covariates ⏳

**Status:** ⏳ **After Phase 2A**

**What we'll build:**
- Promotion flag support
- Holiday indicators
- Marketing spend integration
- Calendar features

**Timeline:** 2-3 weeks

**See:** `COVARIATES_ROADMAP.md`

---

## Phase 3: Hierarchical Forecasting 🔮

**Status:** 🔮 **Future (After Phase 2)**

**Problem:** Multi-location clients - should we forecast separately or aggregate?

**Solution:** Bottom-up with reconciliation

**What we'll build:**
- Location aggregation logic
- Hierarchical reconciliation
- Multi-level forecasting

**Timeline:** 4-6 weeks

**When to prioritize:**
- Multiple clients with multi-location needs
- After Phase 2A & 2B are stable
- When aggregation would significantly improve accuracy

**See:** `HIERARCHICAL_FORECASTING_STRATEGY.md`

---

## Decision Logic: What Phase Next?

```
IF many SKUs have MAPE > 50%:
    → Phase 2A (SKU Classification) ✅ NEXT

ELIF classification working AND need better accuracy:
    → Phase 2B (Covariates)

ELIF multiple locations per SKU AND aggregation would help:
    → Phase 3 (Hierarchical Forecasting)
```

---

## Current Priority: Phase 2A

**Why Phase 2A first?**
1. ✅ Solves immediate problem (high MAPE)
2. ✅ Sets right expectations (user knows which SKUs are hard)
3. ✅ Routes to right method (not all SKUs need ML)
4. ✅ Industry standard (used by SAP, Oracle, etc.)

**After Phase 2A:**
- Users understand forecastability
- System uses appropriate methods
- High MAPE is expected for certain SKU types
- Clear recommendations for each SKU

---

*Roadmap last updated: 2025-12-08*

