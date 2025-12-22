# System Workflows - ASCII Flowcharts

This document contains ASCII flowcharts visualizing the key workflows and decision loops in the e-commerce inventory forecasting system.

---

## High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL DATA SOURCES                                │
│                                                                              │
│  ┌──────────────┐         ┌──────────────┐                                 │
│  │   Online     │         │    Retail    │                                 │
│  │   Channel    │         │   Channel    │                                 │
│  └──────┬───────┘         └──────┬───────┘                                 │
│         │                        │                                           │
│         └──────────┬─────────────┘                                           │
│                    │                                                         │
│                    ▼                                                         │
│         ┌──────────────────────┐                                            │
│         │  MetaKocka BigQuery  │                                            │
│         │   (Data Warehouse)   │                                            │
│         └──────────┬───────────┘                                            │
└────────────────────│─────────────────────────────────────────────────────────┘
                     │
                     │ Daily Sync
                     │
                     ▼
         ┌──────────────────────┐
         │       ETL            │
         │  (Extract, Transform, │
         │       Load)          │
         │                      │
         │ • Data Validation    │
         │ • Data Cleaning      │
         │ • Data Transformation│
         │ • Feature Engineering│
         └──────────┬───────────┘
                     │
                     │ Processed Data
                     │
┌────────────────────▼─────────────────────────────────────────────────────────┐
│                                                                              │
│  ╔═══════════════════════════════════════════════════════════════════════╗  │
│  ║                    OUR SYSTEM (Forecasting Platform)                  ║  │
│  ║                                                                       ║  │
│  ║  ┌─────────────────────────────────────────────────────────────┐   ║  │
│  ║  │  Forecast Engine (Docker)                                    │   ║  │
│  ║  │  Weekly Forecast Cycle or on dema                                       │   ║  │
│  ║  │                                                               │   ║  │
│  ║  │  • Generate Demand Forecasts                                 │   ║  │
│  ║  │  • Calculate DIR (Days of Inventory Remaining)              │   ║  │
│  ║  │  • Assess Stockout Risk                                      │   ║  │
│  ║  │  • Model Selection & Validation                              │   ║  │
│  ║  └───────┬───────────────────────────────┬───────────────────┘   ║  │
│  ║          │                               │                          ║  │
│  ║          │                               │                          ║  │
│  ║          ▼                               ▼                          ║  │
│  ║  ┌──────────────────┐         ┌──────────────────┐               ║  │
│  ║  │ Recommendations   │         │ Inventory        │               ║  │
│  ║  │                   │         │ Overview         │               ║  │
│  ║  │ • REORDER         │         │                   │               ║  │
│  ║  │ • PROMOTE         │         │ • Stock Status     │               ║  │
│  ║  │ • REDUCE_ORDER   │         │ • DIR Metrics     │               ║  │
│  ║  │ • AI Suggestions  │         │ • Risk Scores     │               ║  │
│  ║  └────────┬──────────┘         └────────┬─────────┘               ║  │
│  ║           │                              │                          ║  │
│  ║           │                              │                          ║  │
│  ║           │                              ▼                          ║  │
│  ║           │                   ┌──────────────────┐                 ║  │
│  ║           │                   │  Dashboard KPIs  │                 ║  │
│  ║           │                   │                  │                 ║  │
│  ║           │                   │ • Total SKUs     │                 ║  │
│  ║           │                   │ • Understocked   │                 ║  │
│  ║           │                   │ • Overstocked    │                 ║  │
│  ║           │                   │ • Inventory Value│                 ║  │
│  ║           │                   │ • Avg DIR        │                 ║  │
│  ║           │                   └────────┬─────────┘                 ║  │
│  ║           │                            │                            ║  │
│  ║           ▼                            │                            ║  │
│  ║  ┌─────────────────────────────────────┴──────────┐               ║  │
│  ║  │  Actions: Purchase Orders & Work Orders         │               ║  │
│  ║  │                                                  │               ║  │
│  ║  │  • Create Purchase Orders                       │               ║  │
│  ║  │  • Generate Work Orders                         │               ║  │
│  ║  │  • Order Planning & Cart Management            │               ║  │
│  ║  │  • Supplier Integration                        │               ║  │
│  ║  └────────┬───────────────────────────────────────┘               ║  │
│  ║           │                                                       ║  │
│  ║           │                                                       ║  │
│  ║           ▼                                                       ║  │
│  ║  ┌─────────────────────────────────────────────────────────────┐   ║  │
│  ║  │  Feedback Loop: 7 Days KPIs for Continuous Improvement     │   ║  │
│  ║  │                                                             │   ║  │
│  ║  │  • Monitor Order Performance                               │   ║  │
│  ║  │  • Track Forecast Accuracy                                 │   ║  │
│  ║  │  • Measure Inventory Optimization                          │   ║  │
│  ║  │  • Assess Recommendation Effectiveness                     │   ║  │
│  ║  └─────────────────────────────────────────────────────────────┘   ║  │
│  ║                                                                   ║  │
│  ╚═══════════════════════════════════════════════════════════════════╝  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                     │
                     │ Actions & Results
                     │
                     ▼
         ┌──────────────────────┐
         │    MetaKocka        │
         │  (Operational System)│
         │                      │
         │ • Execute Orders     │
         │ • Track Fulfillment  │
         │ • Update Inventory  │
         └──────────────────────┘
                     │
                     │ Feedback Data
                     │ (7-day KPIs)
                     │
                     ▼
         ┌──────────────────────┐
         │  MetaKocka BigQuery  │
         │   (Data Warehouse)   │
         │                      │
         │ ← Feedback Loop      │
         └──────────────────────┘
