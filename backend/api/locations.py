"""
Locations API Routes

API endpoints for location management.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from models.database import get_db
from models.client import Client
from auth.dependencies import get_current_client
from services.location_service import LocationService
from schemas.location import LocationListResponse, LocationResponse, LocationCreate, LocationUpdate


router = APIRouter(prefix="/api/v1", tags=["locations"])


@router.get("/locations", response_model=LocationListResponse)
async def get_locations(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of locations"""
    service = LocationService(db)
    result = await service.get_locations(
        client_id=client.client_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return LocationListResponse(**result)


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get location detail"""
    service = LocationService(db)
    location = await service.get_location(client.client_id, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationResponse.model_validate(location)


@router.post("/locations", response_model=LocationResponse, status_code=201)
async def create_location(
    data: LocationCreate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Create a new location"""
    service = LocationService(db)
    try:
        location = await service.create_location(
            client_id=client.client_id,
            location_id=data.location_id,
            name=data.name,
            address=data.address,
            city=data.city,
            country=data.country,
        )
        return LocationResponse.model_validate(location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/locations/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: UUID,
    data: LocationUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update location information"""
    service = LocationService(db)
    location = await service.update_location(
        client_id=client.client_id,
        location_id=location_id,
        name=data.name,
        address=data.address,
        city=data.city,
        country=data.country,
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return LocationResponse.model_validate(location)


@router.delete("/locations/{location_id}", status_code=204)
async def delete_location(
    location_id: UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Delete a location"""
    service = LocationService(db)
    try:
        success = await service.delete_location(client.client_id, location_id)
        if not success:
            raise HTTPException(status_code=404, detail="Location not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

