"""
Recommendations Service

Business logic for AI-powered inventory recommendations.
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from decimal import Decimal

from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
from models.product_supplier import ProductSupplierCondition
from models.supplier import Supplier
from services.metrics_service import MetricsService


class RecommendationsService:
    """Service for generating recommendations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)
    
    async def get_recommendations(
        self,
        client_id: UUID,
        recommendation_type: Optional[str] = None,
        role: Optional[str] = None
    ) -> List[Dict]:
        """
        Get recommendations based on inventory metrics and rules.
        
        Types:
        - REORDER: DIR < (lead_time + buffer)
        - URGENT: Stockout risk > 70%
        - REDUCE_ORDER: DIR > 90 days
        - DEAD_STOCK: No sales in X days
        - PROMOTE: DIR > 30 days, not in campaign
        """
        # Get client settings
        settings_result = await self.db.execute(
            select(ClientSettings).where(ClientSettings.client_id == client_id)
        )
        settings = settings_result.scalar_one_or_none()
        
        if not settings:
            return []
        
        # Get recommendation rules
        rules = settings.recommendation_rules or {}
        enabled_types = rules.get("enabled_types", [])
        role_rules = rules.get("role_rules", {})
        
        # Filter by role if provided
        if role and role in role_rules:
            enabled_types = [t for t in enabled_types if t in role_rules[role]]
        
        # Filter by type if provided
        if recommendation_type:
            enabled_types = [t for t in enabled_types if t == recommendation_type]
        
        if not enabled_types:
            return []
        
        # Get all active products
        products_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.client_id == client_id
            )
        )
        products = products_result.scalars().all()
        
        recommendations = []
        
        for product in products:
            # Get metrics
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id
            )
            
            # Get primary supplier
            supplier_result = await self.db.execute(
                select(ProductSupplierCondition, Supplier).join(
                    Supplier, ProductSupplierCondition.supplier_id == Supplier.id
                ).where(
                    ProductSupplierCondition.client_id == client_id,
                    ProductSupplierCondition.item_id == product.item_id,
                    ProductSupplierCondition.is_primary == True
                ).limit(1)
            )
            supplier_data = supplier_result.first()
            
            if not supplier_data:
                continue
            
            condition, supplier = supplier_data
            
            # Generate recommendations based on type
            for rec_type in enabled_types:
                rec = await self._generate_recommendation(
                    product=product,
                    metrics=metrics,
                    condition=condition,
                    supplier=supplier,
                    rec_type=rec_type,
                    settings=settings
                )
                
                if rec:
                    recommendations.append(rec)
        
        # Sort by priority (URGENT > REORDER > others)
        priority_order = {"URGENT": 0, "REORDER": 1, "REDUCE_ORDER": 2, "DEAD_STOCK": 3, "PROMOTE": 4}
        recommendations.sort(key=lambda x: priority_order.get(x["type"], 99))
        
        return recommendations
    
    async def _generate_recommendation(
        self,
        product: Product,
        metrics: Dict,
        condition: ProductSupplierCondition,
        supplier: Supplier,
        rec_type: str,
        settings: ClientSettings
    ) -> Optional[Dict]:
        """Generate a specific recommendation"""
        if not metrics.get("dir") or not metrics.get("stockout_risk"):
            return None
        
        dir_value = metrics["dir"]
        stockout_risk = metrics["stockout_risk"]
        current_stock = metrics["current_stock"]
        
        # Calculate suggested quantity
        suggested_qty = condition.moq
        if metrics.get("forecasted_demand_30d"):
            forecasted = metrics["forecasted_demand_30d"]
            required_stock = forecasted + (Decimal(str(settings.safety_buffer_days)) * forecasted / Decimal("30"))
            suggested_qty = max(condition.moq, int(required_stock - Decimal(current_stock)))
        
        reason = ""
        
        if rec_type == "REORDER":
            required_days = condition.lead_time_days + settings.safety_buffer_days
            if dir_value < required_days:
                reason = f"DIR ({dir_value:.1f} days) < lead time + buffer ({required_days} days)"
                return {
                    "id": f"{product.item_id}_{supplier.id}_{rec_type}",
                    "type": rec_type,
                    "item_id": product.item_id,
                    "product_name": product.product_name,
                    "current_stock": current_stock,
                    "dir": float(dir_value),
                    "stockout_risk": float(stockout_risk),
                    "supplier_id": str(supplier.id),
                    "supplier_name": supplier.name,
                    "suggested_quantity": suggested_qty,
                    "moq": condition.moq,
                    "lead_time_days": condition.lead_time_days,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "high"
                }
        
        elif rec_type == "URGENT":
            if stockout_risk > 70:
                reason = f"Stockout risk ({stockout_risk:.1f}%) > 70%"
                return {
                    "id": f"{product.item_id}_{supplier.id}_{rec_type}",
                    "type": rec_type,
                    "item_id": product.item_id,
                    "product_name": product.product_name,
                    "current_stock": current_stock,
                    "dir": float(dir_value),
                    "stockout_risk": float(stockout_risk),
                    "supplier_id": str(supplier.id),
                    "supplier_name": supplier.name,
                    "suggested_quantity": suggested_qty,
                    "moq": condition.moq,
                    "lead_time_days": condition.lead_time_days,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "urgent"
                }
        
        elif rec_type == "REDUCE_ORDER":
            if dir_value > settings.overstocked_threshold:
                reason = f"DIR ({dir_value:.1f} days) > overstocked threshold ({settings.overstocked_threshold} days)"
                return {
                    "id": f"{product.item_id}_{supplier.id}_{rec_type}",
                    "type": rec_type,
                    "item_id": product.item_id,
                    "product_name": product.product_name,
                    "current_stock": current_stock,
                    "dir": float(dir_value),
                    "stockout_risk": float(stockout_risk),
                    "supplier_id": str(supplier.id),
                    "supplier_name": supplier.name,
                    "suggested_quantity": 0,  # Reduce order
                    "moq": condition.moq,
                    "lead_time_days": condition.lead_time_days,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "medium"
                }
        
        elif rec_type == "DEAD_STOCK":
            # Check last sale date
            last_sale_result = await self.db.execute(
                text("""
                    SELECT MAX(date_local) as last_sale
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND units_sold > 0
                """),
                {"client_id": str(client_id), "item_id": product.item_id}
            )
            last_sale_row = last_sale_result.fetchone()
            
            if last_sale_row and last_sale_row[0]:
                days_since_sale = (date.today() - last_sale_row[0]).days
                if days_since_sale >= settings.dead_stock_days:
                    reason = f"No sales for {days_since_sale} days (threshold: {settings.dead_stock_days} days)"
                    return {
                        "id": f"{product.item_id}_{supplier.id}_{rec_type}",
                        "type": rec_type,
                        "item_id": product.item_id,
                        "product_name": product.product_name,
                        "current_stock": current_stock,
                        "dir": float(dir_value) if dir_value else None,
                        "stockout_risk": float(stockout_risk) if stockout_risk else None,
                        "supplier_id": str(supplier.id),
                        "supplier_name": supplier.name,
                        "suggested_quantity": 0,
                        "moq": condition.moq,
                        "lead_time_days": condition.lead_time_days,
                        "unit_cost": float(condition.supplier_cost or product.unit_cost),
                        "reason": reason,
                        "priority": "low"
                    }
        
        elif rec_type == "PROMOTE":
            if dir_value > 30 and current_stock > 0:
                # Check if product is in active campaign (simplified - would need campaign table)
                reason = f"High inventory (DIR: {dir_value:.1f} days), consider promotion"
                return {
                    "id": f"{product.item_id}_{supplier.id}_{rec_type}",
                    "type": rec_type,
                    "item_id": product.item_id,
                    "product_name": product.product_name,
                    "current_stock": current_stock,
                    "dir": float(dir_value),
                    "stockout_risk": float(stockout_risk),
                    "supplier_id": str(supplier.id),
                    "supplier_name": supplier.name,
                    "suggested_quantity": 0,
                    "moq": condition.moq,
                    "lead_time_days": condition.lead_time_days,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "low"
                }
        
        return None

