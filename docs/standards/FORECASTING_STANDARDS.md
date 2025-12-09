# Forecasting Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for forecasting methodology, model selection, and accuracy expectations.

---

## 1. SKU Classification Standards

### ABC Classification (Volume/Revenue)

| Class | Criteria | Description |
|-------|----------|-------------|
| **A** | Top 80% of revenue/volume | High-value, high-priority SKUs |
| **B** | Next 15% of revenue/volume | Medium-value SKUs |
| **C** | Bottom 5% of revenue/volume | Low-value SKUs |

### XYZ Classification (Variability)

| Class | Coefficient of Variation (CV) | Description |
|-------|-------------------------------|-------------|
| **X** | CV < 0.5 | Low variability, stable demand |
| **Y** | 0.5 ≤ CV < 1.0 | Medium variability |
| **Z** | CV ≥ 1.0 | High variability, erratic demand |

### Demand Patterns

| Pattern | Criteria | Description |
|---------|----------|-------------|
| **Regular** | ADI < 1.32 | Consistent demand with few gaps |
| **Intermittent** | ADI ≥ 1.32, CV² < 0.49 | Sporadic but predictable size |
| **Lumpy** | ADI ≥ 1.32, CV² ≥ 0.49 | Sporadic and variable size |

*ADI = Average Demand Interval (days between non-zero sales)*

---

## 2. Method Selection Standards

### Recommended Methods by Classification

| Classification | Pattern | Recommended Method |
|----------------|---------|-------------------|
| A-X | Regular | Chronos-2 |
| A-Y | Regular | Chronos-2 |
| A-Z | Regular | Chronos-2 |
| A-Z | Lumpy | SBA |
| B-X | Regular | Chronos-2 |
| B-Y | Regular | Chronos-2 |
| B-Z | Regular | Chronos-2 |
| B-Z | Lumpy | SBA |
| C-X | Regular | MA7 |
| C-Y | Regular | MA7 |
| C-Z | Any | Min/Max |
| Any | Intermittent | Croston |
| Any | Lumpy | SBA |

### Method Descriptions

| Method | Type | Best For |
|--------|------|----------|
| **Chronos-2** | ML (Transformer) | Regular demand, high-value SKUs |
| **SBA** | Statistical | Lumpy demand |
| **Croston** | Statistical | Intermittent demand |
| **Min/Max** | Rules-based | C-Z SKUs (low value, high variability) |
| **MA7** | Statistical | Baseline, simple patterns |

---

## 3. Accuracy Standards

### Expected MAPE Ranges

| Classification | Expected MAPE | Notes |
|----------------|---------------|-------|
| A-X | 10-25% | Excellent forecastability |
| A-Y | 20-40% | Good forecastability |
| A-Z | 30-60% | Moderate forecastability |
| B-X | 15-30% | Good forecastability |
| B-Y | 25-50% | Moderate forecastability |
| B-Z | 40-70% | Challenging |
| C-* | 50-100% | Low priority, acceptable |
| Lumpy | 50-90% | Inherently difficult |
| Intermittent | 40-80% | Specialized methods required |

### Accuracy Metrics

| Metric | Formula | Use Case |
|--------|---------|----------|
| **MAPE** | Mean Absolute Percentage Error | Primary accuracy metric |
| **MAE** | Mean Absolute Error | Scale-dependent comparison |
| **RMSE** | Root Mean Squared Error | Penalizes large errors |
| **Bias** | Mean Error | Detects systematic over/under-forecasting |
| **WMAPE** | Weighted MAPE | Aggregate accuracy |

---

## 4. Data Requirements

### Minimum History

| SKU Type | Minimum Days | Recommended |
|----------|--------------|-------------|
| Regular | 30 | 90+ |
| Intermittent | 60 | 180+ |
| Lumpy | 60 | 180+ |
| New Product | 14 | 30+ |

### Data Quality Requirements

- No missing dates (gaps will be filled with zeros)
- Numeric values only (no text in quantity fields)
- Consistent time frequency (daily)
- Outlier detection and handling

---

## 5. Forecast Horizon Standards

| Use Case | Horizon | Frequency |
|----------|---------|-----------|
| Short-term operations | 7 days | Daily |
| Inventory planning | 30 days | Weekly |
| Strategic planning | 90 days | Monthly |

---

## 6. Compliance

All forecasting implementations must:

1. ✅ Use the recommended method for each SKU classification
2. ✅ Calculate and report MAPE for all forecasts
3. ✅ Flag SKUs outside expected MAPE ranges
4. ✅ Store classification data in the database
5. ✅ Log method selection decisions

---

*This standard is mandatory for all forecasting operations.*

