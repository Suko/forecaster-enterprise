# Covariates Implementation Roadmap

**Date:** 2025-12-06  
**Status:** ⏳ **Planned for Phase 2**  
**Current Phase:** Phase 1 (MVP) - No covariates yet

---

## Quick Answer

**Covariates will be implemented in Phase 2** (after MVP is complete and in production).

**Timeline:**
- **Phase 1 (Current):** ✅ No covariates - Simple time series forecasting
- **Phase 2 (Next):** ⏳ Add covariate support - Improve forecast accuracy
- **Phase 3 (Future):** 🔮 Advanced covariates - External data, ML features

---

## Current State (Phase 1 - MVP)

### ✅ What Works Now

**No covariates - pure time series forecasting:**
- Chronos-2 uses only historical sales (`target` column)
- MovingAverage uses only historical sales
- Simple, fast, reliable

**Data Format (Current):**
```python
# What we send to models now:
{
    "id": "SKU001",
    "timestamp": "2024-01-01",
    "target": 125.5  # Only sales data
}
```

### ⚠️ What's Missing

- ❌ No promotion flags
- ❌ No holiday indicators
- ❌ No marketing spend
- ❌ No price/discount data
- ❌ No calendar features (weekend, month, etc.)

**Impact:** Forecasts are less accurate for items affected by promotions, holidays, or marketing campaigns.

---

## Phase 2: Covariate Implementation

### When Will We Start?

**After Phase 1 is in production:**
1. ✅ Phase 1 complete (current)
2. ✅ Production deployment
3. ✅ Baseline accuracy established
4. ⏳ **Then start Phase 2 with covariates**

**Estimated Start:** After 2-4 weeks of Phase 1 production use

### What Will Be Added

#### 1. **Features Layer** (`forecasting/features/`)

```
forecasting/
└── features/
    ├── __init__.py
    ├── covariates/
    │   ├── __init__.py
    │   ├── holiday.py          # Holiday covariates
    │   ├── promo.py             # Promotion covariates
    │   ├── marketing.py         # Marketing spend covariates
    │   └── calendar.py          # Calendar features (weekend, month)
    └── service.py               # CovariateService (orchestrates all)
```

#### 2. **Covariate Types**

**Past Covariates (Observed):**
- `promotion_flag` (0/1)
- `promotion_type` (string: "sale", "bogo", etc.)
- `discount_pct` (0-100)
- `marketing_spend` (dollars)
- `email_sends`, `email_opens`
- `stock_on_hand_end` (inventory level)

**Future Covariates (Known):**
- `holiday_flag` (0/1)
- `holiday_type` (string: "christmas", "black_friday", etc.)
- `planned_promo_flag` (0/1)
- `planned_promo_type` (string)
- `seasonal_indicator` (0-1)

**Calendar Features (Engineered):**
- `is_weekend` (0/1)
- `month_1` through `month_12` (one-hot)
- `day_of_week` (1-7)
- `week_of_year` (1-52)
- `peak_season_flag` (0/1)

#### 3. **Data Flow with Covariates**

```
┌─────────────────────────────────────────────────────────┐
│                    ts_demand_daily                        │
│  (ETL-populated table with covariates)                   │
│                                                           │
│  Columns:                                                │
│  - units_sold (target)                                   │
│  - promotion_flag                                        │
│  - holiday_flag                                          │
│  - marketing_spend                                       │
│  - discount_pct                                          │
│  - ... (all covariates)                                  │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              DataAccess.fetch_historical_data()          │
│  - Fetches target + covariates                          │
│  - Returns DataFrame with all columns                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              CovariateService.prepare()                  │
│                                                           │
│  1. Validate covariates                                 │
│  2. Handle missing data (forward-fill, default to 0)   │
│  3. Handle outliers (cap at 3× median)                  │
│  4. Engineer features (lags, interactions)              │
│  5. Separate past vs future covariates                   │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Chronos2Model.predict()                     │
│                                                           │
│  Input:                                                  │
│  - context_df: target + past_covariates                 │
│  - future_covariates_df: future_covariates              │
│                                                           │
│  Output:                                                 │
│  - Forecast with improved accuracy                       │
└─────────────────────────────────────────────────────────┘
```

