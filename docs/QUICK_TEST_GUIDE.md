# Quick Test Guide - Test Bed Validation

**For:** Quick validation of Test Bed functionality  
**Time:** 10-15 minutes

## Prerequisites

```bash
# 1. Start backend
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 2. Start frontend (new terminal)
cd frontend
bun run dev
```

## Quick Test Steps

### 1. Login & Navigate (1 min)
- [ ] Open `http://localhost:3000`
- [ ] Log in
- [ ] Click "Experiments" in navigation
- [ ] Click "Test Bed" tab

### 2. Basic Forecast (2 min)
- [ ] Select a product from dropdown
- [ ] Select "Chronos-2" model
- [ ] Set horizon to 30 days
- [ ] Click "Generate Forecast & Compare"
- [ ] Wait for chart to appear

**✅ Success:** Chart shows historical + forecast lines

### 3. Check Classification (1 min)
- [ ] Verify classification card appears below chart
- [ ] Check ABC-XYZ classification is shown
- [ ] Check system recommendation badge

**✅ Success:** Classification card visible with correct info

### 4. Check Comparison Table (1 min)
- [ ] Verify table appears below classification
- [ ] Check all methods are listed
- [ ] Check metrics (MAPE, RMSE, MAE) are shown
- [ ] Check system recommendation is highlighted

**✅ Success:** Table shows all methods with metrics

### 5. Test Model Switching (2 min)
- [ ] Change model selector (near rolling average)
- [ ] Verify chart forecast line updates
- [ ] Verify header metrics (MAPE, RMSE, MAE) update
- [ ] Verify forecasted/actual sales update

**✅ Success:** Chart and metrics update when model changes

### 6. Test Rolling Average (1 min)
- [ ] Toggle "Show Rolling Average" on/off
- [ ] Change rolling average window (7, 14, 30 days)
- [ ] Verify chart updates immediately

**✅ Success:** Rolling average toggles and updates live

### 7. Test Chart Interactions (2 min)
- [ ] **Zoom:** Scroll mouse wheel on chart
- [ ] **Pan:** Hold Ctrl and drag chart
- [ ] **Reset:** Click "Reset Zoom" button
- [ ] **Hover:** Hover over data points to see tooltips

**✅ Success:** All interactions work smoothly

### 8. Test Backtesting (3 min)
- [ ] Select product with 60+ days of history
- [ ] Generate forecast with 30-day horizon
- [ ] Verify actual data line appears on chart
- [ ] Verify quality metrics are calculated (not N/A)
- [ ] Check sample count in table matches forecast horizon

**✅ Success:** Backtesting works, metrics are calculated

### 9. Test All Methods (2 min)
- [ ] Generate new forecast (should run all methods automatically)
- [ ] Verify table shows 5 methods:
  - Chronos-2
  - Moving Average (7-day)
  - SBA
  - Croston
  - Min-Max
- [ ] Switch between methods in chart
- [ ] Verify each method's forecast displays

**✅ Success:** All methods appear and can be switched

## Common Issues & Fixes

### Issue: "No forecast generated"
**Fix:** Check backend is running, check product has data

### Issue: "MAPE N/A"
**Fix:** Ensure backtesting is working (actuals available for forecast period)

### Issue: Chart not updating
**Fix:** Check browser console for errors, verify API calls succeed

### Issue: Only 2 methods in table
**Fix:** Verify `run_all_methods=true` is being sent (check Network tab)

## Success Criteria

✅ All 9 steps complete without errors  
✅ Chart displays correctly  
✅ Metrics are calculated  
✅ Model switching works  
✅ No console errors  

## If Everything Works

🎉 **Test Bed is ready!** Proceed to full testing suite or deployment.

## If Issues Found

1. Note the issue
2. Check browser console for errors
3. Check backend logs
4. Refer to full testing plan for detailed validation

---

## Recent Backend Fixes (2025-12-29)

Completed changes:
- Fixed multi-tenant scoping issues in cart/PO/inventory response lookups (ensures `client_id` is always applied).
- Fixed cart → purchase-order flow to use a consistent `session_id` for authenticated users.
- Fixed Sentry startup crash (`os` import).
- Hardened purchase-order creation:
  - PO number generation no longer uses `count+1` (avoids concurrency races).
  - Cart → PO creation is now transactional (PO + cart cleanup commit together).
- ETL performance/consistency improvements (batched upserts, transactional replace for sales history).

How to re-run key tests (from repo root):
- Use `backend/.venv/bin/pytest` (plain `pytest` may run under your system Python and fail due to missing deps like `aiosqlite`).
- `backend/.venv/bin/pytest -q backend/tests/test_services/test_purchase_order_service.py`
- `backend/.venv/bin/pytest -q backend/tests/test_services/test_etl_service.py`
