"""
Client Settings Model

Client-specific settings and thresholds for inventory management.
"""
from sqlalchemy import Column, Integer, DateTime, UniqueConstraint
from sqlalchemy.sql import func
import uuid

from .database import Base
from .forecast import GUID, JSONBType


class ClientSettings(Base):
    """Client settings and thresholds"""
    __tablename__ = "client_settings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), unique=True, nullable=False, index=True)

    # Inventory Thresholds
    safety_buffer_days = Column(Integer, default=7, nullable=False)  # Extra days for safety
    understocked_threshold = Column(Integer, default=14, nullable=False)  # DIR days (lead_time + buffer)
    overstocked_threshold = Column(Integer, default=90, nullable=False)  # DIR days
    dead_stock_days = Column(Integer, default=90, nullable=False)  # No sales for X days = dead stock

    # Recommendation Rules (JSONB)
    recommendation_rules = Column(JSONBType(), default={
        "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
        "role_rules": {
            "CEO": ["URGENT", "DEAD_STOCK"],
            "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
            "MARKETING": ["PROMOTE", "DEAD_STOCK"]
        },
        "min_inventory_value": 0,
        "min_risk_score": 0
    }, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

