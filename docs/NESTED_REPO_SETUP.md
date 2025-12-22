# Nested Git Repository Setup Guide

## Overview

This guide explains how to set up a nested git repository structure where:
- **Main repo** tracks backend code
- **Frontend folder** has its own separate git repository
- Frontend is ignored by main repo

## Current Structure

```
forecaster-enterprise/
├── backend/          # Python FastAPI
├── frontend/         # Nuxt 3 (will become separate repo)
├── docs/             # Shared documentation
└── .gitignore        # Will ignore frontend/
```

## Step-by-Step Setup

### Step 1: Backup Current State

```bash
# Make sure everything is committed
git status
git add -A
git commit -m "Pre-separation commit"
```

### Step 2: Initialize Frontend as Separate Repo

```bash
cd frontend
git init
git add .
git commit -m "Initial frontend commit"
```

### Step 3: Add Frontend Remote (if you have one)

```bash
# If you have a remote repo ready
git remote add origin <your-frontend-repo-url>
git branch -M main
git push -u origin main
```

### Step 4: Update Main Repo's .gitignore

```bash
cd ..  # Back to root
echo "frontend/" >> .gitignore
git add .gitignore
git commit -m "Ignore frontend folder (separate repo)"
```

### Step 5: Remove Frontend from Main Repo History (Optional)

If frontend was previously tracked, remove it:

```bash
# Remove from git index (but keep files)
git rm -r --cached frontend/

# Commit the removal
git commit -m "Remove frontend from main repo (now separate repo)"
```

## Daily Workflow

### Working on Backend

```bash
cd /path/to/forecaster-enterprise
# Make backend changes
git add backend/
git commit -m "Backend changes"
git push
```

### Working on Frontend

```bash
cd /path/to/forecaster-enterprise/frontend
# Make frontend changes
git add .
git commit -m "Frontend changes"
git push
```

### Working on Both

```bash
# Backend
cd /path/to/forecaster-enterprise
git add backend/
git commit -m "Backend changes"

# Frontend
cd frontend
git add .
git commit -m "Frontend changes"
```

## Important Considerations

### Shared Documentation

If `docs/` contains shared documentation:

**Option A: Keep in main repo**
- Backend team maintains it
- Frontend team references it

**Option B: Duplicate in both repos**
- Each repo has its own docs
- Need to sync manually

**Option C: Separate docs repo**
- Create `forecaster-enterprise-docs` repo
- Both repos reference it

### CI/CD Setup

**Backend CI/CD:**
- Triggered by main repo commits
- Builds and deploys backend

**Frontend CI/CD:**
- Triggered by frontend repo commits
- Builds and deploys frontend
- Needs API endpoint URL from environment

### Environment Variables

**Frontend needs:**
```env
# .env in frontend/
NUXT_PUBLIC_API_BASE_URL=https://api.forecaster.com
```

**Backend needs:**
```env
# .env in backend/
DATABASE_URL=...
CORS_ORIGINS=https://app.forecaster.com
```

## Pros and Cons

### Pros ✅
- Simple setup (no submodules)
- Independent versioning
- Can work on both in same workspace
- Independent deployment
- Frontend team can clone just frontend

### Cons ❌
- Two `.git` folders (can be confusing)
- Frontend not in main repo history
- Shared docs need manual sync
- Need to remember which repo you're in
- Can't easily see all changes together

## Alternative: Git Submodules

If you want frontend tracked in main repo but as separate repo:

```bash
# Remove frontend from main repo
git rm -r frontend/

# Add as submodule
git submodule add <frontend-repo-url> frontend

# Clone with submodules
git clone --recurse-submodules <main-repo-url>
```

**Submodules pros:**
- Frontend tracked in main repo
- Can see frontend commits in main repo
- Better for coordination

**Submodules cons:**
- More complex workflow
- Need to remember to update submodules
- Can be confusing for beginners

## Recommendation

**For your use case: Nested repo is fine if:**
- Teams work independently
- You want simple setup
- You don't need frontend in main repo history

**Use submodules if:**
- You want frontend commits visible in main repo
- You need better coordination
- You're comfortable with submodule workflow

## Troubleshooting

### "Frontend folder is empty after clone"

**Problem:** Main repo ignores frontend, so it's not cloned.

**Solution:** Clone frontend separately:
```bash
git clone <frontend-repo-url> frontend
```

### "Git commands not working in frontend"

**Problem:** You're in wrong directory or frontend isn't a git repo.

**Solution:** 
```bash
cd frontend
git status  # Should show frontend repo status
```

### "Want to see all changes together"

**Problem:** Changes are in separate repos.

**Solution:** Use separate terminal windows or tabs for each repo.

## Migration Checklist

- [ ] Backup current repo
- [ ] Initialize frontend as separate repo
- [ ] Add frontend remote
- [ ] Update main repo's .gitignore
- [ ] Remove frontend from main repo (if previously tracked)
- [ ] Update CI/CD pipelines
- [ ] Update documentation
- [ ] Test workflow with team
- [ ] Update README files

