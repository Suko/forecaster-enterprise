# ts_demand_daily - Core Time Series Data Model

**Status:** ✅ **Critical Foundation Table**  
**Purpose:** Daily demand fact table - primary data source for all forecasting  
**Grain:** `(client_id, item_id, location_id, date_local)`

---

## Overview

The `ts_demand_daily` table is the **foundation for all forecasting features**. It stores daily sales data per SKU with all covariates, pricing, inventory, and marketing signals.

**Critical Requirement:** ETL must generate a **full daily series** (including zero-demand days) for each active `(client_id, item_id, location_id)` to preserve:
- ✅ Seasonality patterns
- ✅ Weekday patterns  
- ✅ Promo impact modeling
- ✅ Stockout detection
- ✅ Model compatibility (Chronos-2, TimesFM, Moirai, etc.)

---

## Complete Schema Definition

### Primary Key & Grain

```sql
PRIMARY KEY (client_id, item_id, location_id, date_local)
```

**Grain:** One row per `(client_id, item_id, location_id, date_local)`

### Identity Columns

| Column | Type | Description | Constraints |
|--------|------|-------------|-------------|
| `client_id` | UUID | Client identifier (multi-tenancy) | NOT NULL, FK to clients |
| `item_id` | VARCHAR(255) | Item/SKU identifier | NOT NULL, FK to items |
| `location_id` | UUID | Location identifier (warehouse/store) | NOT NULL, FK to locations |
| `date_local` | DATE | Local date (timezone-aware) | NOT NULL |
| `date_utc` | DATE | UTC date (for consistency) | NOT NULL |
| `observed_at_utc` | TIMESTAMPTZ | When this record was observed/created | NOT NULL |

---

## Target Variables (What We're Forecasting)

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `units_sold` | INTEGER | Units sold on this date | **Primary target** for forecasting |
| `revenue` | NUMERIC(18,2) | Revenue amount | Secondary target (optional) |
| `orders_count` | INTEGER | Number of orders | For analysis only |

**Critical:** `units_sold` is the primary target variable. Must be **0** for zero-demand days (not NULL).

---

## Inventory State

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `stock_on_hand_end` | INTEGER | End-of-day stock level | For stockout detection |
| `stockout_flag` | BOOLEAN | Stockout indicator | **Critical:** Distinguishes true zero demand from lost sales |
| `lost_sales_flag` | BOOLEAN | Lost sales indicator | Optional, derived from stockout + demand |

**Critical Logic:**
```sql
-- stockout_flag should be set when:
stockout_flag = (stock_on_hand_end = 0 OR stock_on_hand_end IS NULL)

-- BUT: If units_sold = 0 AND stockout_flag = true
-- This indicates LOST SALES (demand existed but couldn't be fulfilled)
-- NOT true zero demand
```

**Usage Scenarios:**

| units_sold | stockout_flag | stock_on_hand_end | Interpretation |
|------------|---------------|-------------------|----------------|
| 0 | false | > 0 | **True zero demand** - No one wanted to buy |
| 0 | true | 0 | **Lost sales** - Wanted to buy but out of stock |
| 0 | true | NULL | **Lost sales** - Unknown stock, but flagged as stockout |
| 100 | false | 50 | Normal sales |
| 0 | false | 0 | **Ambiguous** - Could be true zero OR lost sales (needs investigation) |

**ETL Rule:**
- If `stock_on_hand_end = 0` → Set `stockout_flag = true`
- If `units_sold = 0` AND `stockout_flag = true` → This is **lost sales**, not true zero demand
- If `units_sold = 0` AND `stockout_flag = false` AND `stock_on_hand_end > 0` → This is **true zero demand**

