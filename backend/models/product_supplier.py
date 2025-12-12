"""
Product-Supplier Conditions Model

Links products to suppliers and stores app-managed conditions (MOQ, lead time, etc.).
"""
from sqlalchemy import Column, String, Integer, Numeric, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class ProductSupplierCondition(Base):
    """Product-supplier relationship with ordering conditions"""
    __tablename__ = "product_supplier_conditions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)

    # ⚠️ CRITICAL: Use item_id (not sku) to match forecasting engine
    item_id = Column(String(255), nullable=False, index=True)

    supplier_id = Column(GUID(), ForeignKey("suppliers.id"), nullable=False, index=True)

    # App-managed conditions (always managed in app, not synced)
    moq = Column(Integer, default=0, nullable=False)  # Minimum Order Quantity
    lead_time_days = Column(Integer, default=0, nullable=False)  # Days to deliver

    # Supplier-specific product information
    supplier_sku = Column(String(100), nullable=True)  # Supplier's SKU if different
    supplier_cost = Column(Numeric(10, 2), nullable=True)  # Price from this supplier

    # Packaging requirements
    packaging_unit = Column(String(50), nullable=True)  # box, pallet, carton, etc.
    packaging_qty = Column(Integer, nullable=True)  # units per package

    # Primary supplier flag
    is_primary = Column(Boolean, default=False, nullable=False)

    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'item_id', 'supplier_id', name='uq_product_supplier_client_item_supplier'),
        Index('idx_product_supplier_client_item', 'client_id', 'item_id'),
        Index('idx_product_supplier_supplier', 'supplier_id'),
    )

