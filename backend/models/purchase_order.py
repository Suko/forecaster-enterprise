"""
Purchase Order Models

Purchase orders and order line items.
"""
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class PurchaseOrder(Base):
    """Purchase order header"""
    __tablename__ = "purchase_orders"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)
    
    po_number = Column(String(50), nullable=False, unique=True, index=True)
    supplier_id = Column(GUID(), ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Order status
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, confirmed, shipped, received, cancelled
    
    # Dates
    order_date = Column(Date, nullable=False, server_default=func.current_date())
    expected_delivery_date = Column(Date, nullable=True)
    
    # Financials
    total_amount = Column(Numeric(12, 2), nullable=False, default=0)
    
    # Shipping
    shipping_method = Column(String(50), nullable=True)
    shipping_unit = Column(String(50), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    # Audit
    created_by = Column(String(255), nullable=True)  # User ID or email
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        Index('idx_purchase_orders_client', 'client_id'),
        Index('idx_purchase_orders_supplier', 'supplier_id'),
        Index('idx_purchase_orders_status', 'status'),
    )


class PurchaseOrderItem(Base):
    """Purchase order line items"""
    __tablename__ = "purchase_order_items"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    po_id = Column(GUID(), ForeignKey("purchase_orders.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # ⚠️ CRITICAL: Use item_id (not sku) to match forecasting engine
    item_id = Column(String(255), nullable=False, index=True)
    
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)  # quantity * unit_cost
    
    # Packaging
    packaging_unit = Column(String(50), nullable=True)
    packaging_qty = Column(Integer, nullable=True)
    
    # Constraints
    __table_args__ = (
        Index('idx_purchase_order_items_po', 'po_id'),
        Index('idx_purchase_order_items_item', 'item_id'),
    )

