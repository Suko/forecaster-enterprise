# Method Implementation

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document details the implementation of all forecasting methods in the system.

---

## 1. Implemented Methods

| Method | Status | File Location |
|--------|--------|---------------|
| Chronos-2 | ✅ Active | `forecasting/modes/ml/chronos2.py` |
| SBA | ✅ Active | `forecasting/modes/statistical/sba.py` |
| Croston | ✅ Ready | `forecasting/modes/statistical/croston.py` |
| Min/Max | ✅ Ready | `forecasting/modes/statistical/min_max.py` |
| MA7 | ✅ Active | `forecasting/modes/statistical/moving_average.py` |

---

## 2. Chronos-2 (Primary ML Model)

### Overview

| Property | Value |
|----------|-------|
| **Type** | ML (Transformer-based) |
| **Use Case** | Regular demand, high-value SKUs |
| **Model ID** | `chronos-2` |
| **Source** | Amazon Chronos |

### Algorithm

Chronos-2 is a pretrained time series forecasting model based on the T5 architecture. It:

1. Tokenizes time series into discrete bins
2. Uses language model techniques for forecasting
3. Generates probabilistic forecasts (quantiles)

### Implementation

```python
# File: forecasting/modes/ml/chronos2.py

class Chronos2Model(BaseForecastModel):
    def __init__(self):
        self.model_name = "chronos-2"
        self.model_id = "amazon/chronos-t5-small"
        
    async def predict(self, context_df, prediction_length, ...):
        # 1. Prepare time series
        # 2. Generate predictions using pipeline
        # 3. Return DataFrame with forecasts
```

### Input Requirements

| Field | Required | Notes |
|-------|----------|-------|
| `id` | ✅ | SKU identifier |
| `timestamp` | ✅ | Date column |
| `target` | ✅ | Values to forecast |

### Output Format

| Field | Type | Description |
|-------|------|-------------|
| `id` | str | SKU identifier |
| `timestamp` | datetime | Forecast date |
| `point_forecast` | float | Primary prediction |
| `p10` | float | 10th percentile |
| `p50` | float | 50th percentile |
| `p90` | float | 90th percentile |

### Performance

| Classification | Typical MAPE |
|----------------|--------------|
| A-X | 10-25% |
| A-Y | 20-40% |
| A-Z (regular) | 30-60% |

---

## 3. SBA (Syntetos-Boylan Approximation)

### Overview

| Property | Value |
|----------|-------|
| **Type** | Statistical |
| **Use Case** | Lumpy demand |
| **Model ID** | `sba` |

### Algorithm

SBA corrects the bias in Croston's method:

```
ADI = Total days / Non-zero days
ADS = Sum of demand / Non-zero days
SBA_forecast = (ADS / ADI) × (1 - 1/(2×ADI))
```

### Implementation

```python
# File: forecasting/modes/statistical/sba.py

class SBAModel(BaseForecastModel):
    def _calculate_adi(self, series):
        # Average Demand Interval
        return len(series) / (series > 0).sum()
    
    def _calculate_ads(self, series):
        # Average Demand Size
        return series[series > 0].mean()
    
    async def predict(self, context_df, prediction_length, ...):
        adi = self._calculate_adi(target_series)
        ads = self._calculate_ads(target_series)
        sba_forecast = (ads / adi) * (1 - 1 / (2 * adi))
```

### When to Use

| Condition | Use SBA |
|-----------|---------|
| ADI ≥ 1.32 | ✅ Yes |
| CV² ≥ 0.49 | ✅ Yes |
| Lumpy pattern | ✅ Yes |

### Performance

| Scenario | Typical MAPE |
|----------|--------------|
| Lumpy demand | 50-90% |
| Previous (MA7) | 113.8% |
| With SBA | 79.1% |
| **Improvement** | **34.7 points** |

---

## 4. Croston's Method

### Overview

| Property | Value |
|----------|-------|
| **Type** | Statistical |
| **Use Case** | Intermittent demand |
| **Model ID** | `croston` |

### Algorithm

Croston separates demand into two components:

1. **Demand size** (when demand occurs)
2. **Demand interval** (time between demands)

Uses Simple Exponential Smoothing (SES) for both:

```
Forecast = Smoothed_size / Smoothed_interval
```

### Implementation

