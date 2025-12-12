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
from models.location import Location
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.settings import ClientSettings
from services.metrics_service import MetricsService
from schemas.inventory import ProductFilters, ProductResponse, ProductDetailResponse, ProductMetrics, SupplierSummary, LocationStockSummary


class InventoryService:
    """Service for inventory management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_service = MetricsService(db)

    async def get_primary_supplier_id(
        self,
        client_id: UUID,
        item_id: str
    ) -> Optional[UUID]:
        """Get the primary supplier ID for a product"""
        result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.is_primary == True
            ).limit(1)
        )
        condition = result.scalar_one_or_none()
        return condition.supplier_id if condition else None

    async def get_effective_moq(
        self,
        client_id: UUID,
        item_id: str,
        supplier_id: Optional[UUID] = None
    ) -> int:
        """
        Get effective MOQ with fallback chain:
        1. product_supplier_conditions.moq (if exists and > 0)
        2. suppliers.default_moq (if > 0)
        3. System default (0)
        
        If supplier_id is None, uses primary supplier.
        """
        # If no supplier_id provided, use primary supplier
        if supplier_id is None:
            supplier_id = await self.get_primary_supplier_id(client_id, item_id)
            if supplier_id is None:
                return 0  # No supplier, return default
        
        # Check product-supplier condition first
        condition_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = condition_result.scalar_one_or_none()
        if condition and condition.moq > 0:
            return condition.moq

        # Fallback to supplier default
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()
        if supplier and supplier.default_moq > 0:
            return supplier.default_moq

        # System default
        return 0

    async def get_effective_lead_time(
        self,
        client_id: UUID,
        item_id: str,
        supplier_id: Optional[UUID] = None
    ) -> int:
        """
        Get effective lead time with fallback chain:
        1. product_supplier_conditions.lead_time_days (if exists and > 0)
        2. suppliers.default_lead_time_days (if > 0)
        3. System default (14)
        
        If supplier_id is None, uses primary supplier.
        """
        # If no supplier_id provided, use primary supplier
        if supplier_id is None:
            supplier_id = await self.get_primary_supplier_id(client_id, item_id)
            if supplier_id is None:
                return 14  # No supplier, return default
        
        # Check product-supplier condition first
        condition_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = condition_result.scalar_one_or_none()
        if condition and condition.lead_time_days > 0:
            return condition.lead_time_days

        # Fallback to supplier default
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()
        if supplier and supplier.default_lead_time_days > 0:
            return supplier.default_lead_time_days

        # System default
        return 14

    async def get_effective_buffer(
        self,
        client_id: UUID,
        item_id: str
    ) -> int:
        """
        Get effective safety buffer with fallback chain:
        1. products.safety_buffer_days (if set and > 0)
        2. client_settings.safety_buffer_days (if set)
        3. System default (7)
        """
        # Check product override first
        product_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        product = product_result.scalar_one_or_none()
        if product and product.safety_buffer_days is not None and product.safety_buffer_days > 0:
            return product.safety_buffer_days

        # Fallback to client settings
        settings_result = await self.db.execute(
            select(ClientSettings).where(ClientSettings.client_id == client_id)
        )
        settings = settings_result.scalar_one_or_none()
        if settings and settings.safety_buffer_days > 0:
            return settings.safety_buffer_days

        # System default
        return 7

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

            if filters.supplier_id:
                # Use distinct to avoid duplicate products when joining
                query = query.distinct().join(
                    ProductSupplierCondition,
                    and_(
                        ProductSupplierCondition.client_id == client_id,
                        ProductSupplierCondition.item_id == Product.item_id,
                    ),
                ).where(ProductSupplierCondition.supplier_id == filters.supplier_id)

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

        # Compute metrics for each product
        items_with_metrics = []
        for product in products:
            # Get metrics for this product
            metrics = await self.metrics_service.compute_product_metrics(
                client_id=client_id,
                item_id=product.item_id
            )

            # Get all suppliers for this product
            suppliers_list = []
            primary_supplier_name = None
            primary_supplier_moq = None
            primary_supplier_lead_time_days = None
            
            try:
                # Query for all supplier conditions for this product
                supplier_conditions_result = await self.db.execute(
                    select(ProductSupplierCondition).where(
                        ProductSupplierCondition.client_id == client_id,
                        ProductSupplierCondition.item_id == product.item_id
                    ).order_by(
                        ProductSupplierCondition.is_primary.desc(),  # Primary first
                        ProductSupplierCondition.created_at  # Then by creation date
                    )
                )
                conditions = supplier_conditions_result.scalars().all()
                
                # Get supplier info for each condition
                for condition in conditions:
                    supplier_result = await self.db.execute(
                        select(Supplier).where(Supplier.id == condition.supplier_id)
                    )
                    supplier = supplier_result.scalar_one_or_none()
                    
                    if supplier:
                        suppliers_list.append(SupplierSummary(
                            supplier_id=supplier.id,
                            supplier_name=supplier.name,
                            moq=condition.moq,
                            lead_time_days=condition.lead_time_days,
                            is_primary=condition.is_primary
                        ))
                        
                        # Keep primary supplier info for backward compatibility
                        if condition.is_primary:
                            primary_supplier_name = supplier.name
                            primary_supplier_moq = condition.moq
                            primary_supplier_lead_time_days = condition.lead_time_days
            except Exception as e:
                # If supplier query fails, just continue without supplier info
                # This can happen if there's no suppliers or join issues
                pass

            # Get stock levels per location for this product
            locations_list = []
            try:
                # Get all locations for this client
                all_locations_result = await self.db.execute(
                    select(Location).where(
                        Location.client_id == client_id
                    ).order_by(Location.name)
                )
                all_locations = all_locations_result.scalars().all()
                
                # Get all stock levels for this product
                stock_levels_result = await self.db.execute(
                    select(StockLevel).where(
                        StockLevel.client_id == client_id,
                        StockLevel.item_id == product.item_id
                    )
                )
                stock_levels = stock_levels_result.scalars().all()
                
                # Create a map of location_id -> stock level for quick lookup
                stock_by_location = {sl.location_id: sl.current_stock for sl in stock_levels}
                
                # Show all locations, with 0 stock if no stock level exists
                for location in all_locations:
                    current_stock = stock_by_location.get(location.location_id, 0)
                    locations_list.append(LocationStockSummary(
                        location_id=location.location_id,
                        location_name=location.name,
                        current_stock=current_stock
                    ))
            except Exception as e:
                # If location/stock query fails, just continue without location info
                pass

            # Create product response with metrics embedded
            product_response = ProductResponse(
                id=product.id,
                client_id=product.client_id,
                item_id=product.item_id,
                sku=product.sku,
                product_name=product.product_name,
                category=product.category,
                unit_cost=product.unit_cost,
                safety_buffer_days=product.safety_buffer_days,
                created_at=product.created_at,
                updated_at=product.updated_at,
                # Add metrics
                current_stock=metrics.get("current_stock", 0),
                dir=metrics.get("dir"),
                stockout_risk=metrics.get("stockout_risk"),
                inventory_value=metrics.get("inventory_value", Decimal("0.00")),
                status=metrics.get("status", "unknown"),
                # Add all suppliers
                suppliers=suppliers_list if suppliers_list else None,
                # Add stock per location
                locations=locations_list if locations_list else None,
                # Legacy fields (for backward compatibility)
                primary_supplier_name=primary_supplier_name,
                primary_supplier_moq=primary_supplier_moq,
                primary_supplier_lead_time_days=primary_supplier_lead_time_days
            )
            items_with_metrics.append(product_response)

        return {
            "items": items_with_metrics,
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
        metrics = await self.metrics_service.compute_product_metrics(client_id, item_id)

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
        return await self.metrics_service.compute_product_metrics(client_id, item_id, location_id)

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
        moq: Optional[int] = None,
        lead_time_days: Optional[int] = None,
        supplier_cost: Optional[Decimal] = None,
        packaging_unit: Optional[str] = None,
        packaging_qty: Optional[int] = None,
        is_primary: bool = False,
        notes: Optional[str] = None
    ) -> ProductSupplierCondition:
        """
        Link product to supplier with conditions.
        Auto-populates MOQ and lead_time_days from supplier defaults if not provided.
        """
        # Verify product exists
        product_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        if not product_result.scalar_one_or_none():
            raise ValueError(f"Product with item_id {item_id} not found")

        # Verify supplier exists and get defaults
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")

        # Auto-populate MOQ and lead_time_days from supplier defaults if not provided
        if moq is None:
            moq = supplier.default_moq if supplier.default_moq > 0 else 0
        if lead_time_days is None:
            lead_time_days = supplier.default_lead_time_days if supplier.default_lead_time_days > 0 else 14

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