```

### System Components Overview

**External Data Sources:**
- **Online Channel**: E-commerce platform sales data
- **Retail Channel**: Physical store sales data

**Data Pipeline:**
- **MetaKocka BigQuery**: Central data warehouse storing all sales and inventory data
- **ETL Process**: Extracts, transforms, and loads data from BigQuery into the forecasting system
  - Data validation and cleaning
  - Feature engineering
  - Data transformation for forecasting models

**Our System (Forecasting Platform) - Blue Box:**
- **Forecast Engine**: Core forecasting system running weekly cycles in Docker
  - Generates demand forecasts
  - Calculates DIR (Days of Inventory Remaining)
  - Assesses stockout risk
  - Model selection and validation

- **Inventory Overview**: Provides current inventory status and metrics
- **Recommendations**: AI-powered suggestions for inventory actions
- **Dashboard KPIs**: High-level metrics for decision-making
- **Actions**: Purchase order and work order creation
- **Feedback Loop**: Monitors 7-day KPIs for continuous improvement

**Operational System:**
- **MetaKocka**: Executes orders, tracks fulfillment, updates inventory

**Continuous Improvement:**
- Feedback loop sends performance data back to BigQuery
- Data is used to refine forecasts and recommendations
- System learns and improves over time

---

## 1. Decision-Making Loop: Data → Decision → Action

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECISION-MAKING LOOP                         │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   VIEW DATA  │
    │              │
    │ • Dashboard  │
    │ • Products   │
    │ • Forecasts  │
    │ • Metrics    │
    └──────┬───────┘
           │
           ▼
    ┌─────────────────────────────────────┐
    │      ANALYZE & UNDERSTAND           │
    │                                     │
    │ • Stockout Risk Scores              │
    │ • DIR (Days of Inventory Remaining)│
    │ • Forecasted Demand                 │
    │ • Inventory Value                   │
    │ • Overstock/Understock Status       │
    │ • AI Recommendations                │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │         MAKE DECISION               │
    │                                     │
    │ • Which products need attention?   │
    │ • What action to take?              │
    │   - Reorder?                        │
    │   - Reduce order?                   │
    │   - Promote?                        │
    │ • Priority?                         │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │         TAKE ACTION                 │
    │                                     │
    │ • Add to Order Planning Cart         │
    │ • Create Purchase Order              │
    │ • Create Marketing Campaign          │
    │ • Update Product Settings           │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────┐
    │      MONITOR RESULTS                │
    │                                     │
    │ • Track Order Status                 │
    │ • Monitor Inventory Changes         │
    │ • Review Forecast Accuracy           │
    │ • Assess Impact                     │
    └──────────────┬──────────────────────┘
                   │
                   └──────────────┐
                                 │
                                 ▼
                          (Loop Back to View Data)
```

---

