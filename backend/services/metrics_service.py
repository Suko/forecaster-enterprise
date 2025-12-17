"""
Inventory Metrics Service

Calculates inventory metrics: DIR (Days of Inventory Remaining), stockout risk, etc.
"""
from typing import Optional, List, Dict
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from decimal import Decimal

from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
from models.product_supplier import ProductSupplierCondition
from models.inventory_metrics import InventoryMetric


class MetricsService:
    """Service for calculating inventory metrics"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_client_settings(self, client_id: UUID) -> ClientSettings:
        """Get client settings with thresholds"""
        result = await self.db.execute(
            select(ClientSettings).where(ClientSettings.client_id == client_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            # Return default settings
            return ClientSettings(
                client_id=client_id,
                safety_buffer_days=7,
                understocked_threshold=14,
                overstocked_threshold=90,
                dead_stock_days=90
            )

        return settings

    async def calculate_dir(
        self,
        client_id: UUID,
        item_id: str,
        current_stock: int,
        forecasted_demand_30d: Optional[Decimal] = None,
        location_id: Optional[str] = None
    ) -> Optional[Decimal]:
        """
        Calculate DIR (Days of Inventory Remaining).

        DIR = current_stock / average_daily_demand

        If forecasted_demand_30d is provided, use it.
        Otherwise, calculate from historical sales data (ts_demand_daily).
        """
        if current_stock <= 0:
            return Decimal("0.00")

        if forecasted_demand_30d and forecasted_demand_30d > 0:
            # Use forecasted demand
            avg_daily_demand = forecasted_demand_30d / Decimal("30")
        else:
            # Calculate from historical data (last 30 days)
            avg_daily_demand = await self._get_average_daily_demand(
                client_id, item_id, location_id, days=30
            )

        if avg_daily_demand and avg_daily_demand > 0:
            dir_value = Decimal(current_stock) / avg_daily_demand
            return dir_value

        return None

    async def _get_average_daily_demand(
        self,
        client_id: UUID,
        item_id: str,
        location_id: Optional[str] = None,
        days: int = 30
    ) -> Optional[Decimal]:
        """Get average daily demand from ts_demand_daily table"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Use raw SQL for ts_demand_daily table
        from sqlalchemy import text

        # First try: Get average from last 30 days
        if location_id is None:
            sql_query = text("""
                SELECT AVG(daily_total) as avg_demand
                FROM (
                    SELECT date_local, SUM(units_sold) as daily_total
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                    GROUP BY date_local
                ) daily_totals
            """)
            params = {
                "client_id": str(client_id),
                "item_id": item_id,
                "start_date": start_date,
                "end_date": end_date
            }
        else:
            sql_query = text("""
                SELECT AVG(daily_total) as avg_demand
                FROM (
                    SELECT date_local, SUM(units_sold) as daily_total
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND location_id = :location_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                    GROUP BY date_local
                ) daily_totals
            """)
            params = {
                "client_id": str(client_id),
                "item_id": item_id,
                "location_id": str(location_id),
                "start_date": start_date,
                "end_date": end_date
            }

        result = await self.db.execute(sql_query, params)
        row = result.fetchone()

        if row and row[0]:
            return Decimal(str(row[0]))

        # Fallback: If no data in last 30 days, use most recent available data
        # This handles cases where sales data dates haven't been shifted to recent
        if location_id is None:
            fallback_query = text("""
                SELECT AVG(daily_total) as avg_demand
                FROM (
                    SELECT date_local, SUM(units_sold) as daily_total
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND units_sold > 0
                    GROUP BY date_local
                    ORDER BY date_local DESC
                    LIMIT :days
                ) daily_totals
            """)
            fallback_params = {
                "client_id": str(client_id),
                "item_id": item_id,
                "days": days
            }
        else:
            fallback_query = text("""
                SELECT AVG(daily_total) as avg_demand
                FROM (
                    SELECT date_local, SUM(units_sold) as daily_total
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND location_id = :location_id
                      AND units_sold > 0
                    GROUP BY date_local
                    ORDER BY date_local DESC
                    LIMIT :days
                ) daily_totals
            """)
            fallback_params = {
                "client_id": str(client_id),
                "item_id": item_id,
                "location_id": str(location_id),
                "days": days
            }

        result = await self.db.execute(fallback_query, fallback_params)
        row = result.fetchone()

        if row and row[0]:
            return Decimal(str(row[0]))

        return None

    async def calculate_stockout_risk(
        self,
        client_id: UUID,
        item_id: str,
        current_stock: int,
        dir_value: Optional[Decimal],
        lead_time_days: Optional[int] = None,
        safety_buffer_days: Optional[int] = None
    ) -> Optional[Decimal]:
        """
        Calculate stockout risk (0-1 decimal, where 1.0 = 100%).

        Risk increases when:
        - DIR < (lead_time_days + safety_buffer_days)
        - Current stock is low relative to forecasted demand

        Formula:
        - If DIR < (lead_time + buffer): risk = 1 - DIR / (lead_time + buffer)
        - Otherwise: risk = 0
        - Returns 0-1 range (frontend multiplies by 100 to show as percentage)
        """
        if current_stock <= 0:
            return Decimal("1.00")  # Out of stock (100% = 1.0)

        if not dir_value:
            return None

        # Get lead time and safety buffer
        if lead_time_days is None:
            lead_time_days = await self._get_primary_supplier_lead_time(client_id, item_id)

        if safety_buffer_days is None:
            # Use effective buffer (product override or client default)
            from services.inventory_service import InventoryService
            inventory_service = InventoryService(self.db)
            safety_buffer_days = await inventory_service.get_effective_buffer(client_id, item_id)

        if lead_time_days is None:
            lead_time_days = 14  # Default

        total_required_days = lead_time_days + safety_buffer_days

        if dir_value < total_required_days:
            # Calculate risk: 0 when DIR = total_required_days, 1.0 when DIR = 0
            if total_required_days > 0:
                risk = Decimal("1.00") - (dir_value / Decimal(str(total_required_days)))
                return max(Decimal("0.00"), min(Decimal("1.00"), risk))
            else:
                return Decimal("1.00")

        return Decimal("0.00")

    async def _get_primary_supplier_lead_time(
        self,
        client_id: UUID,
        item_id: str
    ) -> Optional[int]:
        """Get lead time from primary supplier (for calculations) - always uses primary supplier"""
        # Get primary supplier condition
        result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.is_primary == True
            ).limit(1)
        )
        condition = result.scalar_one_or_none()

        if condition and condition.lead_time_days > 0:
            return condition.lead_time_days

        # If no primary supplier, try to get supplier default from any supplier
        # (fallback - but calculations should prefer primary)
        if condition:
            from models.supplier import Supplier
            supplier_result = await self.db.execute(
                select(Supplier).where(
                    Supplier.client_id == client_id,
                    Supplier.id == condition.supplier_id
                )
            )
            supplier = supplier_result.scalar_one_or_none()
            if supplier and supplier.default_lead_time_days > 0:
                return supplier.default_lead_time_days

        return None

    async def determine_status(
        self,
        client_id: UUID,
        dir_value: Optional[Decimal],
        current_stock: int,
        last_sale_date: Optional[date] = None
    ) -> str:
        """
        Determine inventory status: understocked, overstocked, normal, dead_stock

        Uses client settings thresholds.
        """
        if current_stock <= 0:
            return "out_of_stock"

        settings = await self.get_client_settings(client_id)

        # Check for dead stock
        if last_sale_date:
            days_since_sale = (date.today() - last_sale_date).days
            if days_since_sale >= settings.dead_stock_days:
                return "dead_stock"

        if not dir_value:
            return "unknown"

        if dir_value < settings.understocked_threshold:
            return "understocked"
        elif dir_value > settings.overstocked_threshold:
            return "overstocked"
        else:
            return "normal"

    async def calculate_inventory_value(
        self,
        client_id: UUID,
        item_id: str,
        current_stock: int,
        location_id: Optional[str] = None
    ) -> Decimal:
        """Calculate inventory value (stock * unit_cost)"""
        result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        product = result.scalar_one_or_none()

        if not product:
            return Decimal("0.00")

        return Decimal(current_stock) * product.unit_cost

    async def compute_product_metrics(
        self,
        client_id: UUID,
        item_id: str,
        location_id: Optional[str] = None,
        forecasted_demand_30d: Optional[Decimal] = None
    ) -> Dict:
        """
        Compute all metrics for a product.

        Returns dict with:
        - current_stock
        - dir
        - stockout_risk
        - forecasted_demand_30d
        - inventory_value
        - status
        """
        # Get current stock
        stock_query = select(StockLevel).where(
            StockLevel.client_id == client_id,
            StockLevel.item_id == item_id
        )
        if location_id:
            stock_query = stock_query.where(StockLevel.location_id == location_id)

        stock_result = await self.db.execute(stock_query)
        stock_levels = stock_result.scalars().all()

        if not stock_levels:
            return {
                "item_id": item_id,
                "current_stock": 0,
                "dir": None,
                "stockout_risk": Decimal("1.00"),  # 100% = 1.0
                "forecasted_demand_30d": forecasted_demand_30d,
                "inventory_value": Decimal("0.00"),
                "status": "out_of_stock"
            }

        total_stock = sum(sl.current_stock for sl in stock_levels)

        # Calculate DIR
        dir_value = await self.calculate_dir(
            client_id=client_id,
            item_id=item_id,
            current_stock=total_stock,
            forecasted_demand_30d=forecasted_demand_30d,
            location_id=location_id
        )

        # Calculate stockout risk
        stockout_risk = await self.calculate_stockout_risk(
            client_id=client_id,
            item_id=item_id,
            current_stock=total_stock,
            dir_value=dir_value
        )

        # Calculate inventory value
        inventory_value = await self.calculate_inventory_value(
            client_id=client_id,
            item_id=item_id,
            current_stock=total_stock,
            location_id=location_id
        )

        # Determine status
        # TODO: Get last_sale_date from ts_demand_daily
        status = await self.determine_status(
            client_id=client_id,
            dir_value=dir_value,
            current_stock=total_stock,
            last_sale_date=None  # Would need to query ts_demand_daily
        )

        return {
            "item_id": item_id,
            "current_stock": total_stock,
            "dir": dir_value,
            "stockout_risk": stockout_risk,
            "forecasted_demand_30d": forecasted_demand_30d,
            "inventory_value": inventory_value,
            "status": status
        }
