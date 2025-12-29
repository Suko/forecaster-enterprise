"""
Dashboard Service Tests

Tests for DashboardService - a critical user-facing service that:
1. Aggregates KPIs from multiple data sources
2. Calculates average demand using SQL with expanding params
3. Triggers background forecast refreshes
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta, datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from services.dashboard_service import DashboardService
from models.forecast import ForecastRun, ForecastResult
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_stock_level,
    create_test_client_settings,
)


# ============================================================================
# Helper to create ts_demand_daily table
# ============================================================================


async def ensure_ts_demand_daily_table(db_session: AsyncSession):
    """Create ts_demand_daily table if it doesn't exist (for tests without populate_test_data)"""
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


# ============================================================================
# get_dashboard_data Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_dashboard_data_empty_products(db_session: AsyncSession, test_client_obj):
    """Test dashboard returns empty metrics when no products exist"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    result = await service.get_dashboard_data(test_client_obj.client_id)
    
    assert result is not None
    assert result.metrics.total_skus == 0
    assert result.metrics.understocked_count == 0
    assert result.metrics.overstocked_count == 0
    assert result.top_understocked == []
    assert result.top_overstocked == []


@pytest.mark.asyncio
async def test_get_dashboard_data_with_products(db_session: AsyncSession, test_client_obj):
    """Test dashboard calculates metrics correctly with products"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Create products with stock
    product1 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="DASH-001",
        unit_cost=Decimal("25.00")
    )
    product2 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="DASH-002",
        unit_cost=Decimal("50.00")
    )
    db_session.add_all([product1, product2])
    
    # Create stock levels
    stock1 = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id="DASH-001",
        current_stock=100
    )
    stock2 = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id="DASH-002",
        current_stock=50
    )
    db_session.add_all([stock1, stock2])
    await db_session.commit()
    
    result = await service.get_dashboard_data(test_client_obj.client_id)
    
    assert result.metrics.total_skus == 2
    # Total inventory value = (100 * 25) + (50 * 50) = 2500 + 2500 = 5000
    assert result.metrics.total_inventory_value == Decimal("5000.00")


@pytest.mark.asyncio
async def test_get_dashboard_data_multi_tenant_isolation(
    db_session: AsyncSession, test_client_obj
):
    """Test dashboard only returns data for the requesting client"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Create product for test client
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="DASH-TENANT-001"
    )
    db_session.add(product)
    
    # Create product for different client (should not be included)
    from models.client import Client
    other_client = Client(name="Other Client")
    db_session.add(other_client)
    await db_session.flush()
    
    other_product = create_test_product(
        client_id=other_client.client_id,
        item_id="DASH-OTHER-001"
    )
    db_session.add(other_product)
    await db_session.commit()
    
    result = await service.get_dashboard_data(test_client_obj.client_id)
    
    # Should only count the test client's product
    assert result.metrics.total_skus == 1


# ============================================================================
# _batch_get_average_daily_demand Tests (via _get_avg_demand_bulk)
# ============================================================================


@pytest.mark.asyncio
async def test_batch_get_average_daily_demand_no_data(
    db_session: AsyncSession, test_client_obj
):
    """Test average demand returns empty dict when no sales data exists"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    result = await service._batch_get_average_daily_demand(
        client_id=test_client_obj.client_id,
        item_ids=["NO-DATA-001", "NO-DATA-002"],
        days=30
    )
    
    assert result == {}


@pytest.mark.asyncio
async def test_batch_get_average_daily_demand_with_data(
    db_session: AsyncSession, test_client_obj
):
    """Test average demand calculation with sales data"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Insert sales data directly using SQL
    today = date.today()
    for i in range(7):
        day = today - timedelta(days=i)
        await db_session.execute(
            text("""
                INSERT INTO ts_demand_daily 
                (client_id, item_id, location_id, date_local, units_sold)
                VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold)
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": "AVG-DEMAND-001",
                "location_id": "LOC-001",
                "date_local": day,
                "units_sold": 10.0,  # 10 units per day
            }
        )
    await db_session.commit()
    
    result = await service._batch_get_average_daily_demand(
        client_id=test_client_obj.client_id,
        item_ids=["AVG-DEMAND-001"],
        days=30
    )
    
    assert "AVG-DEMAND-001" in result
    # Average should be 10 (10 units per day)
    assert result["AVG-DEMAND-001"] == Decimal("10")


