# Test Bed: System Validation & Method Selection

## Overview

The Test Bed demonstrates how the system **automatically validates and selects** the best forecasting method for each SKU using **ABC-XYZ classification**.

## How System Validation Works

### 1. **SKU Classification (Automatic)**

When you generate a forecast, the system:

1. **Analyzes the SKU** using historical sales data:
   - **ABC Classification** (Volume): A (top 80% revenue), B (next 15%), C (bottom 5%)
   - **XYZ Classification** (Variability): X (low CV < 0.5), Y (medium 0.5-1.0), Z (high ≥ 1.0)
   - **Demand Pattern**: Regular, Intermittent, or Lumpy

2. **Recommends a Method** based on classification:
   ```
   A-X (High value, low variability) → Chronos-2
   B-X, C-X → Chronos-2
   A-Y, B-Y → Chronos-2
   C-Y → Moving Average (7-day)
   A-Z → Chronos-2 (with warnings)
   B-Z → Moving Average
   C-Z → Min-Max (simple rules)
   Lumpy demand → SBA (Syntetos-Boylan)
   Intermittent demand → Croston
   ```

3. **Stores Classification** in the forecast response:
   - `classification.abc_class`: A, B, or C
   - `classification.xyz_class`: X, Y, or Z
   - `classification.recommended_method`: System's recommended method
   - `classification.forecastability_score`: 0.0-1.0
   - `classification.expected_mape_range`: [min, max]

### 2. **Method Selection Priority**

The system uses this priority:

1. **User Selection** (if explicitly chosen) → `primary_model`
2. **System Recommendation** (from classification) → `recommended_method`
3. **Default** → Chronos-2

**In Test Bed:**
- You can select any model manually
- System still calculates and shows its recommendation
- Table shows which method the system would choose

### 3. **What the Table Shows**

The **Model Comparison Table** displays:

| Column | Description |
|--------|-------------|
| **Model** | Forecast method name |
| **MAPE** | Mean Absolute Percentage Error (daily accuracy) |
| **RMSE** | Root Mean Squared Error |
| **MAE** | Mean Absolute Error (for safety stock) |
| **Bias** | Systematic over/under-forecasting |
| **Samples** | Number of forecast-actual pairs |
| **System Recommendation** | ✓ if this is the system's recommended method |

### 4. **Visual Indicators**

**In the Model column:**
- **Green "✓ Recommended" badge** appears next to the system's recommended method
- Based on ABC-XYZ classification

**In the System Recommendation column:**
- **"✓ System Choice"** for the recommended method
- **"—"** for other methods (if classification exists)
- **"No classification"** if SKU hasn't been classified yet

## Example Scenario

**SKU Classification:**
- ABC: **A** (high revenue)
- XYZ: **X** (low variability)
- Demand Pattern: **Regular**
- **System Recommendation:** `chronos-2`

**Table Display:**
```
Model              | MAPE  | RMSE | MAE | System Recommendation
Chronos-2          | 39.0% | 1.75 | 0.92| ✓ System Choice
Moving Average (7) | 43.5% | 1.80 | 0.95| —
SBA                | 45.2% | 1.85 | 0.98| —
```

**What This Means:**
- System recommends **Chronos-2** for this A-X SKU
- Chronos-2 has **best MAPE** (39.0% vs 43.5%)
- You can still use other methods, but system suggests Chronos-2

## Why This Matters

### For Inventory Ordering

1. **System Recommendation** = Best method for this SKU type
2. **MAPE** = Daily accuracy (lower is better for operations)
3. **MAE** = Safety stock calculation (lower = less buffer needed)

**Decision:**
- Use **system's recommended method** (usually best MAPE)
- Or choose method with **lowest MAPE** if different
- Add safety stock based on **MAE** of chosen method

### For Validation

The Test Bed lets you:
- ✅ **Verify** system recommendations are correct
- ✅ **Compare** all methods side-by-side
- ✅ **See** which method has best metrics
- ✅ **Understand** why system chose a specific method

## Technical Details

### Classification Logic

**File:** `backend/forecasting/services/sku_classifier.py`

```python
def recommend_method(abc_class, xyz_class, demand_pattern):
    if demand_pattern == "lumpy":
        return "sba"
    elif demand_pattern == "intermittent":
        return "croston"
    
    combined = f"{abc_class}-{xyz_class}"
    routing = {
        "A-X": "chronos2",
        "B-X": "chronos2",
        "C-X": "chronos2",
        "A-Y": "chronos2",
        "B-Y": "chronos2",
        "C-Y": "ma7",
        "A-Z": "chronos2",
        "B-Z": "ma7",
        "C-Z": "min_max",
    }
    return routing.get(combined, "chronos2")
```

### Forecast Response Structure

**File:** `backend/schemas/forecast.py`

```python
class ItemForecast:
    item_id: str
    method_used: str
    predictions: List[Prediction]
    classification: Optional[SKUClassificationInfo]  # ← System recommendation here
```

### Frontend Display

**File:** `frontend/app/pages/experiments/testbed.vue`

- Extracts `classification.recommended_method` from forecast response
- Maps classification method names to display names
- Shows badge in table when method matches recommendation
- Updates dynamically when forecast is regenerated

## Summary

**Yes, the system validates and selects methods automatically:**

1. ✅ **Classification** happens automatically (ABC-XYZ analysis)
2. ✅ **Recommendation** is calculated based on SKU characteristics
3. ✅ **Table shows** which method is recommended (green badge)
4. ✅ **You can verify** if the recommendation matches best metrics

**The Test Bed demonstrates this validation process** by showing:
- All available methods side-by-side
- System's recommended method (highlighted)
- Quality metrics for each method
- Why system chose a specific method (based on classification)

