# Security Findings Analysis & Frontend Impact Assessment

## Current Architecture

### Backend (FastAPI)
- JWT tokens issued via `/auth/login` and `/auth/register`
- Tokens accepted from both `Authorization: Bearer <token>` header AND `access_token` cookie
- CORS configured with `allow_credentials=True`
- No rate limiting, password policy, or CSRF protection

### Frontend (Nuxt.js)
- Uses `nuxt-auth-utils` for session management
- **All API calls go through Nuxt server routes** (`server/api/auth/login.post.ts`)
- **Tokens are sent via Authorization headers only** (not cookies)
- Nuxt stores user session server-side, not JWT in browser cookies
- Frontend → Nuxt server → FastAPI backend (server-to-server)

## Security Findings & Frontend Impact

### 1. JWT Secret Key (CRITICAL - No Frontend Impact)

**Issue**: `JWT_SECRET_KEY` defaults to empty string in development, allowing token forgery.

**Current Code**:
```python
# config.py:38
secret_key: str = os.getenv("JWT_SECRET_KEY", "")
# Only validates in non-dev environments (line 55)
```

**Frontend Impact**: ✅ **NONE** - Frontend doesn't generate tokens, only receives and uses them.

**Solution**: 
- Require non-empty secret in ALL environments
- Generate strong default for development (warn if using default)
- Remove `override=True` from `load_dotenv()` to prevent .env from overwriting runtime secrets

---

### 2. Database Credentials & TLS (CRITICAL - No Frontend Impact)

**Issue**: Default `postgres/postgres` credentials and no TLS enforcement.

**Current Code**:
```python
# config.py:32-35
database_url: str = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/forecaster_enterprise"
)
```

**Frontend Impact**: ✅ **NONE** - Database connection is backend-only.

**Solution**:
- Require `DATABASE_URL` in production (no default)
- Parse and enforce `sslmode=require` for remote databases
- Keep localhost default for development only

---

### 3. Debug Mode & CORS (MEDIUM - Potential Frontend Impact)

**Issue**: `DEBUG=true` and `0.0.0.0` binding with permissive CORS in production.

**Current Code**:
```python
# config.py:28-29, 43
debug: bool = os.getenv("DEBUG", "false").lower() in ["true", "1", "yes"]
api_host: str = os.getenv("API_HOST", "0.0.0.0")
# main.py:21-24 - CORS allows all methods/headers
```

**Frontend Impact**: ⚠️ **POTENTIAL** - If CORS origins are restricted, frontend must be updated.

**Current CORS Config**:
```python
cors_origins: list[str] = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://localhost:5173"
).split(",")
```

**Solution**:
- Disable debug mode in production (fail if DEBUG=true in production)
- Restrict CORS origins in production (keep permissive for dev)
- Bind to `127.0.0.1` in production, `0.0.0.0` only in dev

**Frontend Coordination Needed**: 
- If production CORS changes, ensure frontend origin matches
- Current defaults (`localhost:3000`, `localhost:5173`) should work for dev

---

### 4. Rate Limiting & Password Policy (MEDIUM - Minor Frontend Impact)

**Issue**: No rate limiting on auth endpoints, no password validation.

**Current Code**:
```python
# api/auth.py:40-98 - No rate limiting, no password checks
@router.post("/login", response_model=Token)
@router.post("/register", response_model=UserResponse)
```

**Frontend Impact**: ⚠️ **MINOR UX** - Error messages may change, registration may reject weak passwords.

**Solution**:
- Add rate limiting (e.g., `slowapi` or `fastapi-limiter`)
- Password policy: min 8 chars, max 72 chars (bcrypt limit)
- Return clear error messages for rate limits and password validation

**Frontend Coordination Needed**:
- Update error handling to show rate limit messages
- Add client-side password validation (optional, but improves UX)
- Update registration form to show password requirements

---

### 5. JWT Cookie Support & CSRF (LOW - No Frontend Impact)

**Issue**: Backend accepts JWTs from cookies without CSRF protection, but frontend doesn't use cookies.

**Current Code**:
```python
# auth/dependencies.py:12, 28-30
access_token: Optional[str] = Cookie(None)
# Falls back to cookie if no Authorization header
```

**Frontend Reality**: 
- Frontend uses `Authorization: Bearer <token>` headers only
- Nuxt server routes add headers automatically
- No cookie-based authentication in use

**Frontend Impact**: ✅ **NONE** - Cookie support is unused fallback.

**Solution Options**:

**Option A: Remove Cookie Support (Recommended)**
- Remove `Cookie` parameter from `get_current_user`
- Only accept `Authorization` header
- **No frontend changes needed** ✅

**Option B: Keep Cookies + Add CSRF**
- Add CSRF token validation for cookie-based auth
- Keep header-based auth as primary
- **No frontend changes needed** (frontend uses headers) ✅

**Recommendation**: **Option A** - Simpler, removes attack surface, no frontend impact.

---

### 6. Token Type Validation (LOW - No Frontend Impact)

**Issue**: No validation that refresh tokens aren't used as access tokens.

**Current Code**:
```python
# auth/jwt.py:14-25 - Tokens have "type" field but it's not checked
to_encode.update({"exp": expire, "type": "access"})  # Set but not validated
```

**Frontend Impact**: ✅ **NONE** - Frontend only uses access tokens from login.

**Solution**:
- Validate `type` field in `decode_token()` or `get_current_user()`
- Reject tokens with wrong type
- **No frontend changes needed** ✅

---

## Recommended Implementation Plan

### Phase 1: Critical Security (No Frontend Changes)
1. ✅ Require JWT_SECRET_KEY in all environments
2. ✅ Enforce database TLS for remote connections
3. ✅ Disable debug mode in production
4. ✅ Validate JWT token type

### Phase 2: Medium Priority (Minor Frontend Updates)
5. ⚠️ Add rate limiting (update error handling)
6. ⚠️ Add password policy (update registration form)
7. ⚠️ Restrict CORS in production (coordinate origins)

### Phase 3: Cleanup (No Frontend Impact)
8. ✅ Remove unused cookie support (or add CSRF if keeping)
9. ✅ Improve .env loading (prevent override of runtime secrets)

---

## Frontend Changes Required

### Minimal Changes (Error Handling)
- Update login/register error handling for rate limit responses
- Show password requirements in registration form
- Handle new validation error messages

### No Changes Needed
- Token handling (uses headers, not cookies)
- Authentication flow (server-side via Nuxt)
- CORS (if origins match current config)

---

## Testing Checklist

After implementing fixes:
- [ ] Login still works (Authorization header)
- [ ] Registration validates passwords
- [ ] Rate limiting shows appropriate errors
- [ ] CORS allows frontend origins
- [ ] Token type validation works
- [ ] No cookie-based auth breaks (if removed)

