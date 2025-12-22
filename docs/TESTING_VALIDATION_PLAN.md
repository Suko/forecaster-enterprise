# Testing & Validation Plan

**Date:** 2025-12-22  
**Status:** Ready for Testing  
**Phase:** Post-Implementation Validation

## Overview

Comprehensive testing plan for Test Bed, ROI Calculator, and all recent changes. This ensures everything works correctly before moving to production.

---

## Pre-Testing Checklist

### Environment Setup

- [ ] Backend running on `http://localhost:8000`
- [ ] Frontend running on `http://localhost:3000`
- [ ] Database connected and migrations applied
- [ ] Test data available (at least 30 days of `ts_demand_daily` data)
- [ ] Authentication working (can log in)

### Test Data Requirements

- [ ] At least 1 location/store
- [ ] At least 1 product/SKU with sales history
- [ ] At least 30 days of historical sales data
- [ ] Multiple products for filtering tests
- [ ] Products in different categories (if testing category filter)

---

## 1. Backend API Testing

### 1.1 Forecast API Endpoints

#### Test: Generate Forecast (Basic)
```bash
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["test-item-1"],
    "prediction_length": 30,
    "model": "chronos-2",
    "include_baseline": true
  }'
```

**Expected:**
- ✅ Status: 201 Created
- ✅ Response includes `forecast_id`
- ✅ Response includes `forecasts` array
- ✅ Forecast has predictions for 30 days

#### Test: Generate Forecast (Test Bed Mode)
```bash
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["test-item-1"],
    "prediction_length": 30,
    "model": "chronos-2",
    "include_baseline": true,
    "run_all_methods": true,
    "skip_persistence": true,
    "training_end_date": "2024-11-01"
  }'
```

**Expected:**
- ✅ Status: 201 Created
- ✅ Response includes forecasts for ALL methods (chronos-2, statistical_ma7, sba, croston, min_max)
- ✅ No database entries created (skip_persistence=true)
- ✅ Forecasts start from training_end_date + 1

#### Test: Get Available Models
```bash
curl http://localhost:8000/api/v1/forecast/models \
  -H "Authorization: Bearer <token>"
```

**Expected:**
- ✅ Status: 200 OK
- ✅ Returns list of available models
- ✅ Includes: chronos-2, statistical_ma7, sba, croston, min_max

#### Test: Get Historical Date Range
```bash
curl "http://localhost:8000/api/v1/forecast/date-range?item_id=test-item-1" \
  -H "Authorization: Bearer <token>"
```

**Expected:**
- ✅ Status: 200 OK
- ✅ Returns `min_date` and `max_date`
- ✅ Dates are valid (YYYY-MM-DD format)

#### Test: Get Historical Data
```bash
curl "http://localhost:8000/api/v1/forecast/historical?item_id=test-item-1" \
  -H "Authorization: Bearer <token>"
```

**Expected:**
- ✅ Status: 200 OK
- ✅ Returns array of historical data points
- ✅ Each point has `date` and `units_sold`
- ✅ At least 30 days of data

#### Test: Get Quality Metrics
```bash
curl "http://localhost:8000/api/v1/forecast/quality/test-item-1?forecast_run_id=<id>" \
  -H "Authorization: Bearer <token>"
```

**Expected:**
- ✅ Status: 200 OK
- ✅ Returns quality metrics for each method
- ✅ Includes MAPE, RMSE, MAE, Bias
- ✅ Includes sample counts

### 1.2 SKU Classification

#### Test: Classification in Forecast Response
- Generate forecast and check response includes `classification` field
- Verify `classification.recommended_method` is present
- Verify ABC-XYZ classes are correct

**Expected:**
- ✅ Classification included in forecast response
- ✅ Recommended method matches SKU characteristics
- ✅ ABC class (A, B, or C)
- ✅ XYZ class (X, Y, or Z)
- ✅ Demand pattern (regular, intermittent, or lumpy)

---

## 2. Frontend UI Testing

### 2.1 Test Bed Page (`/experiments/testbed`)

#### Test: Page Loads
- [ ] Navigate to `/experiments/testbed`
- [ ] Page loads without errors
- [ ] All UI components render correctly

**Expected:**
- ✅ No console errors
- ✅ Filters visible (Location, Category, SKU)
- ✅ Forecast configuration visible
- ✅ Chart area visible (empty initially)

#### Test: Filters Work

**Location Filter:**
- [ ] Select "All Stores" → Products from all locations shown
- [ ] Select specific location → Only products from that location shown
- [ ] Dropdown populates correctly

