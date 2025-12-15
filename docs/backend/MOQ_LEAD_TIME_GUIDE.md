# MOQ, Lead Time & Safety Buffer Guide

Complete guide to Minimum Order Quantity (MOQ), Lead Time, and Safety Buffer configuration and management.

---

## Quick Reference

### Configuration Summary

| Parameter | Level | Table | Default | Priority | Where to Set |
|-----------|-------|-------|---------|----------|--------------|
| **MOQ** | Product-Supplier Override | `product_supplier_conditions` | 0 | 1st (highest) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ |
| **MOQ** | Supplier Default | `suppliers` | 0 | 2nd (fallback) | Purchase Orders → Suppliers → [Supplier] → Edit → Default MOQ |
| **Lead Time** | Product-Supplier Override | `product_supplier_conditions` | 0 | 1st (highest) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ |
| **Lead Time** | Supplier Default | `suppliers` | 14 days | 2nd (fallback) | Purchase Orders → Suppliers → [Supplier] → Edit → Default Lead Time |
| **Safety Buffer** | Client (Global) | `client_settings` | 7 days | N/A | Settings → Inventory Thresholds → Safety Buffer |

### Resolution Priority

```
MOQ & Lead Time:
1. product_supplier_conditions.moq/lead_time_days (if > 0) → Product override
2. suppliers.default_moq/default_lead_time_days (if > 0) → Supplier default
3. System default (0 for MOQ, 14 days for Lead Time)

Safety Buffer:
- client_settings.safety_buffer_days (global per client)
```

---

## Part 1: How MOQ & Lead Time Work

### Overview

The system supports **two levels** of MOQ and Lead Time management:

1. **Supplier Level** (`suppliers.default_moq`, `suppliers.default_lead_time_days`) - Default values for a supplier
2. **Product Level** (`product_supplier_conditions.moq`, `product_supplier_conditions.lead_time_days`) - Product-specific overrides

### Priority Order (Highest to Lowest)

```
1. product_supplier_conditions.moq/lead_time_days (if exists and > 0)
   └─ Product-specific override (highest priority)
   
2. suppliers.default_moq/default_lead_time_days (if > 0)
   └─ Supplier default (fallback)
   
3. System default (0 for MOQ, 14 days for Lead Time)
   └─ Final fallback
```

### Example Scenarios

| Scenario | Supplier Default | Product Condition | Effective Value | Source |
|----------|-----------------|-------------------|-----------------|--------|
| Product uses supplier default | MOQ: 100 | Not set (0) | **MOQ: 100** | Supplier default |
| Product has custom MOQ | MOQ: 100 | MOQ: 70 | **MOQ: 70** | Product override |
| Supplier default not set | MOQ: 0 | Not set (0) | **MOQ: 0** | System default |
| Product override = 0 | MOQ: 100 | MOQ: 0 | **MOQ: 100** | Supplier default (0 is ignored) |

**Key Rule:** If `product_supplier_conditions.moq > 0` or `lead_time_days > 0`, it takes precedence. If it's 0 or doesn't exist, the system falls back to supplier defaults.

---

## Part 2: Management Approaches

### Approach 1: Supplier Level (Default)

**Location:** `suppliers.default_moq`, `suppliers.default_lead_time_days`

**When to Use:**
- Supplier has consistent MOQ/lead time requirements across most products
- You want to set values once per supplier
- New products automatically inherit supplier defaults

**How It Works:**
1. Set `suppliers.default_moq = 100` and `default_lead_time_days = 14`
2. When linking a product to this supplier, MOQ/lead time auto-populates from supplier defaults
3. Products can override if needed

**Example:**
```
Supplier "Test Supplier" → default_moq = 100, default_lead_time_days = 14

When linking Product A:
  - Product A gets MOQ = 100, Lead Time = 14 days (auto-populated)
  
When linking Product B:
  - Product B gets MOQ = 100, Lead Time = 14 days (auto-populated)
```

### Approach 2: Product Level (Custom Override)

**Location:** `product_supplier_conditions.moq`, `product_supplier_conditions.lead_time_days`

