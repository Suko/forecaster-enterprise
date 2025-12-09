# Validation Module Plan

**Date:** 2025-12-08  
**Status:** 📋 **Planning**  
**Purpose:** Dedicated module for validating algorithms with messy real-world data

---

## The Problem

> "We have messy data. How do we validate our classification algorithms work correctly?"

**Current State:**
- ✅ Basic data validation (`data_validator.py`) - handles clean data
- ✅ Unit tests - test with clean synthetic data
- ❌ **Missing:** Validation for messy real-world data
- ❌ **Missing:** Classification algorithm validation
- ❌ **Missing:** Edge case testing framework

---

## Proposed Structure

```
forecasting/
├── services/          # Business logic (existing)
├── modes/            # Forecasting models (existing)
├── validation/       # NEW: Validation & testing module
│   ├── __init__.py
│   ├── data_quality/      # Data quality assessment
│   │   ├── messy_data_handler.py
│   │   ├── outlier_detector.py
│   │   ├── missing_data_analyzer.py
│   │   └── data_quality_scorer.py
│   ├── classification/    # Classification validation
│   │   ├── abc_validator.py
│   │   ├── xyz_validator.py
│   │   ├── pattern_validator.py
│   │   └── classification_tester.py
│   ├── edge_cases/        # Edge case testing
│   │   ├── short_history.py
│   │   ├── zero_demand.py
│   │   ├── extreme_outliers.py
│   │   └── intermittent_test.py
│   └── ground_truth/      # Ground truth comparison
│       ├── known_patterns.py
│       ├── synthetic_generator.py
│       └── accuracy_validator.py
```

---

## Module 1: Data Quality Assessment

### Purpose
Handle messy real-world data before classification/forecasting.

### Components

#### 1.1 `messy_data_handler.py`
**Handles:**
- Missing values (gaps, NULLs)
- Inconsistent formats
- Duplicate records
- Out-of-order dates
- Mixed data types

**Methods:**
```python
class MessyDataHandler:
    def detect_issues(self, df: pd.DataFrame) -> Dict[str, List]:
        """Detect all data quality issues"""
    
    def clean_data(self, df: pd.DataFrame, strategy: str) -> pd.DataFrame:
        """Clean data with specified strategy"""
    
    def assess_cleanliness(self, df: pd.DataFrame) -> float:
        """Score data quality (0-1)"""
```

#### 1.2 `outlier_detector.py`
**Detects:**
- Statistical outliers (Z-score, IQR)
- Temporal outliers (sudden spikes/drops)
- Contextual outliers (unusual for this SKU)

**Methods:**
```python
class OutlierDetector:
    def detect_statistical(self, series: pd.Series) -> List[int]:
        """Z-score, IQR methods"""
    
    def detect_temporal(self, series: pd.Series) -> List[int]:
        """Sudden changes"""
    
    def detect_contextual(self, series: pd.Series, context: Dict) -> List[int]:
        """Unusual for this SKU type"""
```

#### 1.3 `missing_data_analyzer.py`
**Analyzes:**
- Missing date patterns (random vs systematic)
- Missing value patterns (MCAR, MAR, MNAR)
- Impact on forecasting

**Methods:**
```python
class MissingDataAnalyzer:
    def analyze_pattern(self, df: pd.DataFrame) -> str:
        """MCAR, MAR, or MNAR?"""
    
    def estimate_impact(self, df: pd.DataFrame) -> Dict:
        """How much does missing data affect accuracy?"""
```

#### 1.4 `data_quality_scorer.py`
**Scores:**
- Overall data quality (0-1)
- Completeness score
- Consistency score
- Accuracy score

**Output:**
```python
{
    "overall_score": 0.75,
    "completeness": 0.90,  # 90% of dates present
    "consistency": 0.80,   # 80% consistent format
    "accuracy": 0.70,      # 70% no outliers
    "issues": [
        {"type": "missing_dates", "count": 15, "severity": "medium"},
        {"type": "outliers", "count": 3, "severity": "low"}
    ]
}
```

---

## Module 2: Classification Validation

### Purpose
Validate ABC-XYZ classification algorithms work correctly.

### Components