## 2. Complete Ordering Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              ORDERING PROCESS - COMPLETE FLOW                    │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────┐
    │   STEP 1: VIEW PRODUCTS NEEDING        │
    │          ATTENTION                      │
    │                                         │
    │ Sources:                                 │
    │ • Dashboard (Top 5 understocked)       │
    │ • Recommendations (AI suggestions)       │
    │ • Product List (filtered by status)    │
    │ • Order Planning Suggestions            │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 2: REVIEW PRODUCT DETAILS       │
    │                                         │
    │ Display:                                 │
    │ • Current Stock                         │
    │ • Forecasted Demand (30d)              │
    │ • DIR (Days of Inventory Remaining)    │
    │ • Stockout Risk Score                   │
    │ • Unit Cost                             │
    │ • Inventory Value                       │
    │ • Supplier Information                  │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 3: CHECK SUPPLIER CONDITIONS   │
    │                                         │
    │ Validate:                               │
    │ • Supplier Assigned? ──No──► Assign Supplier
    │ • MOQ (Minimum Order Quantity)          │
    │ • Lead Time                             │
    │ • Unit Cost                             │
    │ • Packaging Requirements                │
    │ • Shipping Options                      │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 4: ADD TO ORDER PLANNING CART   │
    │                                         │
    │ Actions:                                │
    │ • Click "Add to Cart"                   │
    │ • System validates supplier exists       │
    │ • Sets quantity to MOQ (if not set)     │
    │ • Groups by supplier automatically      │
    │ • Updates cart totals                    │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 5: REVIEW CART                  │
    │                                         │
    │ View:                                    │
    │ • Items grouped by supplier             │
    │ • Quantities (adjustable)                │
    │ • Unit costs                            │
    │ • Subtotals per supplier                │
    │ • Grand total                           │
    │ • MOQ validation                        │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 6: ADJUST QUANTITIES            │
    │                                         │
    │ Actions:                                │
    │ • Increase/decrease quantities           │
    │ • System enforces MOQ minimum           │
    │ • Recalculate totals                    │
    │ • Remove items if needed                │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 7: CONFIGURE SHIPPING           │
    │                                         │
    │ Per Supplier:                            │
    │ • Select shipping method                │
    │ • Set shipping unit                     │
    │ • Add notes/instructions                │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 8: REVIEW ORDER SUMMARY        │
    │                                         │
    │ Display:                                 │
    │ • Supplier name                         │
    │ • Items list (SKU, name, qty, cost)     │
    │ • Total quantity                        │
    │ • Total cost                            │
    │ • Shipping details                     │
    │ • Notes                                 │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 9: CREATE PURCHASE ORDER        │
    │                                         │
    │ Actions:                                │
    │ • Click "Create Order"                  │
    │ • System creates order with:             │
    │   - Supplier ID                         │
    │   - Items (product_id, quantity, cost)  │
    │   - Shipping method                     │
    │   - Shipping unit                       │
    │   - Notes                               │
    │ • Order status: "pending"                │
    │ • Items removed from cart                │
    └──────────────┬──────────────────────────┘
                   │
                   ▼
    ┌─────────────────────────────────────────┐
    │   STEP 10: TRACK ORDER                 │
    │                                         │
    │ Monitor:                                 │
    │ • Order status (pending → confirmed →    │
    │   shipped → received)                    │
    │ • Expected delivery date                │
    │ • Order history                         │
    │ • Update status as order progresses     │
    └─────────────────────────────────────────┘
```

---

## 3. Product Data Flow: From Forecast to Order

```
┌─────────────────────────────────────────────────────────────────┐
│         PRODUCT DATA FLOW: FORECAST → DECISION → ORDER          │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │  HISTORICAL DATA │
    │                  │
    │ • Sales History  │
    │ • Promotions      │
    │ • Holidays         │
    │ • Stockouts        │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────┐
    │  FORECAST ENGINE  │
    │                  │
    │ • Generate        │
    │   Forecast        │
    │ • Calculate       │
    │   DIR             │
    │ • Assess Risk     │
    └────────┬──────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      PRODUCT METRICS                 │
    │                                     │
    │ • Forecasted Demand (30d)            │
    │ • DIR (Days of Inventory Remaining) │
    │ • Stockout Risk Score                │
    │ • Current Stock                      │
    │ • Inventory Value                    │
    │ • Status (understocked/overstocked)   │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      DECISION SUPPORT                │
    │                                     │
    │ • Dashboard Display                  │
    │ • Recommendations (AI)               │
    │ • Product Lists (filtered)           │
    │ • Alerts & Warnings                   │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      USER DECISION                    │
    │                                     │
    │ • Select products to order            │
    │ • Review supplier conditions          │
    │ • Determine quantities                │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      ORDER PLANNING CART              │
    │                                     │
    │ • Add products                        │
    │ • Group by supplier                   │
    │ • Adjust quantities                    │
    │ • Configure shipping                  │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      PURCHASE ORDER                   │
    │                                     │
    │ • Create order                        │
    │ • Track status                        │
    │ • Monitor delivery                   │
    └────────┬─────────────────────────────┘
             │
             ▼
    ┌──────────────────────────────────────┐
    │      INVENTORY UPDATE                 │
    │                                     │
    │ • Receive order                       │
    │ • Update stock levels                 │
    │ • Recalculate metrics                 │
    │ • Update forecasts                    │
    └────────┬─────────────────────────────┘
             │
             └──────────────┐
                            │
                            ▼
                    (Loop Back to Forecast)
