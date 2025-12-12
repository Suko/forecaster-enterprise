"""
Supplier Schemas

Pydantic models for supplier views and APIs.
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class SupplierBase(BaseModel):
    """Base supplier schema"""
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: str = "PO"
    default_moq: int = 0
    default_lead_time_days: int = 14
    notes: Optional[str] = None


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier"""
    external_id: Optional[str] = None


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier"""
    name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: Optional[str] = None
    default_moq: Optional[int] = None
    default_lead_time_days: Optional[int] = None
    notes: Optional[str] = None
    apply_to_existing: bool = False  # If True, update product-supplier conditions that match old defaults


class SupplierResponse(BaseModel):
    """Supplier response"""

    id: UUID
    external_id: Optional[str] = None
    name: str
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    supplier_type: str
    default_moq: int
    default_lead_time_days: int
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

