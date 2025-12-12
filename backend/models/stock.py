"""
Stock Levels Model

Current inventory levels per product and location.
"""
from sqlalchemy import Column, String, Integer, DateTime, UniqueConstraint, Index, ForeignKey
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class StockLevel(Base):
    """Stock levels per product and location"""
    __tablename__ = "stock_levels"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)

    # ⚠️ CRITICAL: Use item_id (not sku) to match forecasting engine
    item_id = Column(String(255), nullable=False, index=True)

    location_id = Column(String(50), nullable=False)

    current_stock = Column(Integer, nullable=False, default=0)

    # Timestamps
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'item_id', 'location_id', name='uq_stock_client_item_location'),
        Index('idx_stock_client_item_location', 'client_id', 'item_id', 'location_id'),
    )

