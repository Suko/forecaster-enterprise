# MOQ, Lead Time & Buffer Configuration Reference

## Current Configuration Locations

### Summary Table

| Parameter | Current Location | Table | Level | Default | Configurable | Priority |
|-----------|------------------|-------|-------|---------|--------------|----------|
| **MOQ** | Product-Supplier Override | `product_supplier_conditions` | Product × Supplier | 0 | ✅ Yes | 1st (highest) |
| **MOQ** | Supplier Default | `suppliers` | Supplier | 0 | ✅ Yes | 2nd (fallback) |
| **Lead Time** | Product-Supplier Override | `product_supplier_conditions` | Product × Supplier | 0 | ✅ Yes | 1st (highest) |
| **Lead Time** | Supplier Default | `suppliers` | Supplier | 14 days | ✅ Yes | 2nd (fallback) |
| **Safety Buffer** | Client Settings | `client_settings` | Client (Global) | 7 days | ✅ Yes | N/A |

**📖 See:** [`MOQ_MANAGEMENT_GUIDE.md`](./MOQ_MANAGEMENT_GUIDE.md) for detailed explanation of the two-level system and how supplier changes affect product-level MOQs.

---

## 1. MOQ (Minimum Order Quantity)

### Current Location
**Table:** `product_supplier_conditions`  
**Column:** `moq`  
**Level:** Product-Supplier Relationship (many-to-many)

### Database Schema
```sql
-- From: backend/models/product_supplier.py
CREATE TABLE product_supplier_conditions (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    item_id VARCHAR(255) NOT NULL,  -- Product identifier
    supplier_id UUID NOT NULL,     -- Supplier identifier
    moq INTEGER DEFAULT 0,         -- Minimum Order Quantity ⭐
    -- ... other fields
    UNIQUE(client_id, item_id, supplier_id)
);
```

### Where It's Set

**Product-Level (Override):**
- **API Endpoint:** `POST /api/v1/products/{item_id}/suppliers` (with custom MOQ)
- **API Endpoint:** `PUT /api/v1/products/{item_id}/suppliers/{supplier_id}` (update MOQ)
- **UI:** Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ / Set MOQ

**Supplier-Level (Default):**
- **API Endpoint:** `PUT /api/v1/suppliers/{supplier_id}` (set `default_moq`)
- **UI:** Purchase Orders → Suppliers → [Supplier] → Edit → Default MOQ
- **Auto-populated:** When linking products, MOQ auto-populates from supplier default if not specified

**CSV Import:** Via product-supplier conditions import

### Current Usage
- ✅ Cart validation: `quantity >= MOQ`
- ✅ Purchase order validation: `quantity >= MOQ`
- ✅ Inventory recommendations: `suggested_qty = max(MOQ, forecasted_demand)`

### Documentation References
- `docs/DATA_MODEL.md` (lines 222, 414, 655)
- `docs/WORKFLOWS.md` (lines 513-514, 732-748)
- `backend/models/product_supplier.py` (line 27)

---

## 2. Lead Time (Days to Deliver)

### Current Location
**Table:** `product_supplier_conditions`  
**Column:** `lead_time_days`  
**Level:** Product-Supplier Relationship (many-to-many)

### Database Schema
```sql
-- From: backend/models/product_supplier.py
CREATE TABLE product_supplier_conditions (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL,
    item_id VARCHAR(255) NOT NULL,  -- Product identifier
    supplier_id UUID NOT NULL,       -- Supplier identifier
    lead_time_days INTEGER DEFAULT 0, -- Days to deliver ⭐
    -- ... other fields
    UNIQUE(client_id, item_id, supplier_id)
);
```

### Where It's Set
- **API Endpoint:** `POST /api/v1/products/{item_id}/suppliers`
- **API Endpoint:** `PUT /api/v1/products/{item_id}/suppliers/{supplier_id}`
- **UI:** Product → Suppliers → Add/Edit Supplier → Lead Time field
- **CSV Import:** Via product-supplier conditions import

