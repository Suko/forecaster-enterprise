# Documentation Reorganization Plan

**Current State:** 14 files in root `docs/` folder  
**Proposed State:** 6 core files in root, organized subfolders

---

## Proposed Structure

### Keep in Root (Core/Essential Docs - 6 files)
These are frequently accessed core documents:
- `README.md` - Main documentation index
- `DATA_MODEL.md` - Core database schema (47KB, frequently referenced)
- `DATA_REQUIREMENTS.md` - User-facing data requirements
- `USER_STORIES.md` - Feature requirements
- `WORKFLOWS.md` - System workflows
- `NEXT_STEPS.md` - Current development priorities

### Move to `setup/` folder (5 files)
Setup and development environment docs:
- `QUICK_START.md` → `setup/QUICK_START.md`
- `DEVELOPMENT_SETUP.md` → `setup/DEVELOPMENT_SETUP.md`
- `SETUP_SCRIPT_GUIDE.md` → `setup/SETUP_SCRIPT_GUIDE.md`
- `ENV_MANAGEMENT.md` → `setup/ENV_MANAGEMENT.md`
- `SHARED_TEST_DATA_SUPABASE.md` → `setup/SHARED_TEST_DATA_SUPABASE.md`

### Move to `features/` folder (1 file)
Feature planning documents:
- `WORKING_ORDERS_FEATURE.md` → `features/WORKING_ORDERS_FEATURE.md`

### Move to `reference/` folder (2 files)
Reference and mapping documents:
- `M5_DATA_MAPPING.md` → `reference/M5_DATA_MAPPING.md`
- `SECURITY_AUDIT_REPORT.md` → `reference/SECURITY_AUDIT_REPORT.md`

---

## Final Structure

```
docs/
├── README.md                    # Main index (update links)
├── DATA_MODEL.md               # Core data structure
├── DATA_REQUIREMENTS.md        # User-facing requirements
├── USER_STORIES.md             # Feature requirements
├── WORKFLOWS.md                # System workflows
├── NEXT_STEPS.md               # Current priorities
│
├── setup/                      # Setup & development
│   ├── QUICK_START.md
│   ├── DEVELOPMENT_SETUP.md
│   ├── SETUP_SCRIPT_GUIDE.md
│   ├── ENV_MANAGEMENT.md
│   └── SHARED_TEST_DATA_SUPABASE.md
│
├── features/                   # Feature planning
│   └── WORKING_ORDERS_FEATURE.md
│
├── reference/                  # Reference docs
│   ├── M5_DATA_MAPPING.md
│   └── SECURITY_AUDIT_REPORT.md
│
├── backend/                    # Backend docs (existing)
│   └── ...
│
├── frontend/                   # Frontend docs (existing)
│   └── ...
│
├── standards/                  # Standards (existing)
│   └── ...
│
└── system/                     # System contracts (existing)
    └── ...
```

---

## Files to Update After Reorganization

1. **docs/README.md** - Update all links to moved files
2. **docs/NEXT_STEPS.md** - Update link to WORKING_ORDERS_FEATURE.md
3. **Any other docs** that reference these files

---

## Benefits

- **Cleaner root**: 6 core files instead of 14
- **Better organization**: Logical grouping by purpose
- **Easier navigation**: Related docs grouped together
- **Scalable**: Easy to add more setup/features/reference docs

---

**Status:** Proposal - Ready to implement

