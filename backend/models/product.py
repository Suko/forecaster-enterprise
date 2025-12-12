"""
Product Model

Product master data. Uses item_id as the primary identifier to match forecasting engine.
"""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class Product(Base):
    """Product master model"""
    __tablename__ = "products"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)

    # ⚠️ CRITICAL: item_id is the canonical identifier used by forecasting engine
    # Must match ts_demand_daily.item_id, forecast_results.item_id, sku_classifications.item_id
    item_id = Column(String(255), nullable=False, index=True)

    # Optional: sku as alias for external systems (if different from item_id)
    sku = Column(String(255), nullable=True)

    product_name = Column(String(255), nullable=False)
    category = Column(String(100), default="Uncategorized", nullable=False)
    unit_cost = Column(Numeric(10, 2), default=0, nullable=False)

    # Safety buffer override (NULL = use client default from client_settings)
    safety_buffer_days = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'item_id', name='uq_products_client_item'),
        Index('idx_products_client_item', 'client_id', 'item_id'),
    )

