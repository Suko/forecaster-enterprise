"""
Order Planning Cart Model

Session-based shopping cart for order planning.
"""
from sqlalchemy import Column, String, Integer, DateTime, Numeric, UniqueConstraint, Index, ForeignKey
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class OrderCartItem(Base):
    """Shopping cart item for order planning"""
    __tablename__ = "order_cart_items"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)

    # Session identifier (can be user_id or session_id)
    session_id = Column(String(255), nullable=False, index=True)

    # ⚠️ CRITICAL: Use item_id (not sku) to match forecasting engine
    item_id = Column(String(255), nullable=False, index=True)

    supplier_id = Column(GUID(), ForeignKey("suppliers.id"), nullable=False, index=True)

    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)  # quantity * unit_cost

    # Packaging info (from product-supplier condition)
    packaging_unit = Column(String(50), nullable=True)
    packaging_qty = Column(Integer, nullable=True)

    # Notes
    notes = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'session_id', 'item_id', 'supplier_id', name='uq_cart_client_session_item_supplier'),
        Index('idx_cart_client_session', 'client_id', 'session_id'),
        Index('idx_cart_item', 'item_id'),
    )

