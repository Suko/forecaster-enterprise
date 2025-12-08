# Backend Integration Guide

**Status:** ✅ Complete  
**Scope:** Integration Guide (All Phases)  
**Quick Start:** See [MVP_UNIFIED.md](MVP_UNIFIED.md) for quick reference

---

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
│   ├── core/                       # Core abstractions
│   │   └── models/                 # BaseForecastModel interface
│   ├── modes/                      # Forecasting methods
│   │   ├── ml/                     # ML models (Chronos-2)
│   │   ├── statistical/            # Statistical models (MA7)
│   │   └── factory.py              # ModelFactory
│   ├── applications/               # Business applications
│   │   └── inventory/              # InventoryCalculator
│   └── services/                   # Service orchestration
│       ├── forecast_service.py     # ForecastService (orchestration)
│       ├── data_access.py          # DataAccess (database/test data)
│       └── quality_calculator.py   # QualityCalculator (MAPE/MAE/RMSE)
│
├── api/                            # EXISTING: API routes
│   ├── auth.py                     # Existing
│   └── forecast.py                 # NEW: Forecast routes
│
├── schemas/                         # EXISTING: Schemas
│   ├── auth.py                     # Existing
│   └── forecast.py                 # NEW: Forecast schemas
│
├── models/                          # EXISTING: Database models
│   ├── user.py                     # Existing
│   └── forecast.py                 # NEW: ForecastRun, ForecastResult
│
└── services/                        # EXISTING: Services
    ├── auth_service.py             # Existing
    └── user_service.py             # Existing
    # Note: Forecasting services are in forecasting/services/
```

---

## Integration Pattern

### API Routes

**Location:** `backend/api/forecast.py` (follows existing pattern)

**Pattern:** Same as `backend/api/auth.py`, but supports both JWT and service API key authentication

```python
# backend/api/forecast.py
from fastapi import APIRouter, Depends, Request
from schemas.forecast import ForecastRequest, ForecastResponse
from forecasting.services.forecast_service import ForecastService
from auth.service_auth import get_client_id_from_request_or_token

router = APIRouter(prefix="/api/v1", tags=["forecast"])

@router.post("/forecast", response_model=ForecastResponse)
async def create_forecast(
    request: ForecastRequest,
    request_obj: Request,
    db: AsyncSession = Depends(get_db),
):
    """Forecast endpoint - supports JWT and service API key"""
    # Get client_id from JWT token OR service API key + request body
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=request.client_id,  # Optional: for service calls
        db=db,
    )
    # ... rest of implementation
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
from forecasting.services.data_access import DataAccess
from forecasting.core.models.base import BaseForecastModel

class ForecastService:
    """Forecast orchestration service"""
    def __init__(self, db: AsyncSession, use_test_data: bool = False):
        self.db = db
        self.model_factory = ModelFactory()
        self.data_access = DataAccess(db, use_test_data=use_test_data)
        # Orchestrates forecasting module
```

---

## Dependency Injection

### Service Registration

```python
# backend/api/forecast.py
from forecasting.services.forecast_service import ForecastService
from models import get_db

@router.post("/forecast")
async def create_forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Forecast endpoint"""
    # Service is created with database session
    service = ForecastService(db, use_test_data=True)  # Auto-detect in production
    return await service.generate_forecast(...)
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
| Database Models | `backend/models/forecast.py` | Follows existing pattern |
| Service Orchestration | `forecasting/services/forecast_service.py` | Module-specific |
| Data Access | `forecasting/services/data_access.py` | Module-specific |
| Quality Metrics | `forecasting/services/quality_calculator.py` | Module-specific |
| Core Logic | `forecasting/core/models/base.py` | Module-specific |
| Forecasting Models | `forecasting/modes/` | Module-specific |
| Inventory Calculator | `forecasting/applications/inventory/calculator.py` | Module-specific |

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
from forecasting.services.data_access import DataAccess  # Forecasting module
from forecasting.core.models.base import BaseForecastModel  # Forecasting module
from models.forecast import ForecastRun, ForecastResult  # Backend models
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

