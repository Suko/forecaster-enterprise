# MOQ Management Guide: Supplier vs Product Level

## Overview

The system supports **two levels** of MOQ (Minimum Order Quantity) management:

1. **Supplier Level** (`suppliers.default_moq`) - Default MOQ for a supplier
2. **Product Level** (`product_supplier_conditions.moq`) - Product-specific MOQ override

## How MOQ Resolution Works

### Priority Order (Highest to Lowest)

```
1. product_supplier_conditions.moq (if exists and > 0)
   └─ Product-specific override (highest priority)
   
2. suppliers.default_moq (if > 0)
   └─ Supplier default (fallback)
   
3. System default (0)
   └─ Final fallback
```

### Example Scenarios

| Scenario | Supplier Default | Product Condition | Effective MOQ | Source |
|----------|-----------------|-------------------|---------------|--------|
| Product uses supplier default | 100 | Not set (0) | **100** | Supplier default |
| Product has custom MOQ | 100 | 70 | **70** | Product override |
| Supplier default not set | 0 | Not set (0) | **0** | System default |
| Product override = 0 | 100 | 0 | **100** | Supplier default (0 is ignored) |

**Key Rule:** If `product_supplier_conditions.moq > 0`, it takes precedence. If it's 0 or doesn't exist, the system falls back to `suppliers.default_moq`.

---

## Two Management Approaches

### Approach 1: Supplier Level (Default MOQ)

**Location:** `suppliers.default_moq`

**When to Use:**
- Supplier has consistent MOQ requirements across most products
- You want to set MOQ once per supplier
- New products automatically inherit supplier default

**How It Works:**
1. Set `suppliers.default_moq = 100`
2. When linking a product to this supplier, MOQ auto-populates to 100
3. Products can override if needed

**Example:**
```
Supplier "Test Supplier" → default_moq = 100

When linking Product A:
  - Product A gets MOQ = 100 (auto-populated)
  
When linking Product B:
  - Product B gets MOQ = 100 (auto-populated)
```

---

### Approach 2: Product Level (Custom Override)

**Location:** `product_supplier_conditions.moq`

**When to Use:**
- Product needs different MOQ than supplier default
- Specific product has unique ordering requirements
- You want to override supplier default for specific products

**How It Works:**
1. Link product to supplier (gets supplier default initially)
2. Manually edit product-supplier condition to set custom MOQ
3. Custom MOQ takes precedence over supplier default

**Example:**
```
Supplier "Test Supplier" → default_moq = 100

Product A:
  - product_supplier_conditions.moq = 100 (uses supplier default)
  
Product B:
  - product_supplier_conditions.moq = 70 (custom override)
  - Effective MOQ = 70 (not 100)
```

---

## Impact of Supplier Default Changes

### Question: Does changing supplier default affect product-level MOQs?

**Answer: It depends on the `apply_to_existing` flag.**

### Scenario 1: `apply_to_existing = False` (Default)

**Behavior:**
- ✅ Supplier default is updated
- ❌ **Product-level MOQs are NOT changed**
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

**Why:** Products with explicit MOQ values are considered "overrides" and are not automatically updated.

---

### Scenario 2: `apply_to_existing = True`

**Behavior:**
- ✅ Supplier default is updated
- ✅ **Product-level MOQs that match OLD supplier default are updated**
- ❌ Products with explicit overrides (different MOQ) remain unchanged

**Logic:**
1. System finds all product-supplier conditions where `moq == old_supplier_default`
2. Updates those conditions to `new_supplier_default`
3. Leaves products with different MOQ values unchanged

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

**Important:** Only products that were using the supplier default (matching the old value) get updated. Products with custom MOQs are preserved.

---

## UI Behavior

### Supplier Edit Page

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
- Existing products keep their current MOQ
- New products use new default

**Apply to Existing Products (apply_to_existing = True):**
- Updates supplier default
- Updates products that match old default
- Preserves products with custom overrides

---

## Best Practices

### When to Use Supplier Default

✅ **Use supplier default when:**
- Supplier has consistent MOQ policy
- Most products will use the same MOQ
- You want to set MOQ once and forget it

### When to Use Product Override

✅ **Use product override when:**
- Product has unique ordering requirements
- Product needs different MOQ than supplier default
- You want to fine-tune specific products

### When to Use `apply_to_existing = True`

✅ **Use when:**
- Supplier changed their MOQ policy
- You want to bulk-update products using old default
- You're confident products matching old default should change

⚠️ **Be careful:**
- Only updates products matching old default
- Products with custom MOQs are preserved
- Review which products will be affected before applying

---

## API Endpoints

### Supplier Level

```http
PUT /api/v1/suppliers/{supplier_id}
{
  "default_moq": 150,
  "apply_to_existing": true  // Optional, default: false
}
```

### Product Level

```http
POST /api/v1/products/{item_id}/suppliers
{
  "supplier_id": "...",
  "moq": 70  // Optional - auto-populates from supplier default if not provided
}

PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
{
  "moq": 70  // Update product-specific MOQ
}
```

---

## Data Model

### Tables

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
  lead_time_days INTEGER DEFAULT 0
)
```

---

## Summary

| Aspect | Supplier Level | Product Level |
|--------|---------------|---------------|
| **Location** | `suppliers.default_moq` | `product_supplier_conditions.moq` |
| **Priority** | Fallback (2nd) | Highest (1st) |
| **Scope** | All products for supplier | Specific product-supplier pair |
| **Auto-populated** | No | Yes (from supplier default) |
| **Affected by supplier change** | Yes (always) | Only if `apply_to_existing = True` and matches old default |
| **Use case** | Consistent supplier policy | Product-specific requirements |

---

## Edge Case: Cart Items When Supplier MOQ Changes

### Scenario

**What happens to products already in the draft/cart when supplier MOQ changes?**

### Current Behavior

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

### Example Flow

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

### Important Points

✅ **What Works:**
- MOQ is always current (recalculated on cart load)
- Visual warnings alert user to invalid quantities
- PO creation is blocked if quantity < MOQ
- User can update quantity before creating PO

⚠️ **Limitations:**
- Cart items with old quantities remain in cart (not auto-updated)
- No automatic notification when MOQ changes
- User must manually update quantities or remove invalid items

### Best Practices

1. **Before Creating PO:**
   - Review cart items for MOQ violations (red warnings)
   - Update quantities to meet new MOQ requirements
   - Or remove items that no longer meet requirements

2. **After Supplier MOQ Changes:**
   - Consider notifying users with items in cart
   - Or automatically flag cart items for review

3. **For Bulk Changes:**
   - If changing supplier MOQ with `apply_to_existing = True`:
     - Only affects product-supplier conditions
     - Does NOT automatically update cart quantities
     - Cart items still need manual review/update

### Future Improvements (Potential)

- **Auto-update cart quantities** when MOQ increases (if quantity < new MOQ)
- **Notification system** when MOQ changes affect cart items
- **Bulk update** option to adjust all cart items to new MOQ
- **Warning banner** on cart page when MOQ changes detected

---

**Last Updated:** 2025-01-27  
**Status:** Current implementation documented
