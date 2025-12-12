from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.sql import func
import uuid
from enum import Enum

# Import the Base class from database.py
from .database import Base
from .forecast import GUID, JSONBType

# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"

# ============================================================================
# USER MODEL
# ============================================================================

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    # Multi-tenant: Link user to client
    client_id = Column(GUID(), ForeignKey("clients.client_id"), nullable=False, index=True)

    is_active = Column(Boolean, default=True)
    role = Column(String, default=UserRole.USER.value, nullable=False)
    
    # User preferences (JSONB for flexibility)
    preferences = Column(JSONBType(), default={}, nullable=True)  # Stores UI preferences like column visibility
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

