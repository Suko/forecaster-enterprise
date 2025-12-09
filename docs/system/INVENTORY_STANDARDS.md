# Inventory Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for inventory data integration with the forecasting system.

---

## 1. Data Schema Requirements

### ts_demand_daily Table

| Column | Type | Required | Description |
|--------|------|----------|-------------|
| `id` | UUID | ✅ | Primary key |
| `client_id` | UUID | ✅ | Multi-tenant identifier |
| `item_id` | VARCHAR(255) | ✅ | SKU identifier |
| `date_local` | DATE | ✅ | Transaction date |
| `units_sold` | NUMERIC | ✅ | Quantity sold |
| `promo_flag` | BOOLEAN | ❌ | Promotional indicator |
| `holiday_flag` | BOOLEAN | ❌ | Holiday indicator |
| `is_weekend` | BOOLEAN | ❌ | Weekend indicator |
| `marketing_spend` | NUMERIC | ❌ | Marketing investment |

### Primary Key

```sql
UNIQUE (client_id, item_id, date_local)
```

---

## 2. Data Quality Requirements

### Completeness

| Requirement | Standard |
|-------------|----------|
| Missing dates | Max 7 consecutive days |
| Required fields | 100% populated |
| History length | Minimum 30 days |

### Accuracy

| Requirement | Standard |
|-------------|----------|
| Numeric precision | 2 decimal places |
| Date format | YYYY-MM-DD |
| Negative values | Not allowed for `units_sold` |

### Consistency

| Requirement | Standard |
|-------------|----------|
| SKU identifiers | Consistent across records |
| Time zone | UTC or local (documented) |
| Duplicates | Not allowed |

---

## 3. Data Ingestion

### Supported Formats

| Format | Status |
|--------|--------|
| CSV | ✅ Supported |
| JSON | ✅ Supported |
| API | ✅ Supported |
| Database sync | ⏳ Planned |

### CSV Requirements

```csv
client_id,item_id,date_local,units_sold
uuid,SKU001,2025-01-01,100
uuid,SKU001,2025-01-02,120
```

### Import Rules

- Headers required
- UTF-8 encoding
- No trailing commas
- Maximum 100MB per file

---

## 4. SKU Standards

### Identifier Requirements

| Requirement | Standard |
|-------------|----------|
| Format | Alphanumeric + underscores |
| Length | 1-255 characters |
| Case | Case-sensitive |
| Special chars | Avoid (except underscore) |

### SKU Examples

| Valid | Invalid |
|-------|---------|
| `SKU001` | `SKU 001` (space) |
| `PRODUCT_A_001` | `SKU/001` (slash) |
| `item-123` | `SKU#001` (hash) |

---

## 5. Time Series Requirements

### Frequency

| Supported | Status |
|-----------|--------|
| Daily | ✅ Primary |
| Weekly | ⏳ Planned |
| Monthly | ⏳ Planned |

### Date Range

| Requirement | Value |
|-------------|-------|
| Minimum history | 30 days |
| Recommended history | 365 days |
| Maximum gap | 7 days |

### Gap Handling

| Scenario | Action |
|----------|--------|
| Missing single day | Fill with 0 |
| Missing 2-7 days | Fill with 0 + warning |
| Missing > 7 days | Error or split series |

---

## 6. Aggregation Rules

### Duplicate Handling

| Scenario | Action |
|----------|--------|
| Same SKU, same date | Sum quantities |
| Different clients | Keep separate |

### Location Aggregation

| Level | Support |
|-------|---------|
| SKU total | ✅ Supported |
| SKU by store | ⏳ Planned |
| SKU by region | ⏳ Planned |

---

## 7. Covariate Data

### Supported Covariates

| Covariate | Type | Use Case |
|-----------|------|----------|
| `promo_flag` | Boolean | Promotional events |
| `holiday_flag` | Boolean | Holiday periods |
| `is_weekend` | Boolean | Weekend patterns |
| `marketing_spend` | Numeric | Marketing correlation |
| `price` | Numeric | Price elasticity |

### Covariate Requirements

- Must align with demand dates
- Boolean covariates: 0 or 1
- Numeric covariates: Non-negative

---

## 8. Data Validation

### Pre-Import Validation

| Check | Action on Failure |
|-------|-------------------|
| Schema match | Reject file |
| Date format | Reject record |
| Negative units | Reject record |
| Duplicate key | Merge or reject |

### Post-Import Validation

| Check | Action |
|-------|--------|
| Gap detection | Generate warning |
| Outlier detection | Flag for review |
| Completeness | Report missing |

---

## 9. Performance Standards

### Import Performance

| Volume | Target Time |
|--------|-------------|
| 10,000 records | < 5 seconds |
| 100,000 records | < 30 seconds |
| 1,000,000 records | < 5 minutes |

### Query Performance

| Query Type | Target Time |
|------------|-------------|
| Single SKU history | < 100ms |
| Multi-SKU (100) | < 1 second |
| Full export | < 30 seconds |

---

## 10. Compliance

All inventory data must:

1. ✅ Follow schema requirements
2. ✅ Include required fields
3. ✅ Pass validation checks
4. ✅ Use correct formats
5. ✅ Be client_id scoped

---

*This standard is mandatory for all inventory data integration.*

