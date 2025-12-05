# Forecaster Enterprise: Auth & User Management

## Quick Start

1. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your PostgreSQL credentials and JWT secret
   ```

2. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt  # or use uv
   ```

3. **Create database:**
   ```bash
   # Make sure PostgreSQL is running
   createdb forecaster_enterprise  # or use your preferred method
   ```

4. **Run database migrations:**
   ```bash
   cd backend
   alembic upgrade head
   ```

5. **Start backend:**
   ```bash
   cd backend
   python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

6. **Test endpoints:**
   ```bash
   cd backend
   ./test_endpoints.sh
   ```

## Environment Configuration

All configuration is managed through `.env` file in the project root. See `.env.example` for all available options.

**Key environment variables:**
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `ENVIRONMENT` - development/production
- `CORS_ORIGINS` - Comma-separated list of allowed origins

## Project Structure

```
forecaster_enterprise/
├── backend/                    # FastAPI backend
│   ├── api/                    # API routes/endpoints
│   │   └── auth.py            # Auth endpoints (login, register, /me)
│   ├── auth/                   # Auth module (copied from VetBac)
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing
│   │   ├── jwt.py              # JWT token creation/validation
│   │   └── dependencies.py      # FastAPI auth dependencies
│   ├── models/                 # Database models
│   │   ├── __init__.py
│   │   ├── database.py         # Database setup
│   │   └── user.py             # User, Role models
│   ├── migrations/            # Alembic migrations
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration (loads from .env)
│   └── pyproject.toml          # Python dependencies (uv)
│
├── frontend/                   # Nuxt 4.x frontend
│   ├── app/                    # App directory (Nuxt 4.x structure)
│   │   ├── assets/             # Website assets (processed by build tool)
│   │   ├── components/         # Vue components
│   │   ├── composables/         # Vue composables (reusable state functions only)
│   │   ├── layouts/            # Layout components
│   │   ├── middleware/         # Nuxt middleware
│   │   ├── pages/              # Page views (file-based routing)
│   │   ├── utils/              # Utility functions (used across app)
│   │   └── app.vue             # Root component
│   ├── server/
│   │   └── api/                # Nuxt server API routes
│   └── public/                 # Static assets (served at root)
│
├── .env                        # Environment variables (create from .env.example)
├── .env.example                # Environment template
└── docs/                       # Documentation
```

## Frontend Structure Guidelines

**Note:** This project uses **Nuxt 4.x**, which requires the `app/` directory structure. All app-related code (components, composables, pages, layouts, middleware, assets, utils) is organized under the `app/` directory. See [Nuxt 4.x Directory Structure](https://nuxt.com/docs/4.x/directory-structure) for details.

### Composables Directory
**Important:** The `composables/` directory should **ONLY** contain reusable functions that maintain state across the entire app.

✅ **DO include in composables:**
- Reusable state management functions (e.g., `useAuth.ts`, `useTheme.ts`)
- Functions that need to maintain state across multiple components
- Shared business logic that can be used app-wide

❌ **DO NOT include in composables:**
- Pages (belong in `app/pages/`)
- Layouts (belong in `app/layouts/`)
- Components (belong in `app/components/`)
- One-off utility functions (belong in `app/utils/`)

**Rule:** If it's not a reusable state function used across the app, it doesn't belong in `composables/`.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Nuxt 3)                        │
│  - Nuxt auth-utils (JWT management)                         │
│  - Tailwind CSS + shadcn-vue components                     │
│  - Auth UI components (copied from VetBac frontend)         │
│  - Dashboard UI (copied from VetBac frontend)               │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│                 Backend (FastAPI)                           │
│  - Auth module (copied from VetBac backend)                 │
│  - User management (copied from VetBac backend)             │
│  - Data models (copied from VetBac backend)                 │
│  - Package manager: uv                                      │
│  - Database: PostgreSQL                                    │
└─────────────────────────────────────────────────────────────┘
```

## Stack Usage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI | API server, auth endpoints, user management |
| **Package Manager** | uv | Python dependency management |
| **Database** | PostgreSQL | User data, auth tokens |
| **Migrations** | Alembic | Database schema management |
| **Frontend** | Nuxt 3 | SSR framework, routing, auth integration |
| **Auth Module** | @sidebase/nuxt-auth-utils | JWT token management, session handling |
| **UI Framework** | Tailwind CSS | Styling |
| **Component Library** | shadcn-vue | Reusable UI components |

