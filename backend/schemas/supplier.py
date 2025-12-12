"""
Supplier Schemas

Pydantic models for supplier views and APIs.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SupplierResponse(BaseModel):
    """Supplier response"""

    id: UUID
    external_id: Optional[str] = None
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: str
    is_synced: bool
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SupplierListResponse(BaseModel):
    """Paginated supplier list response"""

    items: List[SupplierResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

