"""
Client Model

Multi-tenant client/tenant management.
Unified for both SaaS and on-premise deployments.
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID, JSONBType


class Client(Base):
    """Client/tenant model for multi-tenancy"""
    __tablename__ = "clients"
    
    client_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    
    # Client settings
    timezone = Column(String(50), default="UTC", nullable=False)
    currency = Column(String(3), default="EUR", nullable=False)
    settings = Column(JSONBType(), default={})  # Client-specific settings
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

