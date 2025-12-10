"""
Cart Service

Business logic for order planning cart operations.
"""
from typing import List, Optional, Dict
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from decimal import Decimal

from models.order_cart import OrderCartItem
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from schemas.order import CartItemCreate, CartItemUpdate


class CartService:
    """Service for cart management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def _get_session_id(self, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """Get session identifier (prefer user_id if available)"""
        return user_id or session_id or "anonymous"
    
    async def add_to_cart(
        self,
        client_id: UUID,
        session_id: str,
        item_id: str,
        supplier_id: UUID,
        quantity: Optional[int] = None,
        notes: Optional[str] = None
    ) -> OrderCartItem:
        """Add item to cart"""
        # Verify product exists
        product_result = await self.db.execute(
            select(Product).where(
                Product.client_id == client_id,
                Product.item_id == item_id
            )
        )
        product = product_result.scalar_one_or_none()
        if not product:
            raise ValueError(f"Product with item_id {item_id} not found")
        
        # Verify supplier exists
        supplier_result = await self.db.execute(
            select(Supplier).where(
                Supplier.client_id == client_id,
                Supplier.id == supplier_id
            )
        )
        supplier = supplier_result.scalar_one_or_none()
        if not supplier:
            raise ValueError(f"Supplier with id {supplier_id} not found")
        
        # Get product-supplier condition
        condition_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = condition_result.scalar_one_or_none()
        if not condition:
            raise ValueError(f"Product-supplier condition not found for item_id {item_id} and supplier {supplier_id}")
        
        # Use MOQ if quantity not provided
        if quantity is None:
            quantity = condition.moq
        elif quantity < condition.moq:
            raise ValueError(f"Quantity {quantity} is less than MOQ {condition.moq}")
        
        # Calculate costs
        unit_cost = condition.supplier_cost or product.unit_cost
        total_price = Decimal(quantity) * unit_cost
        
        # Check if item already in cart
        existing_result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id,
                OrderCartItem.item_id == item_id,
                OrderCartItem.supplier_id == supplier_id
            )
        )
        existing = existing_result.scalar_one_or_none()
        
        if existing:
            # Update existing item
            existing.quantity = quantity
            existing.unit_cost = unit_cost
            existing.total_price = total_price
            existing.notes = notes
            await self.db.commit()
            await self.db.refresh(existing)
            return existing
        
        # Create new cart item
        cart_item = OrderCartItem(
            client_id=client_id,
            session_id=session_id,
            item_id=item_id,
            supplier_id=supplier_id,
            quantity=quantity,
            unit_cost=unit_cost,
            total_price=total_price,
            packaging_unit=condition.packaging_unit,
            packaging_qty=condition.packaging_qty,
            notes=notes
        )
        
        self.db.add(cart_item)
        await self.db.commit()
        await self.db.refresh(cart_item)
        
        return cart_item
    
    async def get_cart(
        self,
        client_id: UUID,
        session_id: str
    ) -> List[OrderCartItem]:
        """Get all items in cart"""
        result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id
            ).order_by(OrderCartItem.supplier_id, OrderCartItem.created_at)
        )
        return result.scalars().all()
    
    async def update_cart_item(
        self,
        client_id: UUID,
        session_id: str,
        item_id: str,
        supplier_id: UUID,
        quantity: Optional[int] = None,
        notes: Optional[str] = None
    ) -> Optional[OrderCartItem]:
        """Update cart item"""
        result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id,
                OrderCartItem.item_id == item_id,
                OrderCartItem.supplier_id == supplier_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return None
        
        # Get product-supplier condition for MOQ validation
        condition_result = await self.db.execute(
            select(ProductSupplierCondition).where(
                ProductSupplierCondition.client_id == client_id,
                ProductSupplierCondition.item_id == item_id,
                ProductSupplierCondition.supplier_id == supplier_id
            )
        )
        condition = condition_result.scalar_one_or_none()
        
        if quantity is not None:
            if condition and quantity < condition.moq:
                raise ValueError(f"Quantity {quantity} is less than MOQ {condition.moq}")
            cart_item.quantity = quantity
            cart_item.total_price = Decimal(quantity) * cart_item.unit_cost
        
        if notes is not None:
            cart_item.notes = notes
        
        await self.db.commit()
        await self.db.refresh(cart_item)
        
        return cart_item
    
    async def remove_from_cart(
        self,
        client_id: UUID,
        session_id: str,
        item_id: str,
        supplier_id: UUID
    ) -> bool:
        """Remove item from cart"""
        result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id,
                OrderCartItem.item_id == item_id,
                OrderCartItem.supplier_id == supplier_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return False
        
        await self.db.delete(cart_item)
        await self.db.commit()
        
        return True
    
    async def clear_cart(
        self,
        client_id: UUID,
        session_id: str
    ) -> int:
        """Clear entire cart"""
        result = await self.db.execute(
            select(OrderCartItem).where(
                OrderCartItem.client_id == client_id,
                OrderCartItem.session_id == session_id
            )
        )
        items = result.scalars().all()
        
        count = len(items)
        for item in items:
            await self.db.delete(item)
        
        await self.db.commit()
        
        return count

