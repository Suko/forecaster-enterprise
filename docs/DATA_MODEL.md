# Data Model

## Stock Data: Two Perspectives

### Quick Reference

| Table | Stock Field | Granularity | Purpose |
|-------|-------------|-------------|---------|
| `stock_levels` | `current_stock` | **Per Location** | Current inventory snapshot |
| `ts_demand_daily` | `stock_on_date` | **Per SKU (Aggregated)** | Historical stock trends |

### Key Difference

**`stock_levels.current_stock`:**
- ✅ One value per SKU per location
- ✅ Shows where stock is physically located
- ✅ Example: SKU has 200 units at WH-001, 100 at WH-002

**`ts_demand_daily.stock_on_date`:**
- ✅ One value per SKU per date (summed across all locations)
- ✅ Shows total stock available historically
- ✅ Example: Same SKU shows 300 units total on 2025-01-27

**Formula:** `stock_on_date = SUM(current_stock) across all locations`

For detailed explanation, see [STOCK_AGGREGATION.md](./STOCK_AGGREGATION.md)

---

# Data Model & Sync Strategy

This document defines the minimum data required for sync from external sources, what can be managed in the app, and the database table relationships.

---

## 1. Minimum Sync Data (from External Source)

The absolute minimum data needed to run forecasting is **time series sales data** and **SKU identifiers**.

> **Note**: External source can be BigQuery, MetaKocka, or any other ERP/data warehouse. 
> Data is NOT managed in app - app is read-only for synced data.

### 1.1 Required Sync Tables

```
┌─────────────────────────────────────────────────────────────────┐
│                    MINIMUM SYNC DATA                             │
│           (Daily sync from External Source)                      │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  TIME SERIES DATA (ts_demand_daily)                            │
    │  ════════════════════════════════                              │
    │                                                               │
    │  REQUIRED FIELDS:                                             │
    │  • date_local    DATE        - Sale date                       │
    │  • item_id       VARCHAR     - Product identifier (matches     │
    │                                forecasting engine)            │
    │  • units_sold    DECIMAL     - Units sold                      │
    │                                                               │
    │  REQUIRED (multi-location):                                   │
    │  • location_id   VARCHAR     - Warehouse/store identifier      │
    │                                (if multi-location)            │
    │                                                               │
    │  OPTIONAL:                                                    │
    │  • revenue       DECIMAL     - If available                    │
    │  • stock_on_date  INTEGER     - Stock level for this date       │
    │                                (synced or manually updated)     │
    │                                (for stockout detection)         │
    │  • promotion_flag BOOLEAN    - Promotion indicator            │
    │  • holiday_flag  BOOLEAN     - Holiday indicator              │
    │  • is_weekend    BOOLEAN     - Weekend indicator              │
    │  • marketing_spend DECIMAL  - Marketing spend                │
    │                                                               │
    │  HISTORY: 2 years recommended, minimum 3 weeks                │
    │                                                               │
    │  NOTE: stock_on_date allows detecting stockouts:              │
    │  - stock_on_date = 0 AND units_sold = 0 = likely stockout     │
    │  - stock_on_date > 0 AND units_sold = 0 = no demand          │
    │  - Can be synced from external systems or manually updated    │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  PRODUCT MASTER (products_sync)                               │
    │  ══════════════════════════════                               │
    │                                                               │
    │  REQUIRED FIELDS:                                             │
    │  • sku           VARCHAR    - Product identifier (unique)     │
    │  • product_name  VARCHAR    - Product display name            │
    │                                                               │
    │  REQUIRED (from external):                                    │
    │  • category      VARCHAR    - Product category                │
    │                               (default: "Uncategorized")      │
    │  • unit_cost     DECIMAL    - Cost per unit                   │
    │                               (default: 0, flag for review)   │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  INVENTORY LEVELS (stock_sync)                                │
    │  ══════════════════════════════                               │
    │                                                               │
    │  REQUIRED FIELDS:                                             │
    │  • sku           VARCHAR    - Product identifier              │
    │  • location_id   VARCHAR    - Warehouse/store identifier      │
    │  • current_stock INTEGER    - Current inventory level         │
    │                                                               │
    │  READ-ONLY: Stock is managed in source system                │
    │  App does NOT modify stock levels                            │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  LOCATIONS (locations_sync)                                   │
    │  ═══════════════════════════                                  │
    │                                                               │
    │  REQUIRED FIELDS:                                             │
    │  • location_id   VARCHAR    - Location identifier             │
    │  • name          VARCHAR    - Location name                   │
    │                                                               │
    │  OPTIONAL:                                                    │
    │  • address       VARCHAR    - Address                         │
    │  • city          VARCHAR    - City                            │
    │  • country       VARCHAR    - Country                         │
    └──────────────────────────────────────────────────────────────┘
```

