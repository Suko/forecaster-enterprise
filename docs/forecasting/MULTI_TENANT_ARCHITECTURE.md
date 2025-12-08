# Multi-Tenant Architecture Design

**Date:** 2025-12-06  
**Status:** 📋 Design Document  
**Scope:** Unified architecture for both SaaS and on-premise deployments

---

## Overview

The forecasting system uses a **unified architecture** that works for both SaaS and on-premise deployments:

**Key Insight:** No mode configuration needed! The system is agnostic to deployment model.

**How It Works:**
1. **Clients Table**: Stores all clients (1 client = on-premise, multiple = SaaS)
2. **JWT Token**: Provides `client_id` for every request
3. **Queries**: Always filter by `client_id` (unified)
4. **Schema**: Always includes `client_id` column (unified)

**Deployment Models:**
- **SaaS**: Multiple clients in `clients` table, shared database
- **On-Premise**: One client in `clients` table, separate database

**The Code Doesn't Care:**
- Same queries (always filter by `client_id`)
- Same schema (always include `client_id`)
- Same authentication (always get `client_id` from JWT)
- Same database connection (standard `get_db()`)
- No mode detection needed
- No configuration needed

**Result:** One codebase, works for both models automatically.

---

## Architecture Flow Diagrams

**Note:** These diagrams show deployment differences, but the code is identical for both.

### SaaS Deployment (Multiple Clients)

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Request                              │
│              POST /api/v1/forecast                              │
│              JWT Token: { client_id: "client-1" }                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Extract client_id from JWT                    │
│  client_id = "client-1"                                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Connection                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ get_db() → Returns: db (from DATABASE_URL)               │   │
│  │   → Standard dependency, no special manager needed        │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ForecastService                              │
│  Uses: db (standard session)                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DataAccess                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Query: SELECT * FROM ts_demand_daily                    │   │
│  │         WHERE client_id = 'client-1'  ← FILTER          │   │
│  │         AND item_id IN (...)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Shared PostgreSQL Database                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ts_demand_daily                                          │   │
│  │   client_id | item_id | date | units_sold | ...          │   │
│  │   ──────────┼─────────┼──────┼───────────┼────────        │   │
│  │   client-1  | SKU001  | ...  |    10    | ...            │   │
│  │   client-1  | SKU002  | ...  |     5    | ...            │   │
│  │   client-2  | SKU001  | ...  |    20    | ...            │   │
│  │   client-2  | SKU003  | ...  |    15    | ...            │   │
│  │   ──────────┴─────────┴──────┴───────────┴────────        │   │
│  │                                                           │   │
│  │ forecast_runs                                             │   │
│  │   client_id | forecast_run_id | ...                      │   │
│  │   ──────────┼────────────────┼────────                    │   │
│  │   client-1  | run-123        | ...                       │   │
│  │   client-2  | run-456        | ...                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Key Points:
- Single database connection pool
- All queries filter by client_id
- Data isolation via WHERE clause
- Efficient for many small clients
```

### On-Premise Deployment (One Client)

```
┌─────────────────────────────────────────────────────────────────┐
│                         API Request                              │
│              POST /api/v1/forecast                              │
│              JWT Token: { client_id: "client-1" }                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Extract client_id from JWT                    │
│  client_id = "client-1" (always same in on-premise)             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Database Connection                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ get_db() → Returns: db (from DATABASE_URL)             │   │
│  │   → Standard dependency, same as SaaS                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ForecastService                              │
│  Uses: db (standard session, same as SaaS)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DataAccess                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Query: SELECT * FROM ts_demand_daily                    │   │
│  │         WHERE client_id = 'client-1'  ← FILTER          │   │
│  │         AND item_id IN (...)                            │   │
│  │         (Same query as SaaS - unified)                   │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│              Client's PostgreSQL Database                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ts_demand_daily                                          │   │
│  │   client_id | item_id | date | units_sold | ...         │   │
│  │   ──────────┼─────────┼──────┼───────────┼────────        │   │
│  │   client-1 | SKU001  | ...  |    10    | ...            │   │
│  │   client-1 | SKU002  | ...  |     5    | ...            │   │
│  │   ──────────┴─────────┴──────┴───────────┴────────        │   │
│  │   (Always same client_id in on-premise)                  │   │
│  │                                                           │   │
│  │ forecast_runs                                             │   │
│  │   client_id | forecast_run_id | ...                      │   │
│  │   ──────────┼────────────────┼────────                    │   │
│  │   client-1  | run-123        | ...                       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

