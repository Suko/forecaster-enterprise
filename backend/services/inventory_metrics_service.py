"""
Inventory Metrics Service

Helper routines to populate and refresh the `inventory_metrics` table so backend filters stay performant.
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Set
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.product import Product
from models.inventory_metrics import InventoryMetric
from services.metrics_service import MetricsService

DEFAULT_LOCATION_ID = "UNSPECIFIED"


class InventoryMetricsService:
    """Service responsible for seeding and refreshing inventory metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)

    async def ensure_client_metrics(
        self,
        client_id: UUID,
        location_id: str = DEFAULT_LOCATION_ID
    ) -> None:
        """Ensure every product for the client has at least one metric row."""
        product_ids = await self._get_product_ids(client_id)
        if not product_ids:
            return

        existing_ids = await self._get_existing_metric_item_ids(client_id)
        missing_ids = [item_id for item_id in product_ids if item_id not in existing_ids]
        if not missing_ids:
            return

        await self._refresh_items_metrics(client_id, missing_ids, location_id)

    async def refresh_client_metrics(
        self,
        client_id: UUID,
        location_id: str = DEFAULT_LOCATION_ID
    ) -> None:
        """Refresh metrics for all products of a client (useful for cron or manual runs)."""
        product_ids = await self._get_product_ids(client_id)
        if not product_ids:
            return
        await self._refresh_items_metrics(client_id, product_ids, location_id)

    async def _get_product_ids(self, client_id: UUID) -> List[str]:
        result = await self.db.execute(
            select(Product.item_id).where(Product.client_id == client_id)
        )
        return [item_id for item_id in result.scalars().all()]

    async def _get_existing_metric_item_ids(self, client_id: UUID) -> Set[str]:
        result = await self.db.execute(
            select(InventoryMetric.item_id)
            .distinct()
            .where(InventoryMetric.client_id == client_id)
        )
        return {item_id for item_id in result.scalars().all()}

    async def _refresh_items_metrics(
        self,
        client_id: UUID,
        item_ids: List[str],
        location_id: str
    ) -> None:
        if not item_ids:
            return

        metric_rows = []
        for item_id in item_ids:
            metrics = await self.metrics_service.compute_product_metrics(client_id, item_id)
            if not metrics:
                continue

            inventory_value = metrics.get("inventory_value")
            if inventory_value is None:
                inventory_value = Decimal("0.00")

            metric_rows.append(InventoryMetric(
                client_id=client_id,
                item_id=item_id,
                location_id=location_id,
                date=date.today(),
                current_stock=int(metrics.get("current_stock", 0)),
                dir=metrics.get("dir"),
                stockout_risk=metrics.get("stockout_risk"),
                forecasted_demand_30d=metrics.get("forecasted_demand_30d"),
                inventory_value=inventory_value,
                status=metrics.get("status"),
            ))

        if not metric_rows:
            return

        self.db.add_all(metric_rows)
        await self.db.commit()
