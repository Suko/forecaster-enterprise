# Test Data Normalization Plan

**Goal:** Normalize all test product data with synthetic sales/stock data from today backwards, ensuring every SKU has unified recent reference dates for complete testing functionality.

---

## 1. Current State Analysis

### Current Issues
- ❌ Sales data (`ts_demand_daily`) ends at 2024-12-31, but today is 2025-01-27
- ❌ DIR calculation requires last 30 days of sales → returns 0 for all products
- ❌ Status shows "unknown" because DIR cannot be calculated
- ❌ Recommendations empty because they depend on calculated metrics
- ❌ No unified reference date across all SKUs

### Data Sources
- ✅ **M5 Dataset:** Historical data from 2015-2024 (preserved)
- ✅ **Synthetic Data:** Some synthetic data from 2024 backwards
- ❌ **Recent Data Gap:** Missing data from today backwards (last 30-365 days)

### Current Data Structure
- ✅ Products: 40 items
- ✅ Locations: 3 locations
- ✅ Suppliers: 4 suppliers
- ✅ Product-Supplier Conditions: 66 links
- ✅ Stock Levels: 120 records
- ❌ Sales History: Missing recent 30 days

---

## 2. Required Fields for Full Functionality

### 2.1 Core Product Data (`products` table)
**Status:** ✅ Complete
- `item_id` (string) - Product identifier
- `sku` (string, optional) - SKU alias
- `product_name` (string) - Display name
- `category` (string) - Product category
- `unit_cost` (Decimal) - Cost per unit

### 2.2 Sales History (`ts_demand_daily` table)
**Status:** ❌ Missing recent data
**Required Fields:**
- `item_id` (string) - Product identifier
- `date_local` (Date) - Sales date
- `units_sold` (Decimal) - Units sold on this date
- `client_id` (UUID) - Client identifier
- `promotion_flag` (boolean, optional) - Was promotion active
- `holiday_flag` (boolean, optional) - Was holiday
- `is_weekend` (boolean, optional) - Weekend flag
- `marketing_spend` (Decimal, optional) - Marketing spend
- `stock_on_date` (integer, optional) - Stock level at end of day

**Minimum Requirements:**
- ✅ Last 30 days from today (for DIR calculation)
- ✅ Last 90 days from today (for trend analysis)
- ✅ Last 365 days from today (for forecasting)
- ✅ At least 1 sale per week per SKU (to avoid "dead stock" status)

### 2.3 Stock Levels (`stock_levels` table)
**Status:** ✅ Complete
- `item_id` (string) - Product identifier
- `location_id` (string) - Location identifier
- `current_stock` (integer) - Current stock level
- `client_id` (UUID) - Client identifier

### 2.4 Product-Supplier Conditions (`product_supplier_conditions` table)
**Status:** ✅ Complete
- `item_id` (string) - Product identifier
- `supplier_id` (UUID) - Supplier identifier
- `moq` (integer) - Minimum Order Quantity
- `lead_time_days` (integer) - Lead time in days
- `supplier_cost` (Decimal, optional) - Supplier cost
- `packaging_unit` (string, optional) - Packaging unit
- `packaging_qty` (integer, optional) - Units per package
- `is_primary` (boolean) - Primary supplier flag

### 2.5 Client Settings (`client_settings` table)
**Status:** ✅ Complete
- `safety_buffer_days` (integer) - Safety buffer (default: 7)
- `understocked_threshold` (integer) - DIR threshold for understocked (default: 14)
- `overstocked_threshold` (integer) - DIR threshold for overstocked (default: 90)
- `dead_stock_days` (integer) - Days without sales = dead stock (default: 90)

---

## 3. Normalization Strategy

### 3.1 Unified Reference Date
**Decision:** Use `today` as the reference date for all calculations.

**Data Strategy:**
- ✅ **Preserve Historical Data:** Keep all M5 data (2015-2024) and existing synthetic data
- ✅ **Fill Recent Gap:** Generate synthetic data from TODAY backwards (last 30-365 days)
- ✅ **Pattern-Based:** Use historical averages from M5/synthetic data to maintain realism
- ✅ **No Data Loss:** Only fills missing dates, never overwrites existing data