**Category Filter:**
- [ ] Select "All Categories" → All products shown
- [ ] Select specific category → Only products in that category shown
- [ ] Dropdown populates correctly

**SKU/Product Filter:**
- [ ] Dropdown shows all available products
- [ ] Product names are not truncated (should see full names)
- [ ] Can select a product

**Expected:**
- ✅ All filters work independently
- ✅ Filters combine correctly (AND logic)
- ✅ Product dropdown shows full names

#### Test: Forecast Generation

**Basic Flow:**
1. [ ] Select a product
2. [ ] Select forecast model (e.g., "Chronos-2")
3. [ ] Set forecast horizon (e.g., 30 days)
4. [ ] Click "Generate Forecast & Compare"
5. [ ] Wait for forecast to generate

**Expected:**
- ✅ Loading state shows during generation
- ✅ Chart displays after generation
- ✅ No errors in console
- ✅ Chart shows historical data
- ✅ Chart shows forecast line
- ✅ Chart shows actual data (if available for backtesting)

#### Test: Chart Functionality

**Chart Display:**
- [ ] Historical data line visible (blue)
- [ ] Forecast line visible (dashed, colored by model)
- [ ] Actual data line visible (if backtesting)
- [ ] Dates on x-axis correct
- [ ] Values on y-axis reasonable

**Chart Interactions:**
- [ ] **Zoom:** Mouse wheel zooms in/out
- [ ] **Pan:** Ctrl+drag pans chart
- [ ] **Reset Zoom:** Button appears when zoomed, clicking resets
- [ ] **Hover:** Tooltip shows values on hover

**Expected:**
- ✅ All chart elements visible
- ✅ Zoom works (wheel, pinch)
- ✅ Pan works (Ctrl+drag)
- ✅ Reset zoom button functional
- ✅ Tooltips show correct values

#### Test: Rolling Average

**Toggle:**
- [ ] Toggle "Show Rolling Average" on/off
- [ ] Rolling average line appears/disappears

**Window Selection:**
- [ ] Change rolling average window (3, 7, 14, 30 days)
- [ ] Chart updates immediately (no regeneration needed)

**Expected:**
- ✅ Toggle works instantly
- [ ] Window changes update chart live
- ✅ Rolling average line smooths historical data

#### Test: Model Comparison Table

**Table Display:**
- [ ] Table appears after forecast generation
- [ ] Shows all methods that were run
- [ ] Columns: Model, MAPE, RMSE, MAE, Bias, Samples, System Recommendation

**Metrics:**
- [ ] MAPE shown as percentage (e.g., "39.0%")
- [ ] RMSE and MAE shown as numbers (e.g., "1.75")
- [ ] Bias shown as number (e.g., "-0.17")
- [ ] Samples count matches forecast horizon (if all actuals available)

**System Recommendation:**
- [ ] Green badge shows on recommended method
- [ ] "✓ System Choice" appears in recommendation column
- [ ] Recommendation matches SKU classification

**Expected:**
- ✅ Table shows all methods
- ✅ Metrics are formatted correctly
- ✅ System recommendation highlighted
- ✅ Sample counts are reasonable

#### Test: Model Selector for Chart

**Model Selection:**
- [ ] Select different model from dropdown (near rolling average)
- [ ] Chart forecast line updates
- [ ] Metrics in header update (MAPE, RMSE, MAE)
- [ ] Forecasted sales and actual sales update

**Expected:**
- ✅ Chart updates when model changes
- ✅ Metrics update correctly
- ✅ No page reload needed
- ✅ Smooth transition

#### Test: SKU Classification Display

**Classification Card:**
- [ ] Card appears after forecast generation
- [ ] Shows ABC classification (A, B, or C)
- [ ] Shows XYZ classification (X, Y, or Z)
- [ ] Shows demand pattern (regular, intermittent, lumpy)
- [ ] Shows forecastability score (0-100%)
- [ ] Shows system recommended method
- [ ] Shows expected MAPE range

**Expected:**
- ✅ All classification fields visible
- ✅ Values are correct
- ✅ Recommended method matches table badge
- ✅ Explanations are clear

#### Test: Metrics Header

**Metrics Display:**
- [ ] MAPE shown in header (top right of chart)
- [ ] RMSE shown in header
- [ ] MAE shown in header
- [ ] Forecasted sales total shown
- [ ] Actual sales total shown

