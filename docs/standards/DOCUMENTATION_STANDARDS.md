# Documentation Standards

**Version:** 1.0  
**Last Updated:** 2025-12-09

---

## Purpose

This document defines the standards for creating, maintaining, and organizing documentation.

---

## 1. Document Structure

### Required Sections

Every document must include:

1. **Title** - Clear, descriptive name
2. **Metadata** - Version, last updated, status
3. **Purpose** - Why this document exists
4. **Content** - Main body
5. **References** - Links to related documents (if applicable)

### Header Template

```markdown
# Document Title

**Version:** X.X  
**Last Updated:** YYYY-MM-DD  
**Status:** Active | Draft | Archived

---

## Purpose

Brief description of what this document covers.

---
```

---

## 2. Directory Structure

### Allowed Directories

```
/docs/
├── forecasting/           # Forecasting-specific documentation
│   ├── 00_OVERVIEW.md     # Entry point
│   ├── archive/           # Superseded documents
│   └── test_results/      # Test reports
├── standards/             # Global standards
└── system/                # System contracts
```

### Active Forecasting Documents

Only these files are allowed in `/docs/forecasting/`:

| File | Purpose |
|------|---------|
| `00_OVERVIEW.md` | Entry point and navigation |
| `PROGRESS_TRACKER.md` | Single source of truth for progress |
| `CURRENT_OBJECTIVE.md` | Current goals |
| `PHASE_ROADMAP.md` | Project roadmap |
| `ARCHITECTURE.md` | System architecture |
| `DATA_MODELS.md` | Database schemas |
| `METHOD_IMPLEMENTATION.md` | Method details |
| `METHOD_ROUTING_VALIDATION_RESULTS.md` | Routing validation |
| `QUALITY_METRICS_GUIDE.md` | Metrics documentation |
| `EXPECTED_MAPE_RANGES.md` | Accuracy expectations |

---

## 3. Naming Conventions

### Active Documents

- Use `UPPERCASE_WITH_UNDERSCORES.md`
- Be descriptive but concise
- Examples: `PROGRESS_TRACKER.md`, `DATA_MODELS.md`

### Test Results

- Use timestamped naming: `YYYY-MM-DD_description.md`
- Examples: `2025-12-09_sba_validation.md`

### Archives

- Keep original filename
- Place in `/archive/` directory

---

## 4. Content Guidelines

### Writing Style

- Use clear, concise language
- Avoid jargon without explanation
- Use tables for structured data
- Use code blocks for technical content

### Formatting

- Use Markdown formatting
- Use headers hierarchically (H1 → H2 → H3)
- Use bullet points for lists
- Use tables for comparisons

### Status Indicators

| Icon | Meaning |
|------|---------|
| ✅ | Complete/Success |
| ⚠️ | Warning/Needs attention |
| ❌ | Failed/Error |
| 🎯 | Current focus |
| ⏳ | Pending/In progress |
| 📊 | Metrics/Data |
| 💡 | Insight/Recommendation |

---

## 5. Test Results Documentation

### Required Elements

1. **Date** - When test was run
2. **Purpose** - What was being tested
3. **Methodology** - How test was conducted
4. **Results** - Detailed findings
5. **Conclusions** - Key takeaways
6. **Actions** - Next steps (if any)

### Template

```markdown
# Test Name

**Date:** YYYY-MM-DD  
**Status:** Pass | Fail | Partial

---

## Purpose

What was being tested and why.

## Methodology

How the test was conducted.

## Results

Detailed findings with data.

## Conclusions

Key takeaways.

## Actions

Next steps or recommendations.
```

---

## 6. Archiving Rules

### When to Archive

- Document is superseded by newer version
- Information is no longer current
- Document was exploratory/temporary

### Archive Process

1. Move file to `/archive/` directory
2. Update `00_OVERVIEW.md` to remove reference
3. Update relevant active documents
4. Do NOT edit archived documents

### Archive Naming

- Keep original filename
- Do not rename when archiving

---

## 7. Cross-References

### Internal References

- Use relative paths: `[Link](./DOCUMENT.md)`
- Always verify links work

### External References

- Use full URLs
- Add access date if content may change

---

## 8. Maintenance

### Update Frequency

- `PROGRESS_TRACKER.md` - After each milestone
- `00_OVERVIEW.md` - When structure changes
- Other docs - As needed

### Review Cycle

- Monthly: Review all active documents
- Quarterly: Archive cleanup

---

## 9. Enforcement

All documentation must:

1. ✅ Follow naming conventions
2. ✅ Include required sections
3. ✅ Be placed in correct directory
4. ✅ Be referenced from `00_OVERVIEW.md`
5. ✅ Use consistent formatting

---

*This standard is mandatory for all documentation.*

