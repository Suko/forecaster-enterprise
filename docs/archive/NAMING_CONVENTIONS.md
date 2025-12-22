# Naming Conventions

## Item ID Naming Strategy

### Backend (Python/FastAPI)
- **API Path Parameters**: `item_id` (snake_case)
  - Example: `/api/v1/products/{item_id}`
- **Schema Fields**: `item_id` (snake_case)
  - Example: `item_id: str` in Pydantic models
- **Database Columns**: `item_id` (snake_case)
  - Example: `item_id = Column(String(255))`

### Frontend (TypeScript/Nuxt)

#### 1. Route Folders & Parameters
**MUST match backend API path parameter names:**
- ✅ Route folder: `[item_id]` (matches `/products/{item_id}`)
- ✅ Route param extraction: `event.context.params?.item_id`
- ✅ Page route: `[item_id].vue` (matches `/inventory/{item_id}`)

**Why:** Nuxt route parameters must match the backend API paths they proxy to.

#### 2. TypeScript Type Definitions
**MUST match backend schema field names:**
- ✅ Type definitions: `item_id: string` (snake_case)
- ✅ Example: `interface Product { item_id: string }`

**Why:** Type definitions represent backend API responses, so they must match exactly.

#### 3. Variable Names in Code
**RECOMMENDED: Use camelCase for local variables (JavaScript convention)**
- ✅ Local variables: `itemId` (camelCase)
- ✅ Function parameters: `itemId: string`
- ✅ Example: `const itemId = route.params.item_id as string;`

**Alternative: Use snake_case everywhere for consistency**
- ⚠️ Local variables: `item_id` (snake_case)
- ⚠️ More consistent with backend, but not JavaScript convention

**Recommendation:** Use **camelCase** (`itemId`) for local variables to follow JavaScript/TypeScript conventions, while keeping `item_id` for API keys and route parameters.

#### 4. API Request/Response Bodies
**MUST match backend schema field names:**
- ✅ Request body: `{ item_id: "SKU001" }`
- ✅ Response fields: `item_id` (from backend)

**Why:** Backend expects `item_id`, not `itemId`.

### Summary Table

| Context | Convention | Example | Reason |
|---------|-----------|---------|--------|
| Backend API paths | `item_id` | `/products/{item_id}` | Python/FastAPI convention |
| Backend schemas | `item_id` | `item_id: str` | Matches database |
| Frontend route folders | `[item_id]` | `[item_id]/history.get.ts` | Must match backend paths |
| Frontend route params | `item_id` | `params?.item_id` | Must match folder name |
| TypeScript types | `item_id` | `item_id: string` | Must match backend schema |
| Local variables | `itemId` (recommended) | `const itemId = ...` | JavaScript convention |
| API request bodies | `item_id` | `{ item_id: "SKU001" }` | Must match backend schema |

### Examples

#### ✅ Correct: Route Handler
```typescript
// frontend/server/api/products/[item_id]/history.get.ts
export default defineEventHandler(async (event) => {
  const item_id = event.context.params?.item_id; // Matches folder name
  // Use item_id in API call
  return await authenticatedFetch(event, `/api/v1/products/${item_id}/history`);
});
```

#### ✅ Correct: Component with Local Variable
```typescript
// frontend/app/pages/inventory/[item_id].vue
const itemId = computed(() => route.params.item_id as string); // camelCase for local var
const product = await $fetch(`/api/products/${itemId.value}`); // Use camelCase var
```

#### ✅ Correct: API Request Body
```typescript
// frontend/app/composables/useRecommendations.ts
await $fetch("/api/order-planning/cart/add", {
  method: "POST",
  body: {
    item_id: itemId, // Must use item_id (backend expects this)
    supplier_id: supplierId,
  },
});
```

#### ❌ Wrong: Route Folder Mismatch
```typescript
// frontend/server/api/products/[itemId]/history.get.ts
const itemId = event.context.params?.itemId; // ❌ Won't match backend path
```

#### ❌ Wrong: Type Definition Mismatch
```typescript
interface Product {
  itemId: string; // ❌ Backend returns item_id, not itemId
}
```

### Migration Checklist

When standardizing naming:
1. ✅ Route folders: `[itemId]` → `[item_id]`
2. ✅ Route param extraction: `params?.itemId` → `params?.item_id`
3. ✅ Type definitions: Already use `item_id` ✅
4. ⚠️ Variable names: Keep `itemId` (camelCase) OR change to `item_id` (snake_case)
5. ✅ API request bodies: Already use `item_id` ✅

### Decision: Variable Names

**Current State:**
- Route folders: `[item_id]` ✅
- Route params: `item_id` ✅
- Types: `item_id` ✅
- Variables: Mixed (`itemId` and `item_id`)

**Recommendation:**
- Keep route folders and params as `item_id` (required for backend compatibility)
- Keep types as `item_id` (required for backend compatibility)
- **Option A (Recommended):** Keep local variables as `itemId` (JavaScript convention)
- **Option B:** Change all variables to `item_id` (maximum consistency)

**We recommend Option A** - use `itemId` for local variables while keeping `item_id` for API keys and route parameters.

