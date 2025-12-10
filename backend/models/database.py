from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from config import settings
from typing import AsyncGenerator, Optional

# Base class for models (needed for migrations)
Base = declarative_base()

# Lazy engine creation - only create when needed (not during migrations)
_engine: Optional[AsyncEngine] = None
_AsyncSessionLocal: Optional[async_sessionmaker] = None


def _get_database_url() -> str:
    """Get database URL, converting to async format if needed"""
    database_url = settings.database_url
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def get_engine() -> AsyncEngine:
    """Get or create async engine (lazy initialization)"""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            pool_pre_ping=True,  # Verify connections before using
            pool_size=5,
            max_overflow=10,
            echo=False,  # Set to True for SQL query logging
        )
    return _engine


def get_async_session_local() -> async_sessionmaker:
    """Get or create async session maker (lazy initialization)"""
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


# For backward compatibility - module-level accessors
# These will be initialized on first access
def __getattr__(name: str):
    """Lazy attribute access for engine and AsyncSessionLocal"""
    if name == "engine":
        return get_engine()
    elif name == "AsyncSessionLocal":
        return get_async_session_local()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")



# Database functions
async def create_tables():
    """Create all database tables"""
    # Import here to avoid circular imports
    from . import user
    from . import client
    from . import forecast
    from . import product
    from . import location
    from . import stock
    from . import supplier
    from . import product_supplier
    from . import settings
    from . import inventory_metrics
    from . import purchase_order, order_cart
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session"""
    session_local = get_async_session_local()
    async with session_local() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database with tables"""
    await create_tables()
    print("Database initialized successfully")