### 1.2 Minimum Sync SQL Example

```sql
-- 1. TIME SERIES (daily sales per location)
SELECT 
    date as date_local,
    sku as item_id,  -- Note: stored as item_id in ts_demand_daily
    location_id,
    SUM(quantity) as units_sold,
    SUM(revenue) as revenue,  -- optional
    stock_on_date  -- optional: stock level for this date (synced or manually updated, for stockout detection)
FROM sales_transactions
WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 YEAR)  -- 2 years, min 3 weeks
GROUP BY date, sku, location_id, stock_on_date

-- 2. PRODUCT MASTER (with required category and cost)
SELECT 
    sku,
    product_name,
    COALESCE(category, 'Uncategorized') as category,  -- default if missing
    COALESCE(unit_cost, 0) as unit_cost               -- default if missing
FROM products

-- 3. INVENTORY LEVELS (per location)
SELECT 
    sku,
    location_id,
    current_stock
FROM inventory
WHERE current_stock IS NOT NULL

-- 4. LOCATIONS
SELECT 
    location_id,
    name,
    address,
    city,
    country
FROM locations

-- 5. SUPPLIERS (if available in ERP)
SELECT 
    supplier_id as external_id,
    name,
    contact_email,
    contact_phone,
    address
FROM suppliers

-- 6. PRODUCT-SUPPLIER RELATIONSHIPS (which SKUs belong to which supplier)
SELECT 
    sku,
    supplier_id,
    is_primary_supplier  -- optional: flag for main supplier
FROM product_suppliers
```

---

## 2. App-Managed Data (Not Synced)

These tables are created and managed entirely within the app. Users can manually enter data or import via CSV.

> **Note**: Locations, stock, category, and cost come from EXTERNAL source.
> App manages: Suppliers, Product-Supplier links (MOQ, lead time).

```
┌─────────────────────────────────────────────────────────────────┐
│                    APP-MANAGED DATA                              │
│              (Entered/imported in app)                           │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  SUPPLIERS (master data)                                      │
    │  ═══════════════════════                                      │
    │                                                               │
    │  • id                 INTEGER PRIMARY KEY                     │
    │  • external_id        VARCHAR  (ID from ERP if synced)        │
    │  • name               VARCHAR NOT NULL                        │
    │  • contact_email      VARCHAR                                 │
    │  • contact_phone      VARCHAR                                 │
    │  • address            TEXT                                    │
    │  • notes              TEXT                                    │
    │  • client_id          INTEGER FK                              │
    │                                                               │
    │  ➜ BEST CASE: Synced from external (ERP/MetaKocka)            │
    │  ➜ FALLBACK: Created via App UI or CSV Import                 │
    │  ➜ Master data (name, contact) is read-only if synced        │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  PRODUCT-SUPPLIER CONDITIONS (ordering rules)                 │
    │  ═════════════════════════════════════════════                │
    │                                                               │
    │  • id                 INTEGER PRIMARY KEY                     │
    │  • product_id         INTEGER FK (to synced products)         │
    │  • supplier_id        INTEGER FK (to suppliers)               │
    │  • moq                INTEGER  (Minimum Order Quantity)       │
    │  • lead_time_days     INTEGER                                 │
    │  • supplier_sku       VARCHAR  (supplier's SKU if different)  │
    │  • supplier_cost      DECIMAL  (price from this supplier)     │
    │  • packaging_unit     VARCHAR  (box, pallet, etc.)            │
    │  • packaging_qty      INTEGER  (units per package)            │
    │  • is_primary         BOOLEAN  (primary supplier flag)        │
    │  • notes              TEXT                                    │
    │                                                               │
    │  ➜ ALWAYS managed in app (not synced)                         │
    │  ➜ Created via: App UI or CSV Import                          │
    │  ➜ User controls MOQ, lead time, packaging conditions         │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  SETTINGS & THRESHOLDS (per client)                          │
    │  ═══════════════════════════════════                          │
    │                                                               │
    │  Controls for:                                                │
    │                                                               │
    │  INVENTORY THRESHOLDS:                                        │
    │  • safety_buffer_days       (default: 7)                      │
    │    └─ Extra days added to lead time for safety                │
    │  • understocked_threshold   (default: lead_time + buffer)    │
    │    └─ DIR below this = understocked warning                   │
    │  • overstocked_threshold    (default: 90 days)               │
    │    └─ DIR above this = overstocked warning                    │
    │  • dead_stock_days          (default: 90 days)               │
    │    └─ No sales for this many days = dead stock               │
    │                                                               │
    │  RECOMMENDATION RULES:                                        │
    │  • enabled_types            (REORDER, PROMOTE, etc.)          │
    │    └─ Which recommendation types to show                      │
    │  • role_based_rules         (per stakeholder)                 │
    │    └─ CEO, Procurement, Marketing filters                     │
    │  • threshold_filters        (min values to show)              │
    │    └─ Only show if inventory value > X, risk > Y%            │
    │                                                               │
    │  ➜ Configured via: Settings UI                                │
    │  ➜ Affects dashboard, recommendations, alerts                │
    └──────────────────────────────────────────────────────────────┘
```

