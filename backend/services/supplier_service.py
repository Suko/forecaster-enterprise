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

        # Get product counts and aggregate statistics for each supplier
        supplier_ids = [s.id for s in suppliers]
        product_counts = {}
        moq_stats = {}  # {supplier_id: {'avg': float, 'min': int, 'max': int, 'custom_count': int}}
        lead_time_stats = {}  # {supplier_id: {'avg': float, 'min': int, 'max': int, 'custom_count': int}}
        
        if supplier_ids:
            # Count products where supplier is primary/default
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

            # Get MOQ and Lead Time statistics (effective values: condition value if > 0, else supplier default)
            # Only count products where this supplier is PRIMARY (is_primary == True)
            from sqlalchemy import case
            for supplier in suppliers:
                # Fetch product-supplier conditions where this supplier is PRIMARY
                conditions_query = select(ProductSupplierCondition).where(
                    ProductSupplierCondition.client_id == client_id,
                    ProductSupplierCondition.supplier_id == supplier.id,
                    ProductSupplierCondition.is_primary == True
                )
                conditions_result = await self.db.execute(conditions_query)
                conditions = conditions_result.scalars().all()
                
                # Calculate effective MOQ values
                moq_values = []
                custom_moq_count = 0
                for condition in conditions:
                    # Effective MOQ: condition.moq if > 0, else supplier default
                    effective_moq = condition.moq if condition.moq > 0 else (supplier.default_moq or 0)
                    moq_values.append(effective_moq)
                    # Count as custom if condition.moq > 0 and different from default
                    if condition.moq > 0 and condition.moq != (supplier.default_moq or 0):
                        custom_moq_count += 1
                
                if moq_values:
                    moq_stats[supplier.id] = {
                        'avg': sum(moq_values) / len(moq_values),
                        'min': min(moq_values),
                        'max': max(moq_values),
                        'custom_count': custom_moq_count
                    }
                else:
                    moq_stats[supplier.id] = {
                        'avg': supplier.default_moq or 0,
                        'min': supplier.default_moq or 0,
                        'max': supplier.default_moq or 0,
                        'custom_count': 0
                    }

                # Calculate effective Lead Time values
                lead_time_values = []
                custom_lead_time_count = 0
                for condition in conditions:
                    # Effective lead time: condition.lead_time_days if > 0, else supplier default
                    effective_lead_time = condition.lead_time_days if condition.lead_time_days > 0 else (supplier.default_lead_time_days or 14)
                    lead_time_values.append(effective_lead_time)
                    # Count as custom if condition.lead_time_days > 0 and different from default
                    if condition.lead_time_days > 0 and condition.lead_time_days != (supplier.default_lead_time_days or 14):
                        custom_lead_time_count += 1
                
                if lead_time_values:
                    lead_time_stats[supplier.id] = {
                        'avg': sum(lead_time_values) / len(lead_time_values),
                        'min': min(lead_time_values),
                        'max': max(lead_time_values),
                        'custom_count': custom_lead_time_count
                    }
                else:
                    lead_time_stats[supplier.id] = {
                        'avg': supplier.default_lead_time_days or 14,
                        'min': supplier.default_lead_time_days or 14,
                        'max': supplier.default_lead_time_days or 14,
                        'custom_count': 0
                    }

        # Attach statistics to suppliers
        for supplier in suppliers:
            setattr(supplier, 'default_product_count', product_counts.get(supplier.id, 0))
            setattr(supplier, 'effective_moq_avg', int(moq_stats.get(supplier.id, {}).get('avg', supplier.default_moq or 0)))
            setattr(supplier, 'effective_moq_min', moq_stats.get(supplier.id, {}).get('min', supplier.default_moq or 0))
            setattr(supplier, 'effective_moq_max', moq_stats.get(supplier.id, {}).get('max', supplier.default_moq or 0))
            setattr(supplier, 'custom_moq_count', moq_stats.get(supplier.id, {}).get('custom_count', 0))
            setattr(supplier, 'effective_lead_time_avg', int(lead_time_stats.get(supplier.id, {}).get('avg', supplier.default_lead_time_days or 14)))
            setattr(supplier, 'effective_lead_time_min', lead_time_stats.get(supplier.id, {}).get('min', supplier.default_lead_time_days or 14))
            setattr(supplier, 'effective_lead_time_max', lead_time_stats.get(supplier.id, {}).get('max', supplier.default_lead_time_days or 14))
            setattr(supplier, 'custom_lead_time_count', lead_time_stats.get(supplier.id, {}).get('custom_count', 0))

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        return {
            "items": suppliers,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
        }

    async def create_supplier(
        self,
        client_id: UUID,
        name: str,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        address: Optional[str] = None,
        supplier_type: str = "PO",
        default_moq: int = 0,
        default_lead_time_days: int = 14,
        external_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Supplier:
        """Create a new supplier"""
        # Check for duplicate name
        existing = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.name == name
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Supplier with name '{name}' already exists")
        
        # Check for duplicate external_id if provided
        if external_id:
            existing_ext = await self.db.execute(
                select(Supplier).where(
                    Supplier.client_id == client_id,
                    Supplier.external_id == external_id
                )
            )
            if existing_ext.scalar_one_or_none():
                raise ValueError(f"Supplier with external_id '{external_id}' already exists")
        
        supplier = Supplier(
            client_id=client_id,
            name=name,
            contact_email=contact_email,
            contact_phone=contact_phone,
            address=address,
            supplier_type=supplier_type,
            default_moq=default_moq,
            default_lead_time_days=default_lead_time_days,
            external_id=external_id,
            notes=notes,
            is_synced=False
        )
        
        self.db.add(supplier)
        await self.db.commit()
        await self.db.refresh(supplier)
        
        # Calculate effective statistics for new supplier (empty initially)
        setattr(supplier, 'default_product_count', 0)
        setattr(supplier, 'effective_moq_avg', default_moq)
        setattr(supplier, 'effective_moq_min', default_moq)
        setattr(supplier, 'effective_moq_max', default_moq)
        setattr(supplier, 'custom_moq_count', 0)
        setattr(supplier, 'effective_lead_time_avg', default_lead_time_days)
        setattr(supplier, 'effective_lead_time_min', default_lead_time_days)
        setattr(supplier, 'effective_lead_time_max', default_lead_time_days)
        setattr(supplier, 'custom_lead_time_count', 0)
        
        return supplier

    async def get_supplier(self, client_id: UUID, supplier_id: UUID) -> Optional[Supplier]:
        """Get supplier by ID with effective statistics"""
        result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id,
            )
        )
        supplier = result.scalar_one_or_none()
        if not supplier:
            return None
        
        # Calculate effective statistics (same logic as get_suppliers)
        # Only count products where this supplier is PRIMARY (is_primary == True)
        conditions_query = select(ProductSupplierCondition).where(
            ProductSupplierCondition.client_id == client_id,
            ProductSupplierCondition.supplier_id == supplier.id,
            ProductSupplierCondition.is_primary == True
        )
        conditions_result = await self.db.execute(conditions_query)
        conditions = conditions_result.scalars().all()
        
        # Calculate effective MOQ values
        moq_values = []
        custom_moq_count = 0
        for condition in conditions:
            effective_moq = condition.moq if condition.moq > 0 else (supplier.default_moq or 0)
            moq_values.append(effective_moq)
            if condition.moq > 0 and condition.moq != (supplier.default_moq or 0):
                custom_moq_count += 1
        
        if moq_values:
            setattr(supplier, 'effective_moq_avg', int(sum(moq_values) / len(moq_values)))
            setattr(supplier, 'effective_moq_min', min(moq_values))
            setattr(supplier, 'effective_moq_max', max(moq_values))
            setattr(supplier, 'custom_moq_count', custom_moq_count)
        else:
            setattr(supplier, 'effective_moq_avg', supplier.default_moq or 0)
            setattr(supplier, 'effective_moq_min', supplier.default_moq or 0)
            setattr(supplier, 'effective_moq_max', supplier.default_moq or 0)
            setattr(supplier, 'custom_moq_count', 0)
        
        # Calculate effective Lead Time values
        lead_time_values = []
        custom_lead_time_count = 0
        for condition in conditions:
            effective_lead_time = condition.lead_time_days if condition.lead_time_days > 0 else (supplier.default_lead_time_days or 14)
            lead_time_values.append(effective_lead_time)
            if condition.lead_time_days > 0 and condition.lead_time_days != (supplier.default_lead_time_days or 14):
                custom_lead_time_count += 1
        
        if lead_time_values:
            setattr(supplier, 'effective_lead_time_avg', int(sum(lead_time_values) / len(lead_time_values)))
            setattr(supplier, 'effective_lead_time_min', min(lead_time_values))
            setattr(supplier, 'effective_lead_time_max', max(lead_time_values))
            setattr(supplier, 'custom_lead_time_count', custom_lead_time_count)
        else:
            setattr(supplier, 'effective_lead_time_avg', supplier.default_lead_time_days or 14)
            setattr(supplier, 'effective_lead_time_min', supplier.default_lead_time_days or 14)
            setattr(supplier, 'effective_lead_time_max', supplier.default_lead_time_days or 14)
            setattr(supplier, 'custom_lead_time_count', 0)
        
        # Get product count (primary/default products)
        count_query = (
            select(func.count(ProductSupplierCondition.item_id))
            .where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.supplier_id == supplier.id,
                ProductSupplierCondition.is_primary == True
            )
        )
        count_result = await self.db.execute(count_query)
        product_count = count_result.scalar() or 0
        setattr(supplier, 'default_product_count', product_count)
        
        return supplier

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
        
        # Recalculate effective statistics after update (conditions may have changed)
        # Only count products where this supplier is PRIMARY (is_primary == True)
        conditions_query = select(ProductSupplierCondition).where(
            ProductSupplierCondition.client_id == client_id,
            ProductSupplierCondition.supplier_id == supplier.id,
            ProductSupplierCondition.is_primary == True
        )
        conditions_result = await self.db.execute(conditions_query)
        conditions = conditions_result.scalars().all()
        
        # Calculate effective MOQ values
        moq_values = []
        custom_moq_count = 0
        for condition in conditions:
            effective_moq = condition.moq if condition.moq > 0 else (supplier.default_moq or 0)
            moq_values.append(effective_moq)
            if condition.moq > 0 and condition.moq != (supplier.default_moq or 0):
                custom_moq_count += 1
        
        if moq_values:
            setattr(supplier, 'effective_moq_avg', int(sum(moq_values) / len(moq_values)))
            setattr(supplier, 'effective_moq_min', min(moq_values))
            setattr(supplier, 'effective_moq_max', max(moq_values))
            setattr(supplier, 'custom_moq_count', custom_moq_count)
        else:
            setattr(supplier, 'effective_moq_avg', supplier.default_moq or 0)
            setattr(supplier, 'effective_moq_min', supplier.default_moq or 0)
            setattr(supplier, 'effective_moq_max', supplier.default_moq or 0)
            setattr(supplier, 'custom_moq_count', 0)
        
        # Calculate effective Lead Time values
        lead_time_values = []
        custom_lead_time_count = 0
        for condition in conditions:
            effective_lead_time = condition.lead_time_days if condition.lead_time_days > 0 else (supplier.default_lead_time_days or 14)
            lead_time_values.append(effective_lead_time)
            if condition.lead_time_days > 0 and condition.lead_time_days != (supplier.default_lead_time_days or 14):
                custom_lead_time_count += 1
        
        if lead_time_values:
            setattr(supplier, 'effective_lead_time_avg', int(sum(lead_time_values) / len(lead_time_values)))
            setattr(supplier, 'effective_lead_time_min', min(lead_time_values))
            setattr(supplier, 'effective_lead_time_max', max(lead_time_values))
            setattr(supplier, 'custom_lead_time_count', custom_lead_time_count)
        else:
            setattr(supplier, 'effective_lead_time_avg', supplier.default_lead_time_days or 14)
            setattr(supplier, 'effective_lead_time_min', supplier.default_lead_time_days or 14)
            setattr(supplier, 'effective_lead_time_max', supplier.default_lead_time_days or 14)
            setattr(supplier, 'custom_lead_time_count', 0)
        
        # Get product count (primary/default products)
        count_query = (
            select(func.count(ProductSupplierCondition.item_id))
            .where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.supplier_id == supplier.id,
                ProductSupplierCondition.is_primary == True
            )
        )
        count_result = await self.db.execute(count_query)
        product_count = count_result.scalar() or 0
        setattr(supplier, 'default_product_count', product_count)
        
        return supplier