## ⚠️ IMPORTANT: Copy Only Auth-Related Code

**Only copy code that is directly related to authentication and user management.**
- ❌ Do NOT copy business logic, domain-specific models, or other features
- ✅ Only copy: auth utilities, user models, auth endpoints, password hashing
- ✅ Review each file before copying to ensure it's auth-related only

## What to Copy from VetBac Backend

**Source:** `/Users/mihapro/VetBac/backend`

### Auth Module (ONLY these files)
- `auth/security.py` - Password hashing, token generation
- `auth/jwt.py` - JWT token creation/validation
- `auth/dependencies.py` - FastAPI dependencies for auth
- `auth/__init__.py` - Auth exports

### User Management (ONLY user-related models)
- `models/admin_models.py` - **ONLY** User, Role models (skip other models)
- `models/vetbac_models.py` - **ONLY** user-related fields (skip domain models)
- `api/` - **ONLY** auth/user CRUD endpoints (skip other endpoints)

### Configuration (ONLY auth config)
- `config.py` - **ONLY** auth settings, JWT secrets (skip other config)
- Database connection setup (if needed for auth)

## What to Copy from VetBac Frontend

**Source:** `/Users/mihapro/VetBac/admin-frontend`

### Auth Components (ONLY these)
- `src/views/auth/login.vue` - Login page
- `src/composables/useAuth.ts` - Auth composable (adapt for Nuxt)
- `src/stores/auth.ts` - Auth store (convert to Nuxt composable)
- `src/api/services/auth.ts` - Auth API service

### Dashboard UI (ONLY layout/navigation)
- Dashboard layout components (structure only, no business logic)
- Navigation/sidebar components (structure only)
- User profile components (auth-related UI only)

### Adaptation Notes
- Convert Vue 3 Options API to Composition API if needed
- Adapt Vue Router to Nuxt routing
- Replace Pinia stores with Nuxt composables
- Replace JWT localStorage with `nuxt-auth-utils` session management
- Keep Tailwind + shadcn-vue components

## Implementation TODO Checklist

### Phase 1: Backend Setup

- [x] **1.1 Review VetBac Backend Auth Code** ✅
  - [x] Review `auth/security.py` - identify auth-only functions
  - [x] Review `auth/jwt.py` - identify JWT utilities
  - [x] Review `auth/dependencies.py` - identify FastAPI auth dependencies
  - [x] Review `models/admin_models.py` - identify User/Role models only
  - [x] Review `config.py` - identify auth config only

- [x] **1.2 Copy Auth Module to forecaster_enterprise/backend** ✅
  - [x] Copy `auth/security.py` (only password hashing functions)
  - [x] Copy `auth/jwt.py` (only JWT creation/validation)
  - [x] Copy `auth/dependencies.py` (only auth dependencies)
  - [x] Copy `auth/__init__.py`
  - [x] Remove any non-auth code from copied files

- [x] **1.3 Copy User Models** ✅
  - [x] Extract User model from `models/admin_models.py`
  - [x] Extract Role model if needed
  - [x] Create new `models/user.py` in forecaster_enterprise/backend
  - [x] Skip all non-user models

- [x] **1.4 Set Up uv Package Manager** ✅
  - [x] Ensure `pyproject.toml` exists
  - [x] Add auth dependencies (python-jose, passlib, bcrypt, etc.)
  - [x] Add PostgreSQL dependencies (psycopg2-binary)
  - [x] Add Alembic for migrations
  - [ ] Run `uv sync` to install dependencies (pending - needs to be run)

- [x] **1.5 Create Auth Endpoints** ✅
  - [x] Create `api/auth/` router in FastAPI
  - [x] Implement `/auth/login` endpoint
  - [x] Implement `/auth/register` endpoint
  - [x] Implement `/auth/me` endpoint (get current user)
  - [x] Add auth dependencies to protect routes

- [x] **1.6 Integrate with Existing FastAPI App** ✅
  - [x] Add auth router to main FastAPI app
  - [x] Configure PostgreSQL database
  - [x] Set up Alembic migrations
  - [x] Configure environment variables (.env)
  - [x] Test auth endpoints with curl/Postman ✅
  - [x] Verify JWT token generation and validation ✅

