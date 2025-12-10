"""
Purchase Orders API Routes

API endpoints for purchase order management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from models.database import get_db
from models.client import Client
from auth.dependencies import get_current_client
from auth import get_current_user
from models import User
from services.purchase_order_service import PurchaseOrderService
from schemas.order import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
    PurchaseOrderItemResponse,
)

router = APIRouter(prefix="/api/v1", tags=["purchase-orders"])


@router.post("/purchase-orders", response_model=PurchaseOrderResponse, status_code=201)
async def create_purchase_order(
    data: PurchaseOrderCreate,
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new purchase order.
    
    Can be created from:
    - Direct items (provided in request)
    - Cart items (use create_po_from_cart endpoint)
    """
    service = PurchaseOrderService(db)
    
    created_by = user.email if user else None
    
    try:
        po = await service.create_purchase_order(
            client_id=client.client_id,
            data=data,
            created_by=created_by
        )
        
        # Get supplier and items for response
        from sqlalchemy import select
        from models.supplier import Supplier
        from models.product import Product
        from models.purchase_order import PurchaseOrderItem
        
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == po.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        items_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po.id)
        )
        items = items_result.scalars().all()
        
        items_response = []
        for item in items:
            product_result = await db.execute(
                select(Product).where(Product.item_id == item.item_id)
            )
            product = product_result.scalar_one()
            
            items_response.append(PurchaseOrderItemResponse(
                id=item.id,
                item_id=item.item_id,
                product_name=product.product_name,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                total_price=item.total_price,
                packaging_unit=item.packaging_unit,
                packaging_qty=item.packaging_qty
            ))
        
        return PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=supplier.name,
            status=po.status,
            order_date=po.order_date,
            expected_delivery_date=po.expected_delivery_date,
            total_amount=po.total_amount,
            shipping_method=po.shipping_method,
            shipping_unit=po.shipping_unit,
            notes=po.notes,
            created_by=po.created_by,
            items=items_response,
            created_at=po.created_at.date(),
            updated_at=po.updated_at.date()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/purchase-orders/from-cart", response_model=PurchaseOrderResponse, status_code=201)
