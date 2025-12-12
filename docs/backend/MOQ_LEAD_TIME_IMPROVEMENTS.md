# MOQ & Lead Time Management Improvements

## Current State

### Where MOQ & Lead Times Are Set

**Current Location:** `product_supplier_conditions` table (product-supplier relationship level)

```27:28:backend/models/product_supplier.py
    moq = Column(Integer, default=0, nullable=False)  # Minimum Order Quantity
    lead_time_days = Column(Integer, default=0, nullable=False)  # Days to deliver
```

**Current Usage:**
- ✅ Cart validation: `quantity >= MOQ`
- ✅ Purchase order validation: `quantity >= MOQ`
- ✅ Inventory recommendations: `DIR < (lead_time + buffer)`
- ✅ Forecast calculations: Lead time for reorder point calculations
- ✅ Metrics: Stockout risk based on lead time

**Current Limitations:**
- ❌ No product-level defaults (must set MOQ/lead time for each supplier)
- ❌ No supplier-level defaults (must set MOQ/lead time for each product)
- ❌ No fallback mechanism when product-supplier condition doesn't exist
- ❌ Repetitive data entry when same MOQ/lead time applies to multiple suppliers

---

## Proposed Improvements

### Option 1: Product-Level Defaults (Recommended)

**Strategy:** Add MOQ and lead time defaults to `products` table, use as fallback when product-supplier condition doesn't specify.

**Benefits:**
- ✅ Set once per product, use across all suppliers
- ✅ Supplier-specific overrides still possible
- ✅ Reduces data entry for common cases
- ✅ Backward compatible (existing product-supplier conditions take precedence)

**Implementation:**

1. **Add columns to `products` table:**
   ```sql
   ALTER TABLE products ADD COLUMN default_moq INTEGER DEFAULT 0;
   ALTER TABLE products ADD COLUMN default_lead_time_days INTEGER DEFAULT 14;
   ```

2. **Update Product model:**
   ```python
   # backend/models/product.py
   default_moq = Column(Integer, default=0, nullable=False)
   default_lead_time_days = Column(Integer, default=14, nullable=False)
   ```

3. **Update resolution logic (priority order):**
   - **First:** Use `product_supplier_conditions.moq` if exists
   - **Fallback:** Use `products.default_moq`
   - **Final:** Use system default (0 for MOQ, 14 for lead time)

4. **Update services:**
   - `CartService`: Check product default if condition not found
   - `PurchaseOrderService`: Use product default as fallback
   - `RecommendationsService`: Use product default for calculations
   - `MetricsService`: Use product default for DIR calculations

---

### Option 2: Supplier-Level Defaults

**Strategy:** Add MOQ and lead time defaults to `suppliers` table.

**Benefits:**
- ✅ Set once per supplier, use across all products
- ✅ Useful when supplier has consistent MOQ/lead time policies

**Limitations:**
- ❌ Less common use case (suppliers often vary by product)
- ❌ Doesn't solve product-level defaults

**Implementation:**
```sql
ALTER TABLE suppliers ADD COLUMN default_moq INTEGER DEFAULT 0;
ALTER TABLE suppliers ADD COLUMN default_lead_time_days INTEGER DEFAULT 14;
```

---

### Option 3: Hybrid Approach (Best Solution)

**Strategy:** Support defaults at both product and supplier levels, with clear precedence.

**Precedence Order (highest to lowest):**
1. `product_supplier_conditions.moq` / `lead_time_days` (explicit override)
2. `products.default_moq` / `default_lead_time_days` (product default)
3. `suppliers.default_moq` / `default_lead_time_days` (supplier default)
4. System defaults (0 for MOQ, 14 for lead time)

**Benefits:**
- ✅ Maximum flexibility
- ✅ Reduces data entry
- ✅ Supports both product-centric and supplier-centric workflows

---

## Recommended Implementation Plan

### Phase 1: Product-Level Defaults (Priority 1)

**Why:** Most common use case - products often have consistent MOQ/lead time requirements across suppliers.

**Steps:**

1. **Database Migration:**
   - Add `default_moq` and `default_lead_time_days` to `products` table
   - Default values: `default_moq = 0`, `default_lead_time_days = 14`

2. **Model Updates:**
   - Update `Product` model with new columns
   - Update `ProductCreate` and `ProductUpdate` schemas

3. **Service Layer Updates:**
   - Create helper method: `_get_effective_moq(product, condition)` 
   - Create helper method: `_get_effective_lead_time(product, condition)`
   - Update all services to use these helpers:
     - `CartService.add_to_cart()`
     - `PurchaseOrderService.create_purchase_order()`
     - `RecommendationsService.get_recommendations()`
     - `MetricsService.calculate_metrics()`
     - `InventoryService` methods

4. **API Updates:**
   - Update `GET /api/v1/products/{item_id}` to include defaults
   - Update `PUT /api/v1/products/{item_id}` to allow updating defaults
   - Update product creation/update schemas

5. **Frontend Updates:**
   - Add MOQ/lead time fields to product form
   - Show effective MOQ/lead time (with override indicator)
   - Allow setting product defaults

---

### Phase 2: Supplier-Level Defaults (Priority 2)

**Why:** Useful for suppliers with consistent policies (e.g., "all orders minimum 100 units, 14 day lead time").

