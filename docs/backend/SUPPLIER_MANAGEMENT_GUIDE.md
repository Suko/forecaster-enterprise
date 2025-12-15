# Supplier Management Guide

Complete guide to supplier setup, product-supplier relationships, MOQ, Lead Time, and primary supplier management.

---

## Table of Contents

1. [Quick Reference](#quick-reference)
2. [Supplier Setup & Management](#part-1-supplier-setup--management)
3. [Product-Supplier Relationships](#part-2-product-supplier-relationships)
4. [Primary/Default Supplier Management](#part-3-primarydefault-supplier-management)
5. [MOQ & Lead Time Configuration](#part-4-moq--lead-time-configuration)
6. [SKU Relationships](#part-5-sku-relationships)
7. [Effective Statistics](#part-6-effective-statistics)
8. [Safety Buffer](#part-7-safety-buffer)
9. [API Reference](#part-8-api-reference)
10. [Data Model](#part-9-data-model)
11. [Usage in Business Logic](#part-10-usage-in-business-logic)
12. [Best Practices](#part-11-best-practices)
13. [Edge Cases](#part-12-edge-cases)

---

## Quick Reference

### Configuration Summary

| Parameter | Level | Table | Default | Priority | Where to Set |
|-----------|-------|-------|---------|----------|--------------|
| **MOQ** | Product-Supplier Override | `product_supplier_conditions` | 0 | 1st (highest) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ |
| **MOQ** | Supplier Default | `suppliers` | 0 | 2nd (fallback) | Purchase Orders → Suppliers → [Supplier] → Edit → Default MOQ |
| **Lead Time** | Product-Supplier Override | `product_supplier_conditions` | 0 | 1st (highest) | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ |
| **Lead Time** | Supplier Default | `suppliers` | 14 days | 2nd (fallback) | Purchase Orders → Suppliers → [Supplier] → Edit → Default Lead Time |
| **Primary Supplier** | Product-Supplier | `product_supplier_conditions` | false | N/A | Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ → Primary Supplier |
| **Safety Buffer** | Client (Global) | `client_settings` | 7 days | N/A | Settings → Inventory Thresholds → Safety Buffer |

### Resolution Priority

```
MOQ & Lead Time:
1. product_supplier_conditions.moq/lead_time_days (if > 0) → Product override
2. suppliers.default_moq/default_lead_time_days (if > 0) → Supplier default
3. System default (0 for MOQ, 14 days for Lead Time)

Primary Supplier:
- Only one supplier can be primary per product (is_primary = True)
- Primary supplier is used for MOQ/lead time calculations
- Setting a new primary automatically unsets the old one

Safety Buffer:
- client_settings.safety_buffer_days (global per client)
```

---

## Part 1: Supplier Setup & Management

### Overview

Suppliers are the entities from which you purchase products. Each supplier can have:
- Contact information (email, phone, address)
- Default MOQ and Lead Time values
- Supplier type (PO = Purchase Order, WO = Work Order)
- Notes and custom fields

### Creating a Supplier

**Note:** Supplier creation via API is not yet implemented. Suppliers are typically created through:
- Database migrations/seeding
- External system sync (if `is_synced = true`)
- Direct database insertion

**Planned API:** `POST /api/v1/suppliers` (see roadmap)

```http
# Planned endpoint (not yet implemented)
POST /api/v1/suppliers
{
  "name": "Test Supplier",
  "contact_email": "contact@supplier.com",
  "contact_phone": "+1-555-0123",
  "address": "123 Main St, City, State",
  "supplier_type": "PO",
  "default_moq": 100,
  "default_lead_time_days": 14,
  "notes": "Primary supplier for electronics"
}
```

### Editing Supplier Information

**UI:** Purchase Orders → Suppliers → [Supplier] → Edit

You can update:
- Contact information
- Default MOQ and Lead Time
- Supplier type
- Notes

**Important:** When changing default MOQ/Lead Time, you'll be asked if you want to apply changes to existing products.

### Supplier Types

- **PO (Purchase Order):** Standard supplier for purchasing products
- **WO (Work Order):** Supplier for work orders (different workflow)

---

## Part 2: Product-Supplier Relationships

### Overview

Products can be linked to multiple suppliers, and each supplier can supply multiple products. This many-to-many relationship is stored in `product_supplier_conditions`.

### Linking a Product to a Supplier

**UI:** Purchase Orders → Suppliers → [Supplier] → Products → (Link Product)  
**API:** `POST /api/v1/products/{item_id}/suppliers`

When linking a product to a supplier:
- MOQ and Lead Time auto-populate from supplier defaults
- You can override these values at the product level
- You can set the supplier as primary for that product

**Example:**
```http
POST /api/v1/products/SKU-001/suppliers
{
  "supplier_id": "supplier-uuid",
  "moq": 100,  // Optional - uses supplier default if not provided
  "lead_time_days": 14,  // Optional - uses supplier default if not provided
  "is_primary": true,  // Set as primary supplier
  "supplier_sku": "SUP-SKU-001",  // Supplier's SKU if different
  "supplier_cost": 25.50,  // Price from this supplier
  "packaging_unit": "box",
  "packaging_qty": 12,
  "notes": "Preferred supplier for this product"
}
```

### Multiple Suppliers per Product

A product can have multiple suppliers, each with different:
- MOQ values
- Lead times
- Costs
- Packaging requirements
- SKU mappings

**Example:**
```
Product: SKU-001 "Widget"

Supplier A (Primary):
  - MOQ: 100
  - Lead Time: 14 days
  - Cost: $25.50
  - Supplier SKU: SUP-A-001

Supplier B (Secondary):
  - MOQ: 50
  - Lead Time: 21 days
  - Cost: $27.00
  - Supplier SKU: SUP-B-001
```

### Viewing Product-Supplier Relationships

**UI:** 
- Purchase Orders → Suppliers → [Supplier] → Products (see all products for this supplier)
- Inventory → [Product] → Suppliers (see all suppliers for this product)

**API:** `GET /api/v1/products/{item_id}/suppliers`

---

## Part 3: Primary/Default Supplier Management

### Overview

Each product should have **one primary supplier** (`is_primary = True`). The primary supplier is used for:
- MOQ and Lead Time calculations
- Effective statistics
- Default supplier selection in purchase orders
- Inventory recommendations

### Setting Primary Supplier

**UI:** Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ → Check "Set as primary supplier"

**API:**
```http
PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
{
  "is_primary": true
}
```

**Important:** When you set a supplier as primary, the system **automatically unsets** all other primary suppliers for that product. Only one supplier can be primary per product.

### Changing Primary Supplier

To change the primary supplier for a product:

1. **Option 1:** Set the new supplier as primary
   - The old primary is automatically unset
   
2. **Option 2:** Unset the old primary, then set the new one
   - Uncheck "Set as primary supplier" for the old supplier
   - Check "Set as primary supplier" for the new supplier

### Primary Supplier Behavior

- **Automatic Unset:** Setting a new primary automatically unsets the old one
- **Required for Calculations:** Effective MOQ/lead time uses primary supplier
- **Statistics:** Effective statistics only count products where supplier is primary
- **Default Selection:** Primary supplier is used as default in purchase orders

### Example Flow

```
Product: SKU-001

Step 1: Link Supplier A
  - Supplier A: is_primary = true ✅

Step 2: Link Supplier B
  - Supplier B: is_primary = false (default)

Step 3: Set Supplier B as primary
  - Supplier B: is_primary = true ✅
  - Supplier A: is_primary = false (automatically unset) ✅
```

---

## Part 4: MOQ & Lead Time Configuration

### Overview

MOQ (Minimum Order Quantity) and Lead Time can be configured at two levels:
1. **Supplier Level** - Default values for all products from this supplier
2. **Product Level** - Override values for specific products

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

### Supplier-Level Configuration

**Location:** `suppliers.default_moq`, `suppliers.default_lead_time_days`

**When to Use:**
- Supplier has consistent MOQ/lead time requirements across most products
- You want to set values once per supplier
- New products automatically inherit supplier defaults

**How It Works:**
1. Set `suppliers.default_moq = 100` and `default_lead_time_days = 14`
2. When linking a product to this supplier, MOQ/lead time auto-populates from supplier defaults
3. Products can override if needed

### Product-Level Configuration

**Location:** `product_supplier_conditions.moq`, `product_supplier_conditions.lead_time_days`

**When to Use:**
- Product needs different MOQ/lead time than supplier default
- Specific product has unique ordering requirements
- You want to override supplier default for specific products

**UI:** Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ

### Impact of Supplier Default Changes

When you change supplier defaults, you can choose to apply changes to existing products:

**Option 1: `apply_to_existing = False` (Default)**
- ✅ Supplier default is updated
- ❌ Product-level values are NOT changed
- ✅ New products linked to supplier will use new default

**Option 2: `apply_to_existing = True`**
- ✅ Supplier default is updated
- ✅ Product-level values that match OLD supplier default are updated
- ❌ Products with custom overrides remain unchanged

**UI Dialog:**
```
"Apply Default Changes to Existing Products?"

You've changed the supplier defaults. Would you like to apply 
these changes to existing products?

MOQ: 100 → 150
Lead Time: 14 → 21 days

[Skip] [Apply to Existing Products]
```

---

## Part 5: SKU Relationships

### Overview

Products can have different SKUs at the supplier level. This is useful when:
- Supplier uses their own SKU system
- Product has different identifiers in supplier's system
- You need to map your internal SKU to supplier's SKU

### Supplier SKU Field

**Location:** `product_supplier_conditions.supplier_sku`

**Example:**
```
Your System:
  Product: SKU-001 "Widget"

Supplier A:
  - Your SKU: SKU-001
  - Supplier SKU: SUP-A-WIDGET-001
  - Supplier Cost: $25.50

Supplier B:
  - Your SKU: SKU-001
  - Supplier SKU: SUP-B-WID-001
  - Supplier Cost: $27.00
```

### Setting Supplier SKU

**UI:** Purchase Orders → Suppliers → [Supplier] → Products → Edit MOQ → Supplier SKU field  
**API:**
```http
PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
{
  "supplier_sku": "SUP-A-WIDGET-001"
}
```

### Use Cases

- **Purchase Orders:** Include supplier SKU in PO documents
- **Order Tracking:** Match orders to supplier's system
- **Reporting:** Track products by supplier SKU
- **Integration:** Map to external systems

---

## Part 6: Effective Statistics

### Overview

The system calculates **effective statistics** for suppliers, showing:
- Average effective MOQ across all products (where supplier is primary)
- Average effective Lead Time across all products
- Count of products with custom MOQ/Lead Time
- Min/Max values

### What Are Effective Values?

Effective values account for product-level overrides. For example:

```
Supplier Default: MOQ = 100

Product A: Uses supplier default → Effective MOQ = 100
Product B: Custom MOQ = 70 → Effective MOQ = 70
Product C: Uses supplier default → Effective MOQ = 100

Effective Average MOQ = (100 + 70 + 100) / 3 = 90
Custom MOQ Count = 1 (Product B)
```

### Where Effective Statistics Are Shown

**Supplier List Page:**
- Shows default MOQ/Lead Time
- Shows effective average (if different from default)
- Shows custom counts

**Supplier Detail Page:**
- Shows default MOQ/Lead Time
- Shows effective average (if different from default)
- Shows custom counts

### Important Notes

- **Only Primary Products:** Effective statistics only include products where the supplier is **primary** (`is_primary = True`)
- **Real Values:** Effective values show what's actually used, not just defaults
- **Custom Counts:** Shows how many products have custom overrides

---

## Part 7: Safety Buffer

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

## Part 8: API Reference

### Supplier Management

```http
# Get all suppliers (paginated)
GET /api/v1/suppliers?page=1&page_size=50&search=test&supplier_type=PO

# Get supplier by ID
GET /api/v1/suppliers/{supplier_id}

# Create supplier (NOT YET IMPLEMENTED - see roadmap)
# POST /api/v1/suppliers
# {
#   "name": "Test Supplier",
#   "contact_email": "contact@supplier.com",
#   "default_moq": 100,
#   "default_lead_time_days": 14
# }

# Update supplier
PUT /api/v1/suppliers/{supplier_id}
{
  "default_moq": 150,
  "default_lead_time_days": 21,
  "apply_to_existing": true  // Optional, default: false
}
```

### Product-Supplier Relationships

```http
# Link product to supplier
POST /api/v1/products/{item_id}/suppliers
{
  "supplier_id": "...",
  "moq": 70,  // Optional - auto-populates from supplier default
  "lead_time_days": 21,  // Optional - auto-populates from supplier default
  "is_primary": true,  // Set as primary supplier
  "supplier_sku": "SUP-SKU-001",  // Supplier's SKU
  "supplier_cost": 25.50,
  "packaging_unit": "box",
  "packaging_qty": 12
}

# Update product-supplier relationship
PUT /api/v1/products/{item_id}/suppliers/{supplier_id}
{
  "moq": 70,
  "lead_time_days": 21,
  "is_primary": true,  // Setting to true automatically unsets other primaries
  "supplier_sku": "SUP-SKU-001",
  "supplier_cost": 25.50
}

# Get all suppliers for a product
GET /api/v1/products/{item_id}/suppliers

# Remove product-supplier relationship
DELETE /api/v1/products/{item_id}/suppliers/{supplier_id}
```

### Safety Buffer

```http
# Get client settings (including buffer)
GET /api/v1/settings

# Update safety buffer
PUT /api/v1/settings
{
  "safety_buffer_days": 10
}
```

---

## Part 9: Data Model

### Database Schema

```sql
-- Suppliers table
suppliers (
  id UUID PRIMARY KEY,
  client_id UUID NOT NULL,
  external_id VARCHAR(100),  -- ID from ERP (if synced)
  name VARCHAR(255) NOT NULL,
  contact_email VARCHAR(255),
  contact_phone VARCHAR(50),
  address TEXT,
  supplier_type VARCHAR(20) DEFAULT 'PO',  -- PO or WO
  default_moq INTEGER DEFAULT 0,  -- Supplier-level default
  default_lead_time_days INTEGER DEFAULT 14,
  is_synced BOOLEAN DEFAULT FALSE,
  notes TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(client_id, name)
)

-- Product-supplier conditions (many-to-many relationship)
product_supplier_conditions (
  id UUID PRIMARY KEY,
  client_id UUID NOT NULL,
  item_id VARCHAR(255) NOT NULL,  -- Product identifier (item_id, not sku)
  supplier_id UUID NOT NULL,
  
  -- Ordering conditions
  moq INTEGER DEFAULT 0,  -- Product-level override
  lead_time_days INTEGER DEFAULT 0,
  
  -- Supplier-specific product information
  supplier_sku VARCHAR(100),  -- Supplier's SKU if different
  supplier_cost DECIMAL(10,2),  -- Price from this supplier
  
  -- Packaging requirements
  packaging_unit VARCHAR(50),  -- box, pallet, carton, etc.
  packaging_qty INTEGER,  -- units per package
  
  -- Primary supplier flag
  is_primary BOOLEAN DEFAULT FALSE,  -- Only one per product
  
  notes TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(client_id, item_id, supplier_id)
)

-- Client settings (global)
client_settings (
  id UUID PRIMARY KEY,
  client_id UUID UNIQUE NOT NULL,
  safety_buffer_days INTEGER DEFAULT 7,
  -- ... other settings
)
```

### Effective Value Calculation

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

def get_effective_lead_time(item_id, supplier_id):
    condition = get_product_supplier_condition(item_id, supplier_id)
    supplier = get_supplier(supplier_id)
    
    if condition and condition.lead_time_days > 0:
        return condition.lead_time_days  # Product override
    elif supplier and supplier.default_lead_time_days > 0:
        return supplier.default_lead_time_days  # Supplier default
    else:
        return 14  # System default
```

---

## Part 10: Usage in Business Logic

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

## Part 11: Best Practices

### Supplier Setup

✅ **Best Practices:**
- Set realistic default MOQ and Lead Time values
- Keep supplier contact information up to date
- Use supplier types correctly (PO vs WO)
- Add notes for important supplier information

### Product-Supplier Relationships

✅ **Best Practices:**
- Always set a primary supplier for each product
- Use supplier defaults when most products share the same MOQ/lead time
- Use product-level overrides for exceptions
- Keep supplier SKU mappings accurate

### Primary Supplier Management

✅ **Best Practices:**
- Set primary supplier when linking products
- Review primary suppliers periodically
- Change primary supplier if supplier relationship changes
- Ensure only one primary per product

### MOQ & Lead Time

✅ **Best Practices:**
- Use supplier defaults for consistency
- Override at product level only when necessary
- Use `apply_to_existing = True` carefully (review affected products first)
- Keep values realistic and up to date

### Multiple Suppliers

✅ **Best Practices:**
- Use multiple suppliers for redundancy
- Set primary supplier based on reliability/cost
- Keep all supplier relationships up to date
- Use supplier SKU mappings for accurate ordering

### Safety Buffer

✅ **Best Practices:**
- Set safety buffer based on supplier reliability
- More reliable suppliers → lower buffer (5-7 days)
- Less reliable suppliers → higher buffer (10-14 days)
- Review and adjust periodically based on actual delivery performance

---

## Part 12: Edge Cases

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

### Multiple Primary Suppliers

**Scenario:** What if multiple suppliers are set as primary for the same product?

**Answer:** This shouldn't happen - the system automatically unsets old primary when setting a new one. If it does occur (e.g., from direct database changes), the system uses the first primary found.

### No Primary Supplier

**Scenario:** What if a product has no primary supplier?

**Answer:** The system may use the first supplier found, but this is not recommended. Always set a primary supplier for each product.

---

**Last Updated:** 2025-12-15  
**Status:** Complete implementation documented
