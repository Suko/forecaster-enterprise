# Quality Metrics Guide

**Purpose:** Document all available quality/prediction accuracy functions

---

## QualityCalculator Class

**Location:** `backend/forecasting/services/quality_calculator.py`

### Available Methods

#### 1. `calculate_mape(actuals, forecasts)`
**Mean Absolute Percentage Error**

- **Formula:** `MAPE = (100/n) × Σ|Actual - Forecast|/Actual`
- **Industry Standard:** APICS
- **Use Case:** Standard percentage error metric
- **Limitation:** Sensitive to low-volume items (can be inflated)

#### 2. `calculate_mae(actuals, forecasts)`
**Mean Absolute Error**

- **Formula:** `MAE = (1/n) × Σ|Actual - Forecast|`
- **Industry Standard:** Statistical Standard
- **Use Case:** Absolute error in units (not percentage)
- **Advantage:** Not affected by volume

#### 3. `calculate_rmse(actuals, forecasts)`
**Root Mean Squared Error**

- **Formula:** `RMSE = √[(1/n) × Σ(Actual - Forecast)²]`
- **Industry Standard:** Statistical Standard
- **Use Case:** Penalizes large errors more than MAE
- **Advantage:** Better for detecting outliers

#### 4. `calculate_bias(actuals, forecasts)`
**Forecast Bias**

- **Formula:** `Bias = (1/n) × Σ(Forecast - Actual)`
- **Industry Standard:** APICS
- **Use Case:** Detects systematic over/under-forecasting
- **Interpretation:**
  - Positive = over-forecasting
  - Negative = under-forecasting
  - Zero = unbiased

#### 5. `calculate_quality_metrics(client_id, item_id, method, start_date, end_date)`
**Comprehensive Quality Metrics**

- **Returns:** Dictionary with MAPE, MAE, RMSE, Bias, sample_size
- **Use Case:** Get all metrics for a specific item/method from database
- **Requires:** Actual values to be backfilled first

---

## Additional Metrics (Available in Test Scripts)

### 6. WMAPE (Weighted Mean Absolute Percentage Error)
**Better for Low-Volume Items**

- **Formula:** `WMAPE = Σ|Actual - Forecast| / ΣActual × 100`
- **Use Case:** Addresses MAPE sensitivity to low-volume items
- **Advantage:** More stable for products with varying volumes

### 7. Directional Accuracy
**Direction Prediction Accuracy**

- **Formula:** `% of periods where forecast direction matches actual direction`
- **Use Case:** Measures ability to predict trends (up/down)
- **Interpretation:** Higher is better (0-100%)

### 8. R² (Coefficient of Determination)
**Model Fit Quality**

- **Formula:** `R² = 1 - (SS_res / SS_tot)`
- **Use Case:** Measures how well model explains variance
- **Interpretation:**
  - 1.0 = Perfect fit
  - 0.0 = No better than mean
  - Negative = Worse than mean

---

## API Endpoints

### GET `/api/v1/quality/{item_id}`

**Get quality metrics for an item**

**Query Parameters:**
- `start_date` (optional): Start date for analysis
- `end_date` (optional): End date for analysis

**Returns:**
```json
{
  "item_id": "SKU001",
  "period": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "methods": [
    {
      "method": "chronos-2",
      "predictions_count": 100,
      "actuals_count": 100,
      "mape": 15.5,
      "mae": 10.2,
      "rmse": 12.8,
      "bias": -2.1
    },
    {
      "method": "statistical_ma7",
      "predictions_count": 100,
      "actuals_count": 100,
      "mape": 18.3,
      "mae": 12.5,
      "rmse": 15.2,
      "bias": 1.5
    }
  ]
}
```

---

## Usage Examples

### Using QualityCalculator Directly

```python
from forecasting.services.quality_calculator import QualityCalculator

# Static methods (no database needed)
mape = QualityCalculator.calculate_mape(actuals, forecasts)
mae = QualityCalculator.calculate_mae(actuals, forecasts)
rmse = QualityCalculator.calculate_rmse(actuals, forecasts)
bias = QualityCalculator.calculate_bias(actuals, forecasts)

# Instance method (requires database)
quality_calc = QualityCalculator(db)
metrics = await quality_calc.calculate_quality_metrics(
    client_id="...",
    item_id="SKU001",
    method="chronos-2",
    start_date=date(2024, 1, 1),
    end_date=date(2024, 12, 31)
)
```

### In Test Scripts

```python
# Calculate all metrics
quality_calc = QualityCalculator(db)

mape = quality_calc.calculate_mape(actual_values, pred_values)
mae = quality_calc.calculate_mae(actual_values, pred_values)
rmse = quality_calc.calculate_rmse(actual_values, pred_values)
bias = quality_calc.calculate_bias(actual_values, pred_values)

# Additional metrics
wmape = (sum(abs(a - p) for a, p in zip(actuals, preds)) / sum(actuals)) * 100
```

---

## Metric Selection Guide

| Metric | Best For | Limitations |
|--------|----------|-------------|
| **MAPE** | Standard comparison, percentage view | Inflated for low-volume items |
| **WMAPE** | Low-volume items, varying volumes | Less intuitive than MAPE |
| **MAE** | Absolute error, unit-based | Doesn't show percentage |
| **RMSE** | Detecting outliers, large errors | More sensitive to outliers |
| **Bias** | Detecting systematic errors | Doesn't show magnitude |
| **Directional Accuracy** | Trend prediction | Doesn't show magnitude |
| **R²** | Model fit quality | Can be negative |

---

## Industry Standards

All metrics follow industry standards:
- **APICS** (Association for Supply Chain Management)
- **Statistical Standards** (widely accepted in forecasting)

---

*Guide created: 2025-12-08*