**Steps:**

1. **Database Migration:**
   - Add `default_moq` and `default_lead_time_days` to `suppliers` table

2. **Model Updates:**
   - Update `Supplier` model
   - Update supplier schemas

3. **Service Layer Updates:**
   - Update helper methods to check supplier defaults
   - Update resolution logic with full precedence chain

4. **API Updates:**
   - Update supplier endpoints to include defaults
   - Allow updating supplier defaults

---

### Phase 3: UI/UX Improvements (Priority 3)

**Features:**
- Show effective MOQ/lead time with source indicator:
  - "From product default"
  - "From supplier default"
  - "From product-supplier override"
- Bulk update tools:
  - Set product defaults for multiple products
  - Copy MOQ/lead time from one supplier to another
- Validation warnings:
  - Warn when product-supplier MOQ < product default
  - Suggest using product default when all suppliers have same MOQ

---

## Implementation Details

### Helper Method Pattern

```python
# backend/services/inventory_service.py

async def _get_effective_moq(
    self,
    client_id: UUID,
    item_id: str,
    supplier_id: Optional[UUID] = None
) -> int:
    """
    Get effective MOQ with fallback chain:
    1. product_supplier_conditions.moq (if supplier_id provided)
    2. products.default_moq
    3. System default (0)
    """
    # Try product-supplier condition first
    if supplier_id:
        condition_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = condition_result.scalar_one_or_none()
        if condition and condition.moq > 0:
            return condition.moq
    
    # Fallback to product default
    product_result = await self.db.execute(
        select(Product).where(
            Product.client_id == client_id,
            Product.item_id == item_id
        )
    )
    product = product_result.scalar_one_or_none()
    if product and product.default_moq > 0:
        return product.default_moq
    
    # System default
    return 0

async def _get_effective_lead_time(
    self,
    client_id: UUID,
    item_id: str,
    supplier_id: Optional[UUID] = None
) -> int:
    """
    Get effective lead time with fallback chain:
    1. product_supplier_conditions.lead_time_days (if supplier_id provided)
    2. products.default_lead_time_days
    3. System default (14)
    """
    # Similar pattern to _get_effective_moq
    ...
```

---

## Migration Strategy

### Backward Compatibility

1. **Existing Data:**
   - All existing `product_supplier_conditions` continue to work
   - New product defaults are optional (default to 0/14)
   - No breaking changes to existing APIs

2. **Gradual Migration:**
   - Phase 1: Add product defaults, keep existing product-supplier conditions
   - Phase 2: Optionally migrate common MOQ/lead times to product defaults
   - Phase 3: Add supplier defaults

3. **Data Migration Script:**
   ```python
   # scripts/migrate_moq_to_product_defaults.py
   # For products where all suppliers have same MOQ/lead time,
   # migrate to product default and remove from product-supplier conditions
   ```

---

## Testing Plan

### Unit Tests

- ✅ Test `_get_effective_moq()` with all precedence scenarios
- ✅ Test `_get_effective_lead_time()` with all precedence scenarios
- ✅ Test cart validation with product defaults
- ✅ Test purchase order validation with product defaults

### Integration Tests

- ✅ Test product creation with defaults
- ✅ Test product-supplier condition override
- ✅ Test recommendations using product defaults
- ✅ Test metrics calculations with product defaults

---

## API Changes

### New/Updated Endpoints

1. **GET /api/v1/products/{item_id}**
   - Response includes `default_moq` and `default_lead_time_days`

2. **PUT /api/v1/products/{item_id}**
   - Request body can include `default_moq` and `default_lead_time_days`

3. **GET /api/v1/products/{item_id}/suppliers**
   - Response includes `effective_moq` and `effective_lead_time_days` (computed)
   - Response includes `moq_source` and `lead_time_source` (for UI display)

---

## Schema Changes

### Product Schemas

```python
# backend/schemas/inventory.py

class ProductBase(BaseModel):
    item_id: str
    product_name: str
    category: str = "Uncategorized"
    unit_cost: Decimal = Decimal("0.00")
    default_moq: int = Field(0, ge=0, description="Default MOQ for this product")
    default_lead_time_days: int = Field(14, ge=0, description="Default lead time for this product")

class ProductSupplierResponse(ProductSupplierBase):
    # ... existing fields ...
    effective_moq: int  # Computed: condition.moq or product.default_moq
    effective_lead_time_days: int  # Computed: condition.lead_time_days or product.default_lead_time_days
    moq_source: str  # "product_supplier" | "product_default" | "system_default"
    lead_time_source: str  # "product_supplier" | "product_default" | "system_default"
```

---

## Summary

**Current:** MOQ and lead times only at product-supplier level (must set for each supplier)

**Proposed:** 
- ✅ Product-level defaults (Phase 1 - Priority 1)
- ✅ Supplier-level defaults (Phase 2 - Priority 2)
- ✅ Clear precedence chain with fallbacks
- ✅ Backward compatible
- ✅ Reduces data entry
- ✅ More flexible and user-friendly

**Next Steps:**
1. Review and approve plan
2. Create database migration for product defaults
3. Implement helper methods
4. Update services to use helpers
5. Update APIs and schemas
6. Add frontend support

