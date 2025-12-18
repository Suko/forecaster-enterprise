# Working Orders Feature - Complete Plan

**Last Updated:** 2025-12-17  
**Status:** Planning Phase  
**Scope:** Manufacturing/Production Order Management System

---

## Executive Summary

This document outlines the complete Working Orders (WO) feature, which enables manufacturing and production planning. The system connects **SKUs → BOM (Bill of Materials) → Raw Materials → WO Suppliers** to manage production orders, similar to how Purchase Orders work for procurement.

**Key Concepts:**
- **Working Orders (WO)**: Production/manufacturing orders (similar to Purchase Orders for procurement)
- **BOM (Bill of Materials)**: Recipe/ingredients list for finished products
- **Raw Materials**: Input materials/components needed for production
- **WO Suppliers**: Suppliers that perform manufacturing/production work (vs PO suppliers that sell materials)

---

## Current State

### What We Have:
- ✅ **Purchase Orders (PO)**: Complete system for procurement orders
- ✅ **Suppliers**: Model with `supplier_type` field (PO or WO)
- ✅ **Products**: Product master data with `item_id`
- ✅ **Product-Supplier Links**: `ProductSupplierCondition` for MOQ, lead time, etc.

### What We're Missing:
- ❌ **BOM Structure**: No bill of materials/recipe system
- ❌ **Raw Materials**: No separate raw materials catalogue
- ❌ **Working Orders**: No production order management
- ❌ **Production Operations**: No operation steps/workflow management
- ❌ **Product Variants**: No variant management (e.g., color, size)
- ❌ **WO Supplier Integration**: No connection between products and WO suppliers

---

## Feature Overview

### 1. Raw Materials Catalogue
**Goal:** Manage raw materials separately from finished products

**Features:**
- Raw materials catalogue (similar to products catalogue)
- Raw material SKU management
- Stock levels for raw materials (units available, units in transit)
- Lead time and MOQ for raw materials
- Supplier links for raw materials
- Days of Cover calculation for raw materials

**UI Reference:** Similar to "Catalogue" tab showing raw materials table with columns:
- Raw Material Product
- Raw Material SKU
- Units available
- Units in transit/order
- Lead Time
- MOQ Type
- MOQ
- Supplier
- Days of Cover

---

### 2. Bill of Materials (BOM) / Product Recipe
**Goal:** Define what raw materials/components are needed to produce a finished product

**Features:**
- BOM per product (or product variant)
- Ingredients/components list with quantities
- Stock cost calculation (sum of raw material costs)
- Variant-specific BOMs (e.g., different recipe for different colors)
- Copy BOM between variants
- Compare BOMs across variants
- Notes per ingredient

**UI Reference:** "Product recipe / BOM" tab showing:
- Active variant selector
- Ingredients table with: Item, Quantity, Notes, Stock cost
- "per 1 pcs of product" context
- Actions: Make, Copy to/from, Delete, Compare variants

**Database Structure:**
```sql
CREATE TABLE product_bom (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    product_id UUID NOT NULL REFERENCES products(id),  -- Finished product
    variant_id UUID REFERENCES product_variants(id),   -- Optional: variant-specific BOM
    
    -- BOM metadata
    bom_name VARCHAR(255),
    bom_version VARCHAR(50),  -- Version control
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, product_id, variant_id, bom_version)
);

CREATE TABLE product_bom_items (
    id UUID PRIMARY KEY,
    bom_id UUID NOT NULL REFERENCES product_bom(id) ON DELETE CASCADE,
    
    -- Raw material reference
    raw_material_id UUID NOT NULL REFERENCES raw_materials(id),
    item_id VARCHAR(255) NOT NULL,  -- Raw material item_id (for consistency)
    
    -- Quantity per unit of finished product
    quantity DECIMAL(10, 4) NOT NULL,  -- e.g., 5 meters, 1.5 liters
    unit VARCHAR(50) NOT NULL,  -- m, l, kg, pcs, etc.
    
    -- Cost tracking
    unit_cost DECIMAL(10, 2),  -- Cost per unit at time of BOM creation
    total_cost DECIMAL(12, 2),  -- quantity * unit_cost
    
    -- Optional
    notes TEXT,
    sequence INTEGER,  -- Order of operations (if sequence matters)
    
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(bom_id, raw_material_id)
);
```