### What's SYNCED vs APP-MANAGED:

| Data | Source | Managed In | Notes |
|------|--------|------------|-------|
| Products (SKU, name) | External | Read-only | From ERP |
| Category | External | Read-only | From ERP |
| Unit Cost | External | Read-only | From ERP |
| Stock Levels | External | Read-only | From ERP |
| Locations | External | Read-only | From ERP |
| Sales History | External | Read-only | From ERP |
| **Suppliers (name, contact)** | **External (best)** | **Read-only if synced** | Fallback: app-managed |
| **SKU ↔ Supplier Link** | **External (best)** | **Read-only if synced** | Which SKUs belong to which supplier |
| **Supplier Conditions** | **App always** | **App UI / Import** | MOQ, lead time, packaging, price |
| **Settings/Thresholds** | **App** | **Settings UI** | Controls system behavior |

---

## 3. System-Generated Data (Computed)

These tables are populated by the forecasting system, not synced or manually entered.

```
┌─────────────────────────────────────────────────────────────────┐
│                  SYSTEM-GENERATED DATA                           │
│               (Created by forecast engine)                       │
└─────────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  FORECAST_RUNS                                                │
    │  ══════════════                                               │
    │                                                               │
    │  • forecast_run_id     UUID PRIMARY KEY                       │
    │  • client_id           UUID FK                                │
    │  • user_id             VARCHAR FK                             │
    │  • primary_model       VARCHAR                                │
    │  • prediction_length   INTEGER                                │
    │  • status              VARCHAR                                │
    │  • created_at          TIMESTAMP                              │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  FORECAST_RESULTS                                             │
    │  ═════════════════                                            │
    │                                                               │
    │  • result_id           UUID PRIMARY KEY                       │
    │  • forecast_run_id     UUID FK                                │
    │  • item_id             VARCHAR (SKU)                          │
    │  • method              VARCHAR                                │
    │  • date                DATE                                   │
    │  • point_forecast      DECIMAL                                │
    │  • p10, p50, p90       DECIMAL (confidence intervals)         │
    │  • actual_value        DECIMAL (backfilled)                   │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  SKU_CLASSIFICATIONS                                          │
    │  ════════════════════                                         │
    │                                                               │
    │  • id                  UUID PRIMARY KEY                       │
    │  • client_id           UUID FK                                │
    │  • item_id             VARCHAR (SKU)                          │
    │  • abc_class           CHAR(1) (A/B/C)                        │
    │  • xyz_class           CHAR(1) (X/Y/Z)                        │
    │  • demand_pattern      VARCHAR                                │
    │  • recommended_method  VARCHAR                                │
    │  • forecastability     DECIMAL                                │
    └──────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────┐
    │  INVENTORY_METRICS (computed daily)                           │
    │  ═══════════════════════════════════                          │
    │                                                               │
    │  • id                  UUID PRIMARY KEY                       │
    │  • client_id           UUID FK                                │
    │  • sku                 VARCHAR                                │
    │  • date                DATE                                   │
    │  • current_stock       INTEGER                                │
    │  • dir                 DECIMAL (Days of Inventory Remaining)  │
    │  • stockout_risk       DECIMAL (0-100)                        │
    │  • forecasted_demand   DECIMAL (30d)                          │
    │  • inventory_value     DECIMAL                                │
    │  • status              VARCHAR (understocked/overstocked/ok)  │
    └──────────────────────────────────────────────────────────────┘
```

