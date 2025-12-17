# Purchase Order Improvements - Feature Plan

**Last Updated:** 2025-01-27  
**Status:** Planning Phase  
**Scope:** Purchase Order UI/UX improvements and enhancements

---

## Executive Summary

This document outlines improvements for the Purchase Order system, focusing on UI/UX enhancements, expected delivery date calculations, cart improvements, and order management features. The backend APIs are already implemented (see [Backend Roadmap](backend/BACKEND_ROADMAP.md)), so this focuses on frontend improvements.

**Current State:**
- ✅ Backend APIs complete (Order Planning, Cart, Purchase Orders)
- ✅ Cart already grouped by supplier in API response
- ✅ PO creation from cart (removes items automatically)
- ✅ PO status tracking (5 statuses: pending, confirmed, shipped, received, cancelled)
- ✅ PO filtering (by status, supplier, pagination)
- ✅ Full PO detail with all items
- ✅ Order suggestions API with `lead_time_days`, `suggested_quantity`, `priority`
- ⚠️ **Recommendations page deprecated** → Functionality moves here (Order Suggestions in Cart)
- ❌ No frontend PO list page
- ❌ No cart page/UI
- ❌ No expected delivery date display (backend has field, but not auto-calculated)
- ❌ Cart response missing `lead_time_days` (needed for delivery date calculation)

---

## Existing Documentation

### Backend (Complete):
- [Backend Roadmap](backend/BACKEND_ROADMAP.md) - Order Planning & Purchase Orders API (Section 3.1-3.2)
- [API Reference](backend/API_REFERENCE.md) - Complete API endpoint documentation
- [User Stories](USER_STORIES.md) - US-PROC-005, US-PROC-006 (Purchase Order requirements)
- [Workflows](WORKFLOWS.md) - Order planning and PO creation workflows

### Frontend (Needs Work):
- [Frontend Roadmap](frontend/FRONTEND_ROADMAP.md) - Mentions "Order Planning Cart page" and "Purchase Orders list" as Post-MVP (Future Enhancements)

**Gap:** No detailed frontend UI/UX plan for Purchase Orders

---

## Feature Categories

### 1. Expected Delivery Date Calculation
**Goal:** Show "if I order today, when will it arrive?"

**Features:**
- [ ] **Calculate Expected Delivery:**
  - Formula: `Expected Delivery Date = Today + Lead Time Days`
  - Show in cart: "Order today → Arrives: Dec 31, 2024"
  - Show in PO creation: "Expected delivery: Dec 31, 2024"
  - Update dynamically if order date changes

- [ ] **Display in Cart:**
  - Show expected delivery date per item
  - Group by supplier (same supplier = same delivery date)
  - Show earliest/latest delivery for mixed suppliers
  - Format: "Order today (Nov 21) → Arrives: Dec 31, 2024"

- [ ] **Display in PO Creation:**
  - Show expected delivery date prominently
  - Allow manual override if needed
  - Show lead time breakdown (e.g., "40 days lead time")

- [ ] **Display in Inventory (Contextual):**
  - Tooltip or info icon showing "If ordering today: Arrives Dec 31"
  - Not as primary column (keep in PO flow)

**UI Design:**
```
Cart Item:
  Product: SKU-001
  Quantity: 50
  Lead Time: 40 days
  Expected Delivery: Order today (Nov 21) → Arrives: Dec 31, 2024
```

**Implementation:**
- Add `expected_delivery_date` calculation in cart service
- Display in cart component
- Include in PO creation form
- Backend already has `expected_delivery_date` field in PO model

---

### 2. Order Planning Cart Page
**Goal:** Dedicated cart page for reviewing items before creating PO

**Features:**
- [ ] **Cart Page Layout:**
  - List of items in cart
  - Grouped by supplier (default view)
  - Show supplier name, contact info
  - Show total cost per supplier
  - Show expected delivery date per supplier group

- [ ] **Cart Item Display:**
  - Product name, SKU
  - Quantity (editable)
  - Unit cost, total cost
  - MOQ validation (highlight if below MOQ)
  - Lead time and expected delivery date
  - Remove item button

- [ ] **Cart Actions:**
  - "Create PO" button per supplier group
  - "Create All POs" button (creates one PO per supplier)
  - "Clear Cart" button
  - "Continue Shopping" link back to inventory/recommendations