```

---

## 4. Supplier Conditions Integration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│          SUPPLIER CONDITIONS IN ORDERING PROCESS                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────┐
    │  PRODUCT SELECTED     │
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  CHECK: Supplier Assigned?           │
    └──────────┬───────────────────────────┘
               │
        ┌──────┴──────┐
        │             │
       Yes           No
        │             │
        │             ▼
        │    ┌──────────────────────┐
        │    │  ASSIGN SUPPLIER     │
        │    │                      │
        │    │ • Select supplier    │
        │    │ • Set supplier       │
        │    │   product settings   │
        │    └──────────┬───────────┘
        │               │
        │               ▼
        └───────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  LOAD SUPPLIER CONDITIONS            │
    │                                      │
    │ • MOQ (Minimum Order Quantity)       │
    │ • Lead Time                           │
    │ • Unit Cost                           │
    │ • Packaging Unit                      │
    │ • Packaging Quantity                  │
    │ • Shipping Methods Available          │
    │ • Payment Terms                       │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  VALIDATE CONDITIONS                  │
    │                                      │
    │ • MOQ Check:                          │
    │   Quantity >= MOQ? ──No──► Adjust Qty
    │ • Lead Time Check:                    │
    │   DIR > (Lead Time + Safety Buffer)?  │
    │   [Buffer configured in Settings]     │
    │   [Default: 7 days, configurable]    │
    │   ──No──► Show stockout risk warning  │
    │   ──Yes──► Safe to order              │
    │ • Cost Validation                     │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  DISPLAY IN CART                      │
    │                                      │
    │ • Show MOQ requirement               │
    │ • Show lead time                      │
    │ • Show unit cost                      │
    │ • Enforce MOQ in quantity input       │
    │ • Display supplier name               │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  CONFIGURE SHIPPING (Per Supplier)   │
    │                                      │
    │ • Select shipping method              │
    │ • Set shipping unit                   │
    │ • Add notes                           │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  CREATE ORDER WITH CONDITIONS         │
    │                                      │
    │ Order includes:                       │
    │ • supplier_id                         │
    │ • items[]:                            │
    │   - product_id                        │
    │   - quantity (validated >= MOQ)       │
    │   - unit_cost                         │
    │   - packaging_unit                    │
    │   - packaging_quantity               │
    │ • shipping_method                     │
    │ • shipping_unit                       │
    │ • notes                               │
    └──────────────────────────────────────┘
```

---

## 5. Multi-Source Product Selection Flow

```
┌─────────────────────────────────────────────────────────────────┐
│         PRODUCT SELECTION FROM MULTIPLE SOURCES                  │
└─────────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   DASHBOARD      │
                    │                  │
                    │ Top 5            │
                    │ Understocked     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │                  │
                    │  Add to Cart?    │
                    │                  │
                    └────────┬─────────┘
                             │
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ RECOMMENDATIONS│   │ PRODUCT LIST  │   │ ORDER PLANNING│
│                │   │               │   │ SUGGESTIONS   │
│ AI Suggestions │   │ Filtered View │   │ Forecast-based│
│ • REORDER      │   │ • By Status   │   │ • Suggested   │
│ • PROMOTE      │   │ • By Supplier │   │   Quantities  │
│ • REDUCE       │   │ • By Category │   │ • Risk Scores │
└───────┬────────┘   └───────┬───────┘   └───────┬───────┘
        │                    │                    │
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  ORDER PLANNING  │
                    │      CART        │
                    │                  │
                    │ • Grouped by     │
                    │   Supplier       │
                    │ • Quantities     │
                    │ • Costs          │
                    │ • Totals         │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  REVIEW &        │
                    │  CREATE ORDER    │
                    └──────────────────┘
```

---

## 6. Complete System Loop: Forecast → Order → Inventory Update

