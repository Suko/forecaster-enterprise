"""
Supplier Service

Business logic for supplier operations.
"""

from typing import Optional, Dict, List
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition


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

        # Get product counts for each supplier (only primary/default products)
        supplier_ids = [s.id for s in suppliers]
        product_counts = {}
        if supplier_ids:
            count_query = (
                select(
                    ProductSupplierCondition.supplier_id,
                    func.count(ProductSupplierCondition.item_id).label('count')
                )
                .where(
                    ProductSupplierCondition.client_id == client_id,
                    ProductSupplierCondition.supplier_id.in_(supplier_ids),
                    ProductSupplierCondition.is_primary == True
                )
                .group_by(ProductSupplierCondition.supplier_id)
            )
            count_result = await self.db.execute(count_query)
            for row in count_result.all():
                product_counts[row.supplier_id] = row.count

        # Attach product counts to suppliers
        for supplier in suppliers:
            setattr(supplier, 'default_product_count', product_counts.get(supplier.id, 0))

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

    async def update_supplier(
        self,
        client_id: UUID,
        supplier_id: UUID,
        name: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        supplier_type: Optional[str] = None,
        default_moq: Optional[int] = None,
        default_lead_time_days: Optional[int] = None,
        notes: Optional[str] = None,
        apply_to_existing: bool = False,
    ) -> Optional[Supplier]:
        """
        Update supplier and optionally apply new defaults to existing product-supplier conditions.

        If apply_to_existing is True:
        - Updates product-supplier conditions where moq/lead_time_days match the old supplier defaults
        - Leaves conditions with explicit overrides unchanged
        """
        supplier = await self.get_supplier(client_id, supplier_id)
        if not supplier:
            return None

        # Store old defaults before updating
        old_default_moq = supplier.default_moq
        old_default_lead_time_days = supplier.default_lead_time_days

        # Update supplier fields
        if name is not None:
            supplier.name = name
        if contact_email is not None:
            supplier.contact_email = contact_email
        if contact_phone is not None:
            supplier.contact_phone = contact_phone
        if address is not None:
            supplier.address = address
        if supplier_type is not None:
            supplier.supplier_type = supplier_type
        if default_moq is not None:
            supplier.default_moq = default_moq
        if default_lead_time_days is not None:
            supplier.default_lead_time_days = default_lead_time_days
        if notes is not None:
            supplier.notes = notes

        await self.db.flush()

        # If apply_to_existing is True, update product-supplier conditions
        if apply_to_existing:
            from models.product_supplier import ProductSupplierCondition

            # Build update conditions
            conditions_to_update = []

            # If MOQ changed, find conditions matching old MOQ
            if default_moq is not None and default_moq != old_default_moq:
                moq_conditions = await self.db.execute(
                    select(ProductSupplierCondition).where(
                        ProductSupplierCondition.client_id == client_id,
                        ProductSupplierCondition.supplier_id == supplier_id,
                        ProductSupplierCondition.moq == old_default_moq,
                    )
                )
                conditions_to_update.extend(moq_conditions.scalars().all())

            # If lead time changed, find conditions matching old lead time
            if default_lead_time_days is not None and default_lead_time_days != old_default_lead_time_days:
                lead_time_conditions = await self.db.execute(
                    select(ProductSupplierCondition).where(
                        ProductSupplierCondition.client_id == client_id,
                        ProductSupplierCondition.supplier_id == supplier_id,
                        ProductSupplierCondition.lead_time_days == old_default_lead_time_days,
                    )
                )
                # Add to list, avoiding duplicates
                for condition in lead_time_conditions.scalars().all():
                    if condition not in conditions_to_update:
                        conditions_to_update.append(condition)

            # Update conditions that matched old defaults
            for condition in conditions_to_update:
                if default_moq is not None and condition.moq == old_default_moq:
                    condition.moq = default_moq
                if default_lead_time_days is not None and condition.lead_time_days == old_default_lead_time_days:
                    condition.lead_time_days = default_lead_time_days

        await self.db.commit()
        await self.db.refresh(supplier)
        return supplier