#### 4. **Implementation Steps**

**Step 1: Database Schema** (Already exists!)
- ✅ `ts_demand_daily` table already has covariate columns
- ✅ ETL should populate them (if not already)

**Step 2: Create Features Layer**
```python
# forecasting/features/covariates/holiday.py
class HolidayCovariate:
    def prepare_past_covariates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract holiday flags from historical data"""
        # Return DataFrame with holiday_flag, holiday_type columns
    
    def prepare_future_covariates(self, start_date, end_date) -> pd.DataFrame:
        """Generate future holiday flags (known in advance)"""
        # Return DataFrame with holiday_flag, holiday_type for future dates
```

**Step 3: Update DataAccess**
```python
# forecasting/services/data_access.py
async def fetch_historical_data(self, ...):
    # Already fetches all columns from ts_demand_daily
    # Just need to ensure covariates are included
    return df  # Contains target + all covariates
```

**Step 4: Create CovariateService**
```python
# forecasting/features/service.py
class CovariateService:
    def prepare_covariates(
        self,
        historical_df: pd.DataFrame,
        prediction_length: int
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Prepare past and future covariates.
        
        Returns:
            past_covariates_df: Historical covariates
            future_covariates_df: Future covariates (known in advance)
        """
```

**Step 5: Update ForecastService**
```python
# forecasting/services/forecast_service.py
async def generate_forecast(...):
    # 1. Fetch historical data (with covariates)
    context_df = await self.data_access.fetch_historical_data(...)
    
    # 2. Prepare covariates
    past_covariates, future_covariates = await self.covariate_service.prepare_covariates(
        context_df, prediction_length
    )
    
    # 3. Run model with covariates
    predictions = await model.predict(
        context_df=context_df,
        future_covariates_df=future_covariates,
        ...
    )
```

**Step 6: Update Chronos2Model**
```python
# forecasting/modes/ml/chronos2.py
async def predict(
    self,
    context_df: pd.DataFrame,
    prediction_length: int,
    future_covariates_df: Optional[pd.DataFrame] = None,  # ✅ Already supported!
    ...
):
    # Chronos-2 already supports covariates!
    # Just need to pass them correctly
```

#### 5. **Covariate Handling Rules**

**Missing Data:**
- **Past Covariates**: Forward-fill last known value (if within 7 days), else 0
- **Future Covariates**: Use planned values (if available), else 0
- **Calendar Features**: Always available (derived from date)

**Outlier Handling:**
- **Marketing Spend**: Cap at 3× median (prevent extreme values)
- **Discount %**: Cap at 100% (prevent negative prices)
- **Price**: Flag if > 5× median (data quality issue)

**Feature Engineering:**
- **Lag Features**: 7-day, 30-day moving averages
- **Interaction Features**: `promotion_flag × discount_pct`
- **Temporal Features**: Day of week, week of year

---

## Phase 3: Advanced Covariates (Future)

### External Data Sources
- Weather data (temperature, precipitation)
- Economic indicators (GDP, unemployment)
- Competitor pricing
- Social media sentiment
- News events

### ML-Generated Features
- Trend detection
- Seasonality decomposition
- Anomaly scores
- Clustering features

---

## Why Not in Phase 1?

### Reasons for Deferring Covariates

1. **Simplicity First**
   - MVP focuses on core forecasting
   - Covariates add complexity
   - Can validate core system first

2. **Data Requirements**
   - Need ETL to populate covariates
   - Need data quality checks
   - Need validation logic

3. **Incremental Value**
   - Pure time series works well for many items
   - Covariates help most for promotional items
   - Can measure improvement after baseline

4. **Development Speed**
   - Phase 1 faster without covariates
   - Can ship MVP sooner
   - Add covariates when needed

### When Covariates Become Critical

