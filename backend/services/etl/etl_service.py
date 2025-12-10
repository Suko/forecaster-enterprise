"""
ETL Service

Handles data synchronization from external sources to internal database.
"""
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text
from sqlalchemy.dialects.postgresql import insert

from models.product import Product
from models.stock import StockLevel
from models.location import Location
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
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
        inserted_count = 0
        updated_count = 0
        
        if replace:
            # Delete existing data for date range
            delete_query = text("""
                DELETE FROM ts_demand_daily 
                WHERE client_id = :client_id
            """)
            if start_date:
                delete_query = text("""
                    DELETE FROM ts_demand_daily 
                    WHERE client_id = :client_id AND date_local >= :start_date
                """)
                await self.db.execute(delete_query, {
                    "client_id": str(client_id),
                    "start_date": start_date
                })
            else:
                await self.db.execute(delete_query, {"client_id": str(client_id)})
            await self.db.commit()
        
        # Upsert data
        insert_query = text("""
            INSERT INTO ts_demand_daily 
            (item_id, date_local, units_sold, client_id, promotion_flag, holiday_flag, is_weekend, marketing_spend)
            VALUES (:item_id, :date_local, :units_sold, :client_id, :promotion_flag, :holiday_flag, :is_weekend, :marketing_spend)
            ON CONFLICT (item_id, date_local, client_id) DO UPDATE
            SET units_sold = EXCLUDED.units_sold,
                promotion_flag = EXCLUDED.promotion_flag,
                holiday_flag = EXCLUDED.holiday_flag,
                is_weekend = EXCLUDED.is_weekend,
                marketing_spend = EXCLUDED.marketing_spend
        """)
        
        for row_data in validated_data:
            result = await self.db.execute(insert_query, row_data)
            if result.rowcount > 0:
                # Check if it was insert or update by querying first
                # For simplicity, we'll count all as inserted/updated
                inserted_count += 1
        
        await self.db.commit()
        
        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_validated": len(validated_data),
            "rows_inserted": inserted_count,
            "rows_updated": updated_count,
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
        inserted_count = 0
        updated_count = 0
        
        for row in external_data:
            try:
                # Map external fields
                item_id = str(row.get("item_id") or row.get("sku", ""))
                if not item_id:
                    raise ValueError("Missing item_id/sku")
                
                # Check if product exists
                result = await self.db.execute(
                    select(Product).where(
                        and_(
                            Product.client_id == client_id,
                            Product.item_id == item_id
                        )
                    )
                )
                existing_product = result.scalar_one_or_none()
                
                product_data = {
                    "item_id": item_id,
                    "client_id": client_id,
                    "sku": row.get("sku"),  # Optional alias
                    "product_name": row.get("product_name") or row.get("name", "Unknown"),
                    "category": row.get("category", "Uncategorized"),
                    "unit_cost": float(row.get("unit_cost") or row.get("cost", 0)),
                }
                
                if existing_product:
                    # Update existing
                    for key, value in product_data.items():
                        if key != "item_id" and key != "client_id":
                            setattr(existing_product, key, value)
                    updated_count += 1
                else:
                    # Insert new
                    new_product = Product(**product_data)
                    self.db.add(new_product)
                    inserted_count += 1
                
            except Exception as e:
                errors.append({"row": row, "error": str(e)})
        
        await self.db.commit()
        
        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": inserted_count,
            "rows_updated": updated_count,
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
        if replace:
            await self.db.execute(
                text("DELETE FROM stock_levels WHERE client_id = :client_id"),
                {"client_id": str(client_id)}
            )
            await self.db.commit()
        
        # Validate and upsert stock levels
        errors = []
        inserted_count = 0
        
        for row in external_data:
            try:
                item_id = str(row.get("item_id") or row.get("sku", ""))
                location_id = str(row.get("location_id", "default"))
                current_stock = float(row.get("current_stock") or row.get("stock", 0))
                
                if not item_id:
                    raise ValueError("Missing item_id/sku")
                if current_stock < 0:
                    raise ValueError("current_stock must be >= 0")
                
                # Check if stock level exists
                result = await self.db.execute(
                    select(StockLevel).where(
                        and_(
                            StockLevel.client_id == client_id,
                            StockLevel.item_id == item_id,
                            StockLevel.location_id == location_id
                        )
                    )
                )
                existing_stock = result.scalar_one_or_none()
                
                if existing_stock:
                    existing_stock.current_stock = current_stock
                else:
                    new_stock = StockLevel(
                        client_id=client_id,
                        item_id=item_id,
                        location_id=location_id,
                        current_stock=current_stock
                    )
                    self.db.add(new_stock)
                
                inserted_count += 1
                
            except Exception as e:
                errors.append({"row": row, "error": str(e)})
        
        await self.db.commit()
        
        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": inserted_count,
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
        inserted_count = 0
        updated_count = 0
        
        for row in external_data:
            try:
                location_id = str(row.get("location_id", ""))
                if not location_id:
                    raise ValueError("Missing location_id")
                
                # Check if location exists
                result = await self.db.execute(
                    select(Location).where(
                        and_(
                            Location.client_id == client_id,
                            Location.location_id == location_id
                        )
                    )
                )
                existing_location = result.scalar_one_or_none()
                
                # Don't overwrite app-managed locations
                if existing_location and not existing_location.is_synced:
                    continue
                
                location_data = {
                    "client_id": client_id,
                    "location_id": location_id,
                    "name": row.get("name", ""),
                    "address": row.get("address"),
                    "city": row.get("city"),
                    "country": row.get("country"),
                    "is_synced": True,  # Mark as synced
                }
                
                if existing_location:
                    for key, value in location_data.items():
                        if key != "location_id" and key != "client_id":
                            setattr(existing_location, key, value)
                    updated_count += 1
                else:
                    new_location = Location(**location_data)
                    self.db.add(new_location)
                    inserted_count += 1
                
            except Exception as e:
                errors.append({"row": row, "error": str(e)})
        
        await self.db.commit()
        
        return {
            "success": True,
            "rows_fetched": len(external_data),
            "rows_inserted": inserted_count,
            "rows_updated": updated_count,
            "errors": errors[:10]
        }

