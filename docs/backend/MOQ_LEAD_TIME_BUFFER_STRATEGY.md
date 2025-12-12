# MOQ, Lead Time & Buffer Configuration Strategy

## Configuration Hierarchy

### Lead Time & MOQ

```
┌─────────────────────────────────────────────────────────────┐
│                    PRECEDENCE CHAIN                          │
│                                                              │
│  1. product_supplier_conditions.moq/lead_time_days          │
│     └─ Manual override (highest priority)                    │
│                                                              │
│  2. suppliers.default_moq/default_lead_time_days            │
│     └─ Supplier default (auto-populated on create)          │
│                                                              │
│  3. System default (0 for MOQ, 14 for lead time)           │
│     └─ Fallback if supplier default not set                 │
└─────────────────────────────────────────────────────────────┘
```

### Safety Buffer

```
┌─────────────────────────────────────────────────────────────┐
│                    PRECEDENCE CHAIN                          │
│                                                              │
│  1. products.safety_buffer_days                              │
│     └─ Product-level override (highest priority)             │
│                                                              │
│  2. client_settings.safety_buffer_days                      │
│     └─ Client global default (auto-populated)              │
│                                                              │
│  3. System default (7 days)                                 │
│     └─ Fallback if client default not set                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Creating Product-Supplier Link

### When User Creates Product-Supplier Relationship

```
┌─────────────────────────────────────────────────────────────┐
│  USER ACTION: Link Product to Supplier                     │
│  └─ Via: Inventory UI or API                                │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Check Supplier Defaults                            │
│                                                              │
│  SELECT suppliers.default_moq,                              │
│         suppliers.default_lead_time_days                     │
│  FROM suppliers                                              │
│  WHERE id = {supplier_id}                                    │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Supplier has         │
        │  defaults set?        │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
       YES             NO
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────┐
│ Use Supplier │  │ Use System    │
│ Defaults     │  │ Defaults      │
│              │  │ (MOQ: 0)      │
│ MOQ: 100     │  │ (Lead: 14)    │
│ Lead: 14     │  │               │
└───────┬───────┘  └───────┬───────┘
        │                  │
        └──────────┬────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Create Product-Supplier Condition                  │
│                                                              │
│  INSERT INTO product_supplier_conditions                    │
│  (item_id, supplier_id, moq, lead_time_days, ...)           │
│  VALUES                                                      │
│  ({item_id}, {supplier_id},                                 │
│   {supplier.default_moq},      ← Auto-populated             │
│   {supplier.default_lead_time_days}, ← Auto-populated      │
│   ...)                                                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: User Can Manually Override                         │
│                                                              │
│  User edits product-supplier condition:                     │
│  - Change MOQ from 100 → 150                                │
│  - Change Lead Time from 14 → 21                            │
│                                                              │
│  UPDATE product_supplier_conditions                         │
│  SET moq = 150,                                             │
│      lead_time_days = 21                                    │
│  WHERE id = {condition_id}                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Creating Product

### When User Creates New Product

```
┌─────────────────────────────────────────────────────────────┐
│  USER ACTION: Create New Product                            │
│  └─ Via: Inventory UI or API                                │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Check Client Settings for Buffer                   │
│                                                              │
│  SELECT safety_buffer_days                                  │
│  FROM client_settings                                       │
│  WHERE client_id = {client_id}                              │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Client has          │
        │  buffer set?         │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
       YES             NO
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────┐
│ Use Client    │  │ Use System    │
│ Default       │  │ Default       │
│               │  │ (7 days)      │
│ Buffer: 7     │  │               │
└───────┬───────┘  └───────┬───────┘
        │                  │
        └──────────┬────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Create Product                                     │
│                                                              │
│  INSERT INTO products                                       │
│  (item_id, product_name, ..., safety_buffer_days)           │
│  VALUES                                                      │
│  ({item_id}, {name}, ...,                                   │
│   {client_settings.safety_buffer_days}) ← Auto-populated   │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: User Can Override Buffer Per Product               │
│                                                              │
│  User edits product:                                        │
│  - Change Buffer from 7 → 10 (for critical product)         │
│                                                              │
│  UPDATE products                                            │
│  SET safety_buffer_days = 10                                │
│  WHERE item_id = {item_id}                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## Resolution Logic (Effective Values)

### Getting Effective MOQ

```
FUNCTION get_effective_moq(item_id, supplier_id):
    ┌─────────────────────────────────────────┐
    │ 1. Check product-supplier condition    │
    │    (manual override)                     │
    └───────────────┬─────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Condition exists    │
        │  AND moq > 0?        │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
       YES             NO
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────────────────┐
│ RETURN        │  │ 2. Check supplier default │
│ condition.moq │  │                           │
│ (150)         │  │ SELECT default_moq        │
└───────────────┘  │ FROM suppliers            │
                   │ WHERE id = supplier_id    │
                   └───────────┬───────────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
                  YES                     NO
                   │                       │
                   ▼                       ▼
          ┌───────────────┐      ┌──────────────────┐
          │ RETURN        │      │ 3. System default │
          │ supplier.     │      │                   │
          │ default_moq    │      │ RETURN 0          │
          │ (100)         │      └───────────────────┘
          └───────────────┘
