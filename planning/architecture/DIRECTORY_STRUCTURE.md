# Directory Structure - Complete View

**Purpose:** Complete directory structure for forecasting module

---

## Complete Structure

```
backend/
├── forecasting/                          # Forecasting module
│   ├── __init__.py
│   │
│   ├── core/                             # Layer 1: Pure Forecasting
│   │   ├── __init__.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── base.py                   # BaseForecastModel
│   │   ├── pipelines/
│   │   │   ├── __init__.py
│   │   │   └── forecast_pipeline.py      # Core forecasting pipeline
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validation.py             # Data validation
│   │       ├── date_utils.py             # Date utilities
│   │       └── data_conversion.py        # Data format conversion
│   │
│   ├── features/                         # Layer 2: Features & Covariates
│   │   ├── __init__.py
│   │   ├── covariates/
│   │   │   ├── __init__.py
│   │   │   ├── holiday.py                # Holiday covariates
│   │   │   ├── promo.py                  # Promotion covariates
│   │   │   ├── marketing.py              # Marketing covariates
│   │   │   └── calendar.py               # Calendar features
│   │   ├── transformers/
│   │   │   ├── __init__.py
│   │   │   ├── scaling.py                # Data scaling
│   │   │   └── aggregation.py            # Data aggregation
│   │   └── validators/
│   │       ├── __init__.py
│   │       └── feature_validator.py      # Feature validation
│   │
│   ├── modes/                            # Layer 3: Forecasting Methods
│   │   ├── __init__.py
│   │   ├── ml/
│   │   │   ├── __init__.py
│   │   │   ├── chronos2.py               # Chronos-2 model
│   │   │   ├── chronos_bolt.py          # Chronos-Bolt model
│   │   │   └── timesfm.py                # TimesFM model (future)
│   │   ├── statistical/
│   │   │   ├── __init__.py
│   │   │   ├── moving_average.py         # Moving average
│   │   │   ├── exponential.py          # Exponential smoothing
│   │   │   └── naive.py                  # Naive forecast
│   │   └── factory.py                    # Model factory
│   │
│   ├── applications/                     # Layer 4: Business Applications
│   │   ├── __init__.py
│   │   ├── inventory/
│   │   │   ├── __init__.py
│   │   │   ├── calculator.py             # Inventory calculator
│   │   │   ├── metrics.py                # Inventory metrics (APICS)
│   │   │   ├── recommendations.py        # Recommendations
│   │   │   └── schemas.py                # Inventory schemas
│   │   └── profitability/
│   │       ├── __init__.py
│   │       └── calculator.py             # Profitability (future)
│   │
│   └── services/                          # Service orchestration
│       ├── __init__.py
│       ├── forecast_service.py            # Forecast orchestration
│       └── inventory_service.py           # Inventory orchestration
│
└── ... (existing backend structure)
    ├── api/                                # API routes (existing)
    │   ├── auth.py                        # Existing
    │   └── forecast.py                    # NEW: Forecast routes
    ├── schemas/                            # Schemas (existing)
    │   ├── auth.py                        # Existing
    │   └── forecast.py                    # NEW: Forecast schemas
    └── services/                           # Services (existing)
        ├── auth_service.py                # Existing
        └── user_service.py                # Existing
│
└── tests/
    └── forecasting/
        ├── core/
        │   ├── test_models.py
        │   ├── test_pipelines.py
        │   └── test_utils.py
        ├── features/
        │   ├── test_covariates.py
        │   └── test_transformers.py
        ├── modes/
        │   ├── test_ml_models.py
        │   └── test_statistical.py
        ├── applications/
        │   └── test_inventory.py
        └── interfaces/
            ├── test_routes.py
            └── test_services.py
```

---

## File Count by Layer

- **Core:** ~5 files
- **Features:** ~8 files
- **Modes:** ~7 files
- **Applications:** ~5 files
- **Interfaces:** ~6 files
- **Tests:** ~10 files

**Total:** ~41 files

---

## Import Paths

### From Core
```python
from forecasting.core.models import BaseForecastModel
from forecasting.core.pipelines import ForecastPipeline
from forecasting.core.utils import validation, date_utils
```

### From Features
```python
from forecasting.features.covariates import HolidayCovariate, PromoCovariate
from forecasting.features.transformers import scaling
```

### From Modes
```python
from forecasting.modes.ml import Chronos2Model
from forecasting.modes.statistical import MovingAverageModel
from forecasting.modes.factory import ModelFactory
```

### From Applications
```python
from forecasting.applications.inventory import InventoryCalculator
from forecasting.applications.inventory.metrics import calculate_safety_stock
```

### From Backend API (Existing Structure)
```python
# backend/api/forecast.py
from schemas.forecast import ForecastRequest
from forecasting.services.forecast_service import ForecastService
```

### From Forecasting Services
```python
# forecasting/services/forecast_service.py
from forecasting.modes.factory import ModelFactory
from forecasting.features.covariates import CovariateService
```

---

## Benefits

1. **Clear Organization:** Easy to find code by layer
2. **Scalability:** Easy to add new components
3. **Testability:** Clear test boundaries
4. **Maintainability:** Changes isolated to layers
5. **Reusability:** Lower layers reusable

