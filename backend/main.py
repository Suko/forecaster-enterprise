import os
import logging
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from config import settings

from models import init_db
from api import auth, forecast, monitoring, inventory, orders, purchase_orders, etl, suppliers, locations
from api import settings as settings_api, simulation

# Database will be initialized via Alembic migrations
# Run: alembic upgrade head

# Initialize Sentry (BEFORE creating app)
# Only enable Sentry in non-development environments
is_dev = settings.environment.lower() in ["development", "dev", "local"]
if settings.sentry_dsn and not is_dev:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        profiles_sample_rate=settings.sentry_profiles_sample_rate,
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                http_methods_to_capture=["GET", "POST", "PUT", "DELETE"]
            ),
            SqlalchemyIntegration(),
            LoggingIntegration(
                level=logging.INFO,  # Capture INFO and above as breadcrumbs
                event_level=logging.ERROR  # Send ERROR and above as events
            ),
        ],
        # Performance monitoring
        enable_tracing=True,

        # Release tracking
        release=os.getenv("GIT_COMMIT_SHA", "unknown"),

        # Custom tags
        tags={
            "service": "backend",
            "version": "0.1.0",
        }
    )
    print(f"✅ Sentry initialized for {settings.sentry_environment}")
elif is_dev:
    print("ℹ️  Sentry disabled for development environment")
else:
    print("⚠️  Sentry DSN not configured - monitoring disabled")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

# Add client_id to Sentry context for multi-tenant error tracking
@app.middleware("http")
async def add_client_context(request: Request, call_next):
    """Add client_id and other business context to Sentry for better error grouping"""
    # Only add context if Sentry is enabled and initialized
    try:
        if not hasattr(sentry_sdk, '_initialized') or sentry_sdk._initialized is False:
            return await call_next(request)
    except:
        # If we can't check Sentry status, skip context addition
        return await call_next(request)

    try:
        # Try to get client_id from request headers without DB access
        # This avoids database dependency issues in tests
        from auth.dependencies import get_current_client
        try:
            client = await get_current_client(request)
            sentry_sdk.set_tag("client_id", str(client.client_id))
            sentry_sdk.set_tag("auth_type", "jwt_token")
        except Exception:
            # If we can't get client from JWT, try service API key
            api_key = request.headers.get("X-API-Key")
            if api_key:
                sentry_sdk.set_tag("auth_type", "service_api_key")
            else:
                sentry_sdk.set_tag("auth_type", "unauthenticated")
    except Exception:
        # Don't let Sentry context setup break the request
        pass

    # Add basic request context for better error tracking
    try:
        sentry_sdk.set_context("request", {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query": str(request.url.query),
        })
    except Exception:
        pass

    response = await call_next(request)
    return response

# Rate limit exception handler
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail or "Rate limit exceeded. Please try again later.",
            "error": "rate_limit_exceeded"
        },
        headers={"Retry-After": "60"}
    )

# CORS middleware - uses settings from .env
# More restrictive in production
is_dev = settings.environment.lower() in ["development", "dev", "local"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"] if not is_dev else ["*"],
    allow_headers=["Authorization", "Content-Type"] if not is_dev else ["*"],
)

# Include routers
#
# Auth endpoints:
# - Canonical (versioned): `/api/v1/auth/*`
# - Legacy (deprecated): `/auth/*`
#
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth.router, deprecated=True)
app.include_router(forecast.router)
app.include_router(monitoring.router)
app.include_router(inventory.router)
app.include_router(orders.router)
app.include_router(purchase_orders.router)
app.include_router(suppliers.router)
app.include_router(locations.router)
app.include_router(settings_api.router)
app.include_router(etl.router)
app.include_router(simulation.router)


@app.get("/")
async def root():
    return {"message": "Forecaster Enterprise API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
