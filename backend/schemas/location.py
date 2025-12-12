"""
Location Schemas

Pydantic models for location management API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class LocationBase(BaseModel):
    """Base location schema"""
    location_id: str = Field(..., description="External location identifier", max_length=50)
    name: str = Field(..., description="Location name", max_length=255)
    address: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City", max_length=100)
    country: Optional[str] = Field(None, description="Country", max_length=100)


class LocationCreate(LocationBase):
    """Schema for creating a location"""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location"""
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)


class LocationResponse(LocationBase):
    """Schema for location response"""
    id: UUID
    client_id: UUID
    is_synced: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LocationListResponse(BaseModel):
    """Paginated location list response"""
    items: List[LocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