**When to Use:**
- Product needs different MOQ/lead time than supplier default
- Specific product has unique ordering requirements
- You want to override supplier default for specific products

**How It Works:**
1. Link product to supplier (gets supplier default initially)
2. Manually edit product-supplier condition to set custom MOQ/lead time
3. Custom values take precedence over supplier defaults

**Example:**
```
Supplier "Test Supplier" → default_moq = 100, default_lead_time_days = 14

Product A:
  - product_supplier_conditions.moq = 100 (uses supplier default)
  - product_supplier_conditions.lead_time_days = 14 (uses supplier default)
  
Product B:
  - product_supplier_conditions.moq = 70 (custom override)
  - product_supplier_conditions.lead_time_days = 21 (custom override)
  - Effective MOQ = 70, Lead Time = 21 (not supplier defaults)
```

---

## Part 3: Impact of Supplier Default Changes

### Question: Does changing supplier default affect product-level values?

**Answer: It depends on the `apply_to_existing` flag.**

### Scenario 1: `apply_to_existing = False` (Default)

**Behavior:**
- ✅ Supplier default is updated
- ❌ **Product-level values are NOT changed**
- ✅ New products linked to supplier will use new default
- ✅ Products with explicit overrides remain unchanged

**Example:**
```
Before:
  Supplier default_moq = 100
  Product A: moq = 100 (using supplier default)
  Product B: moq = 70 (custom override)

After changing supplier default_moq = 150 (apply_to_existing = False):
  Supplier default_moq = 150 ✅
  Product A: moq = 100 ❌ (unchanged - still 100)
  Product B: moq = 70 ✅ (unchanged - explicit override)
  
New Product C linked:
  Product C: moq = 150 ✅ (uses new supplier default)
```

**Why:** Products with explicit values are considered "overrides" and are not automatically updated.

### Scenario 2: `apply_to_existing = True`

**Behavior:**
- ✅ Supplier default is updated
- ✅ **Product-level values that match OLD supplier default are updated**
- ❌ Products with explicit overrides (different values) remain unchanged

**Logic:**
1. System finds all product-supplier conditions where `moq == old_supplier_default` (or `lead_time_days == old_supplier_default`)
2. Updates those conditions to `new_supplier_default`
3. Leaves products with different values unchanged

**Example:**
```
Before:
  Supplier default_moq = 100
  Product A: moq = 100 (matches supplier default)
  Product B: moq = 70 (custom override)
  Product C: moq = 100 (matches supplier default)

After changing supplier default_moq = 150 (apply_to_existing = True):
  Supplier default_moq = 150 ✅
  Product A: moq = 150 ✅ (updated - matched old default)
  Product B: moq = 70 ✅ (unchanged - explicit override)
  Product C: moq = 150 ✅ (updated - matched old default)
```

**Important:** Only products that were using the supplier default (matching the old value) get updated. Products with custom values are preserved.

### UI Behavior

When editing supplier defaults, you'll see a dialog:

```
"Apply Default Changes to Existing Products?"

You've changed the supplier defaults. Would you like to apply 
these changes to existing products?

MOQ: 100 → 150
Lead Time: 14 → 21 days

[Skip] [Apply to Existing Products]
```

**Skip (apply_to_existing = False):**
- Updates supplier default only
- Existing products keep their current values
- New products use new default

**Apply to Existing Products (apply_to_existing = True):**
- Updates supplier default
- Updates products that match old default
- Preserves products with custom overrides

---

## Part 4: Safety Buffer

### Overview

**Safety Buffer** is a global client-level setting that adds extra days to lead time for safety margin in inventory calculations.

**Location:** `client_settings.safety_buffer_days`  
**Default:** 7 days  
**Level:** Client (Global - applies to all products)

### Usage

Safety buffer is added to lead time in various calculations:

```
Total Required Days = Lead Time + Safety Buffer
Stockout Risk = f(DIR, Total Required Days)
Reorder Point = (avg_daily_demand * lead_time) + safety_stock
```

### Where It's Used

- ✅ Stockout risk calculation: `DIR < (lead_time + safety_buffer)` → High risk
- ✅ Understocked threshold: `understocked_threshold = lead_time + buffer` (default)
- ✅ Reorder recommendations: `REORDER if DIR < (lead_time + buffer)`
- ✅ Inventory calculations: Added to lead time for safety margin

