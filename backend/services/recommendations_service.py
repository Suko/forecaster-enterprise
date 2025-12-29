"""
Recommendations Service

Business logic for AI-powered inventory recommendations.
"""
from typing import List, Optional, Dict, Tuple
from uuid import UUID
from datetime import date, timedelta, datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from decimal import Decimal
import asyncio
import logging

from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
from models.product_supplier import ProductSupplierCondition
from models.supplier import Supplier
from models.forecast import ForecastRun, ForecastResult
from services.metrics_service import MetricsService
from services.inventory_service import InventoryService

logger = logging.getLogger(__name__)

# Module-level task tracking (shared across all service instances)
# Key: f"{client_id}:refresh", Value: asyncio.Task
_forecast_refresh_tasks: Dict[str, asyncio.Task] = {}
_forecast_refresh_lock = asyncio.Lock()


class RecommendationsService:
    """Service for generating recommendations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)
        self.inventory_service = InventoryService(db)

    async def _batch_get_latest_forecast_demand(
        self,
        client_id: UUID,
        item_ids: List[str],
        max_age_days: int = 7
    ) -> Dict[str, Tuple[Optional[Decimal], bool]]:
        """
        Batch get latest forecast demand for multiple items.
        
        Returns:
            Dict mapping item_id to (forecasted_demand_30d, is_fresh)
        """
        result = {}
        
        try:
            # Find latest forecast run for this client
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
            
            forecast_run_result = await self.db.execute(
                select(ForecastRun)
                .where(
                    and_(
                        ForecastRun.client_id == client_id,
                        ForecastRun.status == "completed",
                        ForecastRun.created_at >= cutoff_date
                    )
                )
                .order_by(ForecastRun.created_at.desc())
                .limit(1)
            )
            forecast_run = forecast_run_result.scalar_one_or_none()
            
            if not forecast_run:
                # No fresh forecast - return None for all items
                return {item_id: (None, False) for item_id in item_ids}
            
            # Check which items are in the forecast run
            forecast_item_ids = set(forecast_run.item_ids or [])
            
            # Get forecast results for all items (next 30 days from today)
            today = date.today()
            end_date = today + timedelta(days=30)
            method = forecast_run.recommended_method or forecast_run.primary_model
            
            # Batch query forecast results
            forecast_results = await self.db.execute(
                select(ForecastResult)
                .where(
                    and_(
                        ForecastResult.forecast_run_id == forecast_run.forecast_run_id,
                        ForecastResult.item_id.in_(item_ids),
                        ForecastResult.method == method,
                        ForecastResult.date >= today,
                        ForecastResult.date < end_date
                    )
                )
            )
            results = forecast_results.scalars().all()
            
            # Group by item_id and sum
            forecast_by_item: Dict[str, List[Decimal]] = {}
            for r in results:
                if r.item_id not in forecast_by_item:
                    forecast_by_item[r.item_id] = []
                forecast_by_item[r.item_id].append(Decimal(str(r.point_forecast)))
            
            # Build result dict
            for item_id in item_ids:
                if item_id in forecast_item_ids and item_id in forecast_by_item:
                    total_demand = sum(forecast_by_item[item_id])
                    result[item_id] = (total_demand, True)
                else:
                    result[item_id] = (None, False)
                    
        except Exception as e:
            logger.warning(f"Error batch getting forecast demand: {e}")
            # Return None for all items on error
            return {item_id: (None, False) for item_id in item_ids}
        
        return result

    def _trigger_forecast_refresh(
        self,
        client_id: UUID,
        item_ids: List[str],
        user_id: Optional[str] = None
    ) -> None:
        """
        Trigger background forecast refresh for items.
        Non-blocking - runs in background task (fire-and-forget).
        Uses module-level task tracking to prevent duplicates across concurrent requests.
        
        Note: This is a synchronous function that schedules an async task.
        It does NOT await the task, making it truly non-blocking.
        """
        task_key = f"{client_id}:refresh"
        
        # Create background task function
        async def refresh_task():
            # Create new database session for background task
            from models.database import get_async_session_local
            session_local = get_async_session_local()
            async with session_local() as db_session:
                try:
                    from forecasting.services.forecast_service import ForecastService
                    forecast_service = ForecastService(db_session)
                    
                    logger.info(f"Starting background forecast refresh for {len(item_ids)} items")
                    await forecast_service.generate_forecast(
                        client_id=str(client_id),
                        user_id=user_id,
                        item_ids=item_ids,
                        prediction_length=30,
                        primary_model="chronos-2",
                        include_baseline=False
                    )
                    logger.info(f"Forecast refresh completed for client {client_id}")
                except Exception as e:
                    logger.error(f"Forecast refresh failed for client {client_id}: {e}")
                finally:
                    # Clean up task tracking (thread-safe)
                    async with _forecast_refresh_lock:
                        if task_key in _forecast_refresh_tasks:
                            del _forecast_refresh_tasks[task_key]
        
        # Schedule task atomically (check and create in one operation)
        async def schedule_task():
            async with _forecast_refresh_lock:
                if task_key in _forecast_refresh_tasks:
                    task = _forecast_refresh_tasks[task_key]
                    if not task.done():
                        logger.info(f"Forecast refresh already in progress for client {client_id}")
                        return
                    # Task is done but not cleaned up - remove it
                    del _forecast_refresh_tasks[task_key]
                
                # Create and register task atomically (prevents race condition)
                task = asyncio.create_task(refresh_task())
                _forecast_refresh_tasks[task_key] = task
        
        # Schedule the task scheduling (fire-and-forget - we don't await it)
        # Get the current event loop and schedule the task
        try:
            loop = asyncio.get_running_loop()
            # Create task without awaiting - truly fire-and-forget
            loop.create_task(schedule_task())
        except RuntimeError:
            # No running event loop - try to get/create one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(schedule_task())
                else:
                    # Loop exists but not running - schedule for later
                    asyncio.ensure_future(schedule_task(), loop=loop)
            except RuntimeError:
                # Can't schedule - log and continue (don't block)
                logger.warning(f"Could not schedule forecast refresh task for client {client_id} - no event loop")

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
        - URGENT: Stockout risk > 0.70 (70% in 0-1 decimal range)
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
                Product.client_id == client_id
            )
        )
        products = products_result.scalars().all()

        if not products:
            return []

        item_ids = [p.item_id for p in products]

        # Batch check for forecast freshness (use existing forecasts if available)
        # NOTE: We do NOT auto-trigger refresh here - that should be handled by:
        # 1. Scheduled system jobs (every 7 days) - automatic
        # 2. Manual refresh endpoint - user-initiated
        # Navigation should only check and use existing forecasts, not trigger new ones
        forecast_demands = await self._batch_get_latest_forecast_demand(client_id, item_ids)

        recommendations = []

        for product in products:
            # Get forecast demand if available
            forecast_demand, using_forecast = forecast_demands.get(product.item_id, (None, False))
            
            # Get metrics (will use forecast if provided and fresh)
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id,
                forecasted_demand_30d=forecast_demand if using_forecast else None
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
                    client_id=client_id,
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
        client_id: UUID,
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

        # Get effective values (always use primary supplier for calculations)
        effective_moq = await self.inventory_service.get_effective_moq(
            client_id, product.item_id, None  # None = use primary supplier
        )
        effective_lead_time = await self.inventory_service.get_effective_lead_time(
            client_id, product.item_id, None  # None = use primary supplier
        )
        effective_buffer = await self.inventory_service.get_effective_buffer(
            client_id, product.item_id
        )

        # Calculate suggested quantity
        suggested_qty = effective_moq
        if metrics.get("forecasted_demand_30d"):
            forecasted = metrics["forecasted_demand_30d"]
            required_stock = forecasted + (Decimal(str(effective_buffer)) * forecasted / Decimal("30"))
            suggested_qty = max(effective_moq, int(required_stock - Decimal(current_stock)))

        reason = ""

        if rec_type == "REORDER":
            required_days = effective_lead_time + effective_buffer
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
                    "moq": effective_moq,
                    "lead_time_days": effective_lead_time,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "high"
                }

        elif rec_type == "URGENT":
            # Stockout risk is now 0-1 decimal (0.70 = 70%)
            if stockout_risk > 0.70:
                reason = f"Stockout risk ({stockout_risk * 100:.1f}%) > 70%"
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
                    "moq": effective_moq,
                    "lead_time_days": effective_lead_time,
                    "unit_cost": float(condition.supplier_cost or product.unit_cost),
                    "reason": reason,
                    "priority": "high"  # URGENT maps to high priority
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
                {"client_id": client_id, "item_id": product.item_id}
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

