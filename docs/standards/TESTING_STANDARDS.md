# Testing Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for testing forecasting models, methods, and system components.

---

## 1. Test Categories

### Unit Tests

| Scope | Location | Framework |
|-------|----------|-----------|
| Model logic | `backend/tests/` | pytest |
| Service functions | `backend/tests/` | pytest |
| Utility functions | `backend/tests/` | pytest |

### Integration Tests

| Scope | Location | Framework |
|-------|----------|-----------|
| API endpoints | `backend/tests/` | pytest + httpx |
| Database operations | `backend/tests/` | pytest + SQLAlchemy |
| End-to-end flows | `backend/tests/` | pytest |

### Validation Tests

| Scope | Location | Framework |
|-------|----------|-----------|
| Model accuracy | `backend/scripts/` | Custom scripts |
| Method routing | `backend/scripts/` | Custom scripts |
| Data quality | `backend/scripts/` | Custom scripts |

---

## 2. Test Data Requirements

### Synthetic Data

- 20 SKUs with controlled patterns
- 2 years of daily history
- Known seasonality and trends
- Located in `data/sintetic_data/`

### Real-World Data (M5)

- 20 diverse SKUs from M5 dataset
- Various demand patterns
- Lumpy, intermittent, regular patterns
- Located in `data/m5/`

### Test Data Coverage

| Pattern | SKUs Required | Purpose |
|---------|---------------|---------|
| Regular (A-X) | 10+ | Baseline accuracy |
| Medium variability (A-Y) | 2+ | Edge case testing |
| High variability (A-Z) | 5+ | Stress testing |
| Lumpy | 5+ | SBA validation |
| Intermittent | 2+ | Croston validation |

---

## 3. Accuracy Testing Standards

### Required Metrics

All accuracy tests must calculate:

| Metric | Required | Notes |
|--------|----------|-------|
| MAPE | ✅ Yes | Primary metric |
| MAE | ✅ Yes | Scale comparison |
| RMSE | ✅ Yes | Large error penalty |
| Bias | ✅ Yes | Systematic error |
| Within-range % | ✅ Yes | Expected vs actual |

### Test Configuration

| Parameter | Standard Value |
|-----------|----------------|
| Test period | Last 30 days |
| Prediction horizon | 7 days |
| Training cutoff | test_start - 1 day |

### Pass/Fail Criteria

| Classification | Pass if MAPE | Notes |
|----------------|--------------|-------|
| A-X | ≤ 25% | Excellent |
| A-Y | ≤ 40% | Good |
| A-Z | ≤ 60% | Acceptable |
| Lumpy | ≤ 90% | Expected |

---

## 4. Method Routing Tests

### Required Validations

1. ✅ Correct method selected for each classification
2. ✅ Fallback logic works when primary fails
3. ✅ Method mapping is accurate
4. ✅ All implemented methods are registered

### Test Cases

| Test | Expected Result |
|------|-----------------|
| A-X regular SKU | Routes to Chronos-2 |
| A-Z lumpy SKU | Routes to SBA |
| Intermittent SKU | Routes to Croston |
| C-Z SKU | Routes to Min/Max |
| Unknown pattern | Falls back to Chronos-2 |

---

## 5. Data Quality Tests

### Input Validation

| Check | Action |
|-------|--------|
| Missing dates | Fill with zeros |
| NaN values | Fill or remove |
| Duplicates | Remove |
| Type errors | Convert or reject |

### Output Validation

| Check | Action |
|-------|--------|
| Correct horizon | Must match request |
| Valid forecasts | No NaN, no negative |
| Quantiles present | P10, P50, P90 |
| Timestamps valid | Future dates only |

---

## 6. Test Documentation

### Required Report Elements

1. **Test name and date**
2. **Purpose**
3. **Data used**
4. **Results table**
5. **Pass/fail status**
6. **Actions (if failed)**

### Report Location

- Save to `/docs/forecasting/test_results/`
- Use naming: `YYYY-MM-DD_test_name.md`
- Reference from active documentation

---

## 7. Continuous Testing

### Before Deployment

- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Accuracy validation complete
- [ ] Method routing validated
- [ ] No regressions detected

### After Changes

- [ ] Re-run affected tests
- [ ] Update documentation
- [ ] Verify no breaking changes

---

## 8. Test Scripts

### Available Scripts

| Script | Purpose |
|--------|---------|
| `test_forecast_accuracy.py` | Full accuracy test |
| `validate_method_routing.py` | Routing validation |
| `test_sba_implementation.py` | SBA model test |
| `test_ma7_vs_chronos2_ay.py` | A-Y comparison |

### Running Tests

```bash
# Unit tests
cd backend && uv run pytest tests/

# Validation scripts
cd backend && uv run python scripts/validate_method_routing.py
```

---

## 9. Compliance

All tests must:

1. ✅ Use standardized test data
2. ✅ Calculate required metrics
3. ✅ Document results
4. ✅ Follow pass/fail criteria
5. ✅ Be reproducible

---

*This standard is mandatory for all testing.*