#### 2.1 `abc_validator.py`
**Validates:**
- ABC classification accuracy
- Revenue calculation correctness
- Class boundaries (80/15/5 split)

**Methods:**
```python
class ABCValidator:
    def validate_classification(
        self, 
        skus: List[str], 
        ground_truth: Dict[str, str]
    ) -> Dict:
        """Compare predicted vs ground truth"""
    
    def validate_boundaries(self, revenue_dict: Dict) -> bool:
        """Check 80/15/5 split is correct"""
```

#### 2.2 `xyz_validator.py`
**Validates:**
- XYZ classification accuracy
- CV calculation correctness
- Class boundaries (0.5, 1.0)

**Methods:**
```python
class XYZValidator:
    def validate_classification(
        self,
        skus: List[str],
        ground_truth: Dict[str, str]
    ) -> Dict:
        """Compare predicted vs ground truth"""
    
    def validate_cv_calculation(self, series: pd.Series) -> float:
        """Verify CV = std/mean"""
```

#### 2.3 `pattern_validator.py`
**Validates:**
- Demand pattern detection (regular, intermittent, lumpy)
- ADI calculation
- Pattern classification accuracy

**Methods:**
```python
class PatternValidator:
    def validate_pattern(
        self,
        series: pd.Series,
        expected_pattern: str
    ) -> bool:
        """Check if pattern detected correctly"""
    
    def validate_adi(self, series: pd.Series) -> float:
        """Verify ADI calculation"""
```

#### 2.4 `classification_tester.py`
**Orchestrates:**
- End-to-end classification testing
- Multiple SKU testing
- Performance benchmarking

**Methods:**
```python
class ClassificationTester:
    def test_classification_accuracy(
        self,
        test_skus: List[str],
        ground_truth: Dict[str, Dict]
    ) -> Dict:
        """Test classification on known SKUs"""
    
    def benchmark_performance(self, n_skus: int) -> Dict:
        """Benchmark classification speed"""
```

---

## Module 3: Edge Case Testing

### Purpose
Test edge cases that break normal algorithms.

### Components

#### 3.1 `short_history.py`
**Tests:**
- < 7 days of history
- < 30 days of history
- New products

**Scenarios:**
```python
test_cases = [
    {"days": 3, "expected": "insufficient"},
    {"days": 7, "expected": "minimal"},
    {"days": 30, "expected": "limited"},
]
```

#### 3.2 `zero_demand.py`
**Tests:**
- All zero sales
- Mostly zero sales (>90%)
- Intermittent zeros

**Scenarios:**
```python
test_cases = [
    {"zero_pct": 100, "expected": "no_demand"},
    {"zero_pct": 95, "expected": "intermittent"},
    {"zero_pct": 50, "expected": "regular"},
]
```

#### 3.3 `extreme_outliers.py`
**Tests:**
- Single extreme spike
- Multiple outliers
- Outlier impact on classification

**Scenarios:**
```python
test_cases = [
    {"outlier_type": "single_spike", "magnitude": 10x},
    {"outlier_type": "multiple", "count": 5},
]
```

#### 3.4 `intermittent_test.py`
**Tests:**
- True intermittent (ADI > 1.32)
- Lumpy demand (ADI > 1.32, CV² > 0.49)
- Classification accuracy

---

## Module 4: Ground Truth Comparison

### Purpose
Compare classification results against known ground truth.

### Components

#### 4.1 `known_patterns.py`
**Stores:**
- Known SKU classifications (from M5 dataset, etc.)
- Synthetic SKUs with known patterns
- Test cases with expected results

**Structure:**
```python
KNOWN_PATTERNS = {
    "SKU_AX_001": {
        "abc": "A",
        "xyz": "X",
        "pattern": "regular",
        "cv": 0.3,
        "adi": 1.0,
        "expected_method": "chronos2"
    },
    "SKU_CZ_001": {
        "abc": "C",
        "xyz": "Z",
        "pattern": "lumpy",
        "cv": 2.5,
        "adi": 2.0,
        "expected_method": "min_max"
    }
}
```

#### 4.2 `synthetic_generator.py`
**Generates:**
- SKUs with known characteristics
- Controlled patterns (A-X, B-Y, C-Z, etc.)
- Edge cases (intermittent, lumpy)

