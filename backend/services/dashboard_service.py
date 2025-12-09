"""
Dashboard Service

Calculates dashboard KPIs and aggregates.
"""
from typing import List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from decimal import Decimal

from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
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
        # Get all products for client
        products_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id
            )
        )
        products = products_result.scalars().all()
        
        if not products:
            # Return empty dashboard
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
        
        # Calculate metrics for each product
        product_metrics = []
        total_inventory_value = Decimal("0.00")
        understocked_count = 0
        overstocked_count = 0
        understocked_value = Decimal("0.00")
        overstocked_value = Decimal("0.00")
        dir_sum = Decimal("0.00")
        dir_count = 0
        
        for product in products:
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id
            )
            
            product_metrics.append({
                "product": product,
                "metrics": metrics
            })
            
            # Aggregate totals
            if metrics["inventory_value"]:
                total_inventory_value += metrics["inventory_value"]
            
            if metrics["status"] == "understocked":
                understocked_count += 1
                if metrics["inventory_value"]:
                    understocked_value += metrics["inventory_value"]
            elif metrics["status"] == "overstocked":
                overstocked_count += 1
                if metrics["inventory_value"]:
                    overstocked_value += metrics["inventory_value"]
            
            if metrics["dir"]:
                dir_sum += metrics["dir"]
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
