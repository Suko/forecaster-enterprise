"""
Inventory Metrics Model

Computed inventory metrics (DIR, stockout risk, etc.) for fast dashboard queries.
"""
from sqlalchemy import Column, String, Integer, Date, Numeric, DateTime, Index
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class InventoryMetric(Base):
    """Computed inventory metrics per product and location"""
    __tablename__ = "inventory_metrics"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)

    # ⚠️ CRITICAL: Use item_id (not sku) to match forecasting engine
    item_id = Column(String(255), nullable=False, index=True)

    location_id = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)

    # Current state
    current_stock = Column(Integer, nullable=False)

    # Computed metrics
    dir = Column(Numeric(10, 2), nullable=True)  # Days of Inventory Remaining
    stockout_risk = Column(Numeric(5, 2), nullable=True)  # Risk score (0-100)
    forecasted_demand_30d = Column(Numeric(10, 2), nullable=True)  # Forecasted demand for next 30 days
    inventory_value = Column(Numeric(12, 2), nullable=True)  # Current stock * unit_cost

    # Status
    status = Column(String(20), nullable=True, index=True)  # understocked, overstocked, normal

    # Timestamps
    computed_at = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (
        Index('idx_inventory_metrics_client_item_location_date', 'client_id', 'item_id', 'location_id', 'date'),
        Index('idx_inventory_metrics_status', 'status'),
    )

