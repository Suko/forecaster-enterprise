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
async def test_session(db_session):
    """Alias for db_session to satisfy legacy fixtures."""
    yield db_session

@pytest.fixture
async def db(db_session):
    """Alias for db_session when tests expect `db`."""
    yield db_session

@pytest.fixture
def mock_request():
    """Factory for a minimal FastAPI Request-like object."""
    from fastapi import Request
    from unittest.mock import Mock

    request = Mock(spec=Request)
    request.headers = {}
    client = Mock()
    client.host = "127.0.0.1"
    request.client = client
    request.url = Mock()
    request.url.path = "/test"
    return request


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


@pytest.fixture
async def test_client_obj(db_session):
    """Create a test client for multi-tenant tests"""
    from models.client import Client
    import uuid

    client = Client(
        client_id=uuid.uuid4(),
        name="Test Client",
        timezone="UTC",
        currency="EUR",
        is_active=True,
    )
    db_session.add(client)
    await db_session.commit()
    await db_session.refresh(client)
    return client


@pytest.fixture
async def test_client(db_session):
    """Create an AsyncClient for API testing with database override"""
    from httpx import AsyncClient, ASGITransport
    from main import app
    from models.database import get_db

    # Override database dependency to use test session
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Cleanup
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(db_session, test_client_obj):
    """Create a test user with client_id for multi-tenant tests"""
    from models.user import User
    import uuid

    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        name="Test User",
        hashed_password="hashed_password_here",  # Not used in tests
        client_id=test_client_obj.client_id,
        is_active=True,
        role="user",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_admin_user(db_session, test_client_obj):
    """Create an admin user fixture for admin-only endpoints"""
    from models.user import User
    import uuid

    admin_user = User(
        id=str(uuid.uuid4()),
        email="admin@example.com",
        name="Admin User",
        hashed_password="admin_password_hash",
        client_id=test_client_obj.client_id,
        is_active=True,
        role="admin",
    )
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    return admin_user


@pytest.fixture
def test_jwt_token(test_user):
    """Create a test JWT token for the test user"""
    from auth.jwt import create_access_token

    token_data = {
        "sub": test_user.email,
        "client_id": str(test_user.client_id),
    }
    return create_access_token(data=token_data)


@pytest.fixture
def service_api_key():
    """Get service API key for testing"""
    import os
    # Use test API key from environment or default
    return os.getenv("TEST_SERVICE_API_KEY", "test-service-api-key-12345")


@pytest.fixture
async def populate_test_data(db_session, test_client_obj, test_data_loader):
    """
    Populate ts_demand_daily table with test data for test client.

    This allows tests to use database queries like production,
    with test data stored in the database per client_id.
    """
    from sqlalchemy import text
    from datetime import date

    # Always create table if not exists (simpler approach)
    table_exists = False
    try:
        # Try to check if table has data
        check = await db_session.execute(text("SELECT 1 FROM ts_demand_daily LIMIT 1"))
        check.scalar()
        table_exists = True
    except:
        pass

    if not table_exists:
        # Table doesn't exist - create it (simplified schema for tests)
        # In production, this would be created by migrations/ETL
        # NOTE: Primary key includes location_id (after ETL fix)
        create_table = text("""
            CREATE TABLE IF NOT EXISTS ts_demand_daily (
                client_id VARCHAR(36) NOT NULL,
                item_id VARCHAR(255) NOT NULL,
                location_id VARCHAR(50) NOT NULL DEFAULT 'UNSPECIFIED',
                date_local DATE NOT NULL,
                units_sold NUMERIC(18, 2) NOT NULL DEFAULT 0,
                promotion_flag BOOLEAN DEFAULT FALSE,
                holiday_flag BOOLEAN DEFAULT FALSE,
                is_weekend BOOLEAN DEFAULT FALSE,
                marketing_spend NUMERIC(18, 2) DEFAULT 0,
                PRIMARY KEY (client_id, item_id, location_id, date_local)
            );
        """)
        await db_session.execute(create_table)
        await db_session.commit()

    # Get test client ID
    client_id = test_client_obj.client_id

    # Try to load test data from CSV, fallback to synthetic data
    try:
        loader = test_data_loader
        df = loader.load_csv()

        # Insert test data into database
        # Transform CSV format to ts_demand_daily format
        for _, row in df.iterrows():
            insert_query = text("""
                INSERT INTO ts_demand_daily
                (client_id, item_id, location_id, date_local, units_sold, promotion_flag, holiday_flag, is_weekend, marketing_spend)
                VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold, :promo_flag, :holiday_flag, :is_weekend, :marketing_spend)
                ON CONFLICT (client_id, item_id, location_id, date_local) DO NOTHING
            """)

            await db_session.execute(insert_query, {
                "client_id": str(client_id),
                "item_id": str(row.get("sku", "")),
                "location_id": str(row.get("location_id", "UNSPECIFIED")),  # Match production: ETL uses 'UNSPECIFIED'
                "date_local": row.get("date").date() if hasattr(row.get("date"), "date") else row.get("date"),
                "units_sold": float(row.get("sales_qty", 0)),
                "promo_flag": bool(row.get("promo_flag", False)),
                "holiday_flag": bool(row.get("holiday_flag", False)),
                "is_weekend": bool(row.get("is_weekend", False)),
                "marketing_spend": float(row.get("marketing_spend", 0)),
            })
    except (FileNotFoundError, AttributeError, KeyError):
        # If CSV not available, create synthetic data
        # Create 30 days of data for a few test items
        from datetime import timedelta
        import random

        test_items = ["TEST-001", "TEST-002", "TEST-003"]
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        current_date = start_date
        while current_date <= end_date:
            for item_id in test_items:
                insert_query = text("""
                    INSERT INTO ts_demand_daily
                    (client_id, item_id, location_id, date_local, units_sold, promotion_flag, holiday_flag, is_weekend, marketing_spend)
                    VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold, :promo_flag, :holiday_flag, :is_weekend, :marketing_spend)
                    ON CONFLICT (client_id, item_id, location_id, date_local) DO NOTHING
                """)

                await db_session.execute(insert_query, {
                    "client_id": str(client_id),
                    "item_id": item_id,
                    "location_id": "UNSPECIFIED",  # Match production: ETL uses 'UNSPECIFIED'
                    "date_local": current_date,
                    "units_sold": float(random.randint(10, 100)),
                    "promo_flag": False,
                    "holiday_flag": False,
                    "is_weekend": current_date.weekday() >= 5,
                    "marketing_spend": 0.0,
                })
            current_date += timedelta(days=1)

    await db_session.commit()
    return True