**Benefits:**
- All metrics calculated relative to current date
- DIR calculations work immediately
- Status classifications accurate
- Recommendations generate properly
- Historical data preserved for forecasting

### 3.2 Sales Data Generation Strategy

#### Pattern 1: Normal Products (70% of SKUs)
- **Daily Sales:** 10-50 units/day (randomized with weekly patterns)
- **Weekend Effect:** -30% on weekends
- **Promotions:** 1-2 per month, +50% sales during promotion
- **Seasonality:** None (for simplicity)
- **Trend:** Stable with minor random variation

#### Pattern 2: High-Volume Products (20% of SKUs)
- **Daily Sales:** 50-200 units/day
- **Weekend Effect:** -20% on weekends
- **Promotions:** 2-3 per month, +75% sales
- **Trend:** Slight upward trend

#### Pattern 3: Low-Volume Products (10% of SKUs)
- **Daily Sales:** 1-10 units/day
- **Weekend Effect:** -40% on weekends
- **Promotions:** 0-1 per month, +100% sales
- **Trend:** Stable, occasional spikes

#### Pattern 4: Dead Stock Candidates (5% of SKUs)
- **Daily Sales:** 0 units for last 60+ days
- **Purpose:** Test dead stock detection
- **Stock:** High stock levels (overstocked)

### 3.3 Stock Data Generation Strategy

**Current Stock Calculation:**
```
For each SKU:
  - Calculate average daily sales (last 30 days)
  - Calculate target DIR (based on lead_time + safety_buffer)
  - Set current_stock = avg_daily_sales * target_DIR * random_factor(0.8-1.2)
  - Distribute across locations (60% main warehouse, 30% secondary, 10% store)
```

**Stock History (`stock_on_date` in `ts_demand_daily`):**
```
For each date (backwards from today):
  - Start with current_stock
  - Subtract units_sold for that day
  - Add any restocking (simulate weekly restocking)
  - Store as stock_on_date
```

### 3.4 Supplier Data Generation Strategy

**For Each Product:**
- **Primary Supplier:** 1 supplier (is_primary = true)
  - Lead time: 7-14 days
  - MOQ: 50-200 units
  - Supplier cost: unit_cost * 0.7-0.9
  
- **Secondary Supplier:** 0-1 additional suppliers (is_primary = false)
  - Lead time: 14-21 days
  - MOQ: 100-500 units
  - Supplier cost: unit_cost * 0.8-1.0

---

## 4. Implementation Plan

### Phase 1: Handle 'No Data' Cases First ✅

**Priority:** CRITICAL

**Status:** ✅ **IMPLEMENTED**

**Implementation:** `backend/scripts/generate_recent_sales_data.py`

**Features:**
1. ✅ Generates synthetic sales data from TODAY backwards
2. ✅ Preserves all historical data (M5 2015-2024, synthetic 2024)
3. ✅ Only fills missing dates (never overwrites existing data)
4. ✅ Uses historical averages to maintain realistic patterns
5. ✅ Classifies products by pattern (normal, high-volume, low-volume, dead-stock)
6. ✅ Applies weekend/holiday/promotion effects

**Usage:**
```bash
# Generate last 30 days (minimum for DIR)
uv run python backend/scripts/generate_recent_sales_data.py \
    --client-id <uuid> \
    --days-back 30

# Generate last 365 days (for full forecasting)
uv run python backend/scripts/generate_recent_sales_data.py \
    --client-id <uuid> \
    --days-back 365

# Clear existing recent data first (if needed)
uv run python backend/scripts/generate_recent_sales_data.py \
    --client-id <uuid> \
    --days-back 30 \
    --clear-existing
```

**Integration:** Automatically called by `setup_test_data.py` (Step 9)

### Phase 2: Normalize All SKUs with Unified Reference Date ✅

**Status:** ✅ **IMPLEMENTED**

