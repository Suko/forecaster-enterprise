"""
Location Model

Warehouse/store locations. Can be synced from external source or app-managed.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, UniqueConstraint, Index
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID


class Location(Base):
    """Location model for warehouses/stores"""
    __tablename__ = "locations"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)
    
    # External location identifier (from ERP/system)
    location_id = Column(String(50), nullable=False)
    
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Sync status
    is_synced = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('client_id', 'location_id', name='uq_locations_client_location'),
        Index('idx_locations_client_location', 'client_id', 'location_id'),
    )

