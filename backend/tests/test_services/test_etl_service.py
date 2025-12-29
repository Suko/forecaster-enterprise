import pytest
from datetime import date
from uuid import UUID

from sqlalchemy import text

from services.etl.etl_service import ETLService
from services.etl.connectors import ETLConnector


class StubConnector(ETLConnector):
    def __init__(self, sales_history=None, stock_levels=None):
        self._sales_history = sales_history or []
        self._stock_levels = stock_levels or []

    async def connect(self) -> None:  # pragma: no cover
        return None

    async def disconnect(self) -> None:  # pragma: no cover
        return None

    async def fetch_sales_history(self, client_id: UUID, start_date=None, end_date=None):
        return self._sales_history

    async def fetch_products(self, client_id: UUID):  # pragma: no cover
        return []

    async def fetch_stock_levels(self, client_id: UUID):
        return self._stock_levels

    async def fetch_locations(self, client_id: UUID):  # pragma: no cover
        return []


@pytest.mark.asyncio
async def test_sync_sales_history_replace_is_single_transaction(db_session, test_client_obj):
    # Create minimal ts_demand_daily table (not modeled in SQLAlchemy)
    await db_session.execute(text("""
        CREATE TABLE IF NOT EXISTS ts_demand_daily (
            client_id VARCHAR(36) NOT NULL,
            item_id VARCHAR(255) NOT NULL,
            location_id VARCHAR(50) NOT NULL,
            date_local DATE NOT NULL,
            units_sold REAL NOT NULL,
            promotion_flag BOOLEAN,
            holiday_flag BOOLEAN,
            is_weekend BOOLEAN,
            marketing_spend REAL,
            PRIMARY KEY (client_id, item_id, location_id, date_local)
        )
    """))
    await db_session.commit()

    # Seed a row that should be deleted by replace in range
    await db_session.execute(
        text("""
            INSERT INTO ts_demand_daily (client_id, item_id, location_id, date_local, units_sold)
            VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold)
        """),
        {
            "client_id": str(test_client_obj.client_id),
            "item_id": "SKU1",
            "location_id": "UNSPECIFIED",
            "date_local": date(2025, 1, 1),
            "units_sold": 1.0,
        },
    )
    await db_session.commit()

    connector = StubConnector(
        sales_history=[
            {
                "item_id": "SKU1",
                "location_id": "UNSPECIFIED",
                "date_local": date(2025, 1, 1),
                "units_sold": 5,
            }
        ]
    )
    service = ETLService(db_session)
    result = await service.sync_sales_history(
        client_id=test_client_obj.client_id,
        connector=connector,
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 1),
        replace=True,
    )

    assert result["success"] is True
    assert result["rows_validated"] == 1

    # Row should exist with updated value
    row = (
        await db_session.execute(
            text("""
                SELECT units_sold
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = :item_id
                  AND location_id = :location_id
                  AND date_local = :date_local
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": "SKU1",
                "location_id": "UNSPECIFIED",
                "date_local": date(2025, 1, 1),
            },
        )
    ).one()
    assert float(row[0]) == 5.0


@pytest.mark.asyncio
async def test_sync_stock_levels_replace(db_session, test_client_obj):
    # StockLevel table is part of metadata, already created by fixture.
    # Seed an existing stock row to confirm delete+upsert works.
    await db_session.execute(
        text("""
            INSERT INTO stock_levels (id, client_id, item_id, location_id, current_stock)
            VALUES (:id, :client_id, :item_id, :location_id, :current_stock)
        """),
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "client_id": str(test_client_obj.client_id),
            "item_id": "SKU1",
            "location_id": "UNSPECIFIED",
            "current_stock": 2,
        },
    )
    await db_session.commit()

    connector = StubConnector(
        stock_levels=[
            {"item_id": "SKU1", "location_id": "UNSPECIFIED", "current_stock": 10},
            {"item_id": "SKU2", "location_id": "UNSPECIFIED", "current_stock": 3},
        ]
    )
    service = ETLService(db_session)
    result = await service.sync_stock_levels(
        client_id=test_client_obj.client_id,
        connector=connector,
        replace=True,
    )

    assert result["success"] is True
    assert result["rows_inserted"] == 2

    rows = (
        await db_session.execute(
            text("""
                SELECT item_id, current_stock
                FROM stock_levels
                WHERE client_id = :client_id
                ORDER BY item_id
            """),
            {"client_id": str(test_client_obj.client_id)},
        )
    ).all()
    assert rows == [("SKU1", 10), ("SKU2", 3)]

