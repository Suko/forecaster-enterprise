from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from config import settings

from models import init_db
from api import auth, forecast, monitoring, inventory, orders, purchase_orders, etl, suppliers, locations
from api import settings as settings_api

# Database will be initialized via Alembic migrations
# Run: alembic upgrade head

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

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


@app.get("/")
async def root():
    return {"message": "Forecaster Enterprise API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
