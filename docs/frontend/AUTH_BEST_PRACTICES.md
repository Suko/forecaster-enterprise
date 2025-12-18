# Nuxt Auth Utils - Best Practices Review

## Current Implementation Status

### ✅ What We're Doing Right:

1. **Server-side Protection** ✅
   - Using `requireUserSession(event)` in all protected API routes
   - Properly throws 401 errors when session is missing
   - Example: `server/api/dashboard.get.ts`

2. **Client-side Session Management** ✅
   - Using `useUserSession()` composable correctly
   - Checking `loggedIn.value` in middleware
   - Calling `fetch()` after login to refresh session
   - Using `clear()` to clear session on logout/errors

3. **Session Storage** ✅
   - Using `setUserSession(event, {...})` in login endpoint
   - Storing access token and user info securely
   - Using encrypted HttpOnly cookies (default in nuxt-auth-utils)

4. **Route Protection** ✅
   - Auth middleware checks `loggedIn` before allowing access
   - Applied to all protected pages via `definePageMeta({ middleware: 'auth' })`

### ⚠️ Areas for Improvement:

1. **Middleware ReturnTo Parameter** ⚠️
   - Current: Redirects to `/login` without preserving intended destination
   - Should: Preserve `returnTo` query parameter for better UX

2. **Session Validation** ⚠️
   - Current: Only checks if session exists (`loggedIn.value`)
   - Should: Also validate that session is still valid (token not expired)

3. **Error Handling** ⚠️
   - Current: Manual 401 error handling in each page
   - Should: Could use a global error handler or improve composable

4. **Optional Auth Routes** ⚠️
   - Current: All routes use `requireUserSession` (throws on missing)
   - Should: Use `getUserSession` for optional auth routes (if needed)

## Recommended Improvements

### 1. Enhanced Auth Middleware

```typescript
// app/middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn } = useUserSession()

  if (!loggedIn.value) {
    // Preserve the intended destination
    return navigateTo({
      path: '/login',
      query: { returnTo: to.fullPath }
    })
  }
})
```

### 2. Session Validation (Optional but Recommended)

For routes that need to verify the token is still valid:

```typescript
// In server routes, after requireUserSession
const { user } = await requireUserSession(event)

// Optionally validate token with backend
try {
  await authenticatedFetch(event, '/api/v1/auth/me')
} catch (error) {
  // Token invalid, clear session
  await clearUserSession(event)
  throw createError({
    statusCode: 401,
    statusMessage: 'Session expired'
  })
}
```

### 3. Global Error Handler (Already Implemented ✅)

We have `useAuthError` composable which handles 401 errors properly.

### 4. Session Refresh Strategy

Consider implementing automatic session refresh before expiration:

```typescript
// In a plugin or composable
export default defineNuxtPlugin(() => {
  const { user, fetch } = useUserSession()
  
  // Refresh session periodically (e.g., every 5 minutes)
  if (process.client) {
    setInterval(async () => {
      if (user.value) {
        await fetch()
      }
    }, 5 * 60 * 1000) // 5 minutes
  }
})
```

## Best Practices Checklist

- [x] Use `requireUserSession` in protected server routes
- [x] Use `useUserSession` for client-side session access
- [x] Call `fetch()` after login to refresh session
- [x] Use `clear()` to clear session on logout
- [x] Protect routes with middleware
- [ ] Preserve returnTo in middleware redirect
- [ ] Validate session token periodically (optional)
- [x] Handle 401 errors gracefully
- [x] Use encrypted cookies (default in nuxt-auth-utils)
- [x] Set NUXT_SESSION_PASSWORD in production

## Security Considerations

1. **Session Password**: Ensure `NUXT_SESSION_PASSWORD` is set in production
   - Should be 32+ characters
   - Should be unique per environment
   - Should be stored securely (env vars, secrets manager)

2. **Token Storage**: 
   - ✅ Stored in encrypted HttpOnly cookies (secure)
   - ✅ Not accessible via JavaScript (XSS protection)
   - ✅ Automatically sent with requests

3. **Token Expiration**:
   - Backend controls token expiration
   - Frontend should handle 401 errors gracefully (✅ done)

4. **CSRF Protection**:
   - nuxt-auth-utils handles this automatically
   - Cookies are SameSite by default

## Current Implementation Score: 8.5/10

**Strengths:**
- Proper use of nuxt-auth-utils APIs
- Secure session storage
- Good error handling
- Clean separation of concerns

**Improvements Needed:**
- Preserve returnTo in middleware
- Consider session validation
- Optional: Auto-refresh sessions
