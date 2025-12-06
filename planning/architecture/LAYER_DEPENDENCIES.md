# Layer Dependencies & Interaction

**Purpose:** Define how layers interact and depend on each other

---

## Dependency Graph

```
┌─────────────────────────────────────────────────────────┐
│  backend/api/ (API Routes - Existing Structure)         │
│  - Routes follow existing pattern                       │
│  Dependencies: forecasting/services                     │
└──────────────────┬──────────────────────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────────────────────┐
│  forecasting/services/ (Service Orchestration)          │
│  - Orchestrates all forecasting layers                  │
│  Dependencies: applications, modes, features, core       │
└──────────────────┬──────────────────────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────────────────────┐
│  applications/ (Business Applications)                   │
│  - Inventory, Profitability, Demand Planning            │
│  Dependencies: core, modes, features                      │
└──────────────────┬──────────────────────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────────────────────┐
│  modes/ (Forecasting Methods)                            │
│  - ML Models, Statistical Methods                       │
│  Dependencies: core, features                            │
└──────────────────┬──────────────────────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────────────────────┐
│  features/ (Features & Covariates)                      │
│  - Covariates, Transformers, Validators                 │
│  Dependencies: core                                      │
└──────────────────┬──────────────────────────────────────┘
                   │ depends on
┌──────────────────▼──────────────────────────────────────┐
│  core/ (Pure Forecasting)                                │
│  - Models, Pipelines, Utils                             │
│  Dependencies: NONE (lowest layer)                       │
└─────────────────────────────────────────────────────────┘
```

---

## Dependency Rules

### ✅ Allowed Dependencies

1. **interfaces** → **applications** ✅
2. **interfaces** → **modes** ✅
3. **interfaces** → **features** ✅
4. **interfaces** → **core** ✅
5. **applications** → **modes** ✅
6. **applications** → **features** ✅
7. **applications** → **core** ✅
8. **modes** → **features** ✅
9. **modes** → **core** ✅
10. **features** → **core** ✅

### ❌ Forbidden Dependencies

1. **core** → **features** ❌
2. **core** → **modes** ❌
3. **core** → **applications** ❌
4. **core** → **interfaces** ❌
5. **features** → **modes** ❌
6. **features** → **applications** ❌
7. **features** → **interfaces** ❌
8. **modes** → **applications** ❌
9. **modes** → **interfaces** ❌
10. **applications** → **interfaces** ❌

**Key Rule:** Lower layers NEVER depend on higher layers.

---

## Layer Responsibilities

### Core Layer
- **Can use:** Nothing (lowest layer)
- **Can be used by:** All layers above
- **Purpose:** Pure forecasting logic, no business rules

### Features Layer
- **Can use:** Core layer only
- **Can be used by:** Modes, Applications, Interfaces
- **Purpose:** Feature engineering, covariates

### Modes Layer
- **Can use:** Core, Features
- **Can be used by:** Applications, Interfaces
- **Purpose:** Forecasting methods (ML, statistical)

### Applications Layer
- **Can use:** Core, Features, Modes
- **Can be used by:** Interfaces only
- **Purpose:** Business applications (inventory, profitability)

### Service Orchestration Layer
- **Can use:** All forecasting layers below
- **Can be used by:** `backend/api/` (existing structure)
- **Purpose:** Service orchestration, business logic coordination

### Backend API Layer (Existing Structure)
- **Can use:** `forecasting/services/` and existing `backend/services/`
- **Can be used by:** External (API clients)
- **Purpose:** API endpoints (follows existing pattern)

---

## Import Examples

### ✅ Correct Imports

```python
# features/covariates/holiday.py
from forecasting.core.utils import date_utils  # ✅ Core layer

# modes/ml/chronos2.py
from forecasting.core.models import BaseForecastModel  # ✅ Core layer
from forecasting.features.covariates import HolidayCovariate  # ✅ Features layer

# applications/inventory/calculator.py
from forecasting.core.models import BaseForecastModel  # ✅ Core layer
from forecasting.modes.factory import ModelFactory  # ✅ Modes layer
from forecasting.features.covariates import PromoCovariate  # ✅ Features layer

# forecasting/services/forecast_service.py
from forecasting.applications.inventory import InventoryCalculator  # ✅ Applications
from forecasting.modes.factory import ModelFactory  # ✅ Modes
from forecasting.features.covariates import CovariateService  # ✅ Features
from forecasting.core.pipelines import ForecastPipeline  # ✅ Core

# backend/api/forecast.py
from schemas.forecast import ForecastRequest  # ✅ Existing backend structure
from forecasting.services.forecast_service import ForecastService  # ✅ Forecasting module
```

### ❌ Incorrect Imports

```python
# core/utils/validation.py
from forecasting.features.covariates import HolidayCovariate  # ❌ Core can't use Features

# features/covariates/holiday.py
from forecasting.modes.ml import Chronos2Model  # ❌ Features can't use Modes

# modes/ml/chronos2.py
from forecasting.applications.inventory import InventoryCalculator  # ❌ Modes can't use Applications

# backend/api/forecast.py
from forecasting.core.models import BaseForecastModel  # ❌ API routes should use services, not core directly
```

---

## Testing Dependencies

### Unit Tests
- Test each layer in isolation
- Mock dependencies from lower layers
- No dependencies on higher layers

### Integration Tests
- Test layer interactions
- Use real implementations from lower layers
- Mock external dependencies (databases, APIs)

---

## Benefits

1. **Clear Boundaries:** Easy to understand what depends on what
2. **Testability:** Each layer can be tested independently
3. **Maintainability:** Changes isolated to specific layers
4. **Scalability:** Easy to add new components to each layer
5. **Reusability:** Lower layers reusable across applications

