# Forecasting Methods

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## 1. Chronos-2 (Primary ML Model)

| Property | Value |
|----------|-------|
| Type | ML (Transformer-based) |
| Use Case | Regular demand, high-value SKUs |
| File | `forecasting/modes/ml/chronos2.py` |
| Source | Amazon Chronos |

### Performance

| Classification | Typical MAPE |
|----------------|--------------|
| A-X | 10-25% |
| A-Y | 20-40% |
| A-Z (regular) | 30-60% |

---

## 2. SBA (Syntetos-Boylan Approximation)

| Property | Value |
|----------|-------|
| Type | Statistical |
| Use Case | Lumpy demand |
| File | `forecasting/modes/statistical/sba.py` |

### Algorithm

```
ADI = Total days / Non-zero days
ADS = Sum of demand / Non-zero days
SBA_forecast = (ADS / ADI) × (1 - 1/(2×ADI))
```

### When to Use

| Condition | Value |
|-----------|-------|
| ADI | ≥ 1.32 |
| CV² | ≥ 0.49 |
| Pattern | Lumpy |

### Performance

- **Before (MA7):** 113.8% MAPE
- **After (SBA):** 79.1% MAPE
- **Improvement:** 34.7 points

---

## 3. Croston's Method

| Property | Value |
|----------|-------|
| Type | Statistical |
| Use Case | Intermittent demand |
| File | `forecasting/modes/statistical/croston.py` |

### Algorithm

Separates demand into:
1. **Demand size** (when demand occurs)
2. **Demand interval** (time between demands)

```
Forecast = Smoothed_size / Smoothed_interval
```

### When to Use

| Condition | Value |
|-----------|-------|
| ADI | ≥ 1.32 |
| CV² | < 0.49 |
| Pattern | Intermittent |

---

## 4. Min/Max Rules

| Property | Value |
|----------|-------|
| Type | Rules-based |
| Use Case | C-Z SKUs (low value, high variability) |
| File | `forecasting/modes/statistical/min_max.py` |

### Algorithm

```
Forecast = Average of non-zero demand
P10 = forecast × 0.25 (capped at 0)
P90 = forecast × 1.75
```

---

## 5. MA7 (Moving Average)

| Property | Value |
|----------|-------|
| Type | Statistical |
| Use Case | Baseline, simple patterns |
| File | `forecasting/modes/statistical/moving_average.py` |

### Algorithm

```
Forecast = Average of last 7 days
```

---

## Method Routing

### Logic

```python
method_mapping = {
    "chronos2": "chronos-2",
    "ma7": "statistical_ma7",
    "sba": "sba",
    "croston": "croston",
    "min_max": "min_max",
}

# Route based on classification
for item_id in item_ids:
    classification = sku_classifications[item_id]
    recommended = classification.recommended_method
    actual_method = method_mapping.get(recommended, "chronos-2")
```

### Routing Table

| Classification | Pattern | Method |
|----------------|---------|--------|
| A-X, A-Y, A-Z | Regular | chronos-2 |
| A-Z, B-Z | Lumpy | sba |
| Any | Intermittent | croston |
| C-Z | Any | min_max |
| C-X, C-Y | Regular | statistical_ma7 |

### Validation Results

| Metric | Result |
|--------|--------|
| Routing correctness | 100% (40/40) |
| Methods used | Chronos-2 (29), SBA (11) |
| Within expected MAPE | 60% (24/40) |

---

## Model Factory

```python
# File: forecasting/modes/factory.py

class ModelFactory:
    _models = {
        "chronos-2": Chronos2Model,
        "statistical_ma7": MovingAverageModel,
        "sba": SBAModel,
        "croston": CrostonModel,
        "min_max": MinMaxModel,
    }
    
    @classmethod
    def create_model(cls, model_id: str):
        return cls._models[model_id]()
```

---

## Adding New Methods

1. Create file in `forecasting/modes/statistical/` or `forecasting/modes/ml/`
2. Inherit from `BaseForecastModel`
3. Implement `initialize()`, `predict()`, `get_model_info()`
4. Register in `ModelFactory`
5. Add to method mapping in `forecast_service.py`
6. Update routing logic in `sku_classifier.py`
7. Add tests

---

*Official reference for method implementation*


