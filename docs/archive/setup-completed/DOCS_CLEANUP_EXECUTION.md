# Documentation Cleanup - Execution Plan

**Date:** 2025-12-22  
**Goal:** Archive completed/setup docs, consolidate redundant docs

---

## Files to Archive (One-Time Setup/Completion Docs)

These are completed tasks or one-time setup guides that can be archived:

1. ✅ `CLEANUP_SUMMARY.md` → `archive/` (cleanup completed)
2. ✅ `CLEANUP_AND_SEPARATION_PLAN.md` → `archive/` (separation completed)
3. ✅ `NESTED_REPO_SETUP.md` → `archive/` (setup completed)
4. ✅ `NESTED_REPO_STATUS.md` → `archive/` (status snapshot)
5. ✅ `TEST_EXECUTION_LOG.md` → `archive/` (template, not actively used)

---

## Files to Consolidate

### 1. Merge Calculation Comparison into Feature Summary
- **Source:** `FRONTEND_BACKEND_CALCULATION_COMPARISON.md`
- **Target:** `TEST_BED_FEATURE_SUMMARY.md`
- **Action:** Add "Calculation Verification" section

### 2. Merge Data Validation into Comprehensive Test Plan
- **Source:** `DATA_VALIDATION_TEST_PLAN.md`
- **Target:** `TESTING_VALIDATION_PLAN.md`
- **Action:** Add "Data Validation" section

### 3. Merge Naming Conventions into System Contracts
- **Source:** `NAMING_CONVENTIONS.md`
- **Target:** `system/CONTRACTS.md`
- **Action:** Add naming conventions section (if not already covered)

---

## Files to Keep (Essential)

### Test Bed Feature
- `CHANGELOG_TEST_BED.md` - Change history
- `TEST_BED_FEATURE_SUMMARY.md` - Quick reference (will include calculation verification)
- `features/EXPERIMENTS_PAGE_MIGRATION_PLAN.md` - Migration plan
- `features/TEST_BED_SYSTEM_VALIDATION.md` - System validation
- `features/FORECAST_METHOD_COMPARISON_ANALYSIS.md` - Design decisions

### Testing
- `TEST_RESULTS_SUMMARY.md` - Actual test results
- `TESTING_VALIDATION_PLAN.md` - Comprehensive plan (will include data validation)
- `QUICK_TEST_GUIDE.md` - Quick reference
- `backend/TEST_PLAN.md` - Backend-specific tests

### Setup & Reference
- `FRONTEND_BACKEND_SEPARATION_GUIDE.md` - Still relevant for future reference
- All setup/development docs
- All feature planning docs
- All reference docs

---

## Execution Steps

1. Create archive directory structure
2. Move one-time docs to archive
3. Consolidate docs (merge content)
4. Delete source files after merge
5. Update README.md if needed
6. Commit changes

---

## Expected Result

**Before:** ~60 docs  
**After:** ~50 docs  
**Archived:** 5 docs  
**Consolidated:** 3 docs merged

**Benefit:** Cleaner, easier to navigate, less redundancy