**Metrics Update:**
- [ ] When changing model, metrics update
- [ ] Forecasted sales changes with model
- [ ] Actual sales stays constant (doesn't change with model)

**Expected:**
- ✅ All metrics visible
- ✅ Metrics update when model changes
- ✅ Actual sales is constant (true historical value)
- ✅ Formatting is correct (percentages, decimals)

#### Test: Error Handling

**No Data:**
- [ ] Select product with no historical data
- [ ] Error message shown
- [ ] No crash

**API Errors:**
- [ ] Simulate API error (stop backend)
- [ ] Error message shown
- [ ] No crash

**Expected:**
- ✅ Graceful error messages
- ✅ No console errors
- ✅ User can retry

### 2.2 ROI Calculator Page (`/experiments/roi-calculator`)

#### Test: Page Loads
- [ ] Navigate to `/experiments/roi-calculator`
- [ ] Page loads without errors
- [ ] All sliders visible

#### Test: Sliders Work
- [ ] Annual revenue slider (€500K - €50M)
- [ ] Inventory distortion slider (10-30%)
- [ ] Current MAPE slider (20-60%)
- [ ] Improved MAPE slider (5-50%)

**Expected:**
- ✅ All sliders functional
- ✅ Values update in real-time
- ✅ Calculations update automatically

#### Test: Calculations
- [ ] Change slider values
- [ ] Cost comparison updates
- [ ] Annual savings updates
- [ ] Charts update

**Expected:**
- ✅ Calculations are correct
- ✅ Charts reflect changes
- ✅ Currency formatting correct (EUR)

### 2.3 Navigation

#### Test: Experiments Tab
- [ ] Click "Experiments" in main navigation
- [ ] Navigate to Test Bed
- [ ] Navigate to ROI Calculator
- [ ] Tab switching works

**Expected:**
- ✅ Navigation works
- ✅ Active tab highlighted
- ✅ URL updates correctly

---

## 3. Integration Testing

### 3.1 End-to-End Test Bed Flow

**Complete Workflow:**
1. [ ] Log in
2. [ ] Navigate to Test Bed
3. [ ] Select location (optional)
4. [ ] Select category (optional)
5. [ ] Select product
6. [ ] Select forecast model
7. [ ] Set forecast horizon
8. [ ] Generate forecast
9. [ ] Verify chart displays
10. [ ] Verify classification card shows
11. [ ] Verify comparison table shows
12. [ ] Change model selector
13. [ ] Verify chart updates
14. [ ] Toggle rolling average
15. [ ] Change rolling average window
16. [ ] Zoom chart
17. [ ] Reset zoom

**Expected:**
- ✅ All steps complete without errors
- ✅ Data flows correctly
- ✅ UI updates responsively
- ✅ No console errors

### 3.2 Backtesting Validation

**Test Backtesting Logic:**
1. [ ] Select product with 60+ days of history
2. [ ] Set forecast horizon to 30 days
3. [ ] Generate forecast
4. [ ] Verify cutoff date is calculated (latest_date - 30)
5. [ ] Verify forecast starts from cutoff + 1
6. [ ] Verify actuals are backfilled for forecast period
7. [ ] Verify quality metrics are calculated
8. [ ] Verify metrics are reasonable

**Expected:**
- ✅ Cutoff date calculated correctly
- ✅ Forecast dates overlap with actuals
- ✅ Quality metrics calculated
- ✅ Sample count matches available actuals

### 3.3 Multi-Method Comparison

**Test All Methods:**
1. [ ] Generate forecast with `run_all_methods=true`
2. [ ] Verify all 5 methods appear in table:
   - Chronos-2
   - Moving Average (7-day)
   - SBA
   - Croston
   - Min-Max
3. [ ] Verify each method has metrics
4. [ ] Verify system recommendation is highlighted
5. [ ] Switch between methods in chart
6. [ ] Verify each method's forecast displays correctly

**Expected:**
- ✅ All methods appear
- ✅ All methods have metrics
- ✅ System recommendation correct
- ✅ Chart switching works for all methods

---

## 4. Data Validation

### 4.1 Forecast Data Quality

**Check Forecast Values:**
- [ ] Forecast values are not all the same (for ML models)
- [ ] Statistical models may have constant values (expected)
- [ ] No negative forecast values
- [ ] No NaN or null values
- [ ] Forecast dates are sequential
- [ ] No gaps in forecast dates

**Expected:**
- ✅ Values are reasonable
- ✅ No invalid data
- ✅ Dates are correct

### 4.2 Quality Metrics Validation

**Check Metrics:**
- [ ] MAPE is between 0-100% (or reasonable for SKU type)
- [ ] RMSE is positive
- [ ] MAE is positive
- [ ] Bias can be positive or negative
- [ ] Sample count matches available actuals

**Cross-Validation:**
- [ ] Compare MAPE with manual calculation
- [ ] Verify metrics match backend calculation
- [ ] Check if metrics are reasonable for SKU classification

**Expected:**
- ✅ Metrics are valid
- ✅ Metrics match backend
- ✅ Metrics are reasonable for SKU type

### 4.3 Classification Validation

**Check Classification:**
- [ ] ABC class matches revenue ranking
- [ ] XYZ class matches variability (CV)
- [ ] Demand pattern matches ADI and CV²
- [ ] Recommended method matches classification rules
- [ ] Forecastability score is 0-100%

**Expected:**
- ✅ Classification is correct
- ✅ Recommendation matches rules
- ✅ Score is reasonable

---

## 5. Performance Testing

### 5.1 Forecast Generation Speed

**Test Generation Time:**
- [ ] Single method forecast: < 10 seconds
- [ ] All methods forecast: < 60 seconds
- [ ] No timeout errors
- [ ] UI remains responsive during generation

**Expected:**
- ✅ Generation completes in reasonable time
- ✅ No timeouts
- ✅ UI doesn't freeze

### 5.2 Chart Rendering

**Test Chart Performance:**
- [ ] Chart renders quickly (< 1 second)
- [ ] Zoom/pan is smooth
- [ ] No lag when switching models
- [ ] No lag when toggling rolling average

**Expected:**
- ✅ Smooth interactions
- ✅ No performance issues

### 5.3 Large Dataset Handling

**Test with Large Data:**
- [ ] 100+ days of historical data
- [ ] Multiple products
- [ ] All methods comparison
- [ ] Verify no memory issues
- [ ] Verify no slowdown

**Expected:**
- ✅ Handles large datasets
- ✅ No memory leaks
- ✅ Performance acceptable

---

## 6. Browser Compatibility

### 6.1 Test in Multiple Browsers

- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on Mac)