@pytest.mark.asyncio
async def test_batch_get_average_daily_demand_multiple_items(
    db_session: AsyncSession, test_client_obj
):
    """Test average demand calculation for multiple items (tests expanding IN clause)"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Insert sales data for multiple items
    today = date.today()
    items = ["MULTI-001", "MULTI-002", "MULTI-003"]
    
    for item_id in items:
        for i in range(5):
            day = today - timedelta(days=i)
            await db_session.execute(
                text("""
                    INSERT INTO ts_demand_daily 
                    (client_id, item_id, location_id, date_local, units_sold)
                    VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold)
                """),
                {
                    "client_id": str(test_client_obj.client_id),
                    "item_id": item_id,
                    "location_id": "LOC-001",
                    "date_local": day,
                    "units_sold": 5.0,
                }
            )
    await db_session.commit()
    
    result = await service._batch_get_average_daily_demand(
        client_id=test_client_obj.client_id,
        item_ids=items,
        days=30
    )
    
    # All items should have average demand of 5
    assert len(result) == 3
    for item_id in items:
        assert item_id in result
        assert result[item_id] == Decimal("5")


# ============================================================================
# _batch_get_latest_forecast_demand Tests
# ============================================================================


@pytest.mark.asyncio
async def test_batch_get_latest_forecast_demand_no_forecast(
    db_session: AsyncSession, test_client_obj
):
    """Test returns empty when no forecast exists"""
    service = DashboardService(db_session)
    
    result = await service._batch_get_latest_forecast_demand(
        client_id=test_client_obj.client_id,
        item_ids=["NO-FORECAST-001"],
        max_age_days=7
    )
    
    assert "NO-FORECAST-001" in result
    demand, is_fresh = result["NO-FORECAST-001"]
    assert demand is None
    assert is_fresh is False


@pytest.mark.asyncio
async def test_batch_get_latest_forecast_demand_with_forecast(
    db_session: AsyncSession, test_client_obj
):
    """Test returns forecast demand when fresh forecast exists"""
    service = DashboardService(db_session)
    item_id = "FORECAST-001"
    
    # Create a forecast run
    forecast_run = ForecastRun(
        client_id=test_client_obj.client_id,
        user_id="test_user",
        status="completed",
        item_ids=[item_id],
        primary_model="chronos-2",
        recommended_method="chronos-2",
        prediction_length=30,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(forecast_run)
    await db_session.flush()
    
    # Create forecast results for next 30 days
    today = date.today()
    for i in range(30):
        forecast_result = ForecastResult(
            forecast_run_id=forecast_run.forecast_run_id,
            client_id=test_client_obj.client_id,
            item_id=item_id,
            date=today + timedelta(days=i),
            horizon_day=i + 1,  # 1, 2, 3... days ahead
            method="chronos-2",
            point_forecast=Decimal("10.0"),  # 10 units per day
        )
        db_session.add(forecast_result)
    await db_session.commit()
    
    result = await service._batch_get_latest_forecast_demand(
        client_id=test_client_obj.client_id,
        item_ids=[item_id],
        max_age_days=7
    )
    
    assert item_id in result
    demand, is_fresh = result[item_id]
    assert is_fresh is True
    # 30 days * 10 units = 300 total demand
    assert demand == Decimal("300.0")


# ============================================================================
# DIR (Days of Inventory Remaining) Calculation Tests
# ============================================================================


@pytest.mark.asyncio
async def test_dashboard_calculates_dir_correctly(
    db_session: AsyncSession, test_client_obj
):
    """Test DIR calculation: stock / avg_daily_demand"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Create product with stock
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="DIR-001",
        unit_cost=Decimal("10.00")
    )
    db_session.add(product)
    
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id="DIR-001",
        current_stock=100  # 100 units in stock
    )
    db_session.add(stock)
    
    # Add sales history (10 units per day)
    today = date.today()
    for i in range(30):
        day = today - timedelta(days=i + 1)
        await db_session.execute(
            text("""
                INSERT INTO ts_demand_daily 
                (client_id, item_id, location_id, date_local, units_sold)
                VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold)
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": "DIR-001",
                "location_id": "LOC-001",
                "date_local": day,
                "units_sold": 10.0,
            }
        )
    await db_session.commit()
    
    result = await service.get_dashboard_data(test_client_obj.client_id)
    
    # DIR should be 100 stock / 10 avg daily demand = 10 days
    assert result.metrics.average_dir == Decimal("10")


# ============================================================================
# Understocked/Overstocked Classification Tests
# ============================================================================


@pytest.mark.asyncio
async def test_dashboard_identifies_understocked_products(
    db_session: AsyncSession, test_client_obj
):
    """Test that products with low DIR are flagged as understocked"""
    await ensure_ts_demand_daily_table(db_session)
    service = DashboardService(db_session)
    
    # Create client settings with understocked threshold
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        understocked_threshold=14,  # < 14 days = understocked
    )
    db_session.add(settings)
    
    # Create understocked product (low stock, high demand)
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="UNDERSTOCK-001",
        unit_cost=Decimal("10.00")
    )
    db_session.add(product)
    
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id="UNDERSTOCK-001",
        current_stock=10  # Only 10 units
    )
    db_session.add(stock)
    
    # High demand: 5 units per day = DIR of 2 days (well under threshold)
    today = date.today()
    for i in range(30):
        day = today - timedelta(days=i + 1)
        await db_session.execute(
            text("""
                INSERT INTO ts_demand_daily 
                (client_id, item_id, location_id, date_local, units_sold)
                VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold)
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": "UNDERSTOCK-001",
                "location_id": "LOC-001",
                "date_local": day,
                "units_sold": 5.0,
            }
        )
    await db_session.commit()
    
    result = await service.get_dashboard_data(test_client_obj.client_id)
    
    assert result.metrics.understocked_count == 1
    assert len(result.top_understocked) == 1
    assert result.top_understocked[0].item_id == "UNDERSTOCK-001"