```
┌─────────────────────────────────────────────────────────────────┐
│              COMPLETE SYSTEM LOOP                                │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────┐
    │  1. DATA COLLECTION                 │
    │                                     │
    │ • Sales Data                        │
    │ • Inventory Levels                  │
    │ • Promotions                         │
    │ • External Events                    │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  2. FORECAST GENERATION               │
    │                                     │
    │ • Calculate Forecasted Demand        │
    │ • Generate Forecasts                 │
    │ • Calculate DIR                      │
    │ • Assess Stockout Risk                │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  3. DECISION SUPPORT                  │
    │                                     │
    │ • Dashboard Metrics                  │
    │ • Product Lists                       │
    │ • AI Recommendations                  │
    │ • Alerts & Warnings                   │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  4. USER DECISION                     │
    │                                     │
    │ • Review Data                         │
    │ • Select Products                     │
    │ • Make Ordering Decisions             │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  5. ORDER PLANNING                   │
    │                                     │
    │ • Add to Cart                        │
    │ • Review Supplier Conditions         │
    │ • Adjust Quantities                  │
    │ • Configure Shipping                 │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  6. ORDER CREATION                    │
    │                                     │
    │ • Create Purchase Order              │
    │ • Send to Supplier                    │
    │ • Track Status                        │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  7. ORDER FULFILLMENT                │
    │                                     │
    │ • Supplier Processes                  │
    │ • Order Shipped                       │
    │ • Order Received                      │
    └──────────────┬──────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────┐
    │  8. INVENTORY UPDATE                  │
    │                                     │
    │ • Update Stock Levels                 │
    │ • Recalculate Metrics                │
    │ • Update Forecasts                    │
    │ • Refresh Dashboard                  │
    └──────────────┬──────────────────────┘
                   │
                   └──────────────┐
                                  │
                                  ▼
                          (Loop Back to Step 1)
```

---

## 7. Supplier Conditions Validation Rules

```
┌─────────────────────────────────────────────────────────────────┐
│              SUPPLIER CONDITIONS VALIDATION                    │
└─────────────────────────────────────────────────────────────────┘

    Product Selected
         │
         ▼
    ┌─────────────────┐
    │ Has Supplier?   │───No──► [ERROR: Assign Supplier First]
    └────────┬────────┘
            Yes
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Load Supplier Product Settings      │
    │                                     │
    │ • MOQ                               │
    │ • Lead Time                         │
    │ • Unit Cost                         │
    │ • Packaging Requirements            │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Validate Quantity                   │
    │                                     │
    │ IF quantity < MOQ:                  │
    │   → Set quantity = MOQ              │
    │   → Show warning                    │
    │                                     │
    │ IF quantity >= MOQ:                 │
    │   → Accept quantity                 │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Check Lead Time vs DIR              │
    │                                     │
    │ Load Safety Buffer from Settings:   │
    │ • Default: 7 days                   │
    │ • Configurable per client/product   │
    │ • Set in: Settings → Inventory      │
    │   Thresholds → Safety Buffer        │
    │                                     │
    │ IF DIR < (Lead Time + Safety Buffer):│
    │   → Show stockout risk warning      │
    │   → Recommend urgent order          │
    │   → Highlight as critical           │
    │                                     │
    │ IF DIR >= (Lead Time + Safety Buffer):│
    │   → Safe to order                   │
    │   → No warning displayed            │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Validate Cost                       │
    │                                     │
    │ IF unit_cost = 0 or null:          │
    │   → Show warning                    │
    │   → Prompt to set cost               │
    │                                     │
    │ IF unit_cost > 0:                   │
    │   → Calculate total cost             │
    └────────┬────────────────────────────┘
             │
             ▼
    ┌─────────────────────────────────────┐
    │ Add to Cart with Validated Data     │
    │                                     │
    │ • Quantity (>= MOQ)                  │
    │ • Unit Cost                          │
    │ • Supplier ID                         │
    │ • MOQ (for reference)                │
    └─────────────────────────────────────┘
```

---