**Expected:**
- ✅ Works in all modern browsers
- ✅ No browser-specific errors

---

## 7. Error Scenarios

### 7.1 Network Errors

- [ ] Disconnect network during forecast generation
- [ ] Verify error message shown
- [ ] Verify can retry

### 7.2 Invalid Data

- [ ] Select product with no data
- [ ] Set invalid forecast horizon (negative, too large)
- [ ] Verify validation errors

### 7.3 Backend Errors

- [ ] Stop backend server
- [ ] Try to generate forecast
- [ ] Verify error handling

**Expected:**
- ✅ All errors handled gracefully
- ✅ User-friendly error messages
- ✅ No crashes

---

## 8. Documentation Validation

### 8.1 Check Documentation

- [ ] Test Bed System Validation guide is accurate
- [ ] Inventory Ordering Guide is accurate
- [ ] Metrics Best Practices guide is accurate
- [ ] API Reference is up-to-date
- [ ] Migration Plan marked as complete

**Expected:**
- ✅ All docs accurate
- ✅ Examples work
- ✅ No outdated information

---

## 9. Security Testing

### 9.1 Authentication

- [ ] Test Bed requires authentication
- [ ] Unauthenticated users can't access
- [ ] API calls include auth tokens

### 9.2 Data Isolation

- [ ] User A can't see User B's data
- [ ] Client isolation works correctly
- [ ] Forecasts are scoped to client

**Expected:**
- ✅ Authentication required
- ✅ Data isolation correct
- ✅ No security issues

---

## 10. Regression Testing

### 10.1 Existing Features Still Work

- [ ] Dashboard still works
- [ ] Inventory page still works
- [ ] Purchase orders still work
- [ ] Settings still work
- [ ] All existing features functional

**Expected:**
- ✅ No regressions
- ✅ All existing features work

---

## Test Execution Checklist

### Quick Smoke Test (5 minutes)
- [ ] Backend starts
- [ ] Frontend starts
- [ ] Can log in
- [ ] Can navigate to Test Bed
- [ ] Can generate a forecast
- [ ] Chart displays

### Full Test Suite (30-60 minutes)
- [ ] Complete all sections above
- [ ] Document any issues found
- [ ] Verify fixes

### Production Readiness (Before Deploy)
- [ ] All tests pass
- [ ] No critical bugs
- [ ] Performance acceptable
- [ ] Documentation complete
- [ ] Security validated

---

## Test Results Template