### Current Usage
- ✅ Inventory recommendations: `DIR < (lead_time + buffer)` → REORDER
- ✅ Stockout risk calculation: `risk = f(DIR, lead_time + buffer)`
- ✅ Reorder point calculation: `reorder_point = (avg_daily_demand * lead_time) + safety_stock`
- ✅ Expected delivery date: `order_date + lead_time_days`

### Documentation References
- `docs/DATA_MODEL.md` (lines 223, 415, 656)
- `docs/WORKFLOWS.md` (lines 515-520, 752-765)
- `backend/models/product_supplier.py` (line 28)

---

## 3. Safety Buffer (Days)

### Current Location
**Table:** `client_settings`  
**Column:** `safety_buffer_days`  
**Level:** Client (Global - applies to all products)

### Database Schema
```sql
-- From: backend/models/settings.py
CREATE TABLE client_settings (
    id UUID PRIMARY KEY,
    client_id UUID UNIQUE NOT NULL,
    safety_buffer_days INTEGER DEFAULT 7,  -- Extra days for safety ⭐
    understocked_threshold INTEGER DEFAULT 14,  -- DIR days (lead_time + buffer)
    overstocked_threshold INTEGER DEFAULT 90,
    dead_stock_days INTEGER DEFAULT 90,
    recommendation_rules JSONB,
    -- ... timestamps
);
```

### Where It's Set
- **API Endpoint:** `PUT /api/v1/settings`
- **UI:** Settings → Inventory Thresholds → Safety Buffer
- **Default:** 7 days (if not configured)

### Current Usage
- ✅ Stockout risk: `DIR < (lead_time + safety_buffer)` → High risk
- ✅ Understocked threshold: `understocked_threshold = lead_time + buffer` (default)
- ✅ Reorder recommendations: `REORDER if DIR < (lead_time + buffer)`
- ✅ Inventory calculations: Added to lead time for safety margin

### Formula
```
Total Required Days = Lead Time + Safety Buffer
Stockout Risk = f(DIR, Total Required Days)
```

### Documentation References
- `docs/DATA_MODEL.md` (lines 243-245, 674-675)
- `docs/WORKFLOWS.md` (lines 516-518, 754-758, 911-916, 947-956)
- `backend/models/settings.py` (line 22)

---

## Configuration Hierarchy

### Current Implementation (Two-Level System)
```
┌─────────────────────────────────────────┐
│  MOQ & Lead Time (Priority Order)      │
│  1. product_supplier_conditions.moq     │
│     (product-level override)            │
│  2. suppliers.default_moq              │
│     (supplier-level default)            │
│  3. System default (0/14)               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Safety Buffer                         │
│  └─ client_settings                    │
│     (global per client)                │
└─────────────────────────────────────────┘
```

**📖 See:** [`MOQ_MANAGEMENT_GUIDE.md`](./MOQ_MANAGEMENT_GUIDE.md) for detailed explanation of supplier vs product-level MOQ management and how changes affect each other.

---

## API Endpoints Summary

### MOQ & Lead Time
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/products/{item_id}/suppliers` | Create product-supplier link with MOQ/lead time |
| `PUT` | `/api/v1/products/{item_id}/suppliers/{supplier_id}` | Update MOQ/lead time |
| `GET` | `/api/v1/products/{item_id}/suppliers` | Get all suppliers with MOQ/lead time |

### Safety Buffer
| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/v1/settings` | Get client settings (including buffer) |
| `PUT` | `/api/v1/settings` | Update safety buffer |

---

## Usage in Business Logic

### Cart Service
```python
# backend/services/cart_service.py
# Validates: quantity >= MOQ
if quantity < condition.moq:
    raise ValueError(f"Quantity {quantity} is less than MOQ {condition.moq}")
```

### Purchase Order Service
```python
# backend/services/purchase_order_service.py
# Validates: quantity >= MOQ
if item_data.quantity < condition.moq:
    raise ValueError(f"Quantity {item_data.quantity} is less than MOQ {condition.moq}")
```