- [ ] **Cart Summary:**
  - Total items in cart
  - Total value across all suppliers
  - Number of suppliers
  - Estimated delivery dates range

**UI Design:**
```
Order Planning Cart

[Supplier 1 - ABC Suppliers]
  - SKU-001: 50 units @ €10 = €500 | Lead: 40d → Arrives: Dec 31
  - SKU-002: 30 units @ €15 = €450 | Lead: 40d → Arrives: Dec 31
  Subtotal: €950
  [Create PO for Supplier 1]

[Supplier 2 - XYZ Corp]
  - SKU-003: 20 units @ €20 = €400 | Lead: 14d → Arrives: Dec 5
  Subtotal: €400
  [Create PO for Supplier 2]

Total: €1,350 | 3 items | 2 suppliers
[Create All POs] [Clear Cart]
```

**Implementation:**
- Create `app/pages/order-planning/cart.vue`
- Use `GET /api/v1/order-planning/cart` to fetch items
- **Backend already groups by supplier!** (`suppliers[]` in response)
- Calculate expected delivery dates client-side (or add to API)
  - Formula: `Today + lead_time_days` (need to fetch `lead_time_days` from supplier/product)
- Create PO via `POST /api/v1/purchase-orders/from-cart`
  - Backend already removes items from cart after creating PO ✅

---

### 3. Purchase Orders List Page
**Goal:** View and manage all purchase orders

**Features:**
- [ ] **PO List Table (AG Grid):**
  - Columns:
    - PO Number
    - Supplier
    - Status (badge with color coding)
    - Order Date
    - Expected Delivery Date
    - Total Amount
    - Items Count
    - Created By
    - Actions (View, Edit Status, Cancel)

- [ ] **Status Filtering:**
  - Tabs: All, Pending, Confirmed, Shipped, Received, Cancelled
  - Count badges on each tab
  - Quick filter buttons

- [ ] **Search & Filter:**
  - Search by PO number, supplier name
  - Filter by supplier
  - Filter by date range
  - Filter by status

- [ ] **Status Badges:**
  - 🟡 Pending
  - 🔵 Confirmed
  - 🟠 Shipped
  - 🟢 Received
  - 🔴 Cancelled

**UI Design:**
```
Purchase Orders

[All (25)] [Pending (10)] [Confirmed (8)] [Shipped (5)] [Received (2)]

PO Number    Supplier      Status    Order Date    Expected Delivery    Total      Actions
PO-2025-001  ABC Suppliers  🟡 Pending  Nov 21      Dec 31, 2024        €950      [View] [Edit]
PO-2025-002  XYZ Corp       🔵 Confirmed Nov 20     Dec 5, 2024         €400      [View] [Edit]
```

**Implementation:**
- Create `app/pages/purchase-orders/index.vue`
- Use `GET /api/v1/purchase-orders?status=pending&supplier_id=uuid&page=1`
  - **Backend already supports:** `status`, `supplier_id`, `page`, `page_size` filters ✅
- AG Grid for table
- Status update via `PUT /api/v1/purchase-orders/{id}/status`
  - Valid statuses: `pending`, `confirmed`, `shipped`, `received`, `cancelled` ✅

---

### 4. Purchase Order Detail Page
**Goal:** View full PO details and manage status

**Features:**
- [ ] **PO Header:**
  - PO Number, Status, Order Date
  - Supplier information (name, contact)
  - Expected Delivery Date (prominent)
  - Total Amount
  - Created By, Created At

- [ ] **PO Items Table:**
  - Item ID, Product Name
  - Quantity, Unit Cost, Total Cost
  - Packaging info (if applicable)
  - MOQ, Lead Time

- [ ] **Status Management:**
  - Status dropdown/buttons
  - Update status workflow
  - Status history timeline
  - Notes/comments section

- [ ] **Actions:**
  - Edit status
  - Cancel order
  - Print/Export PO
  - Duplicate PO (create new from existing)

**UI Design:**
```
Purchase Order: PO-2025-001

Supplier: ABC Suppliers
Status: 🟡 Pending
Order Date: Nov 21, 2024
Expected Delivery: Dec 31, 2024 (40 days)
Total: €950.00

Items:
  SKU-001: 50 units @ €10.00 = €500.00
  SKU-002: 30 units @ €15.00 = €450.00

[Update Status] [Cancel Order] [Print] [Export]
```