**Tasks Completed:**
1. ✅ Updated `setup_test_data.py` to generate recent sales data (Step 9)
2. ✅ All SKUs use same reference date (today)
3. ⚠️ Stock history (`stock_on_date`) - Optional, can be added later
4. ⚠️ Validation - Test after running setup

**How It Works:**
- When you run `setup_test_data.py`, it automatically:
  1. Creates products, locations, suppliers, stock levels
  2. Generates recent sales data from TODAY backwards (last 30 days by default)
  3. Preserves all existing historical data (M5, synthetic)
  4. Only fills missing dates

**Example:**
```bash
# Setup test data (includes recent sales generation)
uv run python backend/scripts/setup_test_data.py \
    --client-id <uuid> \
    --days-back 30

# Or skip recent sales if you want to generate separately
uv run python backend/scripts/setup_test_data.py \
    --client-id <uuid> \
    --skip-recent-sales
```

### Phase 3: Add UI Setting for Test Data Population

**Location:** Settings page (`/settings`)

**UI Component:**
```vue
<UCard>
  <template #header>
    <h3>Test Data Management</h3>
  </template>
  
  <div class="space-y-4">
    <UAlert
      color="yellow"
      variant="soft"
      title="Development Only"
      description="This feature is for development and testing purposes only."
    />
    
    <div>
      <h4 class="font-semibold mb-2">Populate Test Data</h4>
      <p class="text-sm text-gray-600 mb-4">
        Generate synthetic sales and stock data for the last 30-365 days.
        This will enable full testing of inventory metrics, recommendations, and forecasting.
      </p>
      
      <div class="space-y-3">
        <UInput
          v-model="daysBack"
          type="number"
          label="Days of History"
          :min="30"
          :max="365"
          help="Generate sales data for this many days (30-365)"
        />
        
        <UCheckbox
          v-model="includeStockHistory"
          label="Include Stock History"
          help="Generate stock_on_date for each day (slower but more complete)"
        />
        
        <UCheckbox
          v-model="clearExisting"
          label="Clear Existing Test Data"
          help="Remove existing test data before generating new data"
        />
        
        <UButton
          @click="populateTestData"
          :loading="loading"
          color="primary"
        >
          Generate Test Data
        </UButton>
      </div>
    </div>
    
    <div v-if="lastGenerated" class="text-sm text-gray-500">
      Last generated: {{ lastGenerated }}
    </div>
  </div>
</UCard>
```

**Backend API Endpoint:**
```python
@router.post("/settings/populate-test-data")
async def populate_test_data(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    days_back: int = Query(30, ge=30, le=365),
    include_stock_history: bool = Query(False),
    clear_existing: bool = Query(False)
):
    """
    Generate synthetic test data for current client.
    
    Development/testing only - not for production use.
    """
    # Generate sales data
    # Generate stock history (if requested)
    # Return summary
```

### Phase 4: Define Auto-Generated Fields

**Complete Field List:**

#### Sales Data (`ts_demand_daily`)
| Field | Auto-Generated? | Generation Logic |
|-------|-----------------|------------------|
| `item_id` | ✅ Yes | From existing products |
| `date_local` | ✅ Yes | From reference_date backwards |
| `units_sold` | ✅ Yes | Based on product pattern (see 3.2) |
| `client_id` | ✅ Yes | From current client |
| `promotion_flag` | ✅ Yes | Random 1-2 per month per SKU |
| `holiday_flag` | ✅ Yes | Based on calendar holidays |
| `is_weekend` | ✅ Yes | Calculated from date |
| `marketing_spend` | ✅ Yes | Random 0-100 EUR, higher during promotions |
| `stock_on_date` | ⚠️ Optional | Calculated backwards from current_stock |

#### Stock Levels (`stock_levels`)
| Field | Auto-Generated? | Generation Logic |
|-------|-----------------|------------------|
| `item_id` | ✅ Yes | From existing products |
| `location_id` | ✅ Yes | Distribute across locations |
| `current_stock` | ✅ Yes | Based on target DIR calculation |
| `client_id` | ✅ Yes | From current client |