### Configuration

- **UI:** Settings → Inventory Thresholds → Safety Buffer
- **API:** `PUT /api/v1/settings` (set `safety_buffer_days`)
- **Default:** 7 days (if not configured)

---

## Part 5: API Reference

### Supplier Level

```http
PUT /api/v1/suppliers/{supplier_id}
{
  "default_moq": 150,
  "default_lead_time_days": 21,
  "apply_to_existing": true  // Optional, default: false
}
```

### Product Level

```http
POST /api/v1/products/{item_id}/suppliers
{
  "supplier_id": "...",
  "moq": 70,  // Optional - auto-populates from supplier default if not provided
  "lead_time_days": 21
}

PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
{
  "moq": 70,  // Update product-specific MOQ
  "lead_time_days": 21
}

GET /api/v1/products/{item_id}/suppliers
// Returns all suppliers with MOQ/lead time for this product
```

### Safety Buffer

```http
GET /api/v1/settings
// Returns client settings including safety_buffer_days

PUT /api/v1/settings
{
  "safety_buffer_days": 10
}
```

---

## Part 6: Data Model

### Database Schema

```sql
-- Supplier defaults
suppliers (
  id UUID,
  default_moq INTEGER DEFAULT 0,  -- Supplier-level default
  default_lead_time_days INTEGER DEFAULT 14
)

-- Product-supplier conditions (overrides)
product_supplier_conditions (
  id UUID,
  item_id VARCHAR(255),
  supplier_id UUID,
  moq INTEGER DEFAULT 0,  -- Product-level override
  lead_time_days INTEGER DEFAULT 0,
  is_primary BOOLEAN DEFAULT FALSE  -- Primary supplier flag
)

-- Client settings (global)
client_settings (
  id UUID,
  client_id UUID UNIQUE,
  safety_buffer_days INTEGER DEFAULT 7
)
```

### Effective Value Calculation

The system calculates effective MOQ/lead time using this logic:

```python
# Pseudo-code
def get_effective_moq(item_id, supplier_id):
    condition = get_product_supplier_condition(item_id, supplier_id)
    supplier = get_supplier(supplier_id)
    
    if condition and condition.moq > 0:
        return condition.moq  # Product override
    elif supplier and supplier.default_moq > 0:
        return supplier.default_moq  # Supplier default
    else:
        return 0  # System default
```

---

## Part 7: Usage in Business Logic

### Cart Validation

```python
# backend/services/cart_service.py
effective_moq = get_effective_moq(item_id, supplier_id)
if quantity < effective_moq:
    raise ValueError(f"Quantity {quantity} is less than MOQ {effective_moq}")
```

### Purchase Order Validation

```python
# backend/services/purchase_order_service.py
effective_moq = get_effective_moq(item_id, supplier_id)
if item_data.quantity < effective_moq:
    raise ValueError(f"Quantity {item_data.quantity} is less than MOQ {effective_moq}")
```

### Recommendations

```python
# backend/services/recommendations_service.py
effective_lead_time = get_effective_lead_time(item_id, supplier_id)
required_days = effective_lead_time + settings.safety_buffer_days
if dir < required_days:
    recommendation_type = "REORDER"
```

### Stockout Risk

```python
# backend/services/metrics_service.py
effective_lead_time = get_effective_lead_time(item_id, supplier_id)
total_required_days = effective_lead_time + safety_buffer_days
if dir < total_required_days:
    risk = 100 * (1 - dir / total_required_days)
```

---

## Part 8: Edge Cases

### Cart Items When Supplier MOQ Changes

**Scenario:** What happens to products already in the draft/cart when supplier MOQ changes?

**Current Behavior:**

1. **Cart Items Don't Store MOQ**
   - Cart items (`order_cart_items`) store `quantity` but **NOT** MOQ
   - MOQ is calculated **dynamically** each time the cart is fetched

2. **MOQ Recalculation on Cart Load**
   - When `GET /api/v1/order-planning/cart` is called, the system:
     - Fetches cart items from database
     - Recalculates `effective_moq` for each item using current supplier/product conditions
     - Returns updated MOQ in response