---

## 4. Complete Table Relationships

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE SCHEMA                               │
└─────────────────────────────────────────────────────────────────┘

                          ┌────────────┐
                          │  CLIENTS   │
                          │────────────│
                          │ client_id  │ (PK)
                          │ name       │
                          │ settings   │
                          └─────┬──────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
          ▼                     ▼                     ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  LOCATIONS   │      │  SUPPLIERS   │      │    USERS     │
│(SYNCED/APP)  │      │ (SYNCED/APP) │      │──────────────│
│──────────────│      │──────────────│      │ id       (PK)│
│ id       (PK)│      │ id       (PK)│      │ email        │
│ location_id  │      │ external_id  │      │ client_id(FK)│
│ name         │      │ name         │      └──────────────┘
│ city         │      │ contact_email│
│ client_id(FK)│      │ is_synced    │
└──────┬───────┘      │ client_id(FK)│
       │              └──────┬───────┘
       │                     │
       │                     │
       ▼                     │
┌──────────────────────┐     │
│      PRODUCTS        │     │
│      (SYNCED)        │     │
│──────────────────────│     │
│ id             (PK)  │     │
│ sku            (UK)  │     │
│ product_name         │     │
│ category             │     │
│ unit_cost            │     │
│ client_id       (FK) │     │
└──────────┬───────────┘     │
           │                 │
           │                 │
           ▼                 ▼
    ┌─────────────────────────────────────┐
    │  PRODUCT_SUPPLIER_CONDITIONS        │
    │  (APP-MANAGED - Many-to-Many)       │
    │─────────────────────────────────────│
    │  Relates which SKUs belong to       │
    │  which suppliers + conditions       │
    │                                     │
    │ id              (PK)                │
    │ sku             (FK → products)     │
    │ supplier_id     (FK → suppliers)    │
    │                                     │
    │ RELATIONSHIP (can be synced):       │
    │ • external_id   (if from ERP)       │
    │ • is_synced     (true if from ERP)  │
    │                                     │
    │ CONDITIONS (always app-managed):    │
    │ • moq           (Min Order Qty)     │
    │ • lead_time_days                    │
    │ • supplier_sku  (if different)      │
    │ • supplier_cost (price)             │
    │ • packaging_unit                    │
    │ • packaging_qty                     │
    │ • is_primary    (main supplier)     │
    │                                     │
    │ UNIQUE(client_id, sku, supplier_id) │
    └──────────────┬──────────────────────┘
                   │
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌──────────────────┐      ┌──────────────────────┐
│  STOCK_LEVELS    │      │    SALES_HISTORY     │
│  (SYNCED)        │      │    (SYNCED)          │
│──────────────────│      │──────────────────────│
│ sku         (FK) │      │ sku             (FK) │
│ location_id (FK) │      │ location_id     (FK) │
│ current_stock    │      │ date                 │
│ client_id   (FK) │      │ quantity             │
└──────────────────┘      │ client_id       (FK) │
                          └──────────┬───────────┘
                                     │
                                     ▼
                          ┌──────────────────────┐
                          │   FORECAST_RESULTS   │
                          │   (COMPUTED)         │
                          │──────────────────────│
                          │ item_id (SKU)        │
                          │ date                 │
                          │ point_forecast       │
                          │ client_id       (FK) │
                          └──────────────────────┘
