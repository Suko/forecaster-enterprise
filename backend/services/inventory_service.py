"""
Inventory Service

Business logic for inventory management operations.
"""
from typing import Optional, List, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.sql import desc, asc
from decimal import Decimal

from models.product import Product
from models.stock import StockLevel
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.inventory_metrics import InventoryMetric
from services.metrics_service import MetricsService
from schemas.inventory import ProductFilters, ProductResponse, ProductDetailResponse, ProductMetrics


class InventoryService:
    """Service for inventory management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)
    
    async def get_products(
        self,
        client_id: UUID,
        filters: Optional[ProductFilters] = None,
        page: int = 1,
        page_size: int = 50,
        sort: Optional[str] = None,
        order: str = "asc"
    ) -> Dict:
        """
        Get paginated list of products with filters and sorting.
        
        Returns:
            dict with items, total, page, page_size, total_pages
        """
        # Base query
        query = select(Product).where(Product.client_id == client_id)
        
        # Apply filters
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.where(
                    or_(
                        Product.item_id.ilike(search_term),
                        Product.product_name.ilike(search_term),
                        Product.category.ilike(search_term)
                    )
                )
            
            if filters.category:
                query = query.where(Product.category == filters.category)
        
        # Get total count before pagination
        # Create a subquery for counting
        count_subquery = query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply sorting
        if sort:
            sort_column = getattr(Product, sort, None)
            if sort_column:
                if order.lower() == "desc":
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
        else:
            # Default sort by item_id
            query = query.order_by(Product.item_id)
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": [ProductResponse.model_validate(p) for p in products],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def get_product(self, client_id: UUID, item_id: str) -> Optional[ProductDetailResponse]:
        """Get product details by item_id"""
        result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        product = result.scalar_one_or_none()
        
        if not product:
            return None
        
        # Get metrics using metrics service
        metrics = await self.metrics_service.calculate_product_metrics(client_id, item_id)
        
        product_detail = ProductDetailResponse.model_validate(product)
        product_detail.metrics = metrics
        
        return product_detail
    
    async def get_product_metrics(
        self,
        client_id: UUID,
        item_id: str,
        location_id: Optional[str] = None
    ) -> Optional[ProductMetrics]:
        """
        Get product metrics (DIR, stockout risk, etc.)
        
        Uses MetricsService to calculate metrics.
        """
        return await self.metrics_service.calculate_product_metrics(client_id, item_id, location_id)
    
    async def get_product_suppliers(
        self,
        client_id: UUID,
        item_id: str
    ) -> List[ProductSupplierCondition]:
        """Get all suppliers for a product with conditions"""
        result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id
            )
        )
        return result.scalars().all()
    
    async def add_product_supplier(
        self,
        client_id: UUID,
        item_id: str,
        supplier_id: UUID,
        moq: int,
        lead_time_days: int,
        supplier_cost: Optional[Decimal] = None,
        packaging_unit: Optional[str] = None,
        packaging_qty: Optional[int] = None,
        is_primary: bool = False,
        notes: Optional[str] = None
    ) -> ProductSupplierCondition:
        """Link product to supplier with conditions"""
        # Verify product exists
        product_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        if not product_result.scalar_one_or_none():
            raise ValueError(f"Product with item_id {item_id} not found")
        
        # Verify supplier exists
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id
            )
        )
        if not supplier_result.scalar_one_or_none():
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        # Check if condition already exists
        existing_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        if existing_result.scalar_one_or_none():
            raise ValueError(f"Product-supplier condition already exists")
        
        # Create condition
        condition = ProductSupplierCondition(
            client_id=client_id,
            item_id=item_id,
            supplier_id=supplier_id,
            moq=moq,
            lead_time_days=lead_time_days,
            supplier_cost=supplier_cost,
            packaging_unit=packaging_unit,
            packaging_qty=packaging_qty,
            is_primary=is_primary,
            notes=notes
        )
        
        self.db.add(condition)
        await self.db.commit()
        await self.db.refresh(condition)
        
        return condition
    
    async def update_product_supplier(
        self,
        client_id: UUID,
        item_id: str,
        supplier_id: UUID,
        moq: Optional[int] = None,
        lead_time_days: Optional[int] = None,
        supplier_cost: Optional[Decimal] = None,
        packaging_unit: Optional[str] = None,
        packaging_qty: Optional[int] = None,
        is_primary: Optional[bool] = None,
        notes: Optional[str] = None
    ) -> Optional[ProductSupplierCondition]:
        """Update product-supplier condition"""
        result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = result.scalar_one_or_none()
        
        if not condition:
            return None
        
        # Update fields
        if moq is not None:
            condition.moq = moq
        if lead_time_days is not None:
            condition.lead_time_days = lead_time_days
        if supplier_cost is not None:
            condition.supplier_cost = supplier_cost
        if packaging_unit is not None:
            condition.packaging_unit = packaging_unit
        if packaging_qty is not None:
            condition.packaging_qty = packaging_qty
        if is_primary is not None:
            condition.is_primary = is_primary
        if notes is not None:
            condition.notes = notes
        
        await self.db.commit()
        await self.db.refresh(condition)
        
        return condition
    
    async def remove_product_supplier(
        self,
        client_id: UUID,
        item_id: str,
        supplier_id: UUID
    ) -> bool:
        """Remove product-supplier link"""
        result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = result.scalar_one_or_none()
        
        if not condition:
            return False
        
        await self.db.delete(condition)
        await self.db.commit()
        
        return True

