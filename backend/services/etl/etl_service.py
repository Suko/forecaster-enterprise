"""
ETL Service

Handles data synchronization from external sources to internal database.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from models.product import Product
from models.stock import StockLevel
from models.location import Location
from .connectors import ETLConnector


class ETLService:
    """Service for ETL operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def sync_sales_history(
        self,
        client_id: UUID,
        connector: ETLConnector,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        replace: bool = False
    ) -> Dict[str, Any]:
        """
        Sync sales history from external source to ts_demand_daily table

        Args:
            client_id: Client UUID
            connector: ETL connector instance
            start_date: Optional start date filter
            end_date: Optional end date filter
            replace: If True, replace existing data; if False, upsert

        Returns:
            dict with sync statistics
        """
        # Fetch data from external source
        await connector.connect()
        try:
            external_data = await connector.fetch_sales_history(
                client_id=client_id,
                start_date=start_date,
                end_date=end_date
            )
        finally:
            await connector.disconnect()

        if not external_data:
            return {
                "success": True,
                "rows_fetched": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "errors": []
            }

        # Validate data
        errors = []
        validated_data = []
        for row in external_data:
            try:
                # Map external fields to internal schema
                validated_row = {
                    "item_id": str(row.get("item_id") or row.get("sku", "")),
                    "location_id": str(row.get("location_id", "UNSPECIFIED")),
                    "date_local": row.get("date_local") or row.get("date"),
                    "units_sold": float(row.get("units_sold") or row.get("quantity", 0)),
                    "client_id": str(client_id),
                    "promotion_flag": bool(row.get("promotion_flag", False)),
                    "holiday_flag": bool(row.get("holiday_flag", False)),
                    "is_weekend": bool(row.get("is_weekend", False)),
                    "marketing_spend": float(row.get("marketing_spend", 0)),
                }

                # Validate required fields
                if not validated_row["item_id"]:
                    raise ValueError("Missing item_id/sku")
                if not validated_row["date_local"]:
                    raise ValueError("Missing date_local/date")
                if validated_row["units_sold"] < 0:
                    raise ValueError("units_sold must be >= 0")

                validated_data.append(validated_row)
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        # Insert/update data
        if not validated_data:
            return {
                "success": True,
                "rows_fetched": len(external_data),
                "rows_validated": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "errors": errors[:10],
            }

        # Note: On CONFLICT, we can't reliably distinguish insert vs update across DBs
        # without DB-specific RETURNING logic. We report total rows upserted.
        upsert_count = len(validated_data)

        insert_query = text("""
            INSERT INTO ts_demand_daily
            (client_id, item_id, location_id, date_local, units_sold, promotion_flag, holiday_flag, is_weekend, marketing_spend)
            VALUES (:client_id, :item_id, :location_id, :date_local, :units_sold, :promotion_flag, :holiday_flag, :is_weekend, :marketing_spend)
            ON CONFLICT (client_id, item_id, location_id, date_local) DO UPDATE
            SET units_sold = EXCLUDED.units_sold,
                promotion_flag = EXCLUDED.promotion_flag,
                holiday_flag = EXCLUDED.holiday_flag,
                is_weekend = EXCLUDED.is_weekend,
                marketing_spend = EXCLUDED.marketing_spend
        """)

        delete_params: Dict[str, Any] = {"client_id": str(client_id)}
        delete_sql = "DELETE FROM ts_demand_daily WHERE client_id = :client_id"
        if start_date is not None:
            delete_sql += " AND date_local >= :start_date"
            delete_params["start_date"] = start_date
        if end_date is not None:
            delete_sql += " AND date_local <= :end_date"
            delete_params["end_date"] = end_date

        async with self.db.begin():
            if replace:
                await self.db.execute(text(delete_sql), delete_params)
            await self.db.execute(insert_query, validated_data)

        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_validated": len(validated_data),
            "rows_inserted": upsert_count,
            "rows_updated": 0,
            "errors": errors[:10]  # Limit error details
        }

    async def sync_products(
        self,
        client_id: UUID,
        connector: ETLConnector
    ) -> Dict[str, Any]:
        """
        Sync products from external source

        Args:
            client_id: Client UUID
            connector: ETL connector instance

        Returns:
            dict with sync statistics
        """
        # Fetch data from external source
        await connector.connect()
        try:
            external_data = await connector.fetch_products(client_id=client_id)
        finally:
            await connector.disconnect()

        if not external_data:
            return {
                "success": True,
                "rows_fetched": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "errors": []
            }

        # Validate and upsert products
        errors = []
        validated_data: List[Dict[str, Any]] = []
        for row in external_data:
            try:
                item_id = str(row.get("item_id") or row.get("sku", "")).strip()
                if not item_id:
                    raise ValueError("Missing item_id/sku")

                validated_data.append({
                    "id": str(uuid.uuid4()),
                    "client_id": str(client_id),
                    "item_id": item_id,
                    "sku": row.get("sku"),
                    "product_name": row.get("product_name") or row.get("name", "Unknown"),
                    "category": row.get("category", "Uncategorized"),
                    "unit_cost": float(row.get("unit_cost") or row.get("cost", 0)),
                })
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        if validated_data:
            upsert_query = text("""
                INSERT INTO products (id, client_id, item_id, sku, product_name, category, unit_cost)
                VALUES (:id, :client_id, :item_id, :sku, :product_name, :category, :unit_cost)
                ON CONFLICT (client_id, item_id) DO UPDATE
                SET sku = EXCLUDED.sku,
                    product_name = EXCLUDED.product_name,
                    category = EXCLUDED.category,
                    unit_cost = EXCLUDED.unit_cost,
                    updated_at = CURRENT_TIMESTAMP
            """)
            async with self.db.begin():
                await self.db.execute(upsert_query, validated_data)

        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": len(validated_data),
            "rows_updated": 0,
            "errors": errors[:10]
        }

    async def sync_stock_levels(
        self,
        client_id: UUID,
        connector: ETLConnector,
        replace: bool = True
    ) -> Dict[str, Any]:
        """
        Sync stock levels from external source

        Args:
            client_id: Client UUID
            connector: ETL connector instance
            replace: If True, replace all stock levels; if False, upsert

        Returns:
            dict with sync statistics
        """
        # Fetch data from external source
        await connector.connect()
        try:
            external_data = await connector.fetch_stock_levels(client_id=client_id)
        finally:
            await connector.disconnect()

        if not external_data:
            return {
                "success": True,
                "rows_fetched": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "errors": []
            }

        # Replace all stock levels if requested
        # Validate and upsert stock levels
        errors = []
        validated_data: List[Dict[str, Any]] = []
        for row in external_data:
            try:
                item_id = str(row.get("item_id") or row.get("sku", "")).strip()
                location_id = str(row.get("location_id", "UNSPECIFIED")).strip()
                current_stock = float(row.get("current_stock") or row.get("stock", 0))

                if not item_id:
                    raise ValueError("Missing item_id/sku")
                if current_stock < 0:
                    raise ValueError("current_stock must be >= 0")

                validated_data.append({
                    "id": str(uuid.uuid4()),
                    "client_id": str(client_id),
                    "item_id": item_id,
                    "location_id": location_id,
                    "current_stock": int(current_stock),
                })
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        upsert_query = text("""
            INSERT INTO stock_levels (id, client_id, item_id, location_id, current_stock)
            VALUES (:id, :client_id, :item_id, :location_id, :current_stock)
            ON CONFLICT (client_id, item_id, location_id) DO UPDATE
            SET current_stock = EXCLUDED.current_stock,
                updated_at = CURRENT_TIMESTAMP
        """)

        async with self.db.begin():
            if replace:
                await self.db.execute(
                    text("DELETE FROM stock_levels WHERE client_id = :client_id"),
                    {"client_id": str(client_id)},
                )
            if validated_data:
                await self.db.execute(upsert_query, validated_data)

        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": len(validated_data),
            "rows_updated": 0,
            "errors": errors[:10]
        }

    async def sync_locations(
        self,
        client_id: UUID,
        connector: ETLConnector
    ) -> Dict[str, Any]:
        """
        Sync locations from external source

        Args:
            client_id: Client UUID
            connector: ETL connector instance

        Returns:
            dict with sync statistics
        """
        # Fetch data from external source
        await connector.connect()
        try:
            external_data = await connector.fetch_locations(client_id=client_id)
        finally:
            await connector.disconnect()

        if not external_data:
            return {
                "success": True,
                "rows_fetched": 0,
                "rows_inserted": 0,
                "rows_updated": 0,
                "errors": []
            }

        # Validate and upsert locations (preserve app-managed ones)
        errors = []
        protected_location_ids: set[str] = set()
        protected_result = await self.db.execute(
            select(Location.location_id).where(
                Location.client_id == client_id,
                Location.is_synced == False,  # noqa: E712
            )
        )
        protected_location_ids.update([loc_id for loc_id in protected_result.scalars().all()])

        validated_data: List[Dict[str, Any]] = []
        for row in external_data:
            try:
                location_id = str(row.get("location_id", "")).strip()
                if not location_id:
                    raise ValueError("Missing location_id")
                if location_id in protected_location_ids:
                    continue

                validated_data.append({
                    "id": str(uuid.uuid4()),
                    "client_id": str(client_id),
                    "location_id": location_id,
                    "name": row.get("name", ""),
                    "address": row.get("address"),
                    "city": row.get("city"),
                    "country": row.get("country"),
                    "is_synced": True,
                })
            except Exception as e:
                errors.append({"row": row, "error": str(e)})

        upsert_query = text("""
            INSERT INTO locations (id, client_id, location_id, name, address, city, country, is_synced)
            VALUES (:id, :client_id, :location_id, :name, :address, :city, :country, :is_synced)
            ON CONFLICT (client_id, location_id) DO UPDATE
            SET name = EXCLUDED.name,
                address = EXCLUDED.address,
                city = EXCLUDED.city,
                country = EXCLUDED.country,
                is_synced = EXCLUDED.is_synced,
                updated_at = CURRENT_TIMESTAMP
        """)

        if validated_data:
            async with self.db.begin():
                await self.db.execute(upsert_query, validated_data)

        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": len(validated_data),
            "rows_updated": 0,
            "errors": errors[:10]
        }