```python
# File: forecasting/modes/statistical/croston.py

class CrostonModel(BaseForecastModel):
    def __init__(self, alpha=0.1):
        self.alpha = alpha  # Smoothing parameter
    
    async def predict(self, context_df, prediction_length, ...):
        # 1. Extract non-zero demands
        # 2. Calculate intervals
        # 3. Apply SES to both
        # 4. Forecast = smoothed_size / smoothed_interval
```

### When to Use

| Condition | Use Croston |
|-----------|-------------|
| ADI ≥ 1.32 | ✅ Yes |
| CV² < 0.49 | ✅ Yes |
| Intermittent pattern | ✅ Yes |

### Performance

| Scenario | Typical MAPE |
|----------|--------------|
| Intermittent demand | 40-80% |

---

## 5. Min/Max Rules

### Overview

| Property | Value |
|----------|-------|
| **Type** | Rules-based |
| **Use Case** | C-Z SKUs (low value, high variability) |
| **Model ID** | `min_max` |

### Algorithm

Simple average-based forecast for low-value SKUs:

```
Forecast = Average of non-zero demand
Quantiles based on historical min/max spread
```

### Implementation

```python
# File: forecasting/modes/statistical/min_max.py

class MinMaxModel(BaseForecastModel):
    async def predict(self, context_df, prediction_length, ...):
        non_zero = target_series[target_series > 0]
        forecast = non_zero.mean()
        
        # Wider spread for uncertainty (75%)
        p10 = max(0, forecast * 0.25)
        p90 = forecast * 1.75
```

### When to Use

| Condition | Use Min/Max |
|-----------|-------------|
| ABC = C | ✅ Yes |
| XYZ = Z | ✅ Yes |
| Low priority | ✅ Yes |

### Performance

| Scenario | Typical MAPE |
|----------|--------------|
| C-Z SKUs | 50-100% |

---

## 6. MA7 (Moving Average)

### Overview

| Property | Value |
|----------|-------|
| **Type** | Statistical |
| **Use Case** | Baseline, simple patterns |
| **Model ID** | `statistical_ma7` |

### Algorithm

7-day simple moving average:

```
Forecast = Average of last 7 days
```

### Implementation

```python
# File: forecasting/modes/statistical/moving_average.py

class MovingAverageModel(BaseForecastModel):
    def __init__(self, window=7):
        self.window = window
    
    async def predict(self, context_df, prediction_length, ...):
        forecast = target_series.tail(self.window).mean()
```

### When to Use

| Scenario | Use MA7 |
|----------|---------|
| Baseline comparison | ✅ Yes |
| Simple patterns | ✅ Yes |
| C-X SKUs | ✅ Yes |

### Performance

| Classification | Typical MAPE |
|----------------|--------------|
| Stable (A-X) | 15-30% |
| Variable | 50-100%+ |

---

## 7. Method Routing

### Routing Logic

```python
# In forecast_service.py

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

| Classification | Pattern | Routed To |
|----------------|---------|-----------|
| A-X | Regular | chronos-2 |
| A-Y | Regular | chronos-2 |
| A-Z | Regular | chronos-2 |
| A-Z | Lumpy | sba |
| B-* | Regular | chronos-2 |
| B-* | Lumpy | sba |
| C-X | Regular | statistical_ma7 |
| C-Y | Regular | statistical_ma7 |
| C-Z | Any | min_max |
| Any | Intermittent | croston |
| Any | Lumpy | sba |

### Routing Validation Results

| Metric | Result |
|--------|--------|
| Routing correctness | 100% (40/40) |
| Methods used | Chronos-2 (29), SBA (11) |
| Within expected MAPE | 60% (24/40) |

---

## 8. Model Factory

### Registration

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
```

### Usage

```python
model = ModelFactory.create_model("sba")
await model.initialize()
predictions = await model.predict(context_df, prediction_length)
```

---

## 9. Adding New Methods

### Steps

1. Create new file in `forecasting/modes/statistical/` or `forecasting/modes/ml/`
2. Inherit from `BaseForecastModel`
3. Implement `initialize()`, `predict()`, `get_model_info()`
4. Register in `ModelFactory`
5. Add to method mapping in `forecast_service.py`
6. Update `sku_classifier.py` routing logic
7. Add tests

### Template

```python
from forecasting.core.models.base import BaseForecastModel

class NewModel(BaseForecastModel):
    def __init__(self):
        super().__init__(model_name="new_model")
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def predict(self, context_df, prediction_length, ...):
        # Implementation
        pass
    
    def get_model_info(self) -> dict:
        return {"name": "New Model", "type": "statistical"}
```

---

*This document is the official reference for method implementation.*

