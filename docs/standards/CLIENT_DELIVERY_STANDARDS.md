# Client Delivery Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for delivering forecasting capabilities to clients.

---

## 1. Forecast Delivery

### API Response Format

```json
{
  "forecast_run_id": "uuid",
  "status": "completed",
  "items": [
    {
      "item_id": "SKU001",
      "classification": {
        "abc_class": "A",
        "xyz_class": "X",
        "demand_pattern": "regular",
        "forecastability_score": 0.85,
        "recommended_method": "chronos2",
        "expected_mape_range": [10, 25]
      },
      "predictions": [
        {
          "date": "2025-12-10",
          "point_forecast": 125.5,
          "quantiles": {
            "p10": 100.0,
            "p50": 125.5,
            "p90": 150.0
          }
        }
      ],
      "method_used": "chronos-2"
    }
  ],
  "quality_metrics": {
    "average_mape": 15.2,
    "skus_within_range": 85
  }
}
```

### Required Fields

| Field | Required | Description |
|-------|----------|-------------|
| `forecast_run_id` | ✅ | Unique identifier |
| `status` | ✅ | completed, failed, pending |
| `item_id` | ✅ | SKU identifier |
| `point_forecast` | ✅ | Primary forecast value |
| `p10`, `p90` | ✅ | Uncertainty bounds |
| `classification` | ✅ | SKU classification info |
| `method_used` | ✅ | Forecasting method |

---

## 2. Classification Reporting

### Client-Facing Classification

| Internal Class | Client Label | Description |
|----------------|--------------|-------------|
| A-X | High Priority - Stable | High volume, predictable |
| A-Y | High Priority - Variable | High volume, moderate variability |
| A-Z | High Priority - Challenging | High volume, high variability |
| B-* | Medium Priority | Medium volume |
| C-* | Low Priority | Low volume |

### Forecastability Communication

| Score | Label | Message |
|-------|-------|---------|
| 0.8-1.0 | Excellent | "High confidence forecasts" |
| 0.6-0.8 | Good | "Reliable forecasts with some uncertainty" |
| 0.4-0.6 | Moderate | "Forecasts available but monitor closely" |
| 0.2-0.4 | Limited | "High uncertainty - use safety stock" |
| 0.0-0.2 | Poor | "Forecasting not recommended" |

---

## 3. Accuracy Guarantees

### What We Promise

| Scenario | Guarantee |
|----------|-----------|
| A-X SKUs | MAPE ≤ 25% (90% of SKUs) |
| A-Y SKUs | MAPE ≤ 40% (80% of SKUs) |
| Lumpy demand | MAPE ≤ 90% (70% of SKUs) |
| Overall portfolio | WMAPE ≤ 30% |

### What We Don't Promise

- 100% accuracy for any SKU
- Predictions for new products (< 14 days history)
- Accuracy during major disruptions (COVID, etc.)

### Disclaimers

Include in all client communications:

> "Forecasts are predictions based on historical data. Actual results may vary due to market conditions, promotions, or other factors not captured in the model."

---

## 4. Error Handling

### Client-Facing Error Messages

| Internal Error | Client Message |
|----------------|----------------|
| No data | "Insufficient history for this SKU" |
| Model failure | "Forecast temporarily unavailable" |
| Invalid input | "Please check SKU identifier" |
| Service unavailable | "System maintenance in progress" |

### Error Response Format

```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_HISTORY",
  "message": "This SKU requires at least 30 days of history",
  "item_id": "SKU001",
  "recommendation": "Use manual forecasting until more data is available"
}
```

---

## 5. Documentation for Clients

### Required Deliverables

| Document | Content |
|----------|---------|
| API Documentation | Endpoints, request/response formats |
| Integration Guide | How to connect and use the API |
| Classification Guide | What classifications mean |
| FAQ | Common questions and answers |

### Onboarding Checklist

- [ ] API credentials provided
- [ ] Test environment access
- [ ] Documentation shared
- [ ] Initial data import complete
- [ ] First forecast generated
- [ ] Accuracy review meeting scheduled

---

## 6. Performance SLAs

### Response Time

| Endpoint | Target | Maximum |
|----------|--------|---------|
| Generate forecast | 30 seconds | 60 seconds |
| Get results | 2 seconds | 5 seconds |
| Classification | 5 seconds | 10 seconds |

### Availability

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Planned maintenance | < 4 hours/month |
| Incident response | < 30 minutes |

---

## 7. Data Requirements

### Client Data Format

| Field | Required | Format |
|-------|----------|--------|
| `item_id` | ✅ | String (max 255 chars) |
| `date` | ✅ | YYYY-MM-DD |
| `units_sold` | ✅ | Numeric (≥ 0) |
| `client_id` | ✅ | UUID |

### Data Quality Requirements

- Daily granularity
- No gaps > 7 days
- Consistent SKU identifiers
- Historical period ≥ 30 days

---

## 8. Support Tiers

### Standard Support

- Email support (business hours)
- Response within 24 hours
- Documentation access

### Premium Support

- Dedicated account manager
- Phone support
- 4-hour response time
- Custom integrations

### Enterprise Support

- 24/7 support
- 1-hour response time
- Custom SLAs
- Dedicated infrastructure

---

## 9. Compliance

All client deliveries must:

1. ✅ Include required API fields
2. ✅ Provide classification information
3. ✅ Use client-friendly error messages
4. ✅ Meet response time SLAs
5. ✅ Include accuracy disclaimers

---

*This standard is mandatory for all client interactions.*

