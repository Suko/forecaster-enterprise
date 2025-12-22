# Cleanup and Backend/Frontend Separation Plan

## Current State Analysis

### Modified Files (Backend)
- `backend/api/forecast.py` - Added `run_all_methods`, `skip_persistence`, `training_end_date`
- `backend/forecasting/services/forecast_service.py` - Test Bed support
- `backend/forecasting/services/quality_calculator.py` - Quality metrics
- `backend/models/forecast.py` - Made `user_id` nullable
- `backend/schemas/forecast.py` - New request fields
- `backend/services/dashboard_service.py` - Fixed `user_id=None`
- `backend/services/inventory_service.py` - Fixed `user_id=None`
- `backend/services/recommendations_service.py` - Fixed `user_id=None`

### New Files (Frontend)
- `frontend/app/pages/experiments/testbed.vue` - **24 console.log statements to clean**
- `frontend/app/pages/experiments/roi-calculator.vue`
- `frontend/app/pages/experiments/index.vue`
- `frontend/app/components/ExperimentsTabs.vue`
- `frontend/app/composables/useExperiments.ts`
- `frontend/app/types/experiments.ts`
- `frontend/server/api/experiments/*` - 7 new API proxy routes
- `frontend/app/layouts/dashboard.vue` - Added Experiments nav

### New Documentation
- `docs/backend/forecasting/INVENTORY_ORDERING_GUIDE.md`
- `docs/backend/forecasting/METRICS_BEST_PRACTICES.md`
- `docs/features/EXPERIMENTS_PAGE_MIGRATION_PLAN.md`
- `docs/features/FORECAST_METHOD_COMPARISON_ANALYSIS.md`
- `docs/features/TEST_BED_SYSTEM_VALIDATION.md`

## Cleanup Tasks

### 1. Remove Debug Code from testbed.vue

**Priority: HIGH**

Remove all `console.log` statements (24 instances found):
- Lines 799, 886-897, 907-921, 1023-1032, 1040, 1052, 1191

**Action:** Replace with proper error handling or remove entirely.

### 2. Code Review Checklist

- [ ] Remove all `console.log` statements
- [ ] Remove any `debugger` statements
- [ ] Remove commented-out code blocks
- [ ] Verify error handling is proper (no console.error in production)
- [ ] Check for hardcoded values that should be configurable
- [ ] Verify all TypeScript types are properly defined
- [ ] Check for unused imports

### 3. Documentation Cleanup

- [ ] Review migration plan doc - mark completed sections
- [ ] Ensure all docs are up-to-date with final implementation
- [ ] Remove any "TODO" or "FIXME" comments from code

## Git Separation Strategy

### Option A: Separate Repositories (Recommended for Production)

**Pros:**
- Clean separation of concerns
- Independent versioning
- Different deployment pipelines
- Team can work independently

**Cons:**
- More complex CI/CD setup
- Need to coordinate API contracts

**Steps:**
1. Create `forecaster-enterprise-backend` repo
2. Create `forecaster-enterprise-frontend` repo
3. Move files accordingly
4. Set up shared API contract documentation
5. Update CI/CD pipelines

### Option B: Monorepo with Separate Branches

**Pros:**
- Keep related code together
- Easier to coordinate changes
- Single CI/CD pipeline

**Cons:**
- Still coupled in same repo
- Harder to separate deployment

**Steps:**
1. Create `backend/` and `frontend/` branches
2. Use git subtree or submodules
3. Coordinate merges carefully

### Option C: Keep Monorepo, Improve Structure (Recommended for Now)

**Pros:**
- Minimal disruption
- Easy to coordinate changes
- Can separate later

**Cons:**
- Still coupled
- Need discipline to maintain boundaries

**Steps:**
1. Clean up current code
2. Commit all changes
3. Document API contracts clearly
4. Plan future separation if needed

## Recommended Approach

**For now: Clean up and commit, plan separation later**

1. **Immediate (Before Commit):**
   - Remove all `console.log` from testbed.vue
   - Review and clean up any debug code
   - Ensure error handling is proper
   - Update documentation

2. **Commit Strategy:**
   - Single commit: "feat(experiments): Add Test Bed and ROI Calculator"
   - Or split into logical commits:
     - Backend changes
     - Frontend UI
     - Documentation

3. **Future Separation (If Needed):**
   - When team grows
   - When deployment needs differ
   - When API is stable

## Cleanup Script

```bash
# Remove console.log from testbed.vue (after review)
# Use sed or manual removal
grep -n "console.log" frontend/app/pages/experiments/testbed.vue
```

## Pre-Commit Checklist

- [ ] All console.log removed
- [ ] All TypeScript errors fixed
- [ ] All linter errors fixed
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
- [ ] Code reviewed
- [ ] No hardcoded secrets/values
- [ ] Error handling in place

## Next Steps

1. **Clean up testbed.vue** - Remove debug logs
2. **Review all new files** - Ensure production-ready
3. **Commit changes** - Clean, well-documented commit
4. **Update .gitignore** - If needed
5. **Plan separation** - If/when needed