---

### 3. Product Variants
**Goal:** Support product variants (e.g., different colors, sizes) with variant-specific BOMs

**Features:**
- Variant management (color, size, etc.)
- Variant-specific BOMs
- Variant-specific production operations
- Compare variants

**Database Structure:**
```sql
CREATE TABLE product_variants (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    product_id UUID NOT NULL REFERENCES products(id),
    
    variant_name VARCHAR(255) NOT NULL,  -- e.g., "brown", "large"
    variant_code VARCHAR(100),  -- e.g., "CT-BR" for Coffee Table Brown
    variant_attributes JSONB,  -- { "color": "brown", "size": "large" }
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, product_id, variant_code)
);
```

---

### 4. Production Operations
**Goal:** Define production workflow/operations for manufacturing

**Features:**
- Operation steps (e.g., Cutting, Gluing, Assembly, Packaging)
- Operation type (Process, Setup, Quality Check, etc.)
- Resource assignment (machine, person, workstation)
- Cost parameters (EUR/h, EUR/unit)
- Time duration per operation
- Sequence/ordering of operations
- Variant-specific operations (e.g., different operations for different colors)

**UI Reference:** "Production operations" tab showing:
- Operations table: Operation, Type, Resource, Cost parameter, Time, Product: Color, Cost
- "Operations are in sequence" toggle
- Drag-and-drop reordering
- Copy operations from other variants

**Database Structure:**
```sql
CREATE TABLE production_operations (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    product_id UUID NOT NULL REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),  -- Optional: variant-specific
    
    operation_name VARCHAR(255) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,  -- Process, Setup, Quality Check, etc.
    
    -- Resource
    resource_id UUID REFERENCES production_resources(id),  -- Machine, person, workstation
    resource_name VARCHAR(255),  -- Denormalized for performance
    
    -- Cost and time
    cost_parameter DECIMAL(10, 2) NOT NULL,  -- EUR/h, EUR/unit, etc.
    cost_unit VARCHAR(20) NOT NULL,  -- "EUR/h", "EUR/unit"
    time_duration INTEGER NOT NULL,  -- Duration in minutes
    calculated_cost DECIMAL(10, 2),  -- cost_parameter * (time_duration / 60) if per hour
    
    -- Sequence
    sequence_order INTEGER NOT NULL,
    is_sequential BOOLEAN DEFAULT TRUE,  -- If operations must be in sequence
    
    -- Variant conditions
    variant_conditions JSONB,  -- { "color": ["brown", "black"], "size": ["large"] }
    
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE production_resources (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    
    resource_name VARCHAR(255) NOT NULL,  -- "Table Saw", "Mary", "Assembly Station"
    resource_type VARCHAR(50) NOT NULL,  -- Machine, Person, Workstation, Tool
    cost_rate DECIMAL(10, 2) NOT NULL,  -- Default cost rate
    cost_unit VARCHAR(20) NOT NULL,  -- "EUR/h", "EUR/unit"
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, resource_name)
);
```

---

### 5. Working Orders (Production Orders)
**Goal:** Create and manage production/manufacturing orders (similar to Purchase Orders)

**Features:**
- Create working orders from recommendations/cart
- WO number generation (WO-2025-001, etc.)
- WO supplier assignment (manufacturing facility)
- Production quantity
- Expected completion date
- Status tracking (pending, in_progress, completed, cancelled)
- Raw materials consumption tracking
- Production operations tracking
- Cost calculation (raw materials + operations)
- Destination/location tracking

**UI Reference:** "Your orders" page with tabs:
- Purchase Orders (existing)
- Production Orders (new)
- Transfers (future)

