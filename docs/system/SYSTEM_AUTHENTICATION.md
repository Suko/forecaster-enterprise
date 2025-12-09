# System Authentication for Automated Forecasts

**Status:** ✅ Implemented  
**Date:** 2025-12-06

---

## Overview

The forecasting API supports two authentication methods:

1. **JWT Token** (User calls): Standard user authentication
2. **Service API Key** (System calls): For automated/scheduled forecasts

---

## Authentication Methods

### 1. JWT Token (User Calls)

**Header:**
```
Authorization: Bearer <jwt_token>
```

**How it works:**
- `client_id` is extracted from JWT token (from user's `client_id` claim or user record)
- `request.client_id` is ignored (JWT takes precedence)
- User ID is set to authenticated user's ID

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001"],
    "prediction_length": 30
  }'
```

### 2. Service API Key (System Calls)

**Header:**
```
X-API-Key: <service_api_key>
```

**How it works:**
- `client_id` **must** be provided in request body
- Service API key is validated against `SERVICE_API_KEY` environment variable
- User ID is set to "system"

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "X-API-Key: <service_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001"],
    "prediction_length": 30,
    "client_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

## Configuration

### Environment Variable

Set `SERVICE_API_KEY` in your environment:

**Option 1: `.env` file (recommended)**
```bash
# backend/.env or project root .env
SERVICE_API_KEY=your-secure-random-api-key-here
```

**Option 2: Environment variable**
```bash
export SERVICE_API_KEY=your-secure-random-api-key-here
```

**Configuration Location:**
- Defined in `backend/config.py` as `service_api_key: Optional[str]`
- Read from `SERVICE_API_KEY` environment variable
- Also accessible via `settings.service_api_key` in code

**See:** `.env.example` for template

**Security:**
- Use a strong, random API key (32+ characters)
- Store securely (environment variable, secrets manager)
- Rotate periodically
- Never commit to version control

---

## Endpoints

### Client-Specific Endpoints (Require client_id)

These endpoints **always** filter by `client_id`:

- `POST /api/v1/forecast` - Generate forecast
- `POST /api/v1/inventory/calculate` - Calculate inventory metrics
- `POST /api/v1/forecasts/actuals` - Backfill actual values
- `GET /api/v1/forecasts/quality/{item_id}` - Get quality metrics

**Authentication:**
- JWT: `client_id` from token
- Service API Key: `client_id` in request body (for POST) or from token (for GET)

### Client-Agnostic Endpoints (Optional client_id)

These endpoints work without `client_id`:

- `GET /health` - Health check (if exists)
- `GET /api/v1/system/status` - System status (if exists)

**Note:** Currently, all forecast endpoints require `client_id` for multi-tenant isolation.

---

## Request Schema Updates

### ForecastRequest

```python
class ForecastRequest(BaseModel):
    item_ids: List[str]
    prediction_length: int = 30
    model: Optional[str] = "chronos-2"
    include_baseline: bool = True
    client_id: Optional[str] = None  # Required for service API key calls
```

### InventoryCalculationRequest

```python
class InventoryCalculationRequest(BaseModel):
    item_ids: List[str]
    prediction_length: int = 30
    inventory_params: Dict[str, InventoryParams]
    model: Optional[str] = "chronos-2"
    client_id: Optional[str] = None  # Required for service API key calls
```

---

## Use Cases

### 1. Scheduled/Automated Forecasts

**Scenario:** Cron job runs every 7 days to generate forecasts for all clients.

```python
import requests
import os

# Service API key from environment
api_key = os.getenv("SERVICE_API_KEY")

# For each client
for client_id in client_ids:
    response = requests.post(
        "http://api:8000/api/v1/forecast",
        headers={"X-API-Key": api_key},
        json={
            "item_ids": get_client_items(client_id),
            "prediction_length": 30,
            "client_id": client_id,  # Required for service calls
        }
    )
```

### 2. User-Initiated Forecasts

**Scenario:** User clicks "Generate Forecast" in UI.

```javascript
// Frontend
const response = await fetch('/api/v1/forecast', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwtToken}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    item_ids: ['SKU001', 'SKU002'],
    prediction_length: 30,
    // client_id not needed - comes from JWT
  }),
});
```

---

## Security Considerations

### 1. API Key Security

- ✅ Store in environment variable (never in code)
- ✅ Use strong, random keys (32+ characters)
- ✅ Rotate periodically
- ✅ Use different keys per environment (dev/staging/prod)
- ✅ Monitor API key usage
- ✅ Revoke compromised keys immediately

### 2. Client ID Validation

- ✅ Service API key calls **must** provide `client_id`
- ✅ `client_id` is validated against `clients` table (future enhancement)
- ✅ All queries filter by `client_id` (defense in depth)

### 3. Rate Limiting

- ⚠️ Service API key calls may need different rate limits
- ⚠️ Consider per-client rate limits for service calls
- ⚠️ Monitor for abuse

---

## Implementation Details

### Authentication Flow

```
Request
  ↓
Check Authorization header
  ├─ Bearer token? → JWT authentication
  │   └─ Extract client_id from JWT/user
  │
  └─ X-API-Key header? → Service token authentication
      ├─ Validate API key
      └─ Require client_id in request body
  ↓
client_id determined
  ↓
All queries filter by client_id (unified)
```

### Code Location

- **Service Auth:** `backend/auth/service_auth.py`
- **API Endpoints:** `backend/api/forecast.py`
- **Schemas:** `backend/schemas/forecast.py`

---

## Future Enhancements

1. **Client ID Validation**: Validate `client_id` exists in `clients` table
2. **Service Account Model**: Create `service_accounts` table for better management
3. **Scoped API Keys**: API keys scoped to specific clients
4. **Rate Limiting**: Different limits for service vs user calls
5. **Audit Logging**: Log all service API key usage

---

## Testing

### Test Service API Key

```bash
# Set API key
export SERVICE_API_KEY=test-api-key-12345

# Test forecast endpoint
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "X-API-Key: test-api-key-12345" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001"],
    "prediction_length": 30,
    "client_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

**Status:** ✅ Implemented and ready for use


---

## Appendix: API Key Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Client Makes Request                                                        │
│                                                                              │
│  POST /api/v1/forecast                                                       │
│  Headers: X-API-Key: <service_api_key>                                      │
│  Body: { "item_ids": [...], "client_id": "..." }                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  get_client_id_from_request_or_token() (auth/service_auth.py)               │
│                                                                              │
│  Priority Check:                                                             │
│  1. client_id in request body? → Use it                                     │
│  2. JWT token in Authorization header? → Extract from JWT                   │
│  3. X-API-Key header? → Verify service API key                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Verify Service API Key                                                      │
│                                                                              │
│  verify_service_token(x_api_key):                                           │
│    valid_api_key = settings.service_api_key or os.getenv("SERVICE_API_KEY") │
│    IF valid_api_key is None: Return False (service auth disabled)           │
│    IF keys match: Return True → Extract client_id from body                 │
│    IF no match: Return False → 401 Unauthorized                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  Process Request with client_id                                              │
│                                                                              │
│  ForecastService.generate_forecast(client_id=..., user_id="system", ...)   │
│  All database queries filter by client_id (multi-tenant isolation)         │
└─────────────────────────────────────────────────────────────────────────────┘
```

**For detailed flow diagrams, see the original API_KEY_FLOW.md (archived).**