## 8. Recommendation Rules Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              RECOMMENDATION RULES CONFIGURATION                   │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────┐
    │  ANALYZE PRODUCT DATA                 │
    │                                      │
    │ • Current Stock                       │
    │ • Forecasted Demand                   │
    │ • DIR (Days of Inventory Remaining)  │
    │ • Sales History                       │
    │ • Inventory Value                     │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  APPLY RECOMMENDATION RULES         │
    │                                      │
    │ Load Rules from Settings:            │
    │ • Global Rules                       │
    │ • Role-Based Rules (per user role)   │
    │ • Enabled/Disabled Types             │
    │ • Threshold Filters                  │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  EVALUATE RECOMMENDATION TYPES       │
    │                                      │
    │ Check Each Type:                     │
    │                                      │
    │ • REORDER?                           │
    │   └─ IF DIR < (Lead Time + Buffer)  │
    │                                      │
    │ • URGENT?                            │
    │   └─ IF Stockout Risk > 70%         │
    │                                      │
    │ • REDUCE_ORDER?                      │
    │   └─ IF DIR > 90 days               │
    │                                      │
    │ • DEAD_STOCK?                        │
    │   └─ IF No sales in X days          │
    │   └─ AND Inventory Value > Threshold│
    │                                      │
    │ • PROMOTE?                           │
    │   └─ IF DIR > 30 days               │
    │   └─ AND Not in active campaign     │
    │                                      │
    │ • OPTIMIZE?                          │
    │   └─ IF Suboptimal inventory level  │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  FILTER BY ROLE-BASED RULES          │
    │                                      │
    │ CEO:                                 │
    │ • Show: URGENT, High-value DEAD_STOCK│
    │ • Hide: Low-priority items           │
    │                                      │
    │ Procurement Manager:                 │
    │ • Show: REORDER, REDUCE_ORDER, URGENT│
    │ • Hide: PROMOTE, DEAD_STOCK          │
    │                                      │
    │ Marketing Manager:                   │
    │ • Show: PROMOTE, DEAD_STOCK          │
    │ • Hide: REORDER, REDUCE_ORDER        │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  APPLY THRESHOLD FILTERS             │
    │                                      │
    │ • Inventory Value > €X?              │
    │ • Risk Score > Y%?                   │
    │ • Category matches?                  │
    │ • Supplier matches?                  │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  GENERATE RECOMMENDATIONS            │
    │                                      │
    │ • Type (REORDER, PROMOTE, etc.)      │
    │ • Priority (High/Medium/Low)         │
    │ • Reason/Explanation                 │
    │ • Suggested Action                   │
    │ • SKU, Product Name, Metrics         │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  DISPLAY TO USER                     │
    │                                      │
    │ • Filtered by role rules             │
    │ • Sorted by priority                 │
    │ • User can apply additional filters  │
    │ • User can dismiss/ignore            │
    └──────────────────────────────────────┘
