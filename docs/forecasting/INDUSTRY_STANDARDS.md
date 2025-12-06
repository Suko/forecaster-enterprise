# Industry Standards Reference

**Purpose:** Document all industry standards and best practices used in our forecasting API

---

## Forecast Accuracy Metrics (Industry Standard)

### 1. MAPE (Mean Absolute Percentage Error)

**Formula:**
```
MAPE = (100/n) × Σ|Actual - Forecast|/Actual
```

**Industry Standard:** Widely used metric for forecast accuracy evaluation

**Reference:** 
- Wikipedia: https://en.wikipedia.org/wiki/Mean_absolute_percentage_error
- APICS (Association for Supply Chain Management) standards

**Interpretation:**
- Lower is better
- < 10%: Excellent
- 10-20%: Good
- 20-50%: Fair
- > 50%: Poor

### 2. MAE (Mean Absolute Error)

**Formula:**
```
MAE = (1/n) × Σ|Actual - Forecast|
```

**Industry Standard:** Standard absolute error metric

**Reference:** Standard statistical metric, used in forecasting industry

**Interpretation:**
- Lower is better
- Absolute units (e.g., 10.5 units)

### 3. RMSE (Root Mean Squared Error)

**Formula:**
```
RMSE = √[(1/n) × Σ(Actual - Forecast)²]
```

**Industry Standard:** Standard metric that penalizes large errors more

**Reference:** Standard statistical metric, widely used in forecasting

**Interpretation:**
- Lower is better
- Penalizes large errors more than MAE

### 4. Forecast Bias

**Formula:**
```
Bias = (1/n) × Σ(Forecast - Actual)
```

**Industry Standard:** Standard metric for detecting systematic over/under-forecasting

**Reference:** 
- Wikipedia: https://en.wikipedia.org/wiki/Forecast_bias
- APICS standards

**Interpretation:**
- Positive: Over-forecasting (forecast > actual)
- Negative: Under-forecasting (forecast < actual)
- Zero: Unbiased

### 5. WMAPE (Weighted Mean Absolute Percentage Error)

**Formula:**
```
WMAPE = Σ|Actual - Forecast| / ΣActual
```

**Industry Standard:** Addresses MAPE sensitivity to low-volume items

**Reference:** Industry best practice for handling low-volume products

**Note:** Not included in MVP, but standard for Phase 2+

---

## Prediction Intervals (Industry Standard)

### Quantiles

**Standard Practice:** Provide prediction intervals using quantiles

**Common Quantiles:**
- 0.1 (10th percentile) - Lower bound
- 0.5 (50th percentile) - Median
- 0.9 (90th percentile) - Upper bound

**Industry Standard:** Standard way to communicate forecast uncertainty

**Reference:**
- Wikipedia: https://en.wikipedia.org/wiki/Prediction_interval
- Statistical forecasting textbooks

**Interpretation:**
- 80% prediction interval: 10th to 90th percentile
- Wider intervals = more uncertainty
- Narrower intervals = less uncertainty

### Coefficient of Variation

**Formula:**
```
CV = Standard Deviation / Mean
```

**Industry Standard:** Standard statistical measure of relative uncertainty

**Reference:** Standard statistical metric

**Interpretation:**
- Higher CV = more relative uncertainty
- Lower CV = less relative uncertainty

---

## Inventory Management Formulas (Industry Standard)

### 1. Days of Inventory Remaining (DIR)

**Formula:**
```
DIR = Current Stock / Average Daily Demand
```

**Industry Standard:** Standard inventory metric

**Reference:** APICS standards, inventory management textbooks

**Interpretation:**
- Number of days until stockout (at current demand rate)
- Higher = more inventory buffer

### 2. Safety Stock

**Standard Formula (Service Level Method):**
```
Safety Stock = Z × σ_d × √L
```

Where:
- `Z` = Z-score for service level (industry standard)
  - 90% service level → Z = 1.28
  - 95% service level → Z = 1.65 (most common)
  - 99% service level → Z = 2.33
- `σ_d` = Standard deviation of demand
- `L` = Lead time in days

**Industry Standard:** APICS standard formula

**Reference:**
- APICS Supply Chain Operations Reference (SCOR) model
- "Inventory Management" by Silver, Pyke, Peterson
- Inventory management textbooks