**Database Structure:**
```sql
CREATE TABLE working_orders (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    
    wo_number VARCHAR(50) NOT NULL UNIQUE,  -- WO-2025-001
    supplier_id UUID NOT NULL REFERENCES suppliers(id),  -- WO supplier (manufacturing facility)
    
    -- Product to produce
    product_id UUID NOT NULL REFERENCES products(id),
    variant_id UUID REFERENCES product_variants(id),  -- Optional
    
    -- Production details
    quantity INTEGER NOT NULL,  -- Quantity to produce
    bom_id UUID REFERENCES product_bom(id),  -- Which BOM version to use
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending',  -- pending, confirmed, in_progress, completed, cancelled
    
    -- Dates
    order_date DATE NOT NULL DEFAULT CURRENT_DATE,
    expected_completion_date DATE,
    actual_completion_date DATE,
    
    -- Financials
    raw_materials_cost DECIMAL(12, 2) DEFAULT 0,
    operations_cost DECIMAL(12, 2) DEFAULT 0,
    total_cost DECIMAL(12, 2) DEFAULT 0,  -- raw_materials_cost + operations_cost
    
    -- Destination
    destination_location_id VARCHAR(255),  -- Where finished product goes
    
    -- Tracking
    units_completed INTEGER DEFAULT 0,
    units_remaining INTEGER,  -- quantity - units_completed
    
    notes TEXT,
    created_by VARCHAR(255),  -- User ID or email
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_working_orders_client (client_id),
    INDEX idx_working_orders_supplier (supplier_id),
    INDEX idx_working_orders_status (status)
);

CREATE TABLE working_order_items (
    id UUID PRIMARY KEY,
    wo_id UUID NOT NULL REFERENCES working_orders(id) ON DELETE CASCADE,
    
    -- Raw material needed
    raw_material_id UUID NOT NULL REFERENCES raw_materials(id),
    item_id VARCHAR(255) NOT NULL,
    
    -- Quantity needed for this WO
    quantity_required DECIMAL(10, 4) NOT NULL,
    quantity_allocated DECIMAL(10, 4) DEFAULT 0,  -- From stock
    quantity_ordered DECIMAL(10, 4) DEFAULT 0,  -- If need to order more
    
    unit VARCHAR(50) NOT NULL,
    unit_cost DECIMAL(10, 2),
    total_cost DECIMAL(12, 2),
    
    notes TEXT,
    
    INDEX idx_wo_items_wo (wo_id),
    INDEX idx_wo_items_material (raw_material_id)
);

CREATE TABLE working_order_operations (
    id UUID PRIMARY KEY,
    wo_id UUID NOT NULL REFERENCES working_orders(id) ON DELETE CASCADE,
    operation_id UUID NOT NULL REFERENCES production_operations(id),
    
    status VARCHAR(20) DEFAULT 'pending',  -- pending, in_progress, completed, skipped
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    actual_duration INTEGER,  -- Actual time in minutes
    actual_cost DECIMAL(10, 2),
    
    notes TEXT,
    
    INDEX idx_wo_operations_wo (wo_id)
);
```

---

### 6. Raw Materials Model
**Goal:** Separate raw materials from finished products

**Database Structure:**
```sql
CREATE TABLE raw_materials (
    id UUID PRIMARY KEY,
    client_id UUID NOT NULL REFERENCES clients(client_id),
    
    -- ⚠️ CRITICAL: item_id for consistency with forecasting engine
    item_id VARCHAR(255) NOT NULL,
    sku VARCHAR(255),  -- Optional alias
    
    material_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) DEFAULT 'Uncategorized',
    unit VARCHAR(50) NOT NULL,  -- m, l, kg, pcs, etc.
    
    -- Stock
    units_available DECIMAL(10, 4) DEFAULT 0,
    units_in_transit DECIMAL(10, 4) DEFAULT 0,  -- On order
    
    -- Supplier info
    primary_supplier_id UUID REFERENCES suppliers(id),
    
    -- Ordering
    lead_time_days INTEGER DEFAULT 14,
    moq_type VARCHAR(20),  -- Fixed, Flexible, etc.
    moq DECIMAL(10, 4) DEFAULT 0,
    
    -- Cost
    unit_cost DECIMAL(10, 2) DEFAULT 0,
    
    -- Metrics
    days_of_cover DECIMAL(10, 2),  -- Calculated metric
    
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(client_id, item_id),
    INDEX idx_raw_materials_client_item (client_id, item_id)
);
```