```

### SKU-Supplier Relationship (Many-to-Many)

```
┌─────────────────────────────────────────────────────────────────┐
│              PRODUCT ←→ SUPPLIER RELATIONSHIP                    │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐                        ┌─────────────┐
    │  PRODUCTS   │                        │  SUPPLIERS  │
    │─────────────│                        │─────────────│
    │ SKU-001     │ ◄──────┐    ┌────────► │ Supplier A  │
    │ SKU-002     │ ◄────┐ │    │ ┌──────► │ Supplier B  │
    │ SKU-003     │ ◄──┐ │ │    │ │ ┌────► │ Supplier C  │
    └─────────────┘    │ │ │    │ │ │      └─────────────┘
                       │ │ │    │ │ │
                       ▼ ▼ ▼    ▼ ▼ ▼
            ┌──────────────────────────────────┐
            │  PRODUCT_SUPPLIER_CONDITIONS     │
            │──────────────────────────────────│
            │ SKU-001 ↔ Supplier A (PRIMARY)   │  ← MOQ: 100, Lead: 14d
            │ SKU-001 ↔ Supplier B             │  ← MOQ: 50,  Lead: 21d
            │ SKU-002 ↔ Supplier B (PRIMARY)   │  ← MOQ: 200, Lead: 7d
            │ SKU-002 ↔ Supplier C             │  ← MOQ: 100, Lead: 10d
            │ SKU-003 ↔ Supplier A (PRIMARY)   │  ← MOQ: 500, Lead: 30d
            └──────────────────────────────────┘

    • One SKU can have MULTIPLE suppliers
    • One supplier can supply MULTIPLE SKUs
    • Each link has its own MOQ, lead time, price
    • One supplier marked as PRIMARY per SKU
```

### Data Source for SKU-Supplier Link:

| Data | Source | Notes |
|------|--------|-------|
| **Which SKUs belong to which supplier** | External (best) | Synced from ERP if available |
| **Fallback** | App | Can link in app if not in ERP |
| **MOQ, lead time, packaging, price** | **Always App** | User manages conditions |

---

## 5. Sync Strategy

### 5.1 ETL Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      ETL SYNC STRATEGY                           │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────┐     Daily Sync     ┌────────────────┐
    │   BigQuery     │ ──────────────────►│      ETL       │
    │   (Source)     │                    │   (Transform)  │
    └────────────────┘                    └───────┬────────┘
                                                  │
                                                  │
                      ┌───────────────────────────┼───────────────────────────┐
                      │                           │                           │
                      ▼                           ▼                           ▼
              ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
              │ sales_history │          │   products    │          │ inventory     │
              │(APPEND/UPSERT)│          │ (UPSERT)      │          │ (REPLACE)     │
              └───────────────┘          └───────────────┘          └───────────────┘
```

### 5.2 Sync Modes by Table

| Table | Sync Mode | Frequency | Source | App Access |
|-------|-----------|-----------|--------|------------|
| `sales_history` | Append/Upsert | Daily | External | Read-only |
| `products` | Upsert by SKU | Daily | External | Read-only |
| `stock_levels` | Replace | Daily | External | Read-only |
| `locations` | Upsert | Daily | External | Read-only |
| `suppliers` | Upsert (if avail) | Daily | External (best) | Read-only if synced |
| `product_supplier_links` | Upsert (if avail) | Daily | External (best) | Read-only if synced |
| `product_supplier_conditions` | Manual | On-demand | **App always** | Read/Write |
| `settings` | Manual | On-demand | App | Read/Write |
| `forecast_results` | System | Weekly | Forecast Engine | Read-only |
| `inventory_metrics` | System | Daily | Compute Job | Read-only |

**Note on Product-Supplier:**
- **Link** (which SKUs belong to which supplier): Synced from external if available, otherwise app-managed
- **Conditions** (MOQ, lead time, packaging, price): **Always app-managed**

### 5.3 Sync Implementation Options

**Option A: Direct BigQuery Connector**
```
BigQuery → Python/SQL → PostgreSQL
- Use google-cloud-bigquery Python client
- Schedule with cron or Airflow
- Incremental sync for sales_history
```

**Option B: CSV Export/Import**
```
BigQuery → Export CSV → Upload → Import
- Manual or scheduled export
- User uploads CSV to app
- App parses and imports
```

**Option C: API Integration**
```
BigQuery → Cloud Function → Our API → PostgreSQL
- Real-time or near-real-time
- Webhook trigger on data changes
- More complex but more responsive
```

---

## 6. Minimum Viable Sync

For MVP, focus on this minimal sync:

### 6.1 Synced Data (from External Source - READ-ONLY)