**Implementation:**
- Create `app/pages/purchase-orders/[id].vue`
- Use `GET /api/v1/purchase-orders/{id}` for details
- Status update via `PUT /api/v1/purchase-orders/{id}/status`

---

### 5. Order Suggestions in Cart (Replaces Recommendations Page)
**Goal:** Show smart order suggestions directly in the Cart page

**Background:**
The separate Recommendations page is being **deprecated**. Its functionality is split between:
- **Inventory "Needs Action" tab** → Shows products needing attention (status-based filtering)
- **Cart Order Suggestions** → Shows suggested quantities, priorities, reasons (this section)

**Existing Backend API:**
```
GET /api/v1/order-planning/suggestions
```
Returns:
- `item_id`, `product_name`, `current_stock`
- `avg_daily_demand`, `days_of_inventory_remaining`
- `stockout_risk`, `status`
- `suggested_quantity`, `priority` (high/medium/low)
- `supplier_id`, `supplier_name`, `lead_time_days`

**Features:**
- [ ] **Suggestions Panel in Cart Page:**
  - "Suggested Items" section above/beside cart
  - Shows products that need ordering (not yet in cart)
  - Priority-sorted (urgent first)
  - Click to add to cart with suggested quantity

- [ ] **Suggestion Cards (Compact):**
  - Product name, SKU
  - Priority badge (🔴 Urgent, 🟠 Reorder, 🟢 Low)
  - Suggested quantity
  - Stockout risk indicator
  - "Add to Cart" button

- [ ] **Quick Actions:**
  - "Add All Urgent" — Add all high-priority items
  - "Add Suggested" — Add top N suggestions
  - Dismiss suggestion (per item)

- [ ] **Empty Cart State:**
  - Show suggestions prominently when cart is empty
  - "Start by adding these suggested items"

**UI Design:**
```
Order Planning Cart

┌─ Suggested Items (5 urgent) ────────────────────────┐
│ 🔴 SKU-001 Widget Pro | Stock: 5 | Risk: 85%        │
│    Suggested: 100 units | [Add to Cart]             │
│                                                     │
│ 🔴 SKU-002 Gadget X   | Stock: 12 | Risk: 72%       │
│    Suggested: 75 units  | [Add to Cart]             │
│                                                     │
│ [Add All Urgent (2)]  [View More...]                │
└─────────────────────────────────────────────────────┘

┌─ Your Cart ─────────────────────────────────────────┐
│ [Supplier 1 - ABC Suppliers]                        │
│   SKU-003: 50 units @ €10 = €500                    │
│   ...                                               │
└─────────────────────────────────────────────────────┘
```

**Implementation:**
- Add to `app/pages/order-planning/cart.vue`
- Use `GET /api/v1/order-planning/suggestions` for suggestions
- Filter out items already in cart
- Show in collapsible/expandable panel

---

### 6. Cart Integration Improvements
**Goal:** Better cart experience across the app

**Features:**
- [ ] **Cart Badge in Header:**
  - Show total items in cart (e.g., green badge "3")
  - Click to navigate to cart page
  - Update in real-time

- [ ] **Add to Cart from Inventory:**
  - "Add to Cart" button per product
  - Show cart indicator if already in cart
  - Bulk add to cart (selected products)

- [ ] **Cart Notification:**
  - Toast notification when item added
  - "X items added to cart"
  - Link to view cart

**Implementation:**
- Enhance existing cart integration
- Add cart badge component to header
- Add to cart handlers in inventory page

---

### 7. PO Creation Flow Enhancements
**Goal:** Streamline PO creation process

**Features:**
- [ ] **PO Creation Modal/Form:**
  - Select supplier (if multiple in cart)
  - Review items (editable quantities)
  - Set expected delivery date (auto-calculated, editable)
  - Add notes
  - Review total cost
  - Create PO button

- [ ] **Validation:**
  - Check quantities >= MOQ
  - Validate supplier exists
  - Check stock levels
  - Show warnings for low stock items

- [ ] **Confirmation:**
  - Success message with PO number
  - Link to view created PO
  - Option to create another PO

**Implementation:**
- Enhance `POST /api/v1/purchase-orders/from-cart` flow
- Add validation in frontend
- Better error handling

---

### 8. Expected Delivery Date Features
**Goal:** Advanced delivery date management