#### Product-Supplier Conditions
| Field | Auto-Generated? | Generation Logic |
|-------|-----------------|------------------|
| `item_id` | ✅ Yes | From existing products |
| `supplier_id` | ✅ Yes | Assign 1-2 suppliers per product |
| `moq` | ✅ Yes | Random 50-500 based on product type |
| `lead_time_days` | ✅ Yes | Random 7-21 days |
| `supplier_cost` | ✅ Yes | unit_cost * 0.7-1.0 |
| `packaging_unit` | ✅ Yes | "box", "pallet", "case" |
| `packaging_qty` | ✅ Yes | Random 12, 24, 48, 96 |
| `is_primary` | ✅ Yes | First supplier = primary |

---

## 5. Detailed Implementation

### 5.1 Sales Data Generation Function

```python
async def generate_synthetic_sales_data(
    client_id: UUID,
    item_ids: List[str],
    days_back: int = 30,
    reference_date: date = None
) -> int:
    """
    Generate synthetic sales data for all products.
    
    Strategy:
    - 70% normal products: 10-50 units/day
    - 20% high-volume: 50-200 units/day
    - 10% low-volume: 1-10 units/day
    - 5% dead stock: 0 units for 60+ days
    """
    if reference_date is None:
        reference_date = date.today()
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        records_created = 0
        
        # Classify products by volume pattern
        normal_products = item_ids[:int(len(item_ids) * 0.70)]
        high_volume = item_ids[int(len(item_ids) * 0.70):int(len(item_ids) * 0.90)]
        low_volume = item_ids[int(len(item_ids) * 0.90):int(len(item_ids) * 0.95)]
        dead_stock = item_ids[int(len(item_ids) * 0.95):]
        
        # Generate data for each product
        for item_id in item_ids:
            pattern = "normal"
            if item_id in high_volume:
                pattern = "high_volume"
            elif item_id in low_volume:
                pattern = "low_volume"
            elif item_id in dead_stock:
                pattern = "dead_stock"
            
            # Generate daily sales
            for day_offset in range(days_back):
                sale_date = reference_date - timedelta(days=day_offset)
                
                # Skip if data already exists
                existing = await session.execute(
                    text("""
                        SELECT 1 FROM ts_demand_daily
                        WHERE client_id = :client_id
                          AND item_id = :item_id
                          AND date_local = :date_local
                    """),
                    {
                        "client_id": str(client_id),
                        "item_id": item_id,
                        "date_local": sale_date
                    }
                )
                if existing.fetchone():
                    continue
                
                # Calculate units_sold based on pattern
                units_sold = calculate_daily_sales(
                    item_id, sale_date, pattern, day_offset
                )
                
                # Determine flags
                is_weekend = sale_date.weekday() >= 5
                is_holiday = is_holiday_date(sale_date)
                is_promotion = is_promotion_date(item_id, sale_date, days_back)
                marketing_spend = calculate_marketing_spend(is_promotion)
                
                # Insert record
                await session.execute(
                    text("""
                        INSERT INTO ts_demand_daily
                        (item_id, date_local, units_sold, client_id,
                         promotion_flag, holiday_flag, is_weekend, marketing_spend)
                        VALUES (:item_id, :date_local, :units_sold, :client_id,
                                :promo_flag, :holiday_flag, :is_weekend, :marketing_spend)
                        ON CONFLICT (item_id, date_local, client_id) DO NOTHING
                    """),
                    {
                        "item_id": item_id,
                        "date_local": sale_date,
                        "units_sold": float(units_sold),
                        "client_id": str(client_id),
                        "promo_flag": is_promotion,
                        "holiday_flag": is_holiday,
                        "is_weekend": is_weekend,
                        "marketing_spend": float(marketing_spend)
                    }
                )
                records_created += 1
        
        await session.commit()
        return records_created


def calculate_daily_sales(
    item_id: str,
    sale_date: date,
    pattern: str,
    day_offset: int
) -> Decimal:
    """Calculate units sold for a specific day based on pattern."""
    import random
    import math
    
    base_seed = hash(f"{item_id}{sale_date}") % 1000
    random.seed(base_seed)
    
    if pattern == "dead_stock":
        # No sales for last 60+ days
        return Decimal("0.00") if day_offset < 60 else Decimal(str(random.randint(0, 5)))
    
    # Base daily sales by pattern
    if pattern == "high_volume":
        base = random.randint(50, 200)
    elif pattern == "low_volume":
        base = random.randint(1, 10)
    else:  # normal
        base = random.randint(10, 50)
    
    # Weekend effect
    if sale_date.weekday() >= 5:
        base = int(base * 0.7)  # -30% on weekends
    
    # Promotion effect
    if is_promotion_date(item_id, sale_date, 365):
        base = int(base * 1.5)  # +50% during promotions
    
    # Holiday effect
    if is_holiday_date(sale_date):
        base = int(base * 1.2)  # +20% on holidays
    
    # Weekly pattern (higher mid-week)
    day_of_week = sale_date.weekday()
    if day_of_week in [1, 2, 3]:  # Tue, Wed, Thu
        base = int(base * 1.1)
    elif day_of_week == 0:  # Monday
        base = int(base * 0.9)
    
    # Add small random variation
    variation = random.randint(-5, 5)
    units = max(0, base + variation)
    
    return Decimal(str(units))
```