async def create_po_from_cart(
    supplier_id: UUID,
    shipping_method: Optional[str] = None,
    shipping_unit: Optional[str] = None,
    notes: Optional[str] = None,
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Create purchase order from cart items for a specific supplier.
    
    Removes items from cart after creating PO.
    """
    service = PurchaseOrderService(db)
    
    session_id = user.email if user else x_session_id or "anonymous"
    created_by = user.email if user else None
    
    try:
        po = await service.create_po_from_cart(
            client_id=client.client_id,
            session_id=session_id,
            supplier_id=supplier_id,
            shipping_method=shipping_method,
            shipping_unit=shipping_unit,
            notes=notes,
            created_by=created_by
        )
        
        # Get supplier and items for response
        from sqlalchemy import select
        from models.supplier import Supplier
        from models.product import Product
        from models.purchase_order import PurchaseOrderItem
        
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == po.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        items_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po.id)
        )
        items = items_result.scalars().all()
        
        items_response = []
        for item in items:
            product_result = await db.execute(
                select(Product).where(Product.item_id == item.item_id)
            )
            product = product_result.scalar_one()
            
            items_response.append(PurchaseOrderItemResponse(
                id=item.id,
                item_id=item.item_id,
                product_name=product.product_name,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                total_price=item.total_price,
                packaging_unit=item.packaging_unit,
                packaging_qty=item.packaging_qty
            ))
        
        return PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=supplier.name,
            status=po.status,
            order_date=po.order_date,
            expected_delivery_date=po.expected_delivery_date,
            total_amount=po.total_amount,
            shipping_method=po.shipping_method,
            shipping_unit=po.shipping_unit,
            notes=po.notes,
            created_by=po.created_by,
            items=items_response,
            created_at=po.created_at.date(),
            updated_at=po.updated_at.date()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/purchase-orders", response_model=dict)
async def get_purchase_orders(
    status: Optional[str] = Query(None),
    supplier_id: Optional[UUID] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of purchase orders"""
    service = PurchaseOrderService(db)
    
    result = await service.get_purchase_orders(
        client_id=client.client_id,
        status=status,
        supplier_id=supplier_id,
        page=page,
        page_size=page_size
    )
    
    # Convert to response format
    from sqlalchemy import select
    from models.supplier import Supplier
    
    orders_response = []
    for po in result["items"]:
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == po.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        orders_response.append({
            "id": str(po.id),
            "po_number": po.po_number,
            "supplier_id": str(po.supplier_id),
            "supplier_name": supplier.name,
            "status": po.status,
            "order_date": po.order_date.isoformat(),
            "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
            "total_amount": float(po.total_amount),
            "created_at": po.created_at.isoformat()
        })
    
    return {
        "items": orders_response,
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"],
        "total_pages": result["total_pages"]
    }


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderResponse)
async def get_purchase_order(
    po_id: UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get purchase order details"""
    service = PurchaseOrderService(db)
    
    po = await service.get_purchase_order(client.client_id, po_id)
    
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    
    # Get supplier and items
    from sqlalchemy import select
    from models.supplier import Supplier
    from models.product import Product
    from models.purchase_order import PurchaseOrderItem
    
    supplier_result = await db.execute(
        select(Supplier).where(Supplier.id == po.supplier_id)
    )
    supplier = supplier_result.scalar_one()
    
    items_result = await db.execute(
        select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po.id)
    )
    items = items_result.scalars().all()
    
    items_response = []
    for item in items:
        product_result = await db.execute(
            select(Product).where(Product.item_id == item.item_id)
        )
        product = product_result.scalar_one()
        
        items_response.append(PurchaseOrderItemResponse(
            id=item.id,
            item_id=item.item_id,
            product_name=product.product_name,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_price=item.total_price,
            packaging_unit=item.packaging_unit,
            packaging_qty=item.packaging_qty
        ))
    
    return PurchaseOrderResponse(
        id=po.id,
        po_number=po.po_number,
        supplier_id=po.supplier_id,
        supplier_name=supplier.name,
        status=po.status,
        order_date=po.order_date,
        expected_delivery_date=po.expected_delivery_date,
        total_amount=po.total_amount,
        shipping_method=po.shipping_method,
        shipping_unit=po.shipping_unit,
        notes=po.notes,
        created_by=po.created_by,
        items=items_response,
        created_at=po.created_at.date(),
        updated_at=po.updated_at.date()
    )


@router.put("/purchase-orders/{po_id}/status", response_model=PurchaseOrderResponse)
async def update_purchase_order_status(
    po_id: UUID,
    data: PurchaseOrderStatusUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update purchase order status"""
    service = PurchaseOrderService(db)
    
    try:
        po = await service.update_purchase_order_status(
            client_id=client.client_id,
            po_id=po_id,
            status=data.status
        )
        
        if not po:
            raise HTTPException(status_code=404, detail="Purchase order not found")
        
        # Get supplier and items for response
        from sqlalchemy import select
        from models.supplier import Supplier
        from models.product import Product
        from models.purchase_order import PurchaseOrderItem
        
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == po.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        items_result = await db.execute(
            select(PurchaseOrderItem).where(PurchaseOrderItem.po_id == po.id)
        )
        items = items_result.scalars().all()
        
        items_response = []
        for item in items:
            product_result = await db.execute(
                select(Product).where(Product.item_id == item.item_id)
            )
            product = product_result.scalar_one()
            
            items_response.append(PurchaseOrderItemResponse(
                id=item.id,
                item_id=item.item_id,
                product_name=product.product_name,
                quantity=item.quantity,
                unit_cost=item.unit_cost,
                total_price=item.total_price,
                packaging_unit=item.packaging_unit,
                packaging_qty=item.packaging_qty
            ))
        
        return PurchaseOrderResponse(
            id=po.id,
            po_number=po.po_number,
            supplier_id=po.supplier_id,
            supplier_name=supplier.name,
            status=po.status,
            order_date=po.order_date,
            expected_delivery_date=po.expected_delivery_date,
            total_amount=po.total_amount,
            shipping_method=po.shipping_method,
            shipping_unit=po.shipping_unit,
            notes=po.notes,
            created_by=po.created_by,
            items=items_response,
            created_at=po.created_at.date(),
            updated_at=po.updated_at.date()
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