```markdown
## Test Results - [Date]

### Backend API
- [ ] Forecast generation: PASS/FAIL
- [ ] Test Bed mode: PASS/FAIL
- [ ] Quality metrics: PASS/FAIL
- [ ] Classification: PASS/FAIL

### Frontend UI
- [ ] Test Bed page: PASS/FAIL
- [ ] Chart functionality: PASS/FAIL
- [ ] Model comparison: PASS/FAIL
- [ ] ROI Calculator: PASS/FAIL

### Integration
- [ ] End-to-end flow: PASS/FAIL
- [ ] Backtesting: PASS/FAIL
- [ ] Multi-method: PASS/FAIL

### Issues Found
1. [Issue description]
2. [Issue description]

### Notes
[Any observations or recommendations]
```

---

## Next Steps After Testing

1. **Fix Critical Issues:** Address any blocking bugs
2. **Document Issues:** Create tickets for non-critical issues
3. **Performance Optimization:** If performance issues found
4. **User Acceptance:** Get stakeholder approval
5. **Deployment:** Deploy to staging/production

---

## Quick Test Commands

### Backend Health Check
```bash
curl http://localhost:8000/health
```

### Frontend Health Check
```bash
curl http://localhost:3000/api/health
```

### Generate Test Forecast (via API)
```bash
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "item_ids": ["<your-item-id>"],
    "prediction_length": 30,
    "model": "chronos-2",
    "run_all_methods": true,
    "skip_persistence": true
  }'
```

---

## 10. Data Validation Testing

**Purpose:** Verify that all displayed data is mathematically correct and matches backend calculations.

### 10.1 Quality Metrics Validation

#### Test: MAPE Calculation Accuracy
- **Formula:** `MAPE = (100/n) × Σ|Actual - Forecast|/Actual`
- **Steps:**
  1. Generate forecast with known actuals
  2. Extract actuals and forecasts from API
  3. Manually calculate MAPE
  4. Compare with displayed MAPE
- **Expected:** Frontend MAPE = Backend MAPE (within 0.1% tolerance)

#### Test: RMSE Calculation Accuracy
- **Formula:** `RMSE = √[(1/n) × Σ(Actual - Forecast)²]`
- **Expected:** Frontend RMSE = Backend RMSE (within 0.01 tolerance)

#### Test: MAE Calculation Accuracy
- **Formula:** `MAE = (1/n) × Σ|Actual - Forecast|`
- **Expected:** Frontend MAE = Backend MAE (within 0.01 tolerance)

#### Test: Bias Calculation Accuracy
- **Formula:** `Bias = (1/n) × Σ(Forecast - Actual)`
- **Expected:** Frontend Bias = Backend Bias (within 0.01 tolerance)

**Status:** ✅ **VERIFIED** - All formulas match between frontend and backend (see `docs/TEST_BED_FEATURE_SUMMARY.md` for details)

### 10.2 Forecast Data Validation

#### Test: Forecast Date Alignment
- Verify forecast start date = `training_end_date + 1`
- Verify all forecast dates are sequential
- Verify no date overlaps with training data

#### Test: Forecast Value Totals
- Sum all `point_forecast` values
- Compare with displayed "Forecasted" total in header
- **Expected:** Sum = Header value

#### Test: Actual Value Totals
- Sum all `actual_value` values
- Compare with displayed "Actual" total in header
- **Expected:** Sum = Header value

#### Test: Sample Count Validation
- Count number of forecast-actual pairs
- Compare with displayed "Samples" in table
- **Expected:** Sample count = Number of matching dates

### 10.3 SKU Classification Validation

#### Test: ABC Classification
- Get revenue data for all products
- Calculate ABC class manually (A=top 80%, B=next 15%, C=bottom 5%)
- Compare with displayed ABC class

#### Test: XYZ Classification
- Calculate Coefficient of Variation (CV = std/mean)
- Classify: X (CV<0.5), Y (0.5≤CV<1.0), Z (CV≥1.0)
- Compare with displayed XYZ class

#### Test: Demand Pattern
- Calculate ADI and CV²
- Classify: Regular (ADI≤1.32), Intermittent (ADI>1.32), Lumpy (ADI>1.32 & CV²>0.49)
- Compare with displayed demand pattern

#### Test: Recommended Method
- Apply recommendation rules based on ABC-XYZ and demand pattern
- Compare with displayed recommended method

**See:** `docs/DATA_VALIDATION_TEST_PLAN.md` for detailed validation steps (archived - content merged here)

---

**Ready to start testing?** Begin with the Quick Smoke Test, then proceed through each section systematically.

