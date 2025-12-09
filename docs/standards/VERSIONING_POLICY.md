# Versioning Policy

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the versioning policy for the forecasting system, including models, APIs, and documentation.

---

## 1. Semantic Versioning

### Format

```
MAJOR.MINOR.PATCH
```

### Version Components

| Component | When to Increment |
|-----------|-------------------|
| **MAJOR** | Breaking changes, incompatible API changes |
| **MINOR** | New features, backward-compatible |
| **PATCH** | Bug fixes, minor improvements |

### Examples

| Version | Change |
|---------|--------|
| 1.0.0 → 2.0.0 | Breaking API change |
| 1.0.0 → 1.1.0 | New forecasting method added |
| 1.0.0 → 1.0.1 | Bug fix in MAPE calculation |

---

## 2. Model Versioning

### Model Version Format

```
model_name-vX.Y.Z
```

### Current Models

| Model | Version | Status |
|-------|---------|--------|
| chronos-2 | v1.0.0 | Active |
| sba | v1.0.0 | Active |
| croston | v1.0.0 | Active |
| min_max | v1.0.0 | Active |
| statistical_ma7 | v1.0.0 | Active |

### Model Changes

| Change Type | Version Impact |
|-------------|----------------|
| New model | MINOR bump |
| Model improvement | PATCH bump |
| Model deprecation | MAJOR bump |
| Parameter change | MINOR or PATCH |

---

## 3. API Versioning

### URL Format

```
/api/v{VERSION}/endpoint
```

### Current API Versions

| Version | Status | Notes |
|---------|--------|-------|
| v1 | Active | Current production |

### API Changes

| Change | Handling |
|--------|----------|
| New endpoint | Add to current version |
| New optional field | Add to current version |
| New required field | New MAJOR version |
| Remove field | New MAJOR version |
| Change field type | New MAJOR version |

### Deprecation Policy

1. Announce deprecation 3 months before removal
2. Provide migration guide
3. Support deprecated version for 6 months
4. Remove in next MAJOR version

---

## 4. Database Schema Versioning

### Migration Naming

```
{revision}_description.py
```

### Migration Rules

- One migration per logical change
- Always include rollback (`downgrade`)
- Test both upgrade and downgrade
- Document breaking changes

### Current Schema Version

| Table | Version | Last Updated |
|-------|---------|--------------|
| forecast_runs | 2.0 | 2025-12-09 |
| forecast_results | 1.0 | 2025-12-01 |
| sku_classifications | 1.0 | 2025-12-09 |

---

## 5. Documentation Versioning

### Document Version Format

```
Version: X.Y
```

### Version Rules

- Increment MAJOR for structural changes
- Increment MINOR for content updates
- Include "Last Updated" date

### Current Documentation Versions

| Document | Version |
|----------|---------|
| FORECASTING_STANDARDS | 1.0 |
| DOCUMENTATION_STANDARDS | 1.0 |
| TESTING_STANDARDS | 1.0 |
| EVALUATION_STANDARDS | 1.0 |
| CLIENT_DELIVERY_STANDARDS | 1.0 |
| VERSIONING_POLICY | 1.0 |

---

## 6. Release Process

### Release Checklist

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Database migrations ready
- [ ] Client notification (if breaking)

### Release Types

| Type | Frequency | Testing |
|------|-----------|---------|
| PATCH | As needed | Unit + integration |
| MINOR | Monthly | Full regression |
| MAJOR | Quarterly | Full + client testing |

---

## 7. Changelog

### Format

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Modifications

### Fixed
- Bug fixes

### Deprecated
- Features to be removed

### Removed
- Removed features
```

### Current Changelog

```markdown
## [1.0.0] - 2025-12-09

### Added
- Chronos-2 forecasting model
- SBA model for lumpy demand
- Croston model for intermittent demand
- Min/Max rules for C-Z SKUs
- SKU classification (ABC-XYZ)
- Method routing system
- Quality metrics (MAPE, MAE, RMSE, Bias)

### Notes
- Initial production release
- Phase 2B complete
```

---

## 8. Backward Compatibility

### Guarantees

| Component | Backward Compatible |
|-----------|---------------------|
| API (same MAJOR) | ✅ Yes |
| Database (same MAJOR) | ✅ Yes |
| Model outputs | ✅ Yes |
| Classification | ✅ Yes |

### Breaking Changes

When making breaking changes:

1. Increment MAJOR version
2. Document all changes
3. Provide migration guide
4. Notify all clients
5. Support old version during transition

---

## 9. Version History

### System Releases

| Version | Date | Description |
|---------|------|-------------|
| 0.1.0 | 2025-11-01 | Initial development |
| 0.2.0 | 2025-11-15 | Chronos-2 integration |
| 0.3.0 | 2025-12-01 | SKU classification |
| 1.0.0 | 2025-12-09 | Production release |

---

## 10. Compliance

All releases must:

1. ✅ Follow semantic versioning
2. ✅ Update changelog
3. ✅ Bump version numbers
4. ✅ Document breaking changes
5. ✅ Pass all tests

---

*This policy is mandatory for all releases.*