### 5.2 Stock History Generation Function

```python
async def generate_stock_history(
    client_id: UUID,
    item_ids: List[str],
    days_back: int = 30,
    reference_date: date = None
) -> int:
    """
    Generate stock_on_date for each day, working backwards from current stock.
    """
    if reference_date is None:
        reference_date = date.today()
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        records_updated = 0
        
        for item_id in item_ids:
            # Get current stock (sum across all locations)
            stock_result = await session.execute(
                text("""
                    SELECT SUM(current_stock) as total_stock
                    FROM stock_levels
                    WHERE client_id = :client_id AND item_id = :item_id
                """),
                {"client_id": str(client_id), "item_id": item_id}
            )
            current_stock = stock_result.scalar() or 0
            
            # Get sales data for this period
            sales_result = await session.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                    ORDER BY date_local DESC
                """),
                {
                    "client_id": str(client_id),
                    "item_id": item_id,
                    "start_date": reference_date - timedelta(days=days_back),
                    "end_date": reference_date
                }
            )
            sales_data = {row.date_local: float(row.units_sold) for row in sales_result}
            
            # Calculate stock backwards from today
            stock = current_stock
            for day_offset in range(days_back):
                sale_date = reference_date - timedelta(days=day_offset)
                units_sold = sales_data.get(sale_date, 0)
                
                # Stock at end of day = stock at start - units_sold + restocking
                # (For simplicity, assume restocking happens weekly)
                if day_offset % 7 == 0 and day_offset > 0:
                    # Weekly restocking: add average weekly sales
                    weekly_sales = sum(
                        sales_data.get(reference_date - timedelta(days=i), 0)
                        for i in range(day_offset, min(day_offset + 7, days_back))
                    )
                    stock += int(weekly_sales * 1.2)  # Restock 120% of weekly sales
                
                stock = max(0, stock + units_sold)  # Add back units_sold (working backwards)
                
                # Update stock_on_date
                await session.execute(
                    text("""
                        UPDATE ts_demand_daily
                        SET stock_on_date = :stock
                        WHERE client_id = :client_id
                          AND item_id = :item_id
                          AND date_local = :date_local
                    """),
                    {
                        "client_id": str(client_id),
                        "item_id": item_id,
                        "date_local": sale_date,
                        "stock": int(stock)
                    }
                )
                records_updated += 1
        
        await session.commit()
        return records_updated
```

---

## 6. Testing Checklist

### After Implementation, Verify:

- [ ] All products have sales data for last 30 days
- [ ] DIR calculates correctly (not 0)
- [ ] Status shows "understocked", "normal", or "overstocked" (not "unknown")
- [ ] Stockout risk calculates (0-100%)
- [ ] Recommendations generate properly
- [ ] Dashboard KPIs show correct values
- [ ] Inventory page shows all metrics
- [ ] Stock history visible (if `include_stock_history = true`)
- [ ] No "no data" errors in UI
- [ ] All SKUs have unified reference date (today)