3. **Visual Feedback**
   - Frontend displays current MOQ next to quantity input
   - If `quantity < moq`, shows:
     - Red text for MOQ display
     - Red ring around quantity input
     - Clear visual warning

4. **PO Creation Validation**
   - When creating purchase order from cart, system validates:
     ```python
     if item_data.quantity < effective_moq:
         raise ValueError(f"Quantity {item_data.quantity} is less than MOQ {effective_moq}")
     ```
   - **PO creation will FAIL** if cart quantity is below new MOQ

**Example Flow:**

```
Step 1: User adds item to cart
  - Product: SKU-001
  - Supplier: Test Supplier (default_moq = 50)
  - Quantity: 70 ✅ (70 >= 50, valid)
  - Cart item stored: quantity = 70

Step 2: Supplier default MOQ changes
  - Supplier default_moq: 50 → 100
  - apply_to_existing: false (or true, doesn't matter for cart)

Step 3: User views cart
  - Cart item still has: quantity = 70
  - System recalculates: effective_moq = 100 (new supplier default)
  - UI shows: 
    - Quantity: 70
    - MOQ: 100 (in red text)
    - Input field with red ring (70 < 100)

Step 4: User tries to create PO
  - System validates: 70 < 100
  - ❌ ERROR: "Quantity 70 is less than MOQ 100"
  - PO creation blocked

Step 5: User updates quantity
  - Changes quantity to 100 (or higher)
  - ✅ PO creation succeeds
```

**Important Points:**

✅ **What Works:**
- MOQ is always current (recalculated on cart load)
- Visual warnings alert user to invalid quantities
- PO creation is blocked if quantity < MOQ
- User can update quantity before creating PO

⚠️ **Limitations:**
- Cart items with old quantities remain in cart (not auto-updated)
- No automatic notification when MOQ changes
- User must manually update quantities or remove invalid items

### Multiple Suppliers

**Scenario:** Product has multiple suppliers - which one's MOQ/lead time is used?

**Answer:** The system uses the **primary supplier** (`is_primary = True`).

- Effective statistics (averages, custom counts) only include products where the supplier is primary
- When calculating effective MOQ/lead time, the system uses the primary supplier's values
- If no primary supplier is set, the system may use the first supplier found (implementation-dependent)

**Best Practice:** Always set `is_primary = True` for the default supplier for each product.

---

## Part 9: Best Practices

### When to Use Supplier Default

✅ **Use supplier default when:**
- Supplier has consistent MOQ/lead time policy
- Most products will use the same values
- You want to set values once and forget it

### When to Use Product Override

✅ **Use product override when:**
- Product has unique ordering requirements
- Product needs different MOQ/lead time than supplier default
- You want to fine-tune specific products

### When to Use `apply_to_existing = True`

✅ **Use when:**
- Supplier changed their MOQ/lead time policy
- You want to bulk-update products using old default
- You're confident products matching old default should change

⚠️ **Be careful:**
- Only updates products matching old default
- Products with custom values are preserved
- Review which products will be affected before applying

### Safety Buffer

✅ **Best Practices:**
- Set safety buffer based on supplier reliability
- More reliable suppliers → lower buffer (5-7 days)
- Less reliable suppliers → higher buffer (10-14 days)
- Review and adjust periodically based on actual delivery performance

---

## Part 10: Summary Table

| Aspect | Supplier Level | Product Level |
|--------|---------------|---------------|
| **Location** | `suppliers.default_moq`<br>`suppliers.default_lead_time_days` | `product_supplier_conditions.moq`<br>`product_supplier_conditions.lead_time_days` |
| **Priority** | Fallback (2nd) | Highest (1st) |
| **Scope** | All products for supplier | Specific product-supplier pair |
| **Auto-populated** | No | Yes (from supplier default) |
| **Affected by supplier change** | Yes (always) | Only if `apply_to_existing = True` and matches old default |
| **Use case** | Consistent supplier policy | Product-specific requirements |

---

**Last Updated:** 2025-12-15  
**Status:** Complete implementation documented
