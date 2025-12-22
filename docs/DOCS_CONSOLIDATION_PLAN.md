# Documentation Consolidation Plan

**Date:** 2025-12-22  
**Goal:** Reduce redundancy, consolidate related docs, archive completed/setup docs

---

## Analysis

### Redundant/Consolidatable Docs

#### 1. Test Documentation (7 files → 2-3 files)
**Current:**
- `TEST_EXECUTION_LOG.md` - Template (can archive)
- `TEST_RESULTS_SUMMARY.md` - Actual results (keep)
- `TESTING_VALIDATION_PLAN.md` - Comprehensive plan (keep)
- `QUICK_TEST_GUIDE.md` - Quick guide (keep, useful)
- `DATA_VALIDATION_TEST_PLAN.md` - Data validation (consolidate into TESTING_VALIDATION_PLAN.md)
- `backend/TEST_PLAN.md` - Backend tests (keep, different scope)
- `archive/backend/TEST_PLAN.md` - Archived (already archived)

**Action:**
- ✅ Keep: `TEST_RESULTS_SUMMARY.md`, `TESTING_VALIDATION_PLAN.md`, `QUICK_TEST_GUIDE.md`, `backend/TEST_PLAN.md`
- 📦 Archive: `TEST_EXECUTION_LOG.md` (template, not needed)
- 🔀 Consolidate: `DATA_VALIDATION_TEST_PLAN.md` → merge into `TESTING_VALIDATION_PLAN.md`

#### 2. Test Bed Feature Docs (9 files → 4-5 files)
**Current:**
- `CHANGELOG_TEST_BED.md` - Change history (keep)
- `TEST_BED_FEATURE_SUMMARY.md` - Quick summary (keep)
- `CLEANUP_SUMMARY.md` - Cleanup report (archive - one-time)
- `CLEANUP_AND_SEPARATION_PLAN.md` - Separation plan (archive - completed)
- `features/EXPERIMENTS_PAGE_MIGRATION_PLAN.md` - Migration plan (keep)
- `features/TEST_BED_SYSTEM_VALIDATION.md` - System validation (keep)
- `FRONTEND_BACKEND_CALCULATION_COMPARISON.md` - Formula comparison (consolidate)
- `FRONTEND_BACKEND_SEPARATION_GUIDE.md` - Separation guide (keep, still relevant)
- `NESTED_REPO_SETUP.md` - Setup guide (archive - one-time setup)
- `NESTED_REPO_STATUS.md` - Status (archive - snapshot)

**Action:**
- ✅ Keep: `CHANGELOG_TEST_BED.md`, `TEST_BED_FEATURE_SUMMARY.md`, `features/EXPERIMENTS_PAGE_MIGRATION_PLAN.md`, `features/TEST_BED_SYSTEM_VALIDATION.md`, `FRONTEND_BACKEND_SEPARATION_GUIDE.md`
- 📦 Archive: `CLEANUP_SUMMARY.md`, `CLEANUP_AND_SEPARATION_PLAN.md`, `NESTED_REPO_SETUP.md`, `NESTED_REPO_STATUS.md`
- 🔀 Consolidate: `FRONTEND_BACKEND_CALCULATION_COMPARISON.md` → merge into `TEST_BED_FEATURE_SUMMARY.md` or `features/TEST_BED_SYSTEM_VALIDATION.md`

#### 3. Duplicate/Similar Docs
- `NAMING_CONVENTIONS.md` vs `system/CONTRACTS.md` - Check if redundant
- Multiple forecasting docs - Check for overlap

---

## Recommended Actions

### Immediate (High Priority)

1. **Archive One-Time Setup Docs:**
   - `CLEANUP_SUMMARY.md` → `archive/`
   - `CLEANUP_AND_SEPARATION_PLAN.md` → `archive/`
   - `NESTED_REPO_SETUP.md` → `archive/`
   - `NESTED_REPO_STATUS.md` → `archive/`
   - `TEST_EXECUTION_LOG.md` → `archive/` (template)

2. **Consolidate Test Docs:**
   - Merge `DATA_VALIDATION_TEST_PLAN.md` into `TESTING_VALIDATION_PLAN.md`
   - Keep `QUICK_TEST_GUIDE.md` separate (useful for quick reference)

3. **Consolidate Test Bed Docs:**
   - Merge `FRONTEND_BACKEND_CALCULATION_COMPARISON.md` into `TEST_BED_FEATURE_SUMMARY.md`

### Optional (Lower Priority)

4. **Review for Further Consolidation:**
   - Check if `NAMING_CONVENTIONS.md` duplicates `system/CONTRACTS.md`
   - Review forecasting docs for overlap

---

## Files to Archive

```
docs/archive/
├── CLEANUP_SUMMARY.md (move from root)
├── CLEANUP_AND_SEPARATION_PLAN.md (move from root)
├── NESTED_REPO_SETUP.md (move from root)
├── NESTED_REPO_STATUS.md (move from root)
└── TEST_EXECUTION_LOG.md (move from root - template)
```

---

## Files to Consolidate

1. **Merge `DATA_VALIDATION_TEST_PLAN.md` → `TESTING_VALIDATION_PLAN.md`**
   - Add "Data Validation" section to comprehensive plan

2. **Merge `FRONTEND_BACKEND_CALCULATION_COMPARISON.md` → `TEST_BED_FEATURE_SUMMARY.md`**
   - Add "Calculation Verification" section to summary

---

## Final Structure (After Cleanup)

### Keep in Root
- `README.md` - Main index
- `NEXT_STEPS.md` - Current priorities
- `CHANGELOG_TEST_BED.md` - Feature changelog
- `TEST_BED_FEATURE_SUMMARY.md` - Quick reference (with calculation verification)
- `TEST_RESULTS_SUMMARY.md` - Test results
- `TESTING_VALIDATION_PLAN.md` - Comprehensive plan (with data validation)
- `QUICK_TEST_GUIDE.md` - Quick test guide
- `FRONTEND_BACKEND_SEPARATION_GUIDE.md` - Still relevant

### Archive
- All one-time setup/completion docs
- Templates that aren't actively used

---

## Summary

**Before:** ~60+ docs  
**After:** ~50-55 docs (consolidated)  
**Archived:** ~5-10 docs  
**Consolidated:** 2 docs merged

**Benefit:** Cleaner structure, easier navigation, less redundancy

