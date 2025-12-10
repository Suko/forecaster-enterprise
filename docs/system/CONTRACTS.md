# System Contracts

**Version:** 1.0  
**Last Updated:** 2025-12-09

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

### Service API Key Flow
- `client_id` **must** be in request body
- User ID set to "system"
- Key stored in `SERVICE_API_KEY` env var

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


