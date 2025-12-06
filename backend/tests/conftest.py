"""
Pytest configuration and shared fixtures
"""
import pytest
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from tests.fixtures.test_data_loader import TestDataLoader


# Test database (in-memory SQLite for fast tests)
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


@pytest.fixture
async def db_session():
    """Create test database session"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        yield session
    
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