**Methods:**
```python
class SyntheticGenerator:
    def generate_sku(
        self,
        abc_class: str,
        xyz_class: str,
        pattern: str,
        days: int = 365
    ) -> pd.DataFrame:
        """Generate SKU with known characteristics"""
```

#### 4.3 `accuracy_validator.py`
**Validates:**
- Classification accuracy vs ground truth
- Method routing correctness
- Overall system accuracy

**Methods:**
```python
class AccuracyValidator:
    def validate_classification(
        self,
        predictions: Dict[str, Dict],
        ground_truth: Dict[str, Dict]
    ) -> Dict:
        """Calculate accuracy metrics"""
    
    def validate_method_routing(
        self,
        skus: List[str],
        expected_methods: Dict[str, str]
    ) -> Dict:
        """Check if correct method was used"""
```

---

## Integration with Existing Code

### How It Fits

```
User uploads messy data
        ↓
┌─────────────────────────┐
│ validation/data_quality │  ← NEW: Assess & clean
│   messy_data_handler     │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│ services/data_validator  │  ← Existing: Basic validation
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│ validation/classification│  ← NEW: Classify SKUs
│   classification_tester  │
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│ services/forecast_service│  ← Existing: Generate forecast
└─────────────────────────┘
        ↓
┌─────────────────────────┐
│ validation/ground_truth  │  ← NEW: Validate results
│   accuracy_validator     │
└─────────────────────────┘
```

---

## Usage Examples

### Example 1: Validate Classification on Messy Data

```python
from forecasting.validation.data_quality import MessyDataHandler
from forecasting.validation.classification import ClassificationTester

# 1. Handle messy data
handler = MessyDataHandler()
clean_df = handler.clean_data(messy_df, strategy="aggressive")

# 2. Test classification
tester = ClassificationTester()
results = tester.test_classification_accuracy(
    test_skus=["SKU001", "SKU002"],
    ground_truth=KNOWN_PATTERNS
)

# 3. Validate accuracy
print(f"ABC Accuracy: {results['abc_accuracy']:.2%}")
print(f"XYZ Accuracy: {results['xyz_accuracy']:.2%}")
```

### Example 2: Test Edge Cases

```python
from forecasting.validation.edge_cases import ShortHistoryTester

tester = ShortHistoryTester()
results = tester.test_all_scenarios()

# Results show which edge cases break our algorithms
```

### Example 3: Generate Synthetic Test Data

```python
from forecasting.validation.ground_truth import SyntheticGenerator

generator = SyntheticGenerator()

# Generate known test cases
sku_ax = generator.generate_sku("A", "X", "regular", days=365)
sku_cz = generator.generate_sku("C", "Z", "lumpy", days=365)

# Test classification on known data
```

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Messy Data Handling** | Dedicated tools for real-world data |
| **Validation** | Test algorithms before production |
| **Edge Cases** | Find breaking points early |
| **Ground Truth** | Compare against known results |
| **Confidence** | Know algorithms work correctly |

---

## Implementation Plan

### Phase 1: Data Quality (Week 1)
- [ ] `messy_data_handler.py`
- [ ] `outlier_detector.py`
- [ ] `data_quality_scorer.py`

### Phase 2: Classification Validation (Week 2)
- [ ] `abc_validator.py`
- [ ] `xyz_validator.py`
- [ ] `pattern_validator.py`
- [ ] `classification_tester.py`

### Phase 3: Edge Cases (Week 3)
- [ ] `short_history.py`
- [ ] `zero_demand.py`
- [ ] `extreme_outliers.py`

### Phase 4: Ground Truth (Week 4)
- [ ] `known_patterns.py`
- [ ] `synthetic_generator.py`
- [ ] `accuracy_validator.py`

---

## Next Steps

1. **Create module structure** - Set up `forecasting/validation/` directory
2. **Start with data quality** - Most critical for messy data
3. **Add classification validation** - Test Phase 2A algorithms
4. **Build edge case tests** - Find breaking points
5. **Create ground truth dataset** - Known test cases

---

*Planning document - Ready to implement*