```sql
-- 1. SALES_HISTORY: Time series for forecasting (2 years, min 3 weeks)
CREATE TABLE sales_history (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    sku             VARCHAR(100) NOT NULL,
    location_id     VARCHAR(50) NOT NULL,  -- multi-location required
    date            DATE NOT NULL,
    quantity        INTEGER NOT NULL,
    revenue         DECIMAL(12,2),  -- optional
    synced_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, sku, location_id, date)
);
CREATE INDEX idx_sales_date ON sales_history(date);
CREATE INDEX idx_sales_sku ON sales_history(sku);

-- 2. PRODUCTS: Product master (from external)
CREATE TABLE products (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    sku             VARCHAR(100) NOT NULL,
    product_name    VARCHAR(255) NOT NULL,
    category        VARCHAR(100) DEFAULT 'Uncategorized',  -- default if missing
    unit_cost       DECIMAL(10,2) DEFAULT 0,               -- default if missing
    synced_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, sku)
);

-- 3. LOCATIONS: Warehouses/stores (from external)
CREATE TABLE locations (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    location_id     VARCHAR(50) NOT NULL,  -- external ID
    name            VARCHAR(255) NOT NULL,
    address         TEXT,
    city            VARCHAR(100),
    country         VARCHAR(100),
    synced_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, location_id)
);

-- 4. STOCK_LEVELS: Current inventory per location (from external)
CREATE TABLE stock_levels (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    sku             VARCHAR(100) NOT NULL,
    location_id     VARCHAR(50) NOT NULL,
    current_stock   INTEGER NOT NULL,
    synced_at       TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, sku, location_id)
);
```

### 6.2 Suppliers (Synced or App-Managed)

```sql
-- 5. SUPPLIERS: Best case synced from external, fallback to app-managed
CREATE TABLE suppliers (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    external_id     VARCHAR(100),           -- ID from ERP (if synced)
    name            VARCHAR(255) NOT NULL,
    contact_email   VARCHAR(255),
    contact_phone   VARCHAR(50),
    address         TEXT,
    supplier_type   VARCHAR(20) DEFAULT 'PO',  -- PO or WO
    notes           TEXT,
    is_synced       BOOLEAN DEFAULT FALSE,  -- true if from external
    synced_at       TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, name),
    UNIQUE(client_id, external_id)  -- if synced
);
```

### 6.3 App-Managed Data (Always in App)

```sql
-- 6. PRODUCT_SUPPLIER_CONDITIONS: MOQ, lead time, packaging (ALWAYS app-managed)
CREATE TABLE product_supplier_conditions (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id),
    sku             VARCHAR(100) NOT NULL,  -- links to products.sku
    supplier_id     INTEGER NOT NULL REFERENCES suppliers(id),
    moq             INTEGER DEFAULT 0,      -- Minimum Order Quantity
    lead_time_days  INTEGER DEFAULT 0,      -- Days to deliver
    supplier_sku    VARCHAR(100),           -- Supplier's SKU if different
    supplier_cost   DECIMAL(10,2),          -- Price from this supplier
    packaging_unit  VARCHAR(50),            -- box, pallet, carton, etc.
    packaging_qty   INTEGER,                -- units per package
    is_primary      BOOLEAN DEFAULT FALSE,  -- primary supplier for this SKU
    notes           TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, sku, supplier_id)
);

-- 7. CLIENT_SETTINGS: Thresholds and configuration
CREATE TABLE client_settings (
    id              SERIAL PRIMARY KEY,
    client_id       UUID NOT NULL REFERENCES clients(client_id) UNIQUE,
    
    -- Inventory Thresholds
    safety_buffer_days      INTEGER DEFAULT 7,   -- extra days for safety
    understocked_threshold  INTEGER DEFAULT 14,  -- DIR days (lead_time + buffer)
    overstocked_threshold   INTEGER DEFAULT 90,  -- DIR days
    dead_stock_days         INTEGER DEFAULT 90,  -- no sales for X days
    
    -- Recommendation Rules
    recommendation_rules    JSONB DEFAULT '{
        "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
        "role_rules": {
            "CEO": ["URGENT", "DEAD_STOCK"],
            "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
            "MARKETING": ["PROMOTE", "DEAD_STOCK"]
        },
        "min_inventory_value": 0,
        "min_risk_score": 0
    }',
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
```

---

