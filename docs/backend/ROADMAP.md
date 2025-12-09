# Forecasting Module Roadmap

**Last Updated:** 2025-12-09  
**Current Status:** Production Ready (85%)

> **Note:** This document focuses on the **forecasting engine** specifically.  
> For the complete backend system roadmap (APIs, ETL, inventory management), see [BACKEND_ROADMAP.md](./BACKEND_ROADMAP.md)

---

## Current Development Todos

### Production Readiness (Immediate)

| Task | Status | Priority |
|------|--------|----------|
| Deployment preparation | ⏳ Pending | 🔴 High |
| Environment setup | ⏳ Pending | 🔴 High |
| Migration scripts | ⏳ Pending | 🔴 High |
| Rollback plan | ⏳ Pending | 🔴 High |
| Load testing | ⏳ Pending | 🟡 Medium |
| Performance profiling | ⏳ Pending | 🟡 Medium |

---

## Forecast Improvements (Known Enhancements)

### 1. A-Y Performance Issue 🔴 High Priority

**Problem:**
- Current MAPE: **111.9%** (expected: 20-40%)
- Affected: 2 SKUs (M5_HOUSEHOLD_1_118, M5_HOUSEHOLD_1_151)
- Chronos-2 is 43.2 points better than MA7, but both struggle

**Investigation Results:**
- CV = 0.76 (medium variability)
- Regular demand pattern (ADI < 1.32)
- Data quality: Good (no missing dates, few outliers)
- Some zero-demand days (7-14%)
- Small negative trends (-0.4% to -0.5%)

**Potential Solutions:**
- [ ] Adjust expected MAPE ranges for A-Y (maybe 30-60% more realistic?)
- [ ] Test exponential smoothing as alternative method
- [ ] Add covariates (promotions, holidays) - Phase 3
- [ ] Investigate if these SKUs have special characteristics
- [ ] Consider ensemble methods for A-Y SKUs

**Estimated Impact:** High - affects 2 high-value SKUs

---

### 2. A-Z Partial Performance 🟡 Medium Priority

**Problem:**
- Current MAPE: **86.6%** (expected: 30-60%)
- Status: ⚠️ Partial compliance
- 55.6% of A-Z SKUs within expected range (10/18)

**Potential Solutions:**
- [ ] Review A-Z classification criteria
- [ ] Test alternative methods for high-variability SKUs
- [ ] Add covariates to improve accuracy
- [ ] Consider hybrid approaches (ML + statistical)

**Estimated Impact:** Medium - affects 18 SKUs

---

### 3. Phase 3: Covariates Integration 🟢 Planned

**Goal:** Improve forecast accuracy with external factors

**Features:**
- [ ] Promotional events (promo_flag)
- [ ] Holiday indicators (holiday_flag)
- [ ] Marketing spend correlation
- [ ] Price elasticity
- [ ] Weekend patterns (is_weekend)

**Expected Benefits:**
- Address A-Y performance issue
- Improve A-Z accuracy
- Better handling of demand spikes

**Estimated Impact:** High - addresses multiple performance issues

---

### 4. Method Optimization

**Current Status:**
- ✅ SBA: 79.1% MAPE (within expected 50-90%)
- ✅ Routing: 100% correctness
- ⚠️ Overall: 60% within expected range (24/40 SKUs)

**Enhancements:**
- [ ] Fine-tune Chronos-2 parameters for A-Y/A-Z
- [ ] Test ensemble methods
- [ ] Optimize SBA for edge cases
- [ ] Validate Croston with synthetic intermittent data
- [ ] Test Min/Max with C-Z SKUs when available

---

## UI Backend Expansion (Next Phase)

### Status: TBD - User Stories Pending

**Scope:** Expand backend to support UI functions

**Planned Areas:**
- [ ] User stories to be defined
- [ ] API endpoints for UI features
- [ ] Data aggregation for dashboards
- [ ] Real-time updates/websockets
- [ ] Export functionality
- [ ] Filtering and search
- [ ] Pagination for large datasets

**Next Steps:**
1. ⏳ Wait for user stories
2. ⏳ Design API contracts
3. ⏳ Implement endpoints
4. ⏳ Add tests

---

## Future Enhancements (Backlog)

### Advanced ML Models
- [ ] TimesFM integration
- [ ] Moirai integration
- [ ] Model comparison framework

### Hierarchical Forecasting
- [ ] Multi-location support
- [ ] Store-level forecasting
- [ ] Region aggregation

### Real-time Features
- [ ] Streaming forecasts
- [ ] Live accuracy monitoring
- [ ] Automated retraining

### Data Quality
- [ ] Advanced outlier detection
- [ ] Missing data imputation
- [ ] Data quality scoring

---

## Priority Matrix

| Priority | Items | Timeline |
|----------|-------|----------|
| 🔴 **Critical** | Production deployment, A-Y performance | This week |
| 🟡 **High** | A-Z improvements, UI backend expansion | Next 2 weeks |
| 🟢 **Medium** | Covariates integration, method optimization | Next month |
| ⚪ **Low** | Advanced ML, hierarchical forecasting | Future |

---

## Success Metrics

### Forecast Accuracy Targets

| Classification | Current | Target | Status |
|----------------|---------|--------|--------|
| A-X | 17.1% | 10-25% | ✅ Met |
| A-Y | 111.9% | 20-40% | ❌ Needs work |
| A-Z | 86.6% | 30-60% | ⚠️ Partial |
| Lumpy | 79.1% | 50-90% | ✅ Met |

### System Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Routing correctness | 100% | 100% | ✅ |
| Within expected MAPE | 60% | 80% | ⚠️ |
| Production readiness | 85% | 100% | ⚠️ |

---

## Notes

- **A-Y Issue:** Top priority - affects high-value SKUs
- **Covariates:** Expected to address multiple performance issues
- **UI Expansion:** Waiting for user stories to define scope
- **Production:** Core functionality ready, deployment prep needed

---

## Related Documentation

- [forecasting/README.md](./forecasting/README.md) - Module status
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture
- [../standards/STANDARDS.md](../standards/STANDARDS.md) - Project standards

---

*This roadmap is updated as priorities and user stories are defined.*

