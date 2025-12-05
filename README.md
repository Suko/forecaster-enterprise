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
   uv sync  # Uses uv package manager (see pyproject.toml)
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
│   ├── api/                    # API routes/endpoints (thin layer)
│   │   └── auth.py            # Auth routes (delegates to services)
│   ├── schemas/                # Pydantic models (request/response)
│   │   └── auth.py            # Token, UserResponse, UserCreate, UserUpdate
│   ├── services/               # Business logic layer
│   │   ├── auth_service.py    # Authentication business logic
│   │   └── user_service.py    # User management business logic
│   ├── core/                   # Core utilities
│   │   └── rate_limit.py     # Rate limiting and password validation
│   ├── auth/                   # Auth module
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing
│   │   ├── jwt.py              # JWT token creation/validation
│   │   ├── dependencies.py      # FastAPI auth dependencies
│   │   └── security_logger.py  # Security event logging
│   ├── models/                 # Database models (SQLAlchemy)
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


## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Nuxt 4)                        │
│  - nuxt-auth-utils (JWT management, session handling)       │
│  - Nuxt UI (official Nuxt component library)              │
│  - Tailwind CSS 4 (styling)                                 │
│  - Dashboard layout with collapsible sidebar               │
│  - Settings management with tabs                           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
┌──────────────────────▼──────────────────────────────────────┐
│                 Backend (FastAPI)                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  API Layer (api/) - Thin route handlers             │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │  Services Layer (services/) - Business logic        │  │
│  └──────────────────┬──────────────────────────────────┘  │
│                      │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │  Models Layer (models/) - SQLAlchemy ORM             │  │
│  └────────────────────────────────────────────────────┘  │
│  - Auth module (JWT, password hashing, security)           │
│  - Schemas (Pydantic models for validation)               │
│  - Core utilities (rate limiting, validation)             │
│  - Package manager: uv                                      │
│  - Database: PostgreSQL                                    │
└─────────────────────────────────────────────────────────────┘
```

### Backend Architecture (FastAPI Best Practices)

The backend follows FastAPI best practices with clear separation of concerns:

- **API Layer** (`api/`): Thin route handlers that delegate to services
- **Schemas** (`schemas/`): Pydantic models for request/response validation
- **Services** (`services/`): Business logic and data operations
- **Models** (`models/`): SQLAlchemy database models
- **Core** (`core/`): Shared utilities (rate limiting, validation)
- **Auth** (`auth/`): Authentication and security utilities

## Stack Usage

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | FastAPI | API server, auth endpoints, user management |
| **Package Manager** | uv | Python dependency management |
| **Database** | PostgreSQL | User data, auth tokens |
| **Migrations** | Alembic | Database schema management |
| **Frontend** | Nuxt 4 | SSR framework, routing, auth integration |
| **Auth Module** | nuxt-auth-utils | JWT token management, session handling |
| **UI Framework** | Nuxt UI | Official Nuxt component library |
| **Styling** | Tailwind CSS 4 | Utility-first CSS framework |
| **Icons** | Lucide Vue Next | Icon library |