## 7. Data Flow Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                      DATA FLOW SUMMARY                           │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │            SYNCED FROM EXTERNAL SOURCE                       │
    │        (BigQuery, MetaKocka, or other ERP)                  │
    │                                                              │
    │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
    │  │ SALES       │  │ PRODUCTS    │  │ STOCK       │          │
    │  │─────────────│  │─────────────│  │─────────────│          │
    │  │ date        │  │ sku         │  │ sku         │          │
    │  │ sku         │  │ name        │  │ location_id │          │
    │  │ location_id │  │ category    │  │ quantity    │          │
    │  │ quantity    │  │ unit_cost   │  └─────────────┘          │
    │  └─────────────┘  └─────────────┘                           │
    │                                                              │
    │  ┌─────────────┐                                            │
    │  │ LOCATIONS   │                                            │
    │  │─────────────│                                            │
    │  │ location_id │                                            │
    │  │ name        │                                            │
    │  │ city        │                                            │
    │  └─────────────┘                                            │
    │                                                              │
    │  History: 2 years recommended, minimum 3 weeks              │
    │  READ-ONLY in app (managed in source system)                │
    └─────────────────────────────────────────────────────────────┘
                                  │
                                  │ ETL Daily Sync
                                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                    OUR DATABASE                              │
    │                                                              │
    │   SYNCED (read-only):   APP-MANAGED:      COMPUTED:         │
    │   ┌─────────────┐       ┌─────────────┐   ┌─────────────┐   │
    │   │ sales_      │       │ suppliers   │   │ forecasts   │   │
    │   │   history   │       │ product_    │   │ DIR metrics │   │
    │   │ products    │       │   suppliers │   │ stockout    │   │
    │   │ stock       │       │ (MOQ, lead  │   │   risk      │   │
    │   │ locations   │       │  time)      │   │ recommend-  │   │
    │   └─────────────┘       │ settings    │   │   ations    │   │
    │                         └─────────────┘   └─────────────┘   │
    └─────────────────────────────────────────────────────────────┘
```

---

## 8. Planning Checklist

### Phase 1: External Sync Setup (Week 1)
- [ ] Define external source tables (BigQuery/MetaKocka/other)
- [ ] Create ETL script for sales_history (with location_id)
- [ ] Create ETL script for products (SKU, name, category, cost)
- [ ] Create ETL script for stock_levels (per location)
- [ ] Create ETL script for locations
- [ ] Set up daily sync schedule
- [ ] Test with sample data (min 3 weeks history)
- [ ] Handle missing data: category → "Uncategorized", cost → 0

### Phase 2: App-Managed Data (Week 2)
- [ ] Create suppliers table + API + UI
- [ ] Create product_suppliers table (MOQ, lead time)
- [ ] Create settings table (thresholds, buffers)
- [ ] Add CSV import for suppliers
- [ ] Add CSV import for product-supplier links
- [ ] Link products to suppliers via UI

### Phase 3: Computed Data (Week 3)
- [ ] Create inventory_metrics table
- [ ] Build DIR calculation job (per location)
- [ ] Build stockout risk calculation
- [ ] Connect to forecast results
- [ ] Aggregate metrics across locations

### Phase 4: Full Integration (Week 4)
- [ ] End-to-end data flow testing
- [ ] Dashboard displaying computed metrics
- [ ] Order planning using all data
- [ ] Multi-location views
- [ ] Feedback loop to external source (optional)

---

## 9. Key Decisions (CONFIRMED)

| Decision | Answer | Notes |
|----------|--------|-------|
| **1. Data Source** | External (BigQuery or other) | Not managed in app, external ETL |
| **2. Multi-location** | ✅ YES | Location-level stock required |
| **3. Category Source** | External | Fallback: "Uncategorized" if not provided |
| **4. Unit Cost Source** | External | Synced from ERP/external source |
| **5. Historical Depth** | 2 years recommended | Minimum: 3 weeks |
| **6. Sync Frequency** | Daily | Standard sync schedule |

### Implications of Decisions:

**External Data Source (not app-managed):**
- App does NOT manage stock levels directly
- Stock comes from external ERP/system via sync
- App is read-only for inventory quantities
- Changes to stock happen in source system (MetaKocka)

**Multi-location Support:**
- Products can exist in multiple warehouses
- Stock tracked per location
- Location sync from external source
- Aggregated views across locations

**Category & Cost from External:**
- Must be included in sync
- If category missing: default to "Uncategorized"
- If cost missing: default to 0 (flag for review)

---

## Notes

- SKU is the primary identifier linking all tables
- client_id enables multi-tenancy
- Stock is READ-ONLY in app (synced from external)
- Suppliers, MOQ, lead time can be managed in app or imported
- Computed data (DIR, risk) is regenerated, not synced
- Foreign keys ensure data integrity
- Minimum 3 weeks history required, 2 years recommended for accurate forecasting