---

## Implementation Phases

### Phase 1: Foundation - Raw Materials & BOM Structure
**Goal:** Set up basic data models for raw materials and BOM

**Tasks:**
- [ ] Create `raw_materials` table migration
- [ ] Create `product_bom` and `product_bom_items` tables
- [ ] Create `product_variants` table
- [ ] Create API models and schemas
- [ ] Create basic CRUD endpoints for raw materials
- [ ] Create basic CRUD endpoints for BOM
- [ ] Add raw materials to ETL sync (if needed)

**Deliverables:**
- Raw materials can be created/managed
- BOM can be defined for products
- Product variants can be created

**Estimated Time:** 1-2 weeks

---

### Phase 2: Production Operations
**Goal:** Define production workflow/operations

**Tasks:**
- [ ] Create `production_resources` table
- [ ] Create `production_operations` table
- [ ] Create API endpoints for resources
- [ ] Create API endpoints for operations
- [ ] Add operation sequence management
- [ ] Add variant-specific operations support

**Deliverables:**
- Production resources can be managed
- Production operations can be defined per product/variant
- Operations can be sequenced and reordered

**Estimated Time:** 1 week

---

### Phase 3: Working Orders - Core Functionality
**Goal:** Create and manage working orders

**Tasks:**
- [ ] Create `working_orders` table
- [ ] Create `working_order_items` table
- [ ] Create `working_order_operations` table
- [ ] Create `WorkingOrderService` (similar to `PurchaseOrderService`)
- [ ] Create API endpoints:
  - `POST /api/v1/working-orders` - Create WO
  - `GET /api/v1/working-orders` - List WOs
  - `GET /api/v1/working-orders/{wo_id}` - Get WO details
  - `PUT /api/v1/working-orders/{wo_id}/status` - Update status
  - `POST /api/v1/working-orders/from-cart` - Create from cart
- [ ] WO number generation
- [ ] Cost calculation (raw materials + operations)
- [ ] Raw materials allocation logic

**Deliverables:**
- Working orders can be created
- WO status can be tracked
- Costs are calculated automatically

**Estimated Time:** 2 weeks

---

### Phase 4: Frontend - Raw Materials Catalogue
**Goal:** UI for managing raw materials

**Tasks:**
- [ ] Create raw materials catalogue page
- [ ] Raw materials table (AG Grid)
- [ ] Add/Edit raw material modal
- [ ] Search and filter functionality
- [ ] Import/Export functionality
- [ ] Days of Cover calculation display

**Deliverables:**
- Raw materials can be managed via UI
- Similar to products catalogue interface

**Estimated Time:** 1 week

---

### Phase 5: Frontend - BOM Management
**Goal:** UI for managing product recipes/BOM

**Tasks:**
- [ ] Add "Product recipe / BOM" tab to product detail page
- [ ] BOM items table
- [ ] Add/Edit BOM item modal
- [ ] Variant selector
- [ ] Copy BOM between variants
- [ ] Compare variants functionality
- [ ] Stock cost calculation display

**Deliverables:**
- BOM can be managed via UI
- Variant-specific BOMs work

**Estimated Time:** 1-2 weeks

---

### Phase 6: Frontend - Production Operations
**Goal:** UI for managing production operations

**Tasks:**
- [ ] Add "Production operations" tab to product detail page
- [ ] Operations table with drag-and-drop reordering
- [ ] Add/Edit operation modal
- [ ] Resource selector
- [ ] Sequence toggle ("Operations are in sequence")
- [ ] Copy operations from variant
- [ ] Cost calculation per operation

**Deliverables:**
- Production operations can be managed via UI
- Operations can be sequenced

**Estimated Time:** 1 week

---

### Phase 7: Frontend - Working Orders
**Goal:** UI for managing working orders

**Tasks:**
- [ ] Add "Production Orders" tab to "Your orders" page
- [ ] Working orders list table
- [ ] Create WO modal/form
- [ ] WO detail page
- [ ] Status updates
- [ ] Raw materials consumption view
- [ ] Operations progress tracking
- [ ] Create WO from cart functionality

**Deliverables:**
- Working orders can be created and managed via UI
- Similar to Purchase Orders interface