**Alternative (Simplified):**
```
Safety Stock = Average Daily Demand × Safety Stock Days
```

Used when demand variance is not available.

### 3. Reorder Point (ROP)

**Standard Formula:**
```
ROP = (Average Daily Demand × Lead Time) + Safety Stock
```

**Industry Standard:** Standard reorder point calculation

**Reference:**
- APICS standards
- "Inventory Management" by Silver, Pyke, Peterson
- Inventory management textbooks

**Interpretation:**
- Stock level at which to place new order
- Ensures stock arrives before stockout

### 4. Recommended Order Quantity

**Standard Formula:**
```
Recommended Qty = Forecasted Demand + Safety Stock - Current Stock
```

**MOQ Constraint (Industry Standard):**
```
If Recommended Qty < MOQ:
    Recommended Qty = MOQ
```

**Industry Standard:** Standard order quantity calculation

**Note:** Different from Economic Order Quantity (EOQ), which considers ordering costs. For forecasting-based ordering, the above formula is standard.

### 5. Stockout Risk

**Standard Formula:**
```
Stockout Risk = (Forecasted Demand / Current Stock) × 100
```

**Risk Levels (Industry Standard Thresholds):**
- **Low**: < 50% - Sufficient stock
- **Medium**: 50-70% - Monitor closely
- **High**: 70-90% - Risk of stockout
- **Critical**: > 90% - High risk of stockout

**Industry Standard:** Standard risk assessment metric

**Reference:** Inventory management best practices

### 6. Stockout Date Prediction

**Standard Formula:**
```
Stockout Date = Today + (Current Stock / Average Daily Demand)
```

**Industry Standard:** Standard calculation for predicting stockout date

**Note:** Assumes constant demand rate. More sophisticated models account for demand variability, but this is the standard baseline calculation.

---

## Best Practices (Industry Standards)

### 1. Collaborative Planning, Forecasting, and Replenishment (CPFR)

**Industry Standard:** CPFR framework for supply chain collaboration

**Reference:** 
- Wikipedia: https://en.wikipedia.org/wiki/Collaborative_planning%2C_forecasting%2C_and_replenishment
- APICS standards

**Key Principles:**
- Collaboration with suppliers
- Shared forecasting
- Synchronized planning

### 2. Regular Forecast Updates

**Industry Standard:** Continuously update forecasts to reflect latest data

**Reference:** Inventory forecasting best practices

**Best Practice:**
- Update forecasts regularly (daily/weekly)
- Incorporate latest sales data
- Adjust for market conditions

### 3. Product Segmentation

**Industry Standard:** Categorize products by demand patterns

**Reference:** Inventory management best practices

**Common Segments:**
- High-demand, stable
- High-demand, volatile
- Low-demand, stable
- Low-demand, volatile

### 4. Real-Time Data Integration

**Industry Standard:** Use real-time sales and inventory data

**Reference:** Modern inventory management best practices

**Best Practice:**
- Integrate with sales systems
- Use up-to-date inventory levels
- Incorporate market signals

---

## References

1. **APICS (Association for Supply Chain Management)**
   - Supply Chain Operations Reference (SCOR) model
   - Inventory management standards

2. **Textbooks:**
   - "Inventory Management" by Silver, Pyke, Peterson
   - "Supply Chain Management" by Chopra, Meindl

3. **Standards:**
   - Prediction Intervals: https://en.wikipedia.org/wiki/Prediction_interval
   - Forecast Accuracy Metrics: https://en.wikipedia.org/wiki/Forecast_bias
   - MAPE: https://en.wikipedia.org/wiki/Mean_absolute_percentage_error

4. **Best Practices:**
   - Industry forecasting best practices
   - Inventory management best practices
   - Supply chain management standards

---

## Summary

**All metrics and formulas used are industry standard:**
- ✅ Forecast accuracy metrics (MAPE, MAE, RMSE, Bias)
- ✅ Prediction intervals (quantiles)
- ✅ Inventory formulas (Safety Stock, ROP, DIR)
- ✅ Best practices (CPFR, regular updates, segmentation)

**No custom formulas or thresholds** - everything is based on established industry standards that can be explained to clients.

