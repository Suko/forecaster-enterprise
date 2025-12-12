"""
Supplier Service

Business logic for supplier operations.
"""

from typing import Optional, Dict, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.supplier import Supplier


class SupplierService:
    """Service for supplier operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_suppliers(
        self,
        client_id: UUID,
        search: Optional[str] = None,
        supplier_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Dict:
        """Get paginated list of suppliers"""
        query = select(Supplier).where(Supplier.client_id == client_id)

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Supplier.name.ilike(search_term),
                    Supplier.external_id.ilike(search_term),
                    Supplier.contact_email.ilike(search_term),
                )
            )

        if supplier_type:
            query = query.where(Supplier.supplier_type == supplier_type)

        count_subquery = query.subquery()
        total_result = await self.db.execute(select(func.count()).select_from(count_subquery))
        total = total_result.scalar() or 0

        query = query.order_by(Supplier.name)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        suppliers: List[Supplier] = result.scalars().all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": suppliers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def get_supplier(self, client_id: UUID, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID"""
        result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id,
            )
        )
        return result.scalar_one_or_none()