---

## 7. UI Setting Implementation

### 7.1 Settings Page Component

**File:** `frontend/app/pages/settings/index.vue`

Add new section:
```vue
<template>
  <div class="space-y-6">
    <!-- Existing settings sections -->
    
    <!-- Test Data Management (Development Only) -->
    <UCard v-if="isDevelopment">
      <template #header>
        <h3 class="text-lg font-semibold">Test Data Management</h3>
      </template>
      
      <TestDataPopulator />
    </UCard>
  </div>
</template>
```

### 7.2 Test Data Populator Component

**File:** `frontend/app/components/TestDataPopulator.vue`

```vue
<script setup lang="ts">
const daysBack = ref(30)
const includeStockHistory = ref(false)
const clearExisting = ref(false)
const loading = ref(false)
const lastGenerated = ref<string | null>(null)

const populateTestData = async () => {
  loading.value = true
  try {
    const response = await $fetch('/api/settings/populate-test-data', {
      method: 'POST',
      body: {
        days_back: daysBack.value,
        include_stock_history: includeStockHistory.value,
        clear_existing: clearExisting.value
      }
    })
    
    lastGenerated.value = new Date().toLocaleString()
    // Show success notification
  } catch (error) {
    // Show error notification
  } finally {
    loading.value = false
  }
}
</script>
```

### 7.3 Backend API Endpoint

**File:** `backend/api/settings.py`

```python
@router.post("/settings/populate-test-data")
async def populate_test_data(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    days_back: int = Query(30, ge=30, le=365),
    include_stock_history: bool = Query(False),
    clear_existing: bool = Query(False)
):
    """
    Generate synthetic test data.
    
    Development/testing only.
    """
    from scripts.setup_test_data import (
        generate_synthetic_sales_data,
        generate_stock_history
    )
    
    # Get all product item_ids
    products_result = await db.execute(
        select(Product.item_id).where(Product.client_id == client.client_id)
    )
    item_ids = [row[0] for row in products_result.fetchall()]
    
    if not item_ids:
        raise HTTPException(400, "No products found. Create products first.")
    
    # Clear existing if requested
    if clear_existing:
        await db.execute(
            text("""
                DELETE FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND date_local >= :start_date
            """),
            {
                "client_id": str(client.client_id),
                "start_date": date.today() - timedelta(days=days_back)
            }
        )
        await db.commit()
    
    # Generate sales data
    sales_count = await generate_synthetic_sales_data(
        client.client_id, item_ids, days_back
    )
    
    # Generate stock history if requested
    stock_count = 0
    if include_stock_history:
        stock_count = await generate_stock_history(
            client.client_id, item_ids, days_back
        )
    
    return {
        "sales_records_created": sales_count,
        "stock_records_updated": stock_count,
        "days_back": days_back,
        "products": len(item_ids)
    }
```

---

## 8. Summary

### Key Decisions
1. ✅ **Reference Date:** Use `today` for all calculations
2. ✅ **Minimum Data:** 30 days of sales history (required for DIR)
3. ✅ **Recommended Data:** 90 days (for trends), 365 days (for forecasting)
4. ✅ **Stock History:** Optional (slower but more complete)
5. ✅ **UI Setting:** Add to Settings page (development mode only)

### Auto-Generated Fields
- ✅ Sales data (`ts_demand_daily`) - All fields
- ✅ Stock history (`stock_on_date`) - Optional
- ✅ Product patterns - 4 types (normal, high-volume, low-volume, dead-stock)
- ✅ Promotions - 1-2 per month per SKU
- ✅ Marketing spend - Correlated with promotions

### Next Steps
1. Implement `generate_synthetic_sales_data()` function
2. Implement `generate_stock_history()` function
3. Update `setup_test_data.py` to call these functions
4. Add UI setting component
5. Add backend API endpoint
6. Test and validate all metrics calculate correctly

---

**Status:** 📋 **PLAN COMPLETE** - Ready for implementation