Key Points:
- One client per deployment (separate database)
- **Same schema as SaaS** (includes `client_id` column - unified)
- **Same queries as SaaS** (filter by `client_id` - unified)
- Complete data isolation (separate deployment)
- Better for large enterprise clients
- **Unified codebase** (no mode-specific logic)
```

### Request Flow Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                    REQUEST FLOW (Unified)                       │
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  API Request                                                    │
│    ↓                                                            │
│  Extract client_id from JWT token                               │
│    ↓                                                            │
│  Get database session (standard get_db())                        │
│    → Returns: db (from DATABASE_URL)                            │
│    ↓                                                            │
│  ForecastService.generate_forecast(client_id="client-1", ...)  │
│    ↓                                                            │
│  DataAccess.fetch_historical_data(client_id="client-1", ...)    │
│    → Query: WHERE client_id = 'client-1'  ← FILTER            │
│    ↓                                                            │
│  Database (shared or separate - code doesn't care)              │
│                                                                  │
│  Note: Same flow for both SaaS and on-premise!                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Startup                          │
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Application Startup                                            │
│    ↓                                                            │
│  Read DATABASE_URL environment variable                         │
│    ↓                                                            │
│  Initialize database connection (standard get_db())              │
│    └─ Single connection from DATABASE_URL                       │
│    ↓                                                            │
│  Ready to handle requests                                       │
│                                                                  │
│  Note: No mode detection needed!                                │
│  - Code works the same for both deployments                     │
│  - Deployment model determined by:                              │
│    1. Number of clients in clients table                        │
│    2. Database architecture (shared vs separate)                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Design

### Core Principle: Unified Database Connection

**Key Insight:** No special tenant manager needed! Just use standard database connection.

**Implementation:**
- Standard `get_db()` dependency (from `models/database.py`)
- Returns `AsyncSession` from `DATABASE_URL`
- Works for both SaaS and on-premise
- No mode detection needed
- No special configuration needed

---

## Implementation Details

### 1. No Mode Detection Needed

**Key Insight:** The system doesn't need to know if it's SaaS or on-premise.

**How It Works:**
- Check `clients` table: 1 client = on-premise deployment, multiple = SaaS deployment
- But the code doesn't need to check - it just filters by `client_id` regardless
- Deployment model is determined by:
  - **Number of clients** in the database (1 vs many)
  - **Database architecture** (shared vs separate) - but this is deployment, not code

**No Configuration Required:**
- No `TENANT_MODE` environment variable needed
- No mode detection logic needed
- Code works the same way for both models

### 2. Database Connection Strategy

**Unified Approach:** Both models use the same database connection strategy.

#### How It Works
- **Single database connection** (from `DATABASE_URL`)
- **All queries filter by `client_id`** (unified)
- **Same schema** (includes `client_id` column)
- **Same connection pool** (same configuration)

#### Deployment Differences (Not Code Differences)
- **SaaS**: Multiple clients share one database (different `client_id` values)
- **On-Premise**: One client per database (same `client_id` value, but still filtered)

**The Code Doesn't Care:**
- Same connection logic
- Same query logic
- Same schema
- No mode-specific code needed

### 3. Service Layer (Unified)

#### ForecastService
**Implementation:**
```python
def __init__(
    self, 
    db: AsyncSession,  # Standard database session
    use_test_data: bool = False
):
    self.db = db
    self.use_test_data = use_test_data

async def generate_forecast(self, client_id: str, ...):
    # client_id from JWT token
    # Use self.db (standard session)
    # All queries filter by client_id (unified)
```

#### DataAccess
**Implementation:**
```python
async def _fetch_from_database(
    self, 
    client_id: str,  # From JWT token
    ...
):
    # Unified query - same for both deployments
    # On-premise: client_id always same value (deployment's client)
    # SaaS: client_id varies per request
    query = text("""
        SELECT ... FROM ts_demand_daily
        WHERE client_id = :client_id  -- Always filter (unified)
    """)
```

### 4. API Layer (Unified)

**Implementation:**
```python
@router.post("/forecast")
async def create_forecast(
    request: ForecastRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),  # Standard dependency
):
    # Get client_id from JWT token (unified for both deployments)
    client_id = current_user.client_id  # From JWT claims
    
    # Use standard database session (works for both SaaS and on-premise)
    service = ForecastService(db, use_test_data=True)
