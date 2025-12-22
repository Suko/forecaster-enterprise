# Frontend/Backend Separation Guide

## Current Architecture

**Backend:** Python FastAPI  
**Frontend:** Nuxt 3 (TypeScript)  
**Communication:** REST API with server proxy routes

**Decision:** We will keep REST API with OpenAPI schema (no tRPC implementation)

---

## Repository Structure Options

### Option A: Monorepo (Current - All Together) ✅ **Recommended for Now**

**Structure:**
```
forecaster-enterprise/          # Single repository
├── backend/                    # Python FastAPI
├── frontend/                   # Nuxt 3
├── docs/                       # Shared documentation
└── docker-compose.yml          # Local development
```

**Pros:**
- ✅ Easy to coordinate changes
- ✅ Single git history
- ✅ Shared documentation
- ✅ Simple local development
- ✅ No API contract management needed

**Cons:**
- ❌ Coupled deployment
- ❌ Can't deploy independently
- ❌ Teams can't work completely independently

**When to use:** Current development phase, small team, rapid iteration

---

### Option B: Separate Repositories (2 Repos)

**Structure:**
```
forecaster-enterprise-backend/  # Backend only
├── api/
├── forecasting/
├── models/
└── main.py

forecaster-enterprise-frontend/ # Frontend only
├── app/
├── server/
└── nuxt.config.ts
```

**Pros:**
- ✅ Independent deployment
- ✅ Team autonomy
- ✅ Technology flexibility
- ✅ Separate CI/CD pipelines

**Cons:**
- ❌ Need API contract management
- ❌ More complex coordination
- ❌ Separate git histories

**When to use:** Larger team, independent deployment needs, stable API

---

### Option C: Hybrid (3 Repos) - **NOT Recommended**

**Structure:**
```
forecaster-enterprise/          # Monorepo (development)
forecaster-enterprise-backend/  # Backend (deployment)
forecaster-enterprise-frontend/ # Frontend (deployment)
```

**Why NOT recommended:**
- ❌ Too complex
- ❌ Sync overhead between repos
- ❌ Confusion about source of truth
- ❌ Maintenance burden

**Only use if:** You have very specific deployment requirements that require this complexity

---

## Recommendation

**Current Phase: Keep Monorepo (Option A)**

**Future (if needed): Separate to 2 Repos (Option B)**

You do **NOT** need 3 repos. Choose:
- **Monorepo** (all together) - Current approach ✅
- **2 separate repos** (FE + BE) - When you need independent deployment

---

## Option 1: Separate Repositories (2 Repos - When Ready)

### Step-by-Step Separation

#### 1. Create Separate Repositories

```bash
# Create backend repository
git clone <current-repo> forecaster-enterprise-backend
cd forecaster-enterprise-backend
git filter-branch --subdirectory-filter backend -- --all
# Or use git subtree:
git subtree push --prefix=backend origin backend-main

# Create frontend repository  
git clone <current-repo> forecaster-enterprise-frontend
cd forecaster-enterprise-frontend
git filter-branch --subdirectory-filter frontend -- --all
# Or use git subtree:
git subtree push --prefix=frontend origin frontend-main
```

#### 2. Update Backend Repository

**Structure:**
```
forecaster-enterprise-backend/
├── api/
├── forecasting/
├── models/
├── services/
├── main.py
├── Dockerfile
├── requirements.txt (or pyproject.toml)
└── README.md
```

**Changes needed:**
- Update import paths (remove `backend/` prefix)
- Update Dockerfile paths
- Add `.env.example` for environment variables
- Update CI/CD pipelines
- Add API documentation endpoint

#### 3. Update Frontend Repository

**Structure:**
```
forecaster-enterprise-frontend/
├── app/
├── server/
├── public/
├── nuxt.config.ts
├── package.json
├── Dockerfile
└── README.md
```

**Changes needed:**
- Update API base URL to point to backend service
- Update environment variables
- Remove backend dependencies
- Update CI/CD pipelines
- Add API client configuration

#### 4. API Contract Management

**Option A: OpenAPI/Swagger (Current)**
- Backend generates OpenAPI schema
- Frontend can generate TypeScript types from schema
- Tools: `openapi-typescript`, `swagger-codegen`

**Option B: Shared Type Definitions**
- Create separate `api-contracts` package/repo
- Define types in TypeScript
- Backend validates against types (using Pydantic)
- Frontend imports types directly

**Option C: OpenAPI Type Generation (Recommended)**

### 5. Deployment Strategy

**Backend:**
- Deploy as separate service (e.g., `api.forecaster.com`)
- CORS configuration for frontend domain
- API authentication via JWT tokens

**Frontend:**
- Deploy as static site or SSR (e.g., `app.forecaster.com`)
- Configure API endpoint in environment variables
- Handle authentication token storage

### 6. Development Workflow

**Monorepo Tools (Alternative):**
- Use `pnpm workspaces` or `npm workspaces`
- Keep repos separate but linked
- Shared types package

**Independent Development:**
- Backend team works on API contracts
- Frontend team works on UI
- Coordinate via API versioning

---

## API Contract Management (REST + OpenAPI)

Since we're keeping the Python FastAPI backend, we'll use **OpenAPI schema** for type safety:

### Approach: OpenAPI → TypeScript Types

**Backend:** FastAPI automatically generates OpenAPI schema at `/docs` or `/openapi.json`