```

### Getting Effective Lead Time

```
FUNCTION get_effective_lead_time(item_id, supplier_id):
    ┌─────────────────────────────────────────┐
    │ 1. Check product-supplier condition    │
    │    (manual override)                     │
    └───────────────┬─────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Condition exists      │
        │  AND lead_time > 0?   │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
       YES             NO
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────────────────┐
│ RETURN        │  │ 2. Check supplier default │
│ condition.    │  │                           │
│ lead_time_    │  │ SELECT default_lead_      │
│ days (21)     │  │       time_days           │
└───────────────┘  │ FROM suppliers            │
                   │ WHERE id = supplier_id    │
                   └───────────┬───────────────┘
                               │
                   ┌───────────┴───────────┐
                   │                       │
                  YES                     NO
                   │                       │
                   ▼                       ▼
          ┌───────────────┐      ┌──────────────────┐
          │ RETURN        │      │ 3. System default │
          │ supplier.     │      │                   │
          │ default_lead_ │      │ RETURN 14         │
          │ time_days     │      └───────────────────┘
          │ (14)          │
          └───────────────┘
```

### Getting Effective Buffer

```
FUNCTION get_effective_buffer(item_id):
    ┌─────────────────────────────────────────┐
    │ 1. Check product override               │
    │                                         │
    │ SELECT safety_buffer_days               │
    │ FROM products                           │
    │ WHERE item_id = item_id                 │
    └───────────────┬─────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │  Product has          │
        │  buffer set?          │
        │  (NOT NULL AND > 0)   │
        └───────┬───────────────┘
                │
        ┌───────┴───────┐
        │               │
       YES             NO
        │               │
        ▼               ▼
┌───────────────┐  ┌───────────────────────────┐
│ RETURN        │  │ 2. Check client settings  │
│ product.      │  │                           │
│ safety_       │  │ SELECT safety_buffer_days │
│ buffer_days   │  │ FROM client_settings      │
│ (10)          │  │ WHERE client_id = ...     │
└───────────────┘  └───────────┬───────────────┘
                                │
                    ┌───────────┴───────────┐
                    │                       │
                   YES                     NO
                    │                       │
                    ▼                       ▼
          ┌───────────────┐      ┌──────────────────┐
          │ RETURN        │      │ 3. System default │
          │ client.       │      │                   │
          │ safety_       │      │ RETURN 7          │
          │ buffer_days   │      └───────────────────┘
          │ (7)           │
          └───────────────┘
```

---

## Database Schema Changes

### 1. Add Supplier Defaults

```sql
-- Migration: Add supplier-level defaults
ALTER TABLE suppliers 
ADD COLUMN default_moq INTEGER DEFAULT 0,
ADD COLUMN default_lead_time_days INTEGER DEFAULT 14;

-- Index for performance
CREATE INDEX idx_suppliers_defaults ON suppliers(client_id, default_moq, default_lead_time_days);
```

### 2. Add Product Buffer Override

```sql
-- Migration: Add product-level buffer override
ALTER TABLE products 
ADD COLUMN safety_buffer_days INTEGER DEFAULT NULL;  -- NULL = use client default

