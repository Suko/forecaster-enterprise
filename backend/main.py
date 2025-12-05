from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from models import init_db
from api import auth

# Database will be initialized via Alembic migrations
# Run: alembic upgrade head

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    debug=settings.debug,
)

# CORS middleware - uses settings from .env
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)


@app.get("/")
async def root():
    return {"message": "Forecaster Enterprise API", "version": "0.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}

