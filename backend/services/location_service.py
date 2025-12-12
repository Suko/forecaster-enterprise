"""
Location Service

Business logic for location operations.
"""

from typing import Optional, Dict, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.location import Location


class LocationService:
    """Service for location operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_locations(
        self,
        client_id: UUID,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        """Get paginated list of locations"""
        query = select(Location).where(Location.client_id == client_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Location.name.ilike(search_term),
                    Location.location_id.ilike(search_term),
                    Location.city.ilike(search_term),
                    Location.country.ilike(search_term),
                )
            )

        count_subquery = query.subquery()
        total_result = await self.db.execute(select(func.count()).select_from(count_subquery))
        total = total_result.scalar() or 0

        query = query.order_by(Location.name)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        locations: List[Location] = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": locations,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_location(self, client_id: UUID, location_id: UUID) -> Optional[Location]:
        """Get location by ID"""
        result = await self.db.execute(
            select(Location).where(
                Location.client_id == client_id,
                Location.id == location_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_location_by_location_id(self, client_id: UUID, location_id_str: str) -> Optional[Location]:
        """Get location by location_id (external ID)"""
        result = await self.db.execute(
            select(Location).where(
                Location.client_id == client_id,
                Location.location_id == location_id_str,
            )
        )
        return result.scalar_one_or_none()

    async def create_location(
        self,
        client_id: UUID,
        location_id: str,
        name: str,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Location:
        """Create a new location"""
        # Check if location_id already exists
        existing = await self.get_location_by_location_id(client_id, location_id)
        if existing:
            raise ValueError(f"Location with ID '{location_id}' already exists")

        location = Location(
            client_id=client_id,
            location_id=location_id,
            name=name,
            address=address,
            city=city,
            country=country,
            is_synced=False,  # App-managed locations are not synced
        )
        self.db.add(location)
        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def update_location(
        self,
        client_id: UUID,
        location_id: UUID,
        name: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Optional[Location]:
        """Update location information"""
        location = await self.get_location(client_id, location_id)
        if not location:
            return None

        if name is not None:
            location.name = name
        if address is not None:
            location.address = address
        if city is not None:
            location.city = city
        if country is not None:
            location.country = country

        await self.db.commit()
        await self.db.refresh(location)
        return location

    async def delete_location(self, client_id: UUID, location_id: UUID) -> bool:
        """Delete a location"""
        location = await self.get_location(client_id, location_id)
        if not location:
            return False

        # Don't allow deletion of synced locations
        if location.is_synced:
            raise ValueError("Cannot delete synced locations. They must be removed from the external source.")

        await self.db.delete(location)
        await self.db.commit()
        return True