```

---

## Configuration

### Configuration (Unified)

**No Mode Configuration Needed!**

```bash
# .env (same for both SaaS and on-premise)
DATABASE_URL=postgresql://user:pass@host/database
```

**That's it!** No `TENANT_MODE` variable needed.

### How Deployment Models Work

#### SaaS Deployment
- **Setup**: Create multiple clients in `clients` table
- **Database**: Shared database with multiple clients
- **Code**: Same as on-premise (filters by `client_id`)

#### On-Premise Deployment
- **Setup**: Create 1 client in `clients` table during initial setup
- **Database**: Separate database (deployment architecture)
- **Code**: Same as SaaS (filters by `client_id`)

**The Code is Identical:**
- Same queries (always filter by `client_id`)
- Same schema (always include `client_id`)
- Same authentication (always get `client_id` from JWT)
- Same database connection (standard `get_db()`)
- No mode detection needed

---

## Migration Path

### Phase 1: Current State
- ✅ All queries filter by `client_id`
- ✅ Single database connection
- ✅ Works for SaaS deployment

### Phase 2: Unified Implementation
- ✅ Ensure `clients` table exists
- ✅ Ensure all tables include `client_id` column
- ✅ Ensure all queries filter by `client_id`
- ✅ Extract `client_id` from JWT token in API layer
- ✅ Use standard `get_db()` dependency (no special manager needed)

### Phase 3: Testing
- ✅ Test with multiple clients (SaaS scenario)
- ✅ Test with single client (on-premise scenario)
- ✅ Same code path for both (no mode-specific tests needed)
- ✅ Integration tests verify `client_id` filtering works

---

## Benefits

### ✅ Maximum Unification
- **Same schema**: Both deployments include `client_id` column
- **Same queries**: Both deployments filter by `client_id`
- **Same authentication**: Both deployments get `client_id` from JWT token
- **Same codebase**: No mode-specific logic needed
- **No configuration needed**: System is agnostic to deployment model

### ✅ Single Codebase
- One implementation for both deployment models
- No code duplication
- Easier maintenance

### ✅ Zero Configuration
- No environment variables needed (except `DATABASE_URL`)
- No mode detection logic
- No special managers needed
- Just works for both deployments

### ✅ Backward Compatible
- Existing code continues to work
- Just add `client_id` filtering to queries
- No breaking changes

### ✅ Simple Implementation
- Use standard `get_db()` dependency
- Queries are identical (both filter by `client_id`)
- Schema is identical (both include `client_id` column)
- Only deployment differs (shared DB vs separate DB) - but code doesn't care

---

## Implementation Checklist

### Step 1: Core Setup ✅
- [x] Create `clients` table (if not exists)
- [x] Ensure all tables include `client_id` column
- [x] Use standard `get_db()` dependency
- [x] All queries filter by `client_id`
- [x] Get `client_id` from JWT token

### Step 2: Update Services
- [ ] Ensure `ForecastService` uses standard `db: AsyncSession`
- [ ] Ensure `DataAccess` always filters by `client_id` (unified)
- [ ] Ensure `QualityCalculator` filters by `client_id` if needed
- [ ] Verify all queries filter by `client_id` (same for both deployments)

### Step 3: Update API Layer
- [ ] Extract `client_id` from JWT token (add to User model or JWT claims)
- [ ] Update forecast endpoints to use `client_id` from JWT
- [ ] Update inventory endpoints to use `client_id` from JWT
- [ ] Update quality endpoints to use `client_id` from JWT

### Step 4: Database Setup
- [ ] Create `clients` table migration (if not exists)
- [ ] Ensure all tables include `client_id` column
- [ ] Document initial setup (create 1 client for on-premise, multiple for SaaS)

### Step 5: Testing
- [ ] Test with multiple clients (SaaS scenario)
- [ ] Test with single client (on-premise scenario)
- [ ] Verify `client_id` filtering works correctly
- [ ] Integration tests (same code path for both)

### Step 6: Documentation
- [ ] Update `ARCHITECTURE.md`
- [ ] Update `INTEGRATION.md`
- [ ] Add deployment guide
- [ ] Document JWT token structure

---

## Current Status

**✅ Design Simplified:** No mode configuration needed!

**✅ Key Decisions:**
- ✅ Unified schema (always include `client_id` column)
- ✅ Unified queries (always filter by `client_id`)
- ✅ Unified authentication (JWT token with `client_id`)
- ✅ Unified codebase (no mode-specific logic)
- ✅ **No `TENANT_MODE` config needed** - system is agnostic
- ✅ **No `TenantDatabaseManager` needed** - use standard `get_db()`

**How It Works:**
- **SaaS**: Multiple clients in `clients` table → system handles multiple clients
- **On-Premise**: One client in `clients` table → system handles one client
- **Code**: Identical for both (just filters by `client_id`)

**⏳ Pending:**
- Ensure `clients` table exists
- Ensure all queries filter by `client_id`
- Extract `client_id` from JWT token in API layer
- Testing (same code path for both deployments)

---

## Design Decisions

### 1. **Client ID Source** ✅ DECIDED
- **Both deployments**: Get `client_id` from JWT token
- **Unified approach**: Same authentication flow for SaaS and on-premise
- **Implementation**: Extract `client_id` from JWT claims (e.g., `client_id` claim)

### 2. **Database Schema** ✅ DECIDED
- **Unified schema**: Same tables, same columns in both deployments
- **Both deployments include `client_id` column**: For consistency and future flexibility
- **On-premise**: `client_id` column exists but always has same value (the deployment's client)
- **SaaS**: `client_id` column used for filtering (different values per client)
- **Benefit**: Same code, same migrations, same schema - just different deployment model

### 3. **Connection Pooling** ✅ DECIDED
- **Both deployments**: Single connection pool (same as SaaS)
- **Pool size**: Same configuration for both deployments
- **Reason**: Same connection needs regardless of deployment model

### 4. **Unified Design** ✅ DECIDED
- **Goal**: Maximum code unification between SaaS and on-premise
- **Implementation**: 
  - Same queries (always filter by `client_id`)
  - Same schema (always include `client_id` column)
  - Same authentication (JWT token with `client_id`)
  - Same database connection (standard `get_db()`)
  - **No configuration needed** - system is agnostic
- **Benefit**: One codebase, works for both deployment models automatically

---

## Is This Good Practice? ✅ YES

### ✅ Industry Best Practices

1. **Single Codebase Principle**
   - ✅ One codebase for multiple deployment models
   - ✅ Reduces maintenance burden
   - ✅ Easier to test and deploy

2. **Configuration Over Code**
   - ✅ No mode-specific logic in code
   - ✅ Deployment model determined by data, not configuration
   - ✅ Follows "convention over configuration" principle

3. **Database Design**
   - ✅ Consistent schema across deployments
   - ✅ Same migrations work for both
   - ✅ Easy to migrate between models

4. **Security**
   - ✅ `client_id` from JWT (authenticated source)
   - ✅ Always filter by `client_id` (defense in depth)
   - ✅ Works even if JWT is compromised (database-level filtering)

5. **Scalability**
   - ✅ SaaS: Efficient for many small clients
   - ✅ On-premise: Complete isolation for enterprise clients
   - ✅ Can scale either model independently

### ✅ Advantages

1. **Simplicity**
   - No mode detection logic
   - No special managers needed
   - Standard database connection
   - Easy to understand and maintain

2. **Flexibility**
   - Can switch between models by changing data (clients table)
   - No code changes needed
   - Easy to test both scenarios

3. **Maintainability**
   - Single code path
   - No mode-specific bugs
   - Easier to debug
   - Clearer codebase

4. **Future-Proof**
   - Easy to add features (work for both models)
   - Can add mode-specific optimizations later if needed
   - Schema supports future requirements

### ⚠️ Considerations

1. **Performance**
   - On-premise: Filtering by `client_id` when there's only one client is redundant
   - **Mitigation**: Database indexes on `client_id` make this negligible
   - **Trade-off**: Acceptable for code simplicity

2. **Schema Overhead**
   - On-premise: `client_id` column always same value
   - **Mitigation**: Minimal storage overhead, worth it for unification
   - **Trade-off**: Acceptable for code simplicity

3. **Initial Setup**
   - On-premise: Must create 1 client in `clients` table
   - **Mitigation**: Simple setup script or migration
   - **Trade-off**: One-time setup, worth it for unification

### ✅ Conclusion

**This is excellent practice!** The unified design:
- ✅ Follows industry best practices
- ✅ Simplifies codebase significantly
- ✅ Reduces maintenance burden
- ✅ Makes testing easier
- ✅ Future-proof architecture

The minor performance overhead (filtering by `client_id` in on-premise) is negligible compared to the benefits of code unification.

---

## Next Steps

1. **Review this design** - Confirm unified approach
2. **Implement unified design** - Use standard `get_db()`, filter by `client_id`
3. **Update API layer** - Extract `client_id` from JWT token
4. **Create clients table** - If not exists
5. **Test both scenarios** - Multiple clients (SaaS) and single client (on-premise)
6. **Update documentation** - Architecture, integration guides

---

**Status:** Design complete, ready for implementation