**Usage:** Critical for distinguishing between:
- ✅ **True zero demand** (no latent demand)
- ⚠️ **Lost sales** (latent demand that couldn't be fulfilled)

---

## Pricing & Promotion Signals

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `regular_price` | NUMERIC(18,2) | Regular price (no promotion) | For price elasticity |
| `actual_price` | NUMERIC(18,2) | Actual selling price | May differ from regular_price |
| `discount_pct` | NUMERIC(9,4) | Discount percentage (0-100) | Calculated: `(regular_price - actual_price) / regular_price * 100` |
| `promotion_flag` | BOOLEAN | Promotion active flag | **Key covariate** |
| `promotion_type` | TEXT | Promotion type | e.g., "sale", "bogo", "clearance" |

**Usage:** Critical for promotion-aware forecasting (Phase 2).

---

## Observed Past Covariates

**These are known for historical dates (from ETL):**

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `marketing_spend` | NUMERIC(18,2) | Marketing spend (dollars) | **Key covariate** |
| `impressions` | INTEGER | Ad impressions | For marketing effectiveness |
| `clicks` | INTEGER | Ad clicks | For marketing effectiveness |
| `email_sends` | INTEGER | Email sends | For email marketing impact |
| `email_opens` | INTEGER | Email opens | For email marketing impact |

**Usage:** Past covariates help models understand historical patterns (Phase 2).

**Missing Data Handling:**
- Forward-fill last known value (if within 7 days)
- Otherwise: 0 (no marketing activity)

---

## Known Future Covariates

**These are known in advance (from planning systems):**

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `holiday_flag` | BOOLEAN | Holiday indicator | **Key covariate** |
| `holiday_type` | TEXT | Holiday type | e.g., "christmas", "black_friday" |
| `planned_promo_flag` | BOOLEAN | Planned promotion flag | **Key covariate** |
| `planned_promo_type` | TEXT | Planned promotion type | e.g., "sale", "bogo" |
| `seasonal_indicator` | NUMERIC(9,4) | Seasonal indicator (0-1) | Engineered: peak season vs off-season |

**Usage:** Future covariates help models predict promotion/holiday impact (Phase 2).

**Missing Data Handling:**
- Use planned values (if available from planning system)
- Otherwise: 0 (no planned activity)

---

## Calendar Features (Engineered)

**These are derived from `date_local` (always available):**

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `is_weekend` | BOOLEAN | Weekend indicator (Sat/Sun) | Derived: `EXTRACT(DOW FROM date_local) IN (0, 6)` |
| `month_1` through `month_12` | BOOLEAN | One-hot encoded months | Exactly one = 1 per row |
| `day_of_week` | INTEGER | Day of week (1=Mon, 7=Sun) | Derived |
| `week_of_year` | INTEGER | Week of year (1-52) | Derived |
| `peak_season_flag` | BOOLEAN | Peak season indicator | Engineered per (item_id, location_id) |

**Usage:** Calendar features help models capture seasonality (Phase 2).

**Note:** These can be calculated on-the-fly or pre-computed by ETL.

---

## Operational Metadata

| Column | Type | Description | Notes |
|--------|------|-------------|-------|
| `currency` | TEXT | Currency code | e.g., "USD", "EUR" |
| `fx_rate_to_client` | NUMERIC(18,6) | FX rate to client currency | For multi-currency |
| `revenue_converted` | NUMERIC(18,2) | Revenue in client currency | Calculated: `revenue * fx_rate_to_client` |
| `created_at` | TIMESTAMPTZ | Record creation timestamp | Auto-set |
| `updated_at` | TIMESTAMPTZ | Record update timestamp | Auto-update |

---

## Complete SQL Schema

```sql
CREATE TABLE ts_demand_daily (
    -- Identity (Primary Key)
    client_id UUID NOT NULL,
    item_id VARCHAR(255) NOT NULL,
    location_id UUID NOT NULL,
    date_local DATE NOT NULL,
    
    -- Date Metadata
    date_utc DATE NOT NULL,
    observed_at_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Target Variables
    units_sold INTEGER NOT NULL DEFAULT 0,  -- Primary target
    revenue NUMERIC(18,2),
    orders_count INTEGER,
    
    -- Inventory State
    stock_on_hand_end INTEGER,
    stockout_flag BOOLEAN DEFAULT FALSE,
    lost_sales_flag BOOLEAN DEFAULT FALSE,
    
    -- Pricing & Promotion
    regular_price NUMERIC(18,2),
    actual_price NUMERIC(18,2),
    discount_pct NUMERIC(9,4),
    promotion_flag BOOLEAN DEFAULT FALSE,
    promotion_type TEXT,
    
    -- Observed Past Covariates
    marketing_spend NUMERIC(18,2),
    impressions INTEGER,
    clicks INTEGER,
    email_sends INTEGER,
    email_opens INTEGER,
    
    -- Known Future Covariates
    holiday_flag BOOLEAN DEFAULT FALSE,
    holiday_type TEXT,
    planned_promo_flag BOOLEAN DEFAULT FALSE,
    planned_promo_type TEXT,
    seasonal_indicator NUMERIC(9,4),
    
    -- Calendar Features (Engineered)
    is_weekend BOOLEAN,
    month_1 BOOLEAN DEFAULT FALSE,
    month_2 BOOLEAN DEFAULT FALSE,
    month_3 BOOLEAN DEFAULT FALSE,
    month_4 BOOLEAN DEFAULT FALSE,
    month_5 BOOLEAN DEFAULT FALSE,
    month_6 BOOLEAN DEFAULT FALSE,
    month_7 BOOLEAN DEFAULT FALSE,
    month_8 BOOLEAN DEFAULT FALSE,
    month_9 BOOLEAN DEFAULT FALSE,
    month_10 BOOLEAN DEFAULT FALSE,
    month_11 BOOLEAN DEFAULT FALSE,
    month_12 BOOLEAN DEFAULT FALSE,
    day_of_week INTEGER,
    week_of_year INTEGER,
    peak_season_flag BOOLEAN DEFAULT FALSE,
    
    -- Operational Metadata
    currency TEXT,
    fx_rate_to_client NUMERIC(18,6),
    revenue_converted NUMERIC(18,2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Primary Key
    PRIMARY KEY (client_id, item_id, location_id, date_local),
    
    -- Foreign Keys
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id),
    FOREIGN KEY (location_id) REFERENCES locations(location_id),
    
    -- Indexes for Performance
    INDEX idx_ts_demand_client_item_date (client_id, item_id, date_local),
    INDEX idx_ts_demand_date (date_local),
    INDEX idx_ts_demand_item (item_id),
    INDEX idx_ts_demand_location (location_id)
);
```

---

## Critical Requirements

### 1. **Full Daily Series (MANDATORY)**

**For each active `(client_id, item_id, location_id)`, ETL must generate:**
- ✅ One row per day (no gaps)
- ✅ Include zero-demand days (`units_sold = 0`)
- ✅ Cover entire active period (from first sale to today)

**Why:** Models need complete time series to detect:
- Seasonality (weekly, monthly patterns)
- Weekday effects (Mon vs Fri)
- Promo impact (before/during/after)
- Stockout patterns

**Example:**
```
❌ BAD (gaps):
SKU001 | 2024-01-01 | 100
SKU001 | 2024-01-03 | 150  -- Missing 2024-01-02!

✅ GOOD (full series):
SKU001 | 2024-01-01 | 100 | stockout_flag=false
SKU001 | 2024-01-02 | 0   | stockout_flag=false  -- True zero demand
SKU001 | 2024-01-03 | 150 | stockout_flag=false

✅ GOOD (with stockout):
SKU001 | 2024-01-01 | 100 | stockout_flag=false
SKU001 | 2024-01-02 | 0   | stockout_flag=true   -- Zero sales BUT stockout!
SKU001 | 2024-01-03 | 0   | stockout_flag=true   -- Still out of stock
SKU001 | 2024-01-04 | 200 | stockout_flag=false  -- Restocked, high demand
```

**Critical Distinction:**
- `units_sold = 0` + `stockout_flag = false` → **True zero demand** (no one wanted to buy)
- `units_sold = 0` + `stockout_flag = true` → **Lost sales** (wanted to buy but couldn't)

**Why This Matters:**
- Models need to distinguish between true zero demand and stockouts
- Stockouts indicate **latent demand** (demand that couldn't be fulfilled)
- This affects forecast accuracy and inventory planning

### 2. **Data Quality Rules**

| Rule | Validation | Action |
|------|------------|--------|
| No NULL `units_sold` | `units_sold IS NOT NULL` | Default to 0 |
| No gaps in date series | Check for missing dates | ETL must fill |
| Valid date range | `date_local >= '2020-01-01'` | Reject invalid |
| Valid item_id | `item_id IN (SELECT item_id FROM items)` | Reject invalid |
| Valid location_id | `location_id IN (SELECT location_id FROM locations)` | Reject invalid |
| **Stockout logic** | If `units_sold = 0` AND `stock_on_hand_end > 0`, then `stockout_flag = false` | Validate consistency |
| **Lost sales logic** | If `units_sold = 0` AND `stockout_flag = true`, flag as lost sales | For analysis |

### 3. **Missing Data Handling**

| Column Type | Missing Data Strategy |
|-------------|----------------------|
| **Target Variables** | `units_sold = 0` (zero-demand day) |
| **Inventory State** | **Critical:** If `stock_on_hand_end` is NULL, check `stockout_flag` to determine if it's lost sales |
| **Past Covariates** | Forward-fill last known value (7-day window), else 0 |
| **Future Covariates** | Use planned values, else 0 |
| **Calendar Features** | Always available (derived from date) |
| **Pricing** | Forward-fill last known price, else NULL |

### 4. **Stockout vs Zero Demand Logic**

**ETL Must Set `stockout_flag` Correctly:**

```sql
-- Rule 1: If stock is 0, it's a stockout
UPDATE ts_demand_daily
SET stockout_flag = TRUE
WHERE stock_on_hand_end = 0;

-- Rule 2: If stock is NULL but we know it was out of stock
UPDATE ts_demand_daily
SET stockout_flag = TRUE
WHERE stock_on_hand_end IS NULL 
  AND lost_sales_flag = TRUE;  -- If we have this signal

-- Rule 3: If stock > 0 and units_sold = 0, it's true zero demand
UPDATE ts_demand_daily
SET stockout_flag = FALSE
WHERE stock_on_hand_end > 0 
  AND units_sold = 0;
```

**Forecasting Impact:**

When `units_sold = 0`:
- **If `stockout_flag = false`** → Model treats as true zero demand (no latent demand)
- **If `stockout_flag = true`** → Model should account for latent demand (lost sales)

**Example for Models:**
```python
# When preparing data for forecasting:
if row['units_sold'] == 0 and row['stockout_flag'] == True:
    # This is lost sales - consider using historical average
    # or flagging for special handling
    target_value = estimate_latent_demand(row)
else:
    # True zero demand or normal sales
    target_value = row['units_sold']
```

---

## ETL & Data Sync Requirements

### Data Sources

**Primary Sources:**
1. **Shopify API** → Orders, Products, Inventory
2. **Marketing Platforms** → Ad spend, impressions, clicks
3. **Email Systems** → Email sends, opens
4. **Planning Systems** → Planned promotions, holidays

### ETL Pipeline Steps

1. **Extract** from sources
2. **Transform:**
   - Aggregate to daily grain
   - Generate full daily series (fill gaps)
   - Calculate derived fields (discount_pct, stockout_flag)
   - Engineer calendar features
3. **Load** into `ts_demand_daily`

### Data Sync Strategy

**Two Sync Modes:**

#### 1. **Daily Scheduled Sync** (Primary)
- **Frequency:** Daily (after business day ends)
- **Window:** Process previous day's data
- **Latency:** Data available within 24 hours
- **Use Case:** Regular forecasting cycles, automated reports
- **Trigger:** Scheduled job (Cron, Airflow, etc.)

#### 2. **On-Demand Sync** (Secondary)
- **Frequency:** Triggered by forecast request
- **Window:** Sync latest data before forecast generation
- **Latency:** Real-time (seconds to minutes)
- **Use Case:** Ad-hoc forecasts, urgent requests
- **Trigger:** API request to sync endpoint

### Sync Implementation

**Daily Sync (Recommended):**
```python
# Scheduled job (daily at 2 AM)
@schedule(cron="0 2 * * *")
async def daily_sync():
    """Sync previous day's data"""
    yesterday = date.today() - timedelta(days=1)
    await sync_date_range(
        start_date=yesterday,
        end_date=yesterday
    )
```

**On-Demand Sync:**
```python
# API endpoint
@router.post("/api/v1/data/sync")
async def sync_data_on_demand(
    item_ids: List[str],
    date_range: Optional[DateRange] = None
):
    """Sync data for specific items/date range"""
    await sync_date_range(
        item_ids=item_ids,
        start_date=date_range.start if date_range else None,
        end_date=date_range.end if date_range else None
    )
```

### Sync Behavior

**When Forecast is Requested:**

1. **Check Data Freshness:**
   ```python
   # Check if data is fresh enough
   last_sync_date = get_last_sync_date(item_ids)
   if last_sync_date < date.today() - timedelta(days=1):
       # Data is stale, trigger on-demand sync
       await sync_data_on_demand(item_ids)
   ```

2. **Sync Only Missing Data:**
   ```python
   # Only sync dates that are missing or stale
   missing_dates = get_missing_dates(item_ids, start_date, end_date)
   if missing_dates:
       await sync_date_range(item_ids, missing_dates)
   ```

3. **Proceed with Forecast:**
   ```python
   # After sync, proceed with forecast
   data = await fetch_historical_data(item_ids)
   forecast = await generate_forecast(data)
   ```

### Data Freshness Requirements

| Use Case | Required Freshness | Sync Strategy |
|----------|-------------------|---------------|
| **Automated Forecasts** | 24 hours | Daily sync sufficient |
| **Ad-Hoc Forecasts** | Real-time | On-demand sync |
| **Urgent Decisions** | Minutes | On-demand sync |
| **Historical Analysis** | Any | Daily sync sufficient |

### Performance Considerations

**Daily Sync:**
- ✅ Efficient (batch processing)
- ✅ Predictable load
- ✅ Can run during off-peak hours
- ⚠️ May have stale data for urgent requests

**On-Demand Sync:**
- ✅ Always fresh data
- ✅ Responsive to urgent needs
- ⚠️ Higher load on source systems
- ⚠️ Slower forecast response time

**Hybrid Approach (Recommended):**
- Daily sync for regular updates
- On-demand sync for urgent requests
- Cache sync status to avoid redundant syncs

---

## Usage in Forecasting

### Phase 1 (Current - MVP)

**What We Use:**
```python
# Minimal query (Phase 1)
SELECT 
    item_id,
    date_local,
    units_sold  -- Only target variable
FROM ts_demand_daily
WHERE client_id = ?
  AND item_id IN (?)
  AND date_local >= ?
  AND date_local <= ?
ORDER BY item_id, date_local
```

**Transformed to:**
```python
# Chronos-2 format
{
    "id": "SKU001",
    "timestamp": "2024-01-01",
    "target": 125.5  # units_sold
}
```

### Phase 2 (With Covariates)

**What We'll Use:**
```python
# Full query (Phase 2)
SELECT 
    item_id,
    date_local,
    units_sold,           # Target
    promotion_flag,       # Past covariate
    marketing_spend,      # Past covariate
    holiday_flag,         # Future covariate
    planned_promo_flag,   # Future covariate
    is_weekend,          # Calendar feature
    month_1, ..., month_12  # Calendar features
FROM ts_demand_daily
WHERE client_id = ?
  AND item_id IN (?)
  AND date_local >= ?
  AND date_local <= ?
ORDER BY item_id, date_local
```

**Transformed to:**
```python
# Chronos-2 format with covariates
{
    "id": "SKU001",
    "timestamp": "2024-01-01",
    "target": 125.5,
    "past_covariates": {
        "promotion_flag": 1,
        "marketing_spend": 500.0
    },
    "future_covariates": {
        "holiday_flag": 0,
        "planned_promo_flag": 1
    }
}
```

---

## Data Access Pattern

### Current Implementation

**File:** `backend/forecasting/services/data_access.py`

```python
async def fetch_historical_data(
    self,
    client_id: str,
    item_ids: List[str],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> pd.DataFrame:
    """
    Fetch historical data from ts_demand_daily.
    
    Returns DataFrame with columns:
    - id (item_id)
    - timestamp (date_local)
    - target (units_sold)
    - [covariates...] (Phase 2)
    """
```

### Query Pattern

```sql
SELECT 
    item_id AS id,
    date_local AS timestamp,
    units_sold AS target,
    -- Phase 2: Add covariates
    promotion_flag,
    marketing_spend,
    holiday_flag,
    ...
FROM ts_demand_daily
WHERE client_id = :client_id
  AND item_id = ANY(:item_ids)
  AND date_local >= :start_date
  AND date_local <= :end_date
ORDER BY item_id, date_local
```

---

## Relationship to Forecasting Tables

```
┌─────────────────────┐
│   ts_demand_daily   │  ← INPUT (Historical data)
│   (Source Data)     │
└──────────┬──────────┘
           │
           │ Used to generate forecasts
           │
           ▼
┌─────────────────────┐
│   forecast_runs     │  ← OUTPUT (Forecast metadata)
│   (Forecast Exec)   │
└──────────┬──────────┘
           │
           │ Links to results
           │
           ▼
┌─────────────────────┐
│  forecast_results  │  ← OUTPUT (Predictions)
│  (Daily Forecasts)  │
└─────────────────────┘
```

**Flow:**
1. `ts_demand_daily` → Historical data (input)
2. `forecast_runs` → Forecast execution (metadata)
3. `forecast_results` → Predictions (output)

---

## Validation Checklist

### For ETL Team

- [ ] Full daily series generated (no gaps)
- [ ] Zero-demand days included (`units_sold = 0`)
- [ ] All required columns populated
- [ ] Foreign keys valid (client_id, item_id, location_id)
- [ ] Date range complete (from first sale to today)
- [ ] Missing data handled (forward-fill, defaults)
- [ ] Calendar features calculated
- [ ] Data quality checks passed

### For Forecasting Team

- [ ] Table exists and is populated
- [ ] Data access layer queries correctly
- [ ] Full daily series available
- [ ] Target variable (`units_sold`) is reliable
- [ ] Covariates available (Phase 2)
- [ ] Data quality is acceptable

---

## Summary

**`ts_demand_daily` is the foundation for all forecasting features.**

**Key Points:**
1. ✅ **Full daily series required** (no gaps, include zeros)
2. ✅ **Primary target:** `units_sold`
3. ✅ **Covariates ready** (for Phase 2)
4. ✅ **Data sync:** Daily scheduled OR on-demand (based on forecast requests)
5. ✅ **Data quality critical** (validates forecasting accuracy)

**Sync Strategy:**
- **Daily sync:** Regular updates (recommended for efficiency)
- **On-demand sync:** Triggered by forecast requests (for fresh data)
- **Hybrid approach:** Best of both worlds

**This table is DEFINITELY within forecasting scope** - it's the primary data source that everything depends on.

---

## Next Steps

1. **ETL Team:** Implement full daily series generation
2. **Forecasting Team:** Verify data access layer works with this schema
3. **Data Quality:** Add validation checks
4. **Phase 2:** Use covariates from this table

