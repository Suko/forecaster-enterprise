"""
Purchase Order Service

Business logic for purchase order operations.
"""
from typing import List, Optional, Dict
from uuid import UUID
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from decimal import Decimal
import uuid

from models.purchase_order import PurchaseOrder, PurchaseOrderItem
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.order_cart import OrderCartItem
from schemas.order import PurchaseOrderCreate


class PurchaseOrderService:
    """Service for purchase order management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_purchase_order(
        self,
        client_id: UUID,
        data: PurchaseOrderCreate,
        created_by: Optional[str] = None
    ) -> PurchaseOrder:
        """Create purchase order from cart items or direct items"""
        # Verify supplier exists
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == data.supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            raise ValueError(f"Supplier with id {data.supplier_id} not found")
        
        # Generate PO number
        po_number = await self._generate_po_number(client_id)
        
        # Calculate total amount
        total_amount = Decimal("0.00")
        items_list = []
        
        for item_data in data.items:
            # Verify product exists
            product_result = await self.db.execute(
                select(Product).where(
                    Product.client_id == client_id,
                    Product.item_id == item_data.item_id
                )
            )
            product = product_result.scalar_one_or_none()
            if not product:
                raise ValueError(f"Product with item_id {item_data.item_id} not found")
            
            # Get product-supplier condition for validation
            condition_result = await self.db.execute(
                select(ProductSupplierCondition).where(
                    ProductSupplierCondition.client_id == client_id,
                    ProductSupplierCondition.item_id == item_data.item_id,
                    ProductSupplierCondition.supplier_id == data.supplier_id
                )
            )
            condition = condition_result.scalar_one_or_none()
            if not condition:
                raise ValueError(f"Product-supplier condition not found for item_id {item_data.item_id}")
            
            # Validate quantity >= MOQ
            if item_data.quantity < condition.moq:
                raise ValueError(f"Quantity {item_data.quantity} is less than MOQ {condition.moq}")
            
            # Calculate item total
            item_total = Decimal(item_data.quantity) * item_data.unit_cost
            total_amount += item_total
            
            # Create PO item
            po_item = PurchaseOrderItem(
                item_id=item_data.item_id,
                quantity=item_data.quantity,
                unit_cost=item_data.unit_cost,
                total_price=item_total,
                packaging_unit=item_data.packaging_unit or condition.packaging_unit,
                packaging_qty=item_data.packaging_qty or condition.packaging_qty
            )
            items_list.append(po_item)
        
        # Create purchase order
        po = PurchaseOrder(
            client_id=client_id,
            po_number=po_number,
            supplier_id=data.supplier_id,
            status="pending",
            order_date=date.today(),
            expected_delivery_date=data.expected_delivery_date,
            total_amount=total_amount,
            shipping_method=data.shipping_method,
            shipping_unit=data.shipping_unit,
            notes=data.notes,
            created_by=created_by
        )
        
        self.db.add(po)
        await self.db.flush()  # Get PO ID
        
        # Add items
        for item in items_list:
            item.po_id = po.id
            self.db.add(item)
        
        await self.db.commit()
        await self.db.refresh(po)
        
        return po
    
    async def _generate_po_number(self, client_id: UUID) -> str:
        """Generate unique PO number"""
        # Get count of POs for this client
        result = await self.db.execute(
            select(func.count(PurchaseOrder.id)).where(
                PurchaseOrder.client_id == client_id
            )
        )
        count = result.scalar() or 0
        
        # Format: PO-{client_id_short}-{count+1}
        client_short = str(client_id)[:8].upper()
        po_number = f"PO-{client_short}-{count + 1:06d}"
        
        # Ensure uniqueness
        existing_result = await self.db.execute(
            select(PurchaseOrder).where(PurchaseOrder.po_number == po_number)
        )
        if existing_result.scalar_one_or_none():
            # If exists, append timestamp
            import time
            po_number = f"{po_number}-{int(time.time())}"
        
        return po_number
    
    async def get_purchase_orders(
        self,
        client_id: UUID,
        status: Optional[str] = None,
        supplier_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Dict:
        """Get paginated list of purchase orders"""
        query = select(PurchaseOrder).where(PurchaseOrder.client_id == client_id)
        
        if status:
            query = query.where(PurchaseOrder.status == status)
        if supplier_id:
            query = query.where(PurchaseOrder.supplier_id == supplier_id)
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(PurchaseOrder.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return {
            "items": orders,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages
        }
    
    async def get_purchase_order(
        self,
        client_id: UUID,
        po_id: UUID
    ) -> Optional[PurchaseOrder]:
        """Get purchase order by ID"""
        result = await self.db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.client_id == client_id,
                PurchaseOrder.id == po_id
            )
        )
        return result.scalar_one_or_none()
    
    async def update_purchase_order_status(
        self,
        client_id: UUID,
        po_id: UUID,
        status: str
    ) -> Optional[PurchaseOrder]:
        """Update purchase order status"""
        result = await self.db.execute(
            select(PurchaseOrder).where(
                PurchaseOrder.client_id == client_id,
                PurchaseOrder.id == po_id
            )
        )
        po = result.scalar_one_or_none()
        
        if not po:
            return None
        
        valid_statuses = ["pending", "confirmed", "shipped", "received", "cancelled"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        po.status = status
        await self.db.commit()
        await self.db.refresh(po)
        
        return po
    
    async def create_po_from_cart(
        self,
        client_id: UUID,
        session_id: str,
        supplier_id: UUID,
        shipping_method: Optional[str] = None,
        shipping_unit: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> PurchaseOrder:
        """Create purchase order from cart items for a specific supplier"""
        # Get cart items for this supplier
        cart_result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id,
                OrderCartItem.supplier_id == supplier_id
            )
        )
        cart_items = cart_result.scalars().all()
        
        if not cart_items:
            raise ValueError("No items in cart for this supplier")
        
        # Convert cart items to PO items
        from schemas.order import PurchaseOrderItemCreate
        
        po_items = []
        for cart_item in cart_items:
            po_items.append(PurchaseOrderItemCreate(
                item_id=cart_item.item_id,
                quantity=cart_item.quantity,
                unit_cost=cart_item.unit_cost,
                packaging_unit=cart_item.packaging_unit,
                packaging_qty=cart_item.packaging_qty
            ))
        
        # Create PO
        po_data = PurchaseOrderCreate(
            supplier_id=supplier_id,
            items=po_items,
            shipping_method=shipping_method,
            shipping_unit=shipping_unit,
            notes=notes
        )
        
        po = await self.create_purchase_order(
            client_id=client_id,
            data=po_data,
            created_by=created_by
        )
        
        # Remove items from cart
        for cart_item in cart_items:
            await self.db.delete(cart_item)
        
        await self.db.commit()
        
        return po

