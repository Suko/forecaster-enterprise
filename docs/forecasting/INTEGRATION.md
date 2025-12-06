# Backend Integration Guide

**Purpose:** How forecasting module integrates with existing backend structure

---

## Existing Backend Structure

```
backend/
├── api/                    # API routes (existing)
│   └── auth.py            # Auth routes
├── schemas/                # Pydantic schemas (existing)
│   └── auth.py            # Auth schemas
├── services/               # Business logic services (existing)
│   ├── auth_service.py
│   └── user_service.py
├── models/                 # Database models (existing)
│   └── user.py
└── ... (other existing files)
```

---

## Forecasting Module Integration

### Where Forecasting Code Lives

```
backend/
├── forecasting/                    # NEW: Forecasting module
│   ├── core/                       # Pure forecasting
│   ├── features/                   # Features & covariates
│   ├── modes/                      # Forecasting methods
│   ├── applications/               # Business applications
│   └── services/                   # Service orchestration
│
├── api/                            # EXISTING: API routes
│   ├── auth.py                     # Existing
│   └── forecast.py                 # NEW: Forecast routes
│
├── schemas/                         # EXISTING: Schemas
│   ├── auth.py                     # Existing
│   └── forecast.py                 # NEW: Forecast schemas
│
└── services/                        # EXISTING: Services
    ├── auth_service.py             # Existing
    ├── user_service.py             # Existing
    └── (forecasting services are in forecasting/services/)
```

---

## Integration Pattern

### API Routes

**Location:** `backend/api/forecast.py` (follows existing pattern)

**Pattern:** Same as `backend/api/auth.py`

```python
# backend/api/forecast.py
from fastapi import APIRouter, Depends
from schemas.forecast import ForecastRequest, ForecastResponse
from forecasting.services.forecast_service import ForecastService
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["forecast"])

@router.post("/forecast", response_model=ForecastResponse)
async def create_forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    service: ForecastService = Depends(get_forecast_service)
):
    """Forecast endpoint - follows existing pattern"""
    return await service.generate_forecast(request, current_user)
```

### Schemas

**Location:** `backend/schemas/forecast.py` (follows existing pattern)

**Pattern:** Same as `backend/schemas/auth.py`

```python
# backend/schemas/forecast.py
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ForecastRequest(BaseModel):
    """Forecast request schema"""
    item_ids: List[str] = Field(..., min_items=1)
    prediction_length: int = Field(..., ge=1, le=365)
    # ... follows existing schema pattern

class ForecastResponse(BaseModel):
    """Forecast response schema"""
    forecast_id: str
    # ... follows existing schema pattern
```

### Services

**Location:** `forecasting/services/forecast_service.py` (module-specific)

**Pattern:** Orchestrates forecasting module layers

```python
# forecasting/services/forecast_service.py
from forecasting.modes.factory import ModelFactory
from forecasting.features.covariates import CovariateService
from forecasting.core.pipelines import ForecastPipeline

class ForecastService:
    """Forecast orchestration service"""
    def __init__(
        self,
        model_factory: ModelFactory,
        covariate_service: CovariateService,
        pipeline: ForecastPipeline
    ):
        # Orchestrates forecasting module
```

---

## Dependency Injection

### Service Registration

```python
# backend/api/forecast.py or backend/core/dependencies.py
from forecasting.services.forecast_service import ForecastService
from forecasting.modes.factory import ModelFactory
from forecasting.features.covariates import CovariateService
from forecasting.core.pipelines import ForecastPipeline

def get_forecast_service() -> ForecastService:
    """Dependency injection for forecast service"""
    model_factory = ModelFactory()
    covariate_service = CovariateService()
    pipeline = ForecastPipeline()
    
    return ForecastService(
        model_factory=model_factory,
        covariate_service=covariate_service,
        pipeline=pipeline
    )
```

### FastAPI Integration

```python
# backend/main.py
from api import auth, forecast  # Import forecast routes

app = FastAPI(...)

# Include existing routers
app.include_router(auth.router)

# Include new forecast router
app.include_router(forecast.router)
```

---

## File Organization

### What Goes Where

| Component | Location | Reason |
|-----------|----------|--------|
| API Routes | `backend/api/forecast.py` | Follows existing pattern |
| Schemas | `backend/schemas/forecast.py` | Follows existing pattern |
| Service Orchestration | `forecasting/services/forecast_service.py` | Module-specific |
| Core Logic | `forecasting/core/` | Module-specific |
| Features | `forecasting/features/` | Module-specific |
| Models | `forecasting/modes/` | Module-specific |
| Applications | `forecasting/applications/` | Module-specific |

---

## Import Examples

### From API Route

```python
# backend/api/forecast.py
from schemas.forecast import ForecastRequest  # Existing backend structure
from forecasting.services.forecast_service import ForecastService  # Forecasting module
```

### From Service

```python
# forecasting/services/forecast_service.py
from forecasting.modes.factory import ModelFactory  # Forecasting module
from forecasting.features.covariates import CovariateService  # Forecasting module
from forecasting.core.pipelines import ForecastPipeline  # Forecasting module
```

### From Core

```python
# forecasting/core/models/base.py
# No imports from other layers (lowest layer)
```

---

## Benefits

1. **Consistency:** API routes and schemas follow existing backend patterns
2. **Separation:** Forecasting module is self-contained
3. **Integration:** Easy to integrate with existing backend
4. **Maintainability:** Clear boundaries between backend and forecasting module

---

## Summary

- **API Routes:** `backend/api/forecast.py` (follows existing pattern)
- **Schemas:** `backend/schemas/forecast.py` (follows existing pattern)
- **Forecasting Module:** `backend/forecasting/` (self-contained module)
- **Service Orchestration:** `forecasting/services/` (module-specific)
- **Integration:** Uses FastAPI dependency injection (same as auth)

