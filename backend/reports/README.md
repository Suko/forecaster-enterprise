# Forecast Accuracy Test Reports

This directory contains detailed JSON reports from forecast accuracy tests.

## Report Format

Each report file (`forecast_accuracy_report_YYYYMMDD_HHMMSS.json`) contains:

### Structure
```json
{
  "test_config": {
    "test_days": 30,
    "prediction_length": 30,
    "max_skus": 20,
    "timestamp": "20241208_153000"
  },
  "summary": {
    "total_tested": 20,
    "successful": 18,
    "failed": 2
  },
  "results": [
    {
      "item_id": "SKU001",
      "status": "success",
      "data_info": {
        "total_days": 731,
        "train_days": 701,
        "test_days": 30,
        "actual_mean": 50.06,
        "actual_std": 18.54,
        "actual_cv": 37.0
      },
      "forecast_run_id": "uuid-here",
      "metrics": {
        "chronos-2": {
          "mape": 18.14,
          "mae": 8.06,
          "rmse": 10.53,
          "bias": -2.55
        },
        "statistical_ma7": {
          "mape": 25.30,
          "mae": 12.45,
          "rmse": 15.20,
          "bias": 1.23
        }
      },
      "validation": {
        "chronos-2": [
          {
            "stage": "INPUT",
            "item_id": "SKU001",
            "data_summary": {...},
            "validation": {...}
          },
          {
            "stage": "OUTPUT",
            "predictions_summary": {...},
            "validation": {...}
          }
        ]
      }
    }
  ]
}
```

## Usage

### Generate Report
```bash
cd backend
uv run python tests/test_forecast_accuracy.py
```

### Analyze Reports
```python
import json

with open('reports/forecast_accuracy_report_20241208_153000.json') as f:
    report = json.load(f)

# Get all MAPE values
mape_values = [
    r["metrics"]["chronos-2"]["mape"]
    for r in report["results"]
    if r["status"] == "success" and "chronos-2" in r["metrics"]
]

print(f"Average MAPE: {sum(mape_values) / len(mape_values):.2f}%")
```

## What to Look For

1. **MAPE < 20%**: Good accuracy
2. **MAPE 20-30%**: Acceptable
3. **MAPE > 30%**: May need investigation

4. **Validation Issues**: Check `validation` field for data quality problems
5. **Bias**: Positive = over-forecasting, Negative = under-forecasting
6. **CV (Coefficient of Variation)**: Higher CV = more variable demand = harder to forecast

## Files

- Reports are auto-generated and should be gitignored
- Keep reports for analysis but don't commit them
- Delete old reports periodically to save space

