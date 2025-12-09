# Project Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## 1. Forecasting Standards

### SKU Classification

| ABC Class | Criteria | XYZ Class | CV Range |
|-----------|----------|-----------|----------|
| **A** | Top 80% revenue | **X** | CV < 0.5 |
| **B** | Next 15% revenue | **Y** | 0.5 ≤ CV < 1.0 |
| **C** | Bottom 5% revenue | **Z** | CV ≥ 1.0 |

### Demand Patterns

| Pattern | Criteria | Method |
|---------|----------|--------|
| **Regular** | ADI < 1.32 | Chronos-2 |
| **Intermittent** | ADI ≥ 1.32, CV² < 0.49 | Croston |
| **Lumpy** | ADI ≥ 1.32, CV² ≥ 0.49 | SBA |

### Method Selection

| Classification | Pattern | Method |
|----------------|---------|--------|
| A-X, A-Y, A-Z | Regular | Chronos-2 |
| A-Z, B-Z | Lumpy | SBA |
| Any | Intermittent | Croston |
| C-Z | Any | Min/Max |
| C-X, C-Y | Regular | MA7 |

### Expected MAPE Ranges

| Classification | Expected | Notes |
|----------------|----------|-------|
| A-X | 10-25% | Excellent |
| A-Y | 20-40% | Good |
| A-Z | 30-60% | Moderate |
| Lumpy | 50-90% | Specialized |
| Intermittent | 40-80% | Specialized |

---

## 2. Evaluation Standards

### Primary Metrics

| Metric | Formula | Use |
|--------|---------|-----|
| **MAPE** | Σ\|actual-forecast\|/actual × 100 | Primary accuracy |
| **MAE** | Σ\|actual-forecast\|/n | Absolute error |
| **RMSE** | √(Σ(actual-forecast)²/n) | Penalize large errors |
| **Bias** | Σ(forecast-actual)/n | Over/under forecasting |

### Pass/Fail Criteria

| Classification | Pass if MAPE |
|----------------|--------------|
| A-X | ≤ 25% |
| A-Y | ≤ 40% |
| A-Z | ≤ 60% |
| Lumpy | ≤ 90% |

---

## 3. Testing Standards

### Test Categories

| Type | Location | Purpose |
|------|----------|---------|
| Unit | `backend/tests/` | Model logic |
| Integration | `backend/tests/` | API endpoints |
| Validation | `backend/scripts/` | Model accuracy |

### Test Data

- **Synthetic:** 20 SKUs, `data/sintetic_data/`
- **Real:** 20 M5 SKUs, `data/m5/`

### Running Tests

```bash
cd backend && uv run pytest tests/
cd backend && uv run python scripts/validate_method_routing.py
```

---

## 4. Documentation Standards

### File Structure

```
docs/
├── README.md              # Entry point
├── backend/              # Backend + forecasting docs
├── standards/            # This file
├── system/               # System contracts
└── reports/              # Audit reports
```

### Naming Conventions

- Use `UPPERCASE_WITH_UNDERSCORES.md`
- Be descriptive but concise

### Required Sections

1. Title with metadata (version, date)
2. Purpose
3. Content
4. References (if applicable)

---

## 5. Versioning Policy

### Semantic Versioning

```
MAJOR.MINOR.PATCH
```

| Component | When to Increment |
|-----------|-------------------|
| MAJOR | Breaking changes |
| MINOR | New features |
| PATCH | Bug fixes |

### Current Versions

| Component | Version |
|-----------|---------|
| API | v1.0.0 |
| chronos-2 | v1.0.0 |
| sba | v1.0.0 |
| croston | v1.0.0 |

---

## 6. Client Delivery Standards

### API Response Format

```json
{
  "forecast_run_id": "uuid",
  "status": "completed",
  "items": [{
    "item_id": "SKU001",
    "classification": {"abc_class": "A", "xyz_class": "X"},
    "predictions": [{"date": "2025-12-10", "point_forecast": 125.5}],
    "method_used": "chronos-2"
  }]
}
```

### Performance SLAs

| Endpoint | Target | Maximum |
|----------|--------|---------|
| Generate forecast | 30s | 60s |
| Get results | 2s | 5s |

### Data Requirements

- Daily granularity
- No gaps > 7 days
- Minimum 30 days history

---

## Compliance

All implementations must:

1. ✅ Use recommended method for each classification
2. ✅ Calculate and report MAPE
3. ✅ Follow semantic versioning
4. ✅ Meet response time SLAs
5. ✅ Pass all tests before deployment

---

*This document consolidates all project standards.*