**Estimated Time:** 2 weeks

---

### Phase 8: Integration & Advanced Features
**Goal:** Connect WO system with existing features

**Tasks:**
- [ ] Recommendations integration (suggest WO creation)
- [ ] Cart integration (add to cart → create WO)
- [ ] Stock level updates (consume raw materials, add finished products)
- [ ] Forecasting integration (forecast raw material needs)
- [ ] Reporting (WO costs, production efficiency)
- [ ] WO supplier filtering (only show WO suppliers in WO creation)

**Deliverables:**
- WO system fully integrated with existing features
- End-to-end production planning workflow

**Estimated Time:** 2 weeks

---

## Database Schema Summary

### New Tables:
1. `raw_materials` - Raw materials catalogue
2. `product_variants` - Product variants (color, size, etc.)
3. `product_bom` - Bill of Materials headers
4. `product_bom_items` - BOM line items (ingredients)
5. `production_resources` - Production resources (machines, people, workstations)
6. `production_operations` - Production operation steps
7. `working_orders` - Working order headers
8. `working_order_items` - WO raw materials needed
9. `working_order_operations` - WO operation tracking

### Modified Tables:
- `suppliers` - Already has `supplier_type` field (PO/WO) ✅
- `products` - May need `is_raw_material` flag or separate table (prefer separate)

---

## API Endpoints Summary

### Raw Materials:
- `GET /api/v1/raw-materials` - List raw materials
- `POST /api/v1/raw-materials` - Create raw material
- `GET /api/v1/raw-materials/{id}` - Get raw material
- `PUT /api/v1/raw-materials/{id}` - Update raw material
- `DELETE /api/v1/raw-materials/{id}` - Delete raw material

### BOM:
- `GET /api/v1/products/{product_id}/bom` - Get product BOM
- `POST /api/v1/products/{product_id}/bom` - Create/update BOM
- `GET /api/v1/products/{product_id}/variants/{variant_id}/bom` - Get variant BOM
- `POST /api/v1/products/{product_id}/bom/copy` - Copy BOM to variant

### Production Operations:
- `GET /api/v1/products/{product_id}/operations` - Get product operations
- `POST /api/v1/products/{product_id}/operations` - Create operation
- `PUT /api/v1/products/{product_id}/operations/{id}` - Update operation
- `DELETE /api/v1/products/{product_id}/operations/{id}` - Delete operation
- `PUT /api/v1/products/{product_id}/operations/reorder` - Reorder operations

### Working Orders:
- `GET /api/v1/working-orders` - List working orders
- `POST /api/v1/working-orders` - Create working order
- `GET /api/v1/working-orders/{wo_id}` - Get WO details
- `PUT /api/v1/working-orders/{wo_id}/status` - Update WO status
- `POST /api/v1/working-orders/from-cart` - Create WO from cart

---

## Key Design Decisions

### 1. Separate Raw Materials Table
**Decision:** Raw materials are separate from finished products  
**Rationale:** Different management needs, different suppliers, different forecasting

### 2. Variant-Specific BOMs
**Decision:** BOMs can be variant-specific (e.g., different recipe for brown vs black)  
**Rationale:** Real-world manufacturing often has variant-specific recipes

### 3. WO Suppliers vs PO Suppliers
**Decision:** Use existing `supplier_type` field (PO/WO)  
**Rationale:** Reuse existing supplier infrastructure, just filter by type

### 4. BOM Versioning
**Decision:** Support BOM versions for change tracking  
**Rationale:** Recipes change over time, need to track which version was used

### 5. Operations Sequence
**Decision:** Support both sequential and parallel operations  
**Rationale:** Some operations must be in sequence, others can run in parallel

---

## Related Documentation

- [Data Model](../DATA_MODEL.md) - Overall database schema
- [Next Steps](../NEXT_STEPS.md) - Development priorities
- [Backend Roadmap (Archived)](../archive/backend/BACKEND_ROADMAP.md) - Historical implementation snapshot

---

**Document Owner:** Development Team  
**Last Updated:** 2025-12-17  
**Status:** Planning Phase - Ready for implementation