**Frontend:** Generate TypeScript types from OpenAPI schema

**Tools:**
- `openapi-typescript` - Generate TypeScript types from OpenAPI
- `swagger-codegen` - Alternative code generator
- `openapi-generator` - Full-featured generator

### Implementation Steps

1. **Backend:** Ensure OpenAPI schema is accessible
   ```python
   # FastAPI automatically generates this
   # Access at: http://localhost:8000/openapi.json
   # Or: http://localhost:8000/docs (Swagger UI)
   ```

2. **Frontend:** Generate types from schema
   ```bash
   npm install -D openapi-typescript
   npx openapi-typescript http://localhost:8000/openapi.json -o app/types/api.ts
   ```

3. **Frontend:** Use generated types
   ```typescript
   import type { paths } from '~/types/api';
   
   type ForecastRequest = paths['/api/v1/forecast']['post']['requestBody']['content']['application/json'];
   type ForecastResponse = paths['/api/v1/forecast']['post']['responses']['201']['content']['application/json'];
   ```

4. **Automation:** Add to package.json
   ```json
   {
     "scripts": {
       "generate:types": "openapi-typescript http://localhost:8000/openapi.json -o app/types/api.ts"
     }
   }
   ```

### Benefits

- ✅ Type safety without code generation overhead
- ✅ Types stay in sync with backend API
- ✅ No need to maintain separate type definitions
- ✅ Works with existing Python FastAPI backend
- ✅ Industry standard approach

---

## Implementation Guide: Separate Repositories

### Step 1: Extract Backend

```bash
# Create new backend repo
mkdir forecaster-enterprise-backend
cd forecaster-enterprise-backend
git init

# Copy backend files
cp -r ../forecaster_enterprise/backend/* .

# Update imports (remove backend/ prefix)
find . -name "*.py" -exec sed -i '' 's/from backend\./from /g' {} \;
```

### Step 2: Extract Frontend

```bash
# Create new frontend repo
mkdir forecaster-enterprise-frontend
cd forecaster-enterprise-frontend
git init

# Copy frontend files
cp -r ../forecaster_enterprise/frontend/* .

# Update API base URL
# In nuxt.config.ts or .env
API_BASE_URL=https://api.forecaster.com
```

### Step 3: API Contract

**Create shared types package:**

```typescript
// packages/api-contracts/src/forecast.ts
export interface ForecastRequest {
  itemIds: string[];
  predictionLength: number;
  model?: string;
}

export interface ForecastResponse {
  forecastId: string;
  forecasts: ItemForecast[];
}
```

**Backend validates with Pydantic:**
```python
# backend/schemas/forecast.py
from pydantic import BaseModel

class ForecastRequest(BaseModel):
    item_ids: List[str]
    prediction_length: int
    model: Optional[str] = None
```

**Frontend uses TypeScript types:**
```typescript
// frontend/app/types/forecast.ts
import type { ForecastRequest, ForecastResponse } from '@forecaster/api-contracts';
```

---

## Migration Checklist

### For Repository Separation

- [ ] Create backend repository
- [ ] Create frontend repository
- [ ] Extract and update backend code
- [ ] Extract and update frontend code
- [ ] Set up API contract management
- [ ] Update CI/CD pipelines
- [ ] Configure CORS on backend
- [ ] Update environment variables
- [ ] Test deployment
- [ ] Update documentation

### For OpenAPI Type Generation

- [ ] Verify OpenAPI schema is accessible (`/openapi.json`)
- [ ] Install `openapi-typescript` in frontend
- [ ] Set up type generation script
- [ ] Generate types from backend schema
- [ ] Update frontend to use generated types
- [ ] Set up CI/CD to regenerate types on API changes
- [ ] Test type safety
- [ ] Update documentation

---

## Cost-Benefit Analysis

### Separate Repositories

**Pros:**
- ✅ Clean separation of concerns
- ✅ Independent deployment
- ✅ Team autonomy
- ✅ Technology flexibility
- ✅ Can deploy frontend and backend independently

**Cons:**
- ❌ More complex CI/CD setup
- ❌ Need API contract management
- ❌ Coordination overhead for API changes

### OpenAPI Type Generation

**Pros:**
- ✅ Type safety without manual type definitions
- ✅ Types automatically stay in sync with backend
- ✅ Works with existing Python FastAPI backend
- ✅ No code generation overhead (just type generation)
- ✅ Industry standard approach

**Cons:**
- ❌ Need to regenerate types when API changes
- ❌ Generated types can be verbose
- ❌ Less flexible than manual type definitions

---

## Recommendation

**For your current situation (Python FastAPI backend + Nuxt frontend):**

✅ **Separate repositories + OpenAPI type generation**
- Keep Python FastAPI backend (no migration needed)
- Generate TypeScript types from OpenAPI schema
- Clean separation without major migration
- Type safety through code generation
- Industry standard approach

**Implementation Priority:**
1. Separate repositories (clean architecture)
2. Set up OpenAPI type generation (type safety)
3. Update CI/CD to regenerate types automatically

---

## References

- [OpenAPI TypeScript Generator](https://github.com/drwpow/openapi-typescript)
- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/advanced/openapi-customization/)
- [Git Subtree Guide](https://www.atlassian.com/git/tutorials/git-subtree)
- [Nuxt 3 API Routes](https://nuxt.com/docs/guide/directory-structure/server)