```

---

## Key Workflow Principles

### 1. Data-Driven Decisions
- All decisions are based on forecasted demand, current stock, and risk metrics
- AI recommendations provide actionable insights
- Dashboard provides at-a-glance status

### 2. Supplier Conditions Integration
- MOQ enforcement ensures orders meet supplier requirements
- Lead time consideration prevents stockouts
- **Safety Buffer Configuration**: 
  - Configurable in Settings → Inventory Thresholds → Safety Buffer
  - Default: 7 days (can be adjusted per client/product category)
  - Used in formula: `DIR > (Lead Time + Safety Buffer)` to determine stockout risk
  - When DIR < (Lead Time + Safety Buffer), system shows urgent order warning
- Shipping options configured per supplier
- Cost validation ensures accurate pricing

### 3. Order Planning Flexibility
- Products can be added from multiple sources (dashboard, recommendations, product list)
- Quantities can be adjusted before order creation
- Cart groups items by supplier automatically
- Review step before final order creation

### 4. Complete Loop
- System tracks orders through fulfillment
- Inventory updates trigger metric recalculation
- New forecasts incorporate updated inventory
- Continuous improvement cycle

---

## Implementation Notes

### Cart State Management
- Cart persists across page navigation
- Items grouped by supplier for efficient ordering
- MOQ validation on quantity changes
- Real-time total calculations

### Supplier Conditions
- Stored per product-supplier relationship
- Validated before adding to cart
- Enforced during order creation
- Displayed in cart for review

### Safety Buffer Configuration
- **Location**: Settings → Inventory Thresholds → Safety Buffer
- **Default Value**: 7 days
- **Purpose**: Additional days added to lead time to account for:
  - Delivery delays
  - Demand variability
  - Processing time
  - Unexpected events
- **Usage**: 
  - Formula: `Stockout Risk = DIR < (Lead Time + Safety Buffer)`
  - When risk is detected, system shows warning and recommends urgent order
  - Can be configured globally or per product category
- **Recommendation**: 
  - Start with 7 days default
  - Adjust based on supplier reliability and demand patterns
  - Higher buffer for critical products or unreliable suppliers

### Recommendation Rules Configuration
- **Location**: Settings → Recommendations → Rules
- **Purpose**: Configure which types of recommendations are shown to different users/stakeholders
- **Recommendation Types**:
  - **REORDER**: Products with stockout risk (DIR < Lead Time + Buffer)
  - **REDUCE_ORDER**: Overstocked products (DIR > 90 days)
  - **PROMOTE**: Products with excess inventory suitable for marketing
  - **DEAD_STOCK**: Slow-moving or obsolete inventory (no sales in X days)
  - **URGENT**: Critical stockout risk requiring immediate action
  - **OPTIMIZE**: Products with suboptimal inventory levels

- **Configuration Options**:
  - **Global Rules**: Apply to all users
  - **Role-Based Rules**: Different rules for CEO, Procurement Manager, Marketing Manager
  - **Threshold-Based**: Show recommendations only when certain conditions are met
    - Example: Only show DEAD_STOCK if inventory value > €X
    - Example: Only show URGENT if stockout risk > 70%

- **Stakeholder-Specific Views**:
  - **CEO**: High-level critical issues only (URGENT, high-value DEAD_STOCK)
  - **Procurement Manager**: REORDER, REDUCE_ORDER, URGENT (operational focus)
  - **Marketing Manager**: PROMOTE, DEAD_STOCK (promotion opportunities)

- **Filtering Options**:
  - Filter by recommendation type
  - Filter by priority (High/Medium/Low)
  - Filter by inventory value threshold
  - Filter by category or supplier
  - Hide dismissed/ignored recommendations

- **Implementation**:
  - Rules stored in database (configurable via Settings UI)
  - Applied when generating recommendations
  - User can override with manual filters
  - Rules can be enabled/disabled per type

### Order Creation
- One order per supplier
- All cart items for supplier included
- Shipping configured per supplier
- Status tracking from creation to receipt

### Data Table Interface for Inventory Management
- **Purpose**: Provide a clean, filterable, and sortable data table for viewing and managing inventory
- **Core Features**:

  **1. Sortable Columns**
  - Click column header to sort ascending
  - Click again to sort descending
  - Click third time to remove sort
  - Visual indicator (arrow up/down) shows sort direction
  - Multi-column sorting (Shift+Click additional headers)

  **2. Filterable Columns**
  - Filter icon/dropdown in column header
  - Text search for text columns
  - Range filters for numeric columns (min/max)
  - Dropdown selection for categorical columns (supplier, category, status)
  - Multiple filter values (checkboxes)
  - Clear filter button
  - Active filters shown with badge/count

  **3. Table Display**
  - Clean table layout with clear column headers
  - Row hover highlighting
  - Alternating row colors for readability
  - Responsive design (horizontal scroll on mobile)
  - Pagination for large datasets
  - Configurable page size (10, 25, 50, 100 items per page)

  **4. Column Visibility**
  - Show/hide columns menu
  - Save column preferences per user
  - Default visible columns configurable
  - Column width auto-adjust or manual resize

  **5. Data Display**
  - All product fields displayed in columns
  - Calculated fields (DIR, Inventory Value) shown
  - Status indicators (color-coded badges)
  - Conditional formatting (highlight understocked/overstocked)
  - Click row to view product details

  **6. Search and Filter Bar**
  - Global search across all columns
  - Quick filters (Understocked, Overstocked, All)
  - Advanced filter panel (expandable)
  - Clear all filters button
  - Filter count indicator

  **7. Export Functionality**
  - Export filtered/sorted data to CSV
  - Export to Excel (optional)
  - Export includes current filters and sort order
  - One-click export button

- **Table Columns** (typical display):
  - Checkbox (for selection)
  - SKU
  - Product Name
  - Category
  - Supplier
  - Current Stock
  - Unit Cost
  - Inventory Value
  - DIR (Days of Inventory Remaining)
  - Stockout Risk Score
  - Status (Understocked/Overstocked/Normal)
  - Actions (View Details, Edit, Add to Cart)

- **User Experience**:
  - Fast filtering and sorting for quick data analysis
  - Clear visual feedback for active filters/sorts
  - Easy to find specific products
  - Export for external analysis
  - Responsive and performant with large datasets

---

## 9. Data Table Interface Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              DATA TABLE - FILTERING & SORTING                    │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────┐
    │  LOAD INVENTORY DATA                  │
    │                                      │
    │ • Products with all fields           │
    │ • Calculated metrics (DIR, Value)    │
    │ • Status indicators                  │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  DISPLAY DATA TABLE                   │
    │                                      │
    │ ┌──────────────────────────────────┐ │
    │ │ [✓] SKU │ Name │ Cost │ DIR │...│ │
    │ │  [↑]    │      │      │     │    │ │
    │ ├──────────────────────────────────┤ │
    │ │ [ ] ABC │ Prod1│ 10.0 │ 15  │...│ │
    │ │ [ ] DEF │ Prod2│ 20.0 │ 45  │...│ │
    │ │ [ ] GHI │ Prod3│ 15.0 │ 120 │...│ │
    │ └──────────────────────────────────┘ │
    │                                      │
    │ • Sortable column headers (↑↓)       │
    │ • Filter icons in headers            │
    │ • Pagination controls                │
    │ • Search bar                         │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  USER FILTERS DATA                    │
    │                                      │
    │ • Click filter icon → Open filter     │
    │ • Select filter values                │
    │ • Apply filter → Table updates        │
    │ • Multiple filters can be active      │
    │ • Clear filter → Remove filter        │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  USER SORTS DATA                      │
    │                                      │
    │ • Click column header → Sort         │
    │ • Click again → Reverse sort          │
    │ • Click third time → Remove sort      │
    │ • Shift+Click → Multi-column sort     │
    │ • Visual indicator shows direction   │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  DISPLAY FILTERED/SORTED RESULTS      │
    │                                      │
    │ • Updated table with filters applied │
    │ • Active filters shown (badges)      │
    │ • Sort indicators visible            │
    │ • Pagination updated                 │
    │ • Result count displayed             │
    └──────────┬───────────────────────────┘
               │
               ▼
    ┌──────────────────────────────────────┐
    │  USER ACTIONS                         │
    │                                      │
    │ • Click row → View product details   │
    │ • Select rows → Bulk actions         │
    │ • Export → Download CSV/Excel        │
    │ • Clear filters → Reset view          │
    └──────────────────────────────────────┘
```