**Add covariates when:**
- ✅ Phase 1 is stable in production
- ✅ Baseline accuracy is measured
- ✅ Items with promotions show poor accuracy
- ✅ ETL is ready to populate covariates
- ✅ Data quality is validated

---

## Current Data Support

### ✅ What's Already Available

**Test Data:**
- ✅ `synthetic_ecom_chronos2_demo.csv` includes covariates:
  - `promo_flag`
  - `holiday_flag`
  - `is_weekend`
  - `marketing_index`

**Database Schema:**
- ✅ `ts_demand_daily` table designed with covariate columns
- ✅ Ready for ETL to populate

**Model Support:**
- ✅ Chronos-2 supports covariates (via `future_covariates_df` parameter)
- ✅ `BaseForecastModel` interface supports covariates

### ⚠️ What's Missing

- ❌ Features layer (`forecasting/features/`)
- ❌ CovariateService
- ❌ Covariate preparation logic
- ❌ Missing data handling for covariates
- ❌ Outlier handling for covariates
- ❌ Integration in ForecastService

---

## Implementation Estimate

### Phase 2 Covariates (Full Implementation)

**Time Estimate:** 1-2 weeks

| Task | Time | Complexity |
|------|------|------------|
| Create features layer structure | 2 hours | Low |
| Implement HolidayCovariate | 4 hours | Low |
| Implement PromoCovariate | 4 hours | Low |
| Implement MarketingCovariate | 4 hours | Medium |
| Implement CalendarCovariate | 2 hours | Low |
| Create CovariateService | 4 hours | Medium |
| Update ForecastService | 4 hours | Medium |
| Update DataAccess | 2 hours | Low |
| Missing data handling | 4 hours | Medium |
| Outlier handling | 4 hours | Medium |
| Unit tests | 8 hours | Medium |
| Integration tests | 4 hours | Medium |
| **Total** | **46 hours** | **~1-2 weeks** |

---

## Quick Start: Minimal Covariates (Phase 2.1)

**If you want to add covariates quickly:**

**Minimal Implementation (1 week):**
1. ✅ Use existing covariates from `ts_demand_daily`
2. ✅ Simple forward-fill for missing data
3. ✅ Pass to Chronos-2 directly (no feature engineering)
4. ✅ Test with promotional items

**This gives you:**
- ✅ Promotion-aware forecasts
- ✅ Holiday-aware forecasts
- ✅ ~80% of the value with 20% of the effort

**Then enhance later:**
- Feature engineering
- Advanced missing data handling
- Outlier detection
- ML-generated features

---

## Summary

| Question | Answer |
|----------|--------|
| **When?** | Phase 2 (after Phase 1 is in production) |
| **Why not now?** | Simplicity, speed, validate core first |
| **What's needed?** | Features layer, CovariateService, integration |
| **How long?** | 1-2 weeks for full implementation |
| **Quick start?** | 1 week for minimal covariates |
| **Current support?** | ✅ Data schema ready, ✅ Model supports it, ✅ Test data has it |
| **⚠️ Important:** | Covariates don't always help - see [Covariate Management](COVARIATE_MANAGEMENT.md) |

**Recommendation:** Complete Phase 1, deploy to production, measure baseline accuracy, then add covariates in Phase 2 when you can measure the improvement.

**⚠️ Critical:** Covariates can sometimes hurt accuracy. See [Covariate Management Strategy](COVARIATE_MANAGEMENT.md) for how to handle this.

---

## Next Steps

1. **Complete Phase 1** ✅ (Current)
2. **Deploy to Production** ⏳ (Next)
3. **Measure Baseline Accuracy** ⏳ (After deployment)
4. **Start Phase 2: Covariates** ⏳ (When ready)

**Files to Create (Phase 2):**
- `forecasting/features/__init__.py`
- `forecasting/features/covariates/__init__.py`
- `forecasting/features/covariates/holiday.py`
- `forecasting/features/covariates/promo.py`
- `forecasting/features/covariates/marketing.py`
- `forecasting/features/covariates/calendar.py`
- `forecasting/features/service.py`

