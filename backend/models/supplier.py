"""
Supplier Model

Supplier master data. Can be synced from external source or app-managed.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class Supplier(Base):
    """Supplier model"""
    __tablename__ = "suppliers"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)
    
    # External supplier identifier (from ERP/system)
    external_id = Column(String(100), nullable=True)
    
    name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    
    # Supplier type: PO (Purchase Order) or WO (Work Order)
    supplier_type = Column(String(20), default="PO", nullable=False)
    
    # Sync status
    is_synced = Column(Boolean, default=False, nullable=False)
    
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'name', name='uq_suppliers_client_name'),
        UniqueConstraint('client_id', 'external_id', name='uq_suppliers_client_external'),
        Index('idx_suppliers_client', 'client_id'),
    )