### Data Table Key Interactions

**Filtering Flow:**
```
Click Filter Icon → Open Filter Dropdown
    │
    ├─ Text Column → Search Input
    │   │
    │   └─ Type → Filter Results
    │
    ├─ Numeric Column → Min/Max Inputs
    │   │
    │   └─ Set Range → Filter Results
    │
    └─ Categorical Column → Checkboxes
        │
        └─ Select Values → Filter Results
```

**Sorting Flow:**
```
Click Column Header → Sort Ascending (↑)
    │
    Click Again → Sort Descending (↓)
    │
    Click Third Time → Remove Sort
    │
    Shift+Click Another Header → Multi-Column Sort
```

**Search Flow:**
```
Type in Search Bar → Filter All Columns
    │
    Results Update in Real-Time
    │
    Clear Search → Show All Results
```

---

## Next Steps for Implementation

1. **Complete Order Planning Cart**
   - [ ] Add supplier conditions display
   - [ ] Implement MOQ validation
   - [ ] Add quantity adjustment with validation
   - [ ] Group by supplier visualization

2. **Supplier Conditions Integration**
   - [ ] Load supplier product settings
   - [ ] Validate MOQ on add to cart
   - [ ] Display lead time warnings
   - [ ] Configure shipping per supplier

3. **Order Creation Flow**
   - [ ] Review order summary page
   - [ ] Create order API integration
   - [ ] Order status tracking
   - [ ] Inventory update on receipt

4. **Dashboard Enhancements**
   - [ ] Real-time metric updates
   - [ ] Click-through to order planning
   - [ ] Quick actions from dashboard
   - [ ] Alert system for critical items

5. **Safety Buffer Configuration**
   - [ ] Add Safety Buffer setting in Settings → Inventory Thresholds
   - [ ] Default value: 7 days
   - [ ] Allow global and per-category configuration
   - [ ] Use buffer in lead time validation: `DIR < (Lead Time + Safety Buffer)`
   - [ ] Display buffer value in product details and cart
   - [ ] Show warnings when buffer threshold is exceeded

6. **Recommendation Rules Configuration**
   - [ ] Create Settings → Recommendations → Rules UI
   - [ ] Define recommendation types (REORDER, REDUCE_ORDER, PROMOTE, DEAD_STOCK, URGENT, OPTIMIZE)
   - [ ] Implement role-based rules (CEO, Procurement, Marketing)
   - [ ] Add threshold-based filtering (inventory value, risk score)
   - [ ] Create recommendation filtering UI in Recommendations page
   - [ ] Store rules in database with enable/disable per type
   - [ ] Apply rules when generating recommendations
   - [ ] Allow user override with manual filters

7. **Data Table Interface for Inventory Management**
   - [ ] Implement sortable columns (click header to sort)
   - [ ] Add filterable columns (filter dropdown in header)
   - [ ] Create text search filters for text columns
   - [ ] Add range filters for numeric columns (min/max)
   - [ ] Implement dropdown filters for categorical columns
   - [ ] Add global search bar across all columns
   - [ ] Create quick filter buttons (Understocked, Overstocked, All)
   - [ ] Add pagination with configurable page size
   - [ ] Implement column visibility toggle
   - [ ] Add active filter indicators (badges)
   - [ ] Create export to CSV functionality
   - [ ] Add conditional formatting (highlight by status)
   - [ ] Implement row selection (checkbox)
   - [ ] Add click row to view details
   - [ ] Save column preferences per user
   - [ ] Add responsive design for mobile
   - [ ] Implement virtual scrolling for large datasets (optional)