### Recommendations Service
```python
# backend/services/recommendations_service.py
# REORDER if: DIR < (lead_time + buffer)
required_days = condition.lead_time_days + settings.safety_buffer_days
if dir < required_days:
    recommendation_type = "REORDER"
```

### Metrics Service
```python
# backend/services/metrics_service.py
# Stockout risk calculation
total_required_days = lead_time_days + safety_buffer_days
if dir < total_required_days:
    risk = 100 * (1 - dir / total_required_days)
```

---

## Current Implementation Status

### MOQ & Lead Time
- ✅ **Supplier-level defaults** (`suppliers.default_moq`) - **IMPLEMENTED**
- ✅ **Product-level overrides** (`product_supplier_conditions.moq`) - **IMPLEMENTED**
- ✅ **Fallback chain** (product override → supplier default → system default) - **IMPLEMENTED**
- ✅ **Auto-population** from supplier defaults when linking products - **IMPLEMENTED**
- ✅ **Selective updates** via `apply_to_existing` flag - **IMPLEMENTED**
- ✅ **UI for product-level MOQ editing** - **IMPLEMENTED** (Purchase Orders → Suppliers → [Supplier] → Products)

**📖 See:** [`MOQ_MANAGEMENT_GUIDE.md`](./MOQ_MANAGEMENT_GUIDE.md) for detailed explanation of how supplier and product-level MOQs interact.

### Safety Buffer
- ✅ Already at client level (good)
- ⚠️ Cannot be set per product or per supplier (by design - global setting)

---
- Implement fallback chain: product-supplier → product → supplier → system default

---

## Quick Reference

### Where to Set Each Parameter

| Parameter | Level | Where to Set | Example |
|-----------|-------|--------------|---------|
| **MOQ** | Supplier (Default) | Purchase Orders → Suppliers → [Supplier] → Edit → Default MOQ | Supplier "A" → Default MOQ: 100 |
| **MOQ** | Product (Override) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ | Product "SKU-001" with Supplier "A" → MOQ: 70 (overrides supplier default) |
| **Lead Time** | Supplier (Default) | Purchase Orders → Suppliers → [Supplier] → Edit → Default Lead Time | Supplier "A" → Default Lead Time: 14 days |
| **Lead Time** | Product (Override) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ | Product "SKU-001" with Supplier "A" → Lead Time: 21 days (overrides supplier default) |
| **Safety Buffer** | Client (Global) | Settings → Inventory Thresholds → Safety Buffer | Client-wide → Safety Buffer: 7 days |

### Current Defaults

| Parameter | Default Value | Can Be Changed At |
|-----------|---------------|-------------------|
| MOQ | 0 | ✅ Supplier level (default) or Product level (override) |
| Lead Time | 14 days | ✅ Supplier level (default) or Product level (override) |
| Safety Buffer | 7 days | ✅ Client level (global) |

**Note:** Product-level MOQ/Lead Time overrides supplier defaults. See [`MOQ_MANAGEMENT_GUIDE.md`](./MOQ_MANAGEMENT_GUIDE.md) for details on how changes at supplier level affect product level.

---

## Documentation Sources

1. **Data Model:** `docs/DATA_MODEL.md`
   - Lines 222-223: MOQ and lead_time_days in product_supplier_conditions
   - Lines 243-245: safety_buffer_days in client_settings

2. **Workflows:** `docs/WORKFLOWS.md`
   - Lines 513-520: MOQ and lead time validation
   - Lines 911-916: Safety buffer configuration
   - Lines 947-956: Safety buffer usage

3. **Models:**
   - `backend/models/product_supplier.py`: MOQ and lead_time_days
   - `backend/models/settings.py`: safety_buffer_days

4. **API Reference:** `docs/backend/API_REFERENCE.md`
   - Lines 155-210: Product-supplier endpoints
   - Lines 509-530: Settings endpoints

---

**Last Updated:** 2025-12-15  
**Status:** Current implementation documented