-- Index for performance
CREATE INDEX idx_products_buffer ON products(client_id, safety_buffer_days);
```

---

## API Changes

### Supplier API

```python
# GET /api/v1/suppliers/{id}
# Response includes defaults
{
    "id": "...",
    "name": "Supplier A",
    "default_moq": 100,              # NEW
    "default_lead_time_days": 14,    # NEW
    ...
}

# PUT /api/v1/suppliers/{id}
# Allow updating defaults
{
    "name": "Supplier A",
    "default_moq": 100,              # NEW
    "default_lead_time_days": 14,    # NEW
    ...
}
```

### Product API

```python
# GET /api/v1/products/{item_id}
# Response includes buffer override
{
    "item_id": "SKU-001",
    "product_name": "...",
    "safety_buffer_days": 10,  # NEW (NULL = use client default)
    ...
}

# PUT /api/v1/products/{item_id}
# Allow updating buffer override
{
    "product_name": "...",
    "safety_buffer_days": 10,  # NEW (NULL = use client default)
    ...
}
```

### Product-Supplier API

```python
# POST /api/v1/products/{item_id}/suppliers
# Auto-populate from supplier defaults if not provided
{
    "supplier_id": "...",
    "moq": null,              # Optional - auto-populate from supplier.default_moq
    "lead_time_days": null,    # Optional - auto-populate from supplier.default_lead_time_days
    ...
}

# Response shows effective values
{
    "id": "...",
    "item_id": "SKU-001",
    "supplier_id": "...",
    "moq": 100,                    # Effective value
    "lead_time_days": 14,          # Effective value
    "moq_source": "supplier_default",      # NEW: Shows source
    "lead_time_source": "supplier_default", # NEW: Shows source
    ...
}
```

---

## UI Flow

### Supplier Management

```
┌─────────────────────────────────────────┐
│  SUPPLIER SETTINGS                      │
│                                         │
│  Name: Supplier A                       │
│  Contact: ...                           │
│                                         │
│  Default MOQ: [100] ────────────────┐  │
│  Default Lead Time: [14] days ──────┤  │
│                                     │  │
│  [Save]                             │  │
└─────────────────────────────────────┴──┘
         │
         │ These defaults are used when
         │ linking products to this supplier
         ▼
```

### Product-Supplier Link Creation

```
┌─────────────────────────────────────────┐
│  ADD SUPPLIER TO PRODUCT               │
│                                         │
│  Product: SKU-001                      │
│  Supplier: [Select: Supplier A]       │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │  Auto-populated from Supplier A:  │ │
│  │  MOQ: [100] ← from supplier       │ │
│  │  Lead Time: [14] days ← supplier  │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Override] ← User can change values   │
│                                         │
│  MOQ: [150] ← Manual override          │
│  Lead Time: [21] days ← Manual override│
│                                         │
│  [Save]                                 │
└─────────────────────────────────────────┘
```

### Product Buffer Override

```
┌─────────────────────────────────────────┐
│  PRODUCT SETTINGS                       │
│                                         │
│  Item ID: SKU-001                       │
│  Name: Product Name                     │
│                                         │
│  Safety Buffer:                         │
│  ┌───────────────────────────────────┐ │
│  │  [Use Client Default: 7 days]      │ │
│  │  OR                                │ │
│  │  [Override: 10] days               │ │
│  └───────────────────────────────────┘ │
│                                         │
│  [Save]                                 │
└─────────────────────────────────────────┘
```

---

## Summary

### Configuration Strategy

| Parameter | Default Location | Override Location | Auto-Populate |
|-----------|------------------|-------------------|---------------|
| **MOQ** | `suppliers.default_moq` | `product_supplier_conditions.moq` | ✅ Yes (on create) |
| **Lead Time** | `suppliers.default_lead_time_days` | `product_supplier_conditions.lead_time_days` | ✅ Yes (on create) |
| **Buffer** | `client_settings.safety_buffer_days` | `products.safety_buffer_days` | ✅ Yes (on product create) |

### Key Points

1. **Supplier Defaults**: Set once per supplier, used for all products
2. **Product-Supplier Override**: Can manually change MOQ/lead time per product-supplier link
3. **Client Buffer**: Global default, can override per product
4. **Auto-Population**: When creating links, defaults are automatically filled
5. **Flexibility**: Manual overrides always take precedence

---

**Status:** Strategy defined, ready for implementation  
**Next Steps:** Create database migrations and update services