**Features:**
- [ ] **Delivery Date Calculation:**
  - Base: `Today + Lead Time`
  - Account for weekends/holidays (optional)
  - Account for supplier business days
  - Show delivery date range (min/max)

- [ ] **Delivery Date Display:**
  - In cart: "Arrives: Dec 31, 2024"
  - In PO: "Expected Delivery: Dec 31, 2024"
  - In PO list: Show delivery date column
  - Color-code by urgency (past due = red)

- [ ] **Delivery Tracking:**
  - Update actual delivery date when received
  - Compare expected vs actual
  - Show delivery performance metrics

**Implementation:**
- Add delivery date calculation utility
- Display in multiple places
- Backend already supports `expected_delivery_date` field

---

## Implementation Phases

### Phase 1: Cart & Order Suggestions (Week 1)
**Priority: High**

**Tasks:**
- [ ] Create cart page (`app/pages/order-planning/cart.vue`)
- [ ] Add Order Suggestions panel (replaces Recommendations page)
  - Use `GET /api/v1/order-planning/suggestions`
  - Show suggested items not yet in cart
  - "Add to Cart" action per suggestion
- [ ] Add expected delivery date calculation
- [ ] Display expected delivery in cart
- [ ] Add cart badge to header
- [ ] Last sync indicator in header

**Deliverables:**
- Cart page functional with Order Suggestions
- Expected delivery dates shown
- Cart badge working
- **Recommendations page can be removed**

---

### Phase 2: Purchase Orders List (Week 2)
**Priority: High**

**Tasks:**
- [ ] Create PO list page (`app/pages/purchase-orders/index.vue`)
- [ ] Implement AG Grid table
- [ ] Add status filtering tabs
- [ ] Add search and filters
- [ ] Status badges and color coding

**Deliverables:**
- PO list page functional
- Filtering and search working

---

### Phase 3: PO Detail & Status Management (Week 3)
**Priority: Medium**

**Tasks:**
- [ ] Create PO detail page (`app/pages/purchase-orders/[id].vue`)
- [ ] Implement status update workflow
- [ ] Add status history display
- [ ] Add print/export functionality

**Deliverables:**
- PO detail page functional
- Status management working

---

### Phase 4: Advanced Features (Week 4)
**Priority: Medium**

**Tasks:**
- [ ] Delivery date enhancements (weekends, holidays)
- [ ] Delivery tracking and metrics
- [ ] PO duplication
- [ ] Bulk status updates
- [ ] Export PO list

**Deliverables:**
- Advanced features functional

---

## Technical Implementation

### Frontend Components

**New Components:**
- `OrderPlanningCart.vue` - Cart page
- `CartItem.vue` - Cart item component
- `ExpectedDeliveryDate.vue` - Delivery date display
- `PurchaseOrderList.vue` - PO list page
- `PurchaseOrderDetail.vue` - PO detail page
- `POStatusBadge.vue` - Status badge component
- `POStatusUpdate.vue` - Status update modal

**Modified Components:**
- `Header.vue` - Add cart badge
- `InventoryPage.vue` - Enhance add to cart
- `RecommendationsPage.vue` - Enhance add to cart (already done)

### Backend API Status

**Already Implemented — Cart:**
- ✅ `GET /api/v1/order-planning/cart` — Returns:
  - Items with `product_name`, `supplier_name`, `moq`, `unit_cost`, `total_price`
  - **Already grouped by supplier** (`suppliers[]` array)
  - `total_items`, `total_value`
- ✅ `POST /api/v1/order-planning/cart/add` — Add item with validation (MOQ check)
- ✅ `PUT /api/v1/order-planning/cart/{item_id}` — Update quantity (validates MOQ)
- ✅ `DELETE /api/v1/order-planning/cart/{item_id}` — Remove item
- ✅ `POST /api/v1/order-planning/cart/clear` — Clear entire cart

**Already Implemented — Purchase Orders:**
- ✅ `POST /api/v1/purchase-orders` — Create PO (accepts `expected_delivery_date` in request)
- ✅ `POST /api/v1/purchase-orders/from-cart` — Create PO from cart (removes items from cart)
- ✅ `GET /api/v1/purchase-orders` — List POs with:
  - Filtering: `?status=pending&supplier_id=uuid`
  - Pagination: `?page=1&page_size=50`
  - Returns: `po_number`, `supplier_name`, `status`, `order_date`, `expected_delivery_date`, `total_amount`
