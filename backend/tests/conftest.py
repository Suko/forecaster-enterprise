"""
Pytest configuration and shared fixtures
"""
import pytest
import pandas as pd
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool, NullPool

from models.database import Base
from tests.fixtures.test_data_loader import TestDataLoader


# ============================================================================
# Database Configuration
# ============================================================================

# Check if we should use PostgreSQL for tests (set TEST_POSTGRES=true)
USE_POSTGRES = os.getenv("TEST_POSTGRES", "false").lower() in ["true", "1", "yes"]

if USE_POSTGRES:
    # Use PostgreSQL test database
    TEST_DATABASE_URL = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise_test"
    )
    # Convert postgres:// to postgresql+asyncpg://
    if TEST_DATABASE_URL.startswith("postgres://"):
        TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    elif TEST_DATABASE_URL.startswith("postgresql://"):
        TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        pool_pre_ping=True,
        poolclass=NullPool,  # No connection pooling for tests (each test gets fresh connection)
        echo=False,
    )
else:
    # Use in-memory SQLite for fast tests (default)
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    test_engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def db_session():
    """
    Create test database session.
    
    Uses PostgreSQL if TEST_POSTGRES=true, otherwise SQLite (default).
    
    Environment Variables:
        TEST_POSTGRES: Set to "true" to use PostgreSQL instead of SQLite
        TEST_DATABASE_URL: PostgreSQL connection string (if using PostgreSQL)
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Yield session
    async with TestSessionLocal() as session:
        yield session
    
    # Cleanup: Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def test_data_loader():
    """Load test data from CSV"""
    return TestDataLoader()


@pytest.fixture
def sample_item_data(test_data_loader):
    """Get sample item data for testing"""
    # Use SKU001 which should have good data
    return test_data_loader.get_item_data("SKU001")


@pytest.fixture
def sample_item_ids(test_data_loader):
    """Get sample item IDs for testing"""
    items = test_data_loader.get_available_items()
    # Return first 3 items for testing
    return items[:3] if len(items) >= 3 else items
