# Authentication with nuxt-auth-utils

This document explains how authentication is managed in the frontend using `nuxt-auth-utils`, following the [official Nuxt 4.x guide](https://nuxt.com/docs/4.x/guide/recipes/sessions-and-authentication).

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │         │  Nuxt Server │         │  FastAPI    │
│   (Client)  │────────▶│   Routes    │────────▶│   Backend   │
└─────────────┘         └──────────────┘         └─────────────┘
     Session Cookie          JWT Token              JWT Validation
```

## Setup

### 1. Module Installation

The `nuxt-auth-utils` module is installed and configured in `nuxt.config.ts`:

```typescript
modules: ['nuxt-auth-utils']
```

### 2. Cookie Encryption Key

Session cookies are encrypted using `NUXT_SESSION_PASSWORD` environment variable (set in `.env` file).

### 3. Server Utilities (`server/utils/api.ts`)

**`getAccessToken(event)`**: Retrieves the JWT token from the user session.

**`authenticatedFetch(event, endpoint, options)`**: Makes authenticated requests to the FastAPI backend. Automatically:
- Retrieves JWT token from session
- Adds `Authorization: Bearer <token>` header
- Handles authentication errors

**`validateToken(event)`**: Validates the JWT token with the backend by calling `/auth/me`.

### 4. Server Routes

#### `/api/login` (`server/api/login.post.ts`)
- Uses `readValidatedBody` with Zod schema validation (official pattern)
- Forwards credentials to FastAPI `/auth/login`
- Receives JWT `access_token` from backend
- Fetches user info from `/auth/me` using the token
- Stores token and user info in session using `setUserSession()`
- Returns empty object `{}` (official pattern)

#### `/api/me` (`server/api/me.get.ts`)
- Protected with `requireUserSession()` (official pattern)
- Fetches current user info from backend `/auth/me`
- Updates session with latest user info
- Automatically clears session if token is invalid

### 5. Client Composable (`app/composables/useApi.ts`)

**`useApi()`**: Provides `apiCall()` method for making authenticated API calls from client components.

```typescript
const { apiCall } = useApi()
const data = await apiCall('/some-endpoint', { method: 'GET' })
```

All client API calls go through Nuxt server routes, which handle JWT tokens automatically.

### 6. Middleware (`app/middleware/auth.ts`)

- Uses `loggedIn` from `useUserSession()` (official pattern)
- Redirects unauthenticated users to `/login`
- Applied to protected routes via `definePageMeta({ middleware: 'auth' })`

## Authentication Flow

### Login Flow

1. User submits credentials on `/login` page
2. Frontend calls `/api/login` (Nuxt server route)
3. Nuxt server validates body with Zod schema using `readValidatedBody` (official pattern)
4. Nuxt server forwards to FastAPI `/auth/login`
5. FastAPI validates credentials and returns JWT token
6. Nuxt server fetches user info from `/auth/me` using token
7. Nuxt server stores token and user info in session using `setUserSession()`
8. Client calls `refreshSession()` from `useUserSession()` composable (official pattern)
9. Browser receives session cookie (HttpOnly, secure)
10. User is redirected to `/dashboard`

### Authenticated Request Flow

1. Client makes request to `/api/some-endpoint` (Nuxt server route)
2. Nuxt server route uses `authenticatedFetch()` utility
3. Utility retrieves JWT token from session
4. Utility adds `Authorization: Bearer <token>` header
5. Request is forwarded to FastAPI backend
6. FastAPI validates token and processes request
7. Response is returned to client

### Token Validation

- Tokens are validated on each authenticated request
- If token is invalid (401), session is automatically cleared
- User is redirected to login page

## Security Features

1. **JWT tokens never exposed to browser JavaScript**
   - Tokens stored only in server-side session
   - Browser only receives session cookie

2. **Automatic token validation**
   - Every authenticated request validates token with backend
   - Invalid tokens automatically clear session

3. **Session management**
   - Sessions managed by `nuxt-auth-utils`
   - Configurable session expiry (default: 7 days)
   - Secure, HttpOnly cookies

## Usage Examples

### Making Authenticated Requests from Server Routes

```typescript
// server/api/inventory.get.ts
import { authenticatedFetch } from '../utils/api'

export default defineEventHandler(async (event) => {
  const inventory = await authenticatedFetch(event, '/api/inventory')
  return inventory
})
```

### Making Authenticated Requests from Client

```vue
<script setup>
const { apiCall } = useApi()

const fetchInventory = async () => {
  try {
    const data = await apiCall('/inventory', { method: 'GET' })
    // Handle data
  } catch (error) {
    // Handle error
  }
}
</script>
```

### Accessing User Session

```vue
<script setup>
const { loggedIn, user, clear: clearSession } = useUserSession()

// Check if user is logged in (official pattern)
if (loggedIn.value) {
  console.log('User is logged in')
  console.log(user.value?.email)
}

// Logout (official pattern)
async function logout() {
  await clearSession()
  await navigateTo('/login')
}
</script>
```

## Configuration

### Environment Variables

`.env` file contains:
```
NUXT_SESSION_PASSWORD=your-secure-random-password-with-at-least-32-characters
```

This is automatically generated in development if not set.

## Backend Integration

The backend expects:
- JWT tokens in `Authorization: Bearer <token>` header
- Token type validation ("access" vs "refresh")
- Token expiry: 30 minutes (configurable in backend)

## Notes

- JWT tokens expire after 30 minutes (backend setting)
- Sessions expire after 7 days (frontend setting)
- When token expires, user must log in again
- All API calls go through Nuxt server routes (no direct backend calls from browser)