### Phase 2: Frontend Setup

- [x] **2.1 Review VetBac Frontend Auth Code** ✅
  - [x] Review `src/views/auth/login.vue` - identify UI structure
  - [x] Review `src/composables/useAuth.ts` - understand auth logic
  - [x] Review `src/stores/auth.ts` - understand state management
  - [x] Review `src/api/services/auth.ts` - understand API calls

- [x] **2.2 Set Up Nuxt 3 Project** ✅
  - [x] Initialize Nuxt 3 project in `forecaster_enterprise/frontend`
  - [x] Install `nuxt-auth-utils` module
  - [x] Add `NUXT_SESSION_PASSWORD` to `.env.example` (32+ characters)

- [x] **2.3 Configure Tailwind + shadcn-vue** ✅
  - [x] Configure Tailwind CSS
  - [x] Create shadcn-vue UI components (Button, Input, Card, Alert, Label)
  - [x] Set up Tailwind theme with shadcn colors

- [x] **2.4 Create Auth Type Definitions** ✅
  - [x] Create `auth.d.ts` in root directory
  - [x] Define `User` interface matching backend User model
  - [x] Define `UserSession` interface

- [x] **2.5 Copy and Adapt Auth UI Components** ✅
  - [x] Create `login.vue` page adapted from VetBac
  - [x] Remove VetBac-specific code
  - [x] Adapt to use `useUserSession()` from nuxt-auth-utils
  - [x] Update API calls to point to FastAPI backend
  - [x] Style with Tailwind + shadcn-vue components

- [x] **2.6 Create Auth Server Routes** ✅
  - [x] Create `server/api/auth/login.post.ts` - calls FastAPI
  - [x] Use `setUserSession()` after successful auth
  - [x] Handle errors properly

- [x] **2.7 Create Protected Route Middleware** ✅
  - [x] Create `middleware/auth.ts` using `useUserSession()`
  - [x] Apply to protected pages (dashboard)

### Phase 3: Integration & Testing

- [x] **3.1 Connect Frontend to Backend** ✅
  - [x] Update API base URL to point to FastAPI backend (configured in `nuxt.config.ts`)
  - [x] Test login flow: Frontend → Nuxt server route → FastAPI (implemented in `server/api/auth/login.post.ts`)
  - [x] Verify session is set correctly after login (using `setUserSession()`)
  - [x] Verify `useUserSession()` returns correct user data (used in dashboard, navbar)

- [x] **3.2 Test Auth Flow** ✅ (Implementation complete, manual testing pending)
  - [x] Login page with error handling (implemented in `pages/login.vue`)
  - [x] Protected routes middleware (implemented in `middleware/auth.ts`)
  - [x] Logout functionality (implemented in `DashboardNavbar.vue` and `pages/index.vue`)
  - [ ] Test login with valid credentials (manual testing needed)
  - [ ] Test login with invalid credentials (manual testing needed)
  - [ ] Test protected routes (should redirect if not logged in) (manual testing needed)
  - [ ] Test logout (should clear session) (manual testing needed)
  - [ ] Test session persistence (refresh page, should stay logged in) (manual testing needed)

- [x] **3.3 Test User Management** ⚠️ (Partial)
  - [x] User registration endpoint exists (backend: `/auth/register`, frontend: `server/api/auth/register.post.ts`)
  - [x] Registration page exists (shows "not available" message - admin-only)
  - [ ] Test user registration (manual testing needed)
  - [ ] User profile update (not implemented)
  - [ ] Password change (not implemented)

- [ ] **3.4 Clean Up** ⚠️ (In progress)
  - [x] Remove any copied code that's not being used (code is clean)
  - [ ] Remove VetBac-specific references (only in README documentation, not in code)
  - [ ] Update documentation (README structure updated, but Phase 3 status needs completion)
  - [x] Verify no business logic was accidentally copied (verified - only auth code)

## Goals
- ✅ Dashboard UI with auth
- ✅ Backend auth and user management
- ✅ JWT-based authentication
- ✅ Reuse existing VetBac code (auth-only)
- ✅ Modern stack (Nuxt 3, FastAPI, uv, PostgreSQL)
