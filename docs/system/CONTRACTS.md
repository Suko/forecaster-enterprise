# System Contracts

**Version:** 1.0  
**Last Updated:** 2025-12-17

---

## 1. Authentication

### Methods

| Method | Header | Use Case |
|--------|--------|----------|
| JWT Token | `Authorization: Bearer <token>` | User calls |
| Service API Key | `X-API-Key: <key>` | Automated/scheduled calls |

### JWT Flow
- `client_id` extracted from token
- User ID from authenticated user
- **Contract rule:** for JWT-authenticated requests, `client_id` must come from JWT/user context (request-body `client_id` must not override tenant context).

### Service API Key Flow
- `client_id` **must** be in request body
- User ID set to "system"
- Key stored in `SERVICE_API_KEY` env var
- **Contract rule:** request-body `client_id` is accepted **only** when a valid `X-API-Key` is present.

### API Base Paths (current)
- Auth endpoints (canonical): `/api/v1/auth/*`
- Auth endpoints (legacy): `/auth/*` (deprecated)
- Versioned business APIs: `/api/v1/*`

### Example (Service API Key)

```bash
curl -X POST "http://localhost:8000/api/v1/forecast" \
  -H "X-API-Key: <service_api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["SKU001"],
    "client_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

---

## 2. Multi-Tenant Isolation

| Resource | Isolation |
|----------|-----------|
| Database | `client_id` filter on all queries |
| API | Token-based filtering |
| Cache | Client-scoped keys |

---

## 3. Data Security

### Encryption

| Layer | Standard |
|-------|----------|
| At rest | AES-256 |
| In transit | TLS 1.3 |

### Key Rotation

| Key Type | Rotation |
|----------|----------|
| JWT signing | Quarterly |
| API keys | 90 days |
| TLS certs | Annually |

### Data Retention

| Data | Retention |
|------|-----------|
| Forecasts | 2 years |
| Sales data | 3 years |
| Audit logs | 7 years |
| Sessions | 90 days |

---

## 4. Inventory Data Contract

### Required Schema (ts_demand_daily)

| Column | Type | Required |
|--------|------|----------|
| `client_id` | UUID | ✅ |
| `item_id` | VARCHAR(255) | ✅ |
| `date_local` | DATE | ✅ |
| `units_sold` | NUMERIC | ✅ |
| `promo_flag` | BOOLEAN | ❌ |
| `holiday_flag` | BOOLEAN | ❌ |

### Data Quality

| Requirement | Standard |
|-------------|----------|
| Minimum history | 30 days |
| Max gap | 7 consecutive days |
| Date format | YYYY-MM-DD |
| Negative values | Not allowed |

### SKU Identifiers

- Alphanumeric + underscores
- 1-255 characters
- Case-sensitive

### Detailed Naming Strategy

#### Backend (Python/FastAPI)
- **API Path Parameters**: `item_id` (snake_case)
  - Example: `/api/v1/products/{item_id}`
- **Schema Fields**: `item_id` (snake_case)
  - Example: `item_id: str` in Pydantic models
- **Database Columns**: `item_id` (snake_case)
  - Example: `item_id = Column(String(255))`

#### Frontend (TypeScript/Nuxt)

**1. Route Folders & Parameters**
- **MUST match backend API path parameter names:**
  - ✅ Route folder: `[item_id]` (matches `/products/{item_id}`)
  - ✅ Route param extraction: `event.context.params?.item_id`
  - ✅ Page route: `[item_id].vue` (matches `/inventory/{item_id}`)
- **Why:** Nuxt route parameters must match the backend API paths they proxy to.

**2. TypeScript Type Definitions**
- **MUST match backend schema field names:**
  - ✅ Type definitions: `item_id: string` (snake_case)
  - ✅ Example: `interface Product { item_id: string }`
- **Why:** Type definitions represent backend API responses, so they must match exactly.

**3. Variable Names in Code**
- **RECOMMENDED: Use camelCase for local variables (JavaScript convention)**
  - ✅ Local variables: `itemId` (camelCase)
  - ✅ Function parameters: `itemId: string`
  - ✅ Example: `const itemId = route.params.item_id as string;`
- **Alternative:** Use snake_case everywhere for consistency (not recommended)

**4. API Request/Response Bodies**
- **MUST match backend schema field names:**
  - ✅ Request body: `{ item_id: "SKU001" }`
  - ✅ Response fields: `item_id` (from backend)

#### Summary Table

| Context | Convention | Example | Reason |
|---------|-----------|---------|--------|
| Backend API paths | `item_id` | `/products/{item_id}` | Python/FastAPI convention |
| Backend schemas | `item_id` | `item_id: str` | Matches database |
| Frontend route folders | `[item_id]` | `[item_id]/history.get.ts` | Must match backend paths |
| Frontend route params | `item_id` | `params?.item_id` | Must match folder name |
| TypeScript types | `item_id` | `item_id: string` | Must match backend schema |
| Local variables | `itemId` (recommended) | `const itemId = ...` | JavaScript convention |
| API request bodies | `item_id` | `{ item_id: "SKU001" }` | Must match backend schema |

#### Examples

**✅ Correct: Route Handler**
```typescript
// frontend/server/api/products/[item_id]/history.get.ts
export default defineEventHandler(async (event) => {
  const item_id = event.context.params?.item_id; // Matches folder name
  return await authenticatedFetch(event, `/api/v1/products/${item_id}/history`);
});
```

**✅ Correct: Component with Local Variable**
```typescript
// frontend/app/pages/inventory/[item_id].vue
const itemId = computed(() => route.params.item_id as string); // camelCase for local var
const product = await $fetch(`/api/products/${itemId.value}`);
```

**✅ Correct: API Request Body**
```typescript
await $fetch("/api/order-planning/cart/add", {
  method: "POST",
  body: {
    item_id: itemId, // Must use item_id (backend expects this)
  },
});
```
---

## 5. API Response Contract

### Forecast Response

```json
{
  "forecast_run_id": "uuid",
  "status": "completed",
  "items": [{
    "item_id": "SKU001",
    "classification": {"abc_class": "A", "xyz_class": "X"},
    "predictions": [{"date": "2025-12-10", "point_forecast": 125.5}]
  }]
}
```

### Error Response

```json
{
  "status": "error",
  "error_code": "INSUFFICIENT_HISTORY",
  "message": "This SKU requires at least 30 days of history"
}
```

---

## 6. Performance SLAs

| Endpoint | Target | Maximum |
|----------|--------|---------|
| Generate forecast | 30s | 60s |
| Get results | 2s | 5s |
| Classification | 5s | 10s |

| Metric | Target |
|--------|--------|
| Uptime | 99.9% |
| Incident response | < 30 min |

---

## 7. Time & Date Management

### Timezone Handling

| Layer | Standard | Timezone |
|-------|----------|----------|
| Database | `TIMESTAMP WITH TIME ZONE` | UTC |
| Models | `DateTime(timezone=True)` | UTC |
| API Schemas | `datetime` (ISO 8601) | UTC |
| Business Logic | `date` for business dates | Client timezone |
| API Responses | ISO 8601 strings | UTC |

### Date vs DateTime

| Field Type | Database | Model | Schema | Use Case |
|------------|----------|-------|--------|----------|
| **Timestamps** | `TIMESTAMP WITH TIME ZONE` | `DateTime(timezone=True)` | `datetime` | `created_at`, `updated_at`, `order_date` |
| **Business Dates** | `DATE` | `Date` | `date` | `date_local`, `expected_delivery_date`, `start_date` |

### Rules

1. **All timestamps in UTC**: Database stores all `DateTime` fields in UTC
2. **Business dates are date-only**: No time component for dates like `date_local`, delivery dates
3. **API serialization**: All `datetime` fields serialized as ISO 8601 strings in UTC
4. **Client timezone**: Business dates respect client timezone for display, but stored as UTC dates
5. **Schema validation**: Use `datetime` for timestamps, `date` for business dates

### Examples

**Database Model:**
```python
created_at = Column(DateTime(timezone=True), server_default=func.now())
date_local = Column(Date, nullable=False)
```

**Pydantic Schema:**
```python
created_at: datetime  # For timestamps
date_local: date      # For business dates
```

**API Response:**
```json
{
  "created_at": "2025-12-10T08:28:37Z",
  "date_local": "2025-12-10"
}
```

---

## 8. Logging & Monitoring

### Required Logs

- Authentication events
- Authorization events
- Data access
- Admin actions
- Security events

### Alert Thresholds

| Metric | Threshold |
|--------|-----------|
| Failed logins | > 5 in 5 min |
| API errors | > 10% rate |
| CPU/Memory | > 80% |

---

## Compliance

All systems must:

1. ✅ Enforce multi-tenant isolation
2. ✅ Use encryption standards
3. ✅ Log security events
4. ✅ Meet SLA targets
5. ✅ Validate input data

---

*This document consolidates all system contracts.*
