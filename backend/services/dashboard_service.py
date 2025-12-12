"""
Dashboard Service

Calculates dashboard KPIs and aggregates.
"""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from decimal import Decimal

from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
from models.product_supplier import ProductSupplierCondition
from services.metrics_service import MetricsService
from schemas.inventory import DashboardMetrics, TopProduct, DashboardResponse


class DashboardService:
    """Service for dashboard calculations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)

    async def get_dashboard_data(self, client_id: UUID) -> DashboardResponse:
        """
        Get complete dashboard data:
        - Overall metrics (total SKUs, inventory value, counts)
        - Top understocked products
        - Top overstocked products
        """
        # Batch load all data
        products_result = await self.db.execute(
            select(Product).where(Product.client_id == client_id)
        )
        products = products_result.scalars().all()

        if not products:
            return DashboardResponse(
                metrics=DashboardMetrics(
                    total_skus=0,
                    total_inventory_value=Decimal("0.00"),
                    understocked_count=0,
                    overstocked_count=0,
                    average_dir=Decimal("0.00"),
                    understocked_value=Decimal("0.00"),
                    overstocked_value=Decimal("0.00")
                ),
                top_understocked=[],
                top_overstocked=[]
            )

        item_ids = [p.item_id for p in products]
        product_map = {p.item_id: p for p in products}

        # Batch load stock levels
        stock_result = await self.db.execute(
            select(StockLevel).where(
                StockLevel.client_id == client_id,
                StockLevel.item_id.in_(item_ids)
            )
        )
        stock_levels = stock_result.scalars().all()
        stock_by_item = {}
        for sl in stock_levels:
            if sl.item_id not in stock_by_item:
                stock_by_item[sl.item_id] = 0
            stock_by_item[sl.item_id] += sl.current_stock

        # Batch load average daily demands
        avg_demands = await self._batch_get_average_daily_demand(client_id, item_ids)

        # Batch load supplier conditions
        supplier_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id.in_(item_ids)
            )
        )
        supplier_conditions = supplier_result.scalars().all()
        lead_times = {}
        for sc in supplier_conditions:
            if sc.item_id not in lead_times or sc.is_primary:
                lead_times[sc.item_id] = sc.lead_time_days

        # Load client settings once
        settings_result = await self.db.execute(
            select(ClientSettings).where(ClientSettings.client_id == client_id)
        )
        settings = settings_result.scalar_one_or_none()
        if not settings:
            settings = ClientSettings(
                client_id=client_id,
                safety_buffer_days=7,
                understocked_threshold=14,
                overstocked_threshold=90,
                dead_stock_days=90
            )

        # Calculate metrics for all products
        product_metrics = []
        total_inventory_value = Decimal("0.00")
        understocked_count = 0
        overstocked_count = 0
        understocked_value = Decimal("0.00")
        overstocked_value = Decimal("0.00")
        dir_sum = Decimal("0.00")
        dir_count = 0

        for product in products:
            current_stock = stock_by_item.get(product.item_id, 0)
            avg_demand = avg_demands.get(product.item_id)

            # Calculate DIR
            dir_value = None
            if current_stock > 0 and avg_demand and avg_demand > 0:
                dir_value = Decimal(current_stock) / avg_demand

            # Calculate stockout risk
            stockout_risk = None
            if current_stock <= 0:
                stockout_risk = Decimal("100.00")
            elif dir_value:
                lead_time = lead_times.get(product.item_id) or 14
                total_required = lead_time + settings.safety_buffer_days
                if dir_value < total_required:
                    if total_required > 0:
                        risk = Decimal("100.00") * (Decimal("1.00") - (dir_value / Decimal(str(total_required))))
                        stockout_risk = max(Decimal("0.00"), min(Decimal("100.00"), risk))
                    else:
                        stockout_risk = Decimal("100.00")
                else:
                    stockout_risk = Decimal("0.00")

            # Calculate inventory value
            inventory_value = Decimal(current_stock) * product.unit_cost

            # Determine status
            if current_stock <= 0:
                status = "out_of_stock"
            elif not dir_value:
                status = "unknown"
            elif dir_value < settings.understocked_threshold:
                status = "understocked"
            elif dir_value > settings.overstocked_threshold:
                status = "overstocked"
            else:
                status = "normal"

            metrics = {
                "item_id": product.item_id,
                "current_stock": current_stock,
                "dir": dir_value,
                "stockout_risk": stockout_risk,
                "inventory_value": inventory_value,
                "status": status
            }

            product_metrics.append({
                "product": product,
                "metrics": metrics
            })

            # Aggregate totals
            if inventory_value:
                total_inventory_value += inventory_value

            if status == "understocked":
                understocked_count += 1
                if inventory_value:
                    understocked_value += inventory_value
            elif status == "overstocked":
                overstocked_count += 1
                if inventory_value:
                    overstocked_value += inventory_value

            if dir_value:
                dir_sum += dir_value
                dir_count += 1

        # Calculate average DIR
        average_dir = dir_sum / Decimal(str(dir_count)) if dir_count > 0 else Decimal("0.00")

        # Build dashboard metrics
        dashboard_metrics = DashboardMetrics(
            total_skus=len(products),
            total_inventory_value=total_inventory_value,
            understocked_count=understocked_count,
            overstocked_count=overstocked_count,
            average_dir=average_dir,
            understocked_value=understocked_value,
            overstocked_value=overstocked_value
        )

        # Get top understocked (by risk, then by value)
        understocked_products = [
            pm for pm in product_metrics
            if pm["metrics"]["status"] == "understocked"
        ]
        understocked_products.sort(
            key=lambda x: (
                x["metrics"]["stockout_risk"] or Decimal("0.00"),
                x["metrics"]["inventory_value"] or Decimal("0.00")
            ),
            reverse=True
        )
        top_understocked = [
            TopProduct(
                item_id=pm["product"].item_id,
                product_name=pm["product"].product_name,
                current_stock=pm["metrics"]["current_stock"],
                dir=pm["metrics"]["dir"] or Decimal("0.00"),
                stockout_risk=pm["metrics"]["stockout_risk"] or Decimal("0.00"),
                inventory_value=pm["metrics"]["inventory_value"] or Decimal("0.00")
            )
            for pm in understocked_products[:10]  # Top 10
        ]

        # Get top overstocked (by value)
        overstocked_products = [
            pm for pm in product_metrics
            if pm["metrics"]["status"] == "overstocked"
        ]
        overstocked_products.sort(
            key=lambda x: x["metrics"]["inventory_value"] or Decimal("0.00"),
            reverse=True
        )
        top_overstocked = [
            TopProduct(
                item_id=pm["product"].item_id,
                product_name=pm["product"].product_name,
                current_stock=pm["metrics"]["current_stock"],
                dir=pm["metrics"]["dir"] or Decimal("0.00"),
                stockout_risk=pm["metrics"]["stockout_risk"] or Decimal("0.00"),
                inventory_value=pm["metrics"]["inventory_value"] or Decimal("0.00")
            )
            for pm in overstocked_products[:10]  # Top 10
        ]

        return DashboardResponse(
            metrics=dashboard_metrics,
            top_understocked=top_understocked,
            top_overstocked=top_overstocked
        )

    async def _batch_get_average_daily_demand(
        self, client_id: UUID, item_ids: List[str], days: int = 30
    ) -> Dict[str, Optional[Decimal]]:
        """Batch get average daily demand for multiple items"""
        if not item_ids:
            return {}

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        # Optimized batch query using array operator
        # SQLAlchemy will handle type conversion automatically
        sql_query = text("""
            SELECT item_id, AVG(daily_total) as avg_demand
            FROM (
                SELECT item_id, date_local, SUM(units_sold) as daily_total
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = ANY(:item_ids)
                  AND date_local >= :start_date
                  AND date_local <= :end_date
                GROUP BY item_id, date_local
            ) daily_totals
            GROUP BY item_id
        """)

        result = await self.db.execute(
            sql_query,
            {
                "client_id": str(client_id),
                "item_ids": item_ids,
                "start_date": start_date,
                "end_date": end_date
            }
        )

        # Build result map
        demands = {}
        for row in result:
            if row[1]:  # avg_demand
                demands[row[0]] = Decimal(str(row[1]))

        # Fallback for items without recent data - optimized query
        missing_items = [item_id for item_id in item_ids if item_id not in demands]
        if missing_items:
            # Simplified fallback: get most recent N days per item using window function
            fallback_query = text("""
                WITH daily_totals AS (
                    SELECT
                        item_id,
                        date_local,
                        SUM(units_sold) as daily_total
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = ANY(:item_ids)
                      AND units_sold > 0
                    GROUP BY item_id, date_local
                ),
                ranked_days AS (
                    SELECT
                        item_id,
                        date_local,
                        daily_total,
                        ROW_NUMBER() OVER (PARTITION BY item_id ORDER BY date_local DESC) as rn
                    FROM daily_totals
                )
                SELECT item_id, AVG(daily_total) as avg_demand
                FROM ranked_days
                WHERE rn <= :days
                GROUP BY item_id
            """)

            fallback_result = await self.db.execute(
                fallback_query,
                {
                    "client_id": str(client_id),
                    "item_ids": missing_items,
                    "days": days
                }
            )

            for row in fallback_result:
                if row[1]:  # avg_demand
                    demands[row[0]] = Decimal(str(row[1]))

        return demands