- ✅ `GET /api/v1/purchase-orders/{id}` — Full PO details:
  - All items with `product_name`, `quantity`, `unit_cost`, `total_price`
  - Supplier info, shipping, notes, `created_by`
- ✅ `PUT /api/v1/purchase-orders/{id}/status` — Update status (pending, confirmed, shipped, received, cancelled)

**Already Implemented — Order Suggestions:**
- ✅ `GET /api/v1/order-planning/suggestions` — Returns:
  - `lead_time_days` (for each suggestion!)
  - `suggested_quantity`, `stockout_risk`, `reason`
  - `supplier_id`, `supplier_name`, `moq`, `unit_cost`, `total_cost`

**What's Missing (Needs Implementation):**
- [ ] `GET /api/v1/order-planning/cart` — Add `lead_time_days` to cart response
  - Currently cart has `moq` but not `lead_time_days`
  - Need to fetch from `ProductSupplierCondition` or `Supplier`
- [ ] `GET /api/v1/order-planning/cart` — Add `expected_delivery_date` (calculated: `Today + lead_time_days`)
- [ ] `POST /api/v1/purchase-orders/from-cart` — Auto-calculate `expected_delivery_date` if not provided
  - Currently accepts `expected_delivery_date` but doesn't auto-calculate
  - Should calculate from max `lead_time_days` of items in cart

### Data Models

**Current Cart Response (Already Implemented):**
```typescript
interface CartItemResponse {
  id: UUID;
  session_id: string;
  item_id: string;
  supplier_id: UUID;
  quantity: number;
  unit_cost: Decimal;
  total_price: Decimal;
  packaging_unit?: string;
  packaging_qty?: number;
  notes?: string;
  product_name: string;      // ✅ Already included
  supplier_name: string;     // ✅ Already included
  moq: number;               // ✅ Already included
  created_at: datetime;
  updated_at: datetime;
}

interface CartResponse {
  items: CartItemResponse[];
  total_items: number;       // ✅ Already included
  total_value: Decimal;      // ✅ Already included
  suppliers: Array<{         // ✅ Already grouped by supplier!
    supplier_id: string;
    supplier_name: string;
    items: string[];         // Array of item_ids
  }>;
}
```

**Needs to be Added:**
```typescript
// Add to CartItemResponse:
lead_time_days: number;              // From ProductSupplierCondition
expected_delivery_date: string;      // Calculated: Today + lead_time_days
```

**Purchase Order Response (Already Complete):**
```typescript
interface PurchaseOrderResponse {
  id: UUID;
  po_number: string;                 // ✅ Auto-generated
  supplier_id: UUID;
  supplier_name: string;             // ✅ Already included
  status: string;                    // ✅ pending, confirmed, shipped, received, cancelled
  order_date: date;                  // ✅ Today's date
  expected_delivery_date?: date;     // ✅ Optional, can be set
  total_amount: Decimal;             // ✅ Calculated
  shipping_method?: string;
  shipping_unit?: string;
  notes?: string;
  created_by?: string;               // ✅ User email
  items: PurchaseOrderItemResponse[]; // ✅ Full item details
  created_at: datetime;
  updated_at: datetime;
}
```

---

## Success Metrics

### User Experience
- ✅ Users can see expected delivery date when adding to cart
- ✅ Users can review cart before creating PO
- ✅ Users can view and manage all POs
- ✅ Users can track PO status easily

### Performance
- ✅ Cart page loads < 1 second
- ✅ PO list loads < 2 seconds
- ✅ PO creation < 3 seconds

---

## Related Documentation

- [Backend Roadmap](backend/BACKEND_ROADMAP.md) - Order Planning & Purchase Orders API (Section 3.1-3.2)
- [API Reference](backend/API_REFERENCE.md) - Purchase Order endpoints
- [User Stories](USER_STORIES.md) - US-PROC-005, US-PROC-006
- [Workflows](WORKFLOWS.md) - Order planning workflows
- [Inventory Improvements](INVENTORY_IMPROVEMENTS.md) - Related inventory features

---

**Document Owner:** Development Team  
**Last Updated:** 2025-01-27  
**Status:** Planning Phase - Ready for implementation

