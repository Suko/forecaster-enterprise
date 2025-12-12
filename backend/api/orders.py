"""
Order Planning & Purchase Orders API Routes

API endpoints for order planning cart and purchase orders.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from models.database import get_db
from models.client import Client
from auth.dependencies import get_current_client
from auth import get_current_user
from models.user import User
from services.cart_service import CartService
from services.recommendations_service import RecommendationsService
from services.metrics_service import MetricsService
from schemas.order import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
    CartItemResponse,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
    OrderSuggestionsResponse,
    OrderSuggestion,
)

router = APIRouter(prefix="/api/v1", tags=["orders"])


def get_session_id(user_id: Optional[str] = None, x_session_id: Optional[str] = None) -> str:
    """Get session identifier (prefer user_id if available)"""
    return user_id or x_session_id or "anonymous"


# ============================================================================
# Order Planning Cart API
# ============================================================================

@router.post("/order-planning/cart/add", response_model=CartItemResponse)
async def add_to_cart(
    item: CartItemCreate,
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Add item to order planning cart.

    Validates:
    - Product exists
    - Supplier exists and is linked to product
    - Quantity >= MOQ
    """
    service = CartService(db)

    session_id = get_session_id(user_id=str(user.id) if user else None, x_session_id=x_session_id)

    try:
        cart_item = await service.add_to_cart(
            client_id=client.client_id,
            session_id=session_id,
            item_id=item.item_id,
            supplier_id=item.supplier_id,
            quantity=item.quantity,
            notes=item.notes
        )

        # Get product and supplier info for response
        from sqlalchemy import select
        from models.product import Product
        from models.supplier import Supplier

        product_result = await db.execute(
            select(Product).where(Product.item_id == cart_item.item_id)
        )
        product = product_result.scalar_one()

        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == cart_item.supplier_id)
        )
        supplier = supplier_result.scalar_one()

        return CartItemResponse(
            id=cart_item.id,
            session_id=cart_item.session_id,
            item_id=cart_item.item_id,
            supplier_id=cart_item.supplier_id,
            quantity=cart_item.quantity,
            unit_cost=cart_item.unit_cost,
            total_price=cart_item.total_price,
            packaging_unit=cart_item.packaging_unit,
            packaging_qty=cart_item.packaging_qty,
            notes=cart_item.notes,
            product_name=product.product_name,
            supplier_name=supplier.name,
            created_at=cart_item.created_at.date(),
            updated_at=cart_item.updated_at.date()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/order-planning/cart", response_model=CartResponse)
async def get_cart(
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get current cart items grouped by supplier"""
    service = CartService(db)

    session_id = get_session_id(user_id=str(user.id) if user else None, x_session_id=x_session_id)

    cart_items = await service.get_cart(client.client_id, session_id)

    # Get product and supplier info
    from sqlalchemy import select
    from models.product import Product
    from models.supplier import Supplier

    items_response = []
    suppliers_dict = {}
    total_value = Decimal("0.00")

    for item in cart_items:
        product_result = await db.execute(
            select(Product).where(Product.item_id == item.item_id)
        )
        product = product_result.scalar_one()

        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == item.supplier_id)
        )
        supplier = supplier_result.scalar_one()

        items_response.append(CartItemResponse(
            id=item.id,
            session_id=item.session_id,
            item_id=item.item_id,
            supplier_id=item.supplier_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_price=item.total_price,
            packaging_unit=item.packaging_unit,
            packaging_qty=item.packaging_qty,
            notes=item.notes,
            product_name=product.product_name,
            supplier_name=supplier.name,
            created_at=item.created_at.date(),
            updated_at=item.updated_at.date()
        ))

        total_value += item.total_price

        # Group by supplier
        if str(supplier.id) not in suppliers_dict:
            suppliers_dict[str(supplier.id)] = {
                "supplier_id": str(supplier.id),
                "supplier_name": supplier.name,
                "items": []
            }
        suppliers_dict[str(supplier.id)]["items"].append(item.item_id)

    return CartResponse(
        items=items_response,
        total_items=len(items_response),
        total_value=total_value,
        suppliers=list(suppliers_dict.values())
    )


@router.put("/order-planning/cart/{item_id}", response_model=CartItemResponse)
async def update_cart_item(
    item_id: str,
    supplier_id: UUID,
    update: CartItemUpdate,
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """Update cart item quantity or notes"""
    service = CartService(db)

    session_id = get_session_id(user_id=str(user.id) if user else None, x_session_id=x_session_id)

    try:
        cart_item = await service.update_cart_item(
            client_id=client.client_id,
            session_id=session_id,
            item_id=item_id,
            supplier_id=supplier_id,
            quantity=update.quantity,
            notes=update.notes
        )

        if not cart_item:
            raise HTTPException(status_code=404, detail="Cart item not found")

        # Get product and supplier info
        from sqlalchemy import select
        from models.product import Product
        from models.supplier import Supplier

        product_result = await db.execute(
            select(Product).where(Product.item_id == cart_item.item_id)
        )
        product = product_result.scalar_one()

        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == cart_item.supplier_id)
        )
        supplier = supplier_result.scalar_one()

        return CartItemResponse(
            id=cart_item.id,
            session_id=cart_item.session_id,
            item_id=cart_item.item_id,
            supplier_id=cart_item.supplier_id,
            quantity=cart_item.quantity,
            unit_cost=cart_item.unit_cost,
            total_price=cart_item.total_price,
            packaging_unit=cart_item.packaging_unit,
            packaging_qty=cart_item.packaging_qty,
            notes=cart_item.notes,
            product_name=product.product_name,
            supplier_name=supplier.name,
            created_at=cart_item.created_at.date(),
            updated_at=cart_item.updated_at.date()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/order-planning/cart/{item_id}")
async def remove_from_cart(
    item_id: str,
    supplier_id: UUID,
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """Remove item from cart"""
    service = CartService(db)

    session_id = get_session_id(user_id=str(user.id) if user else None, x_session_id=x_session_id)

    success = await service.remove_from_cart(
        client_id=client.client_id,
        session_id=session_id,
        item_id=item_id,
        supplier_id=supplier_id
    )

    if not success:
        raise HTTPException(status_code=404, detail="Cart item not found")

    return {"message": "Item removed from cart"}


@router.post("/order-planning/cart/clear")
async def clear_cart(
    client: Client = Depends(get_current_client),
    user: Optional[User] = Depends(get_current_user),
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: AsyncSession = Depends(get_db),
):
    """Clear entire cart"""
    service = CartService(db)

    session_id = get_session_id(user_id=str(user.id) if user else None, x_session_id=x_session_id)

    count = await service.clear_cart(client.client_id, session_id)

    return {"message": f"Cart cleared ({count} items removed)"}


# ============================================================================
# Order Suggestions API
# ============================================================================

@router.get("/order-planning/suggestions", response_model=OrderSuggestionsResponse)
async def get_order_suggestions(
    location_id: Optional[str] = None,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get order suggestions based on forecasted demand, current stock, and lead time.

    Suggests products that need reordering based on:
    - Forecasted demand
    - Current stock
    - Lead time + safety buffer
    """
    metrics_service = MetricsService(db)

    # Get all active products
    from sqlalchemy import select
    from models.product import Product
    from models.product_supplier import ProductSupplierCondition
    from models.supplier import Supplier

    products_result = await db.execute(
        select(Product).where(
            Product.client_id == client.client_id
        )
    )
    products = products_result.scalars().all()

    suggestions = []
    total_value = Decimal("0.00")

    for product in products:
        # Get metrics
        metrics = await metrics_service.compute_product_metrics(
            client_id=client.client_id,
            item_id=product.item_id,
            location_id=location_id
        )

        # Get primary supplier
        supplier_result = await db.execute(
            select(ProductSupplierCondition, Supplier).join(
                Supplier, ProductSupplierCondition.supplier_id == Supplier.id
            ).where(
                ProductSupplierCondition.client_id == client.client_id,
                ProductSupplierCondition.item_id == product.item_id,
                ProductSupplierCondition.is_primary == True
            ).limit(1)
        )
        supplier_data = supplier_result.first()

        if not supplier_data:
            continue

        condition, supplier = supplier_data

        # Calculate suggested quantity
        suggested_qty = condition.moq
        if metrics.get("forecasted_demand_30d") and metrics.get("dir"):
            forecasted = metrics["forecasted_demand_30d"]
            required_stock = forecasted + (Decimal("30") * forecasted / Decimal("30"))  # Simplified
            suggested_qty = max(condition.moq, int(required_stock - Decimal(metrics["current_stock"])))

        # Only suggest if stockout risk is high
        if metrics.get("stockout_risk") and metrics["stockout_risk"] > 50:
            unit_cost = condition.supplier_cost or product.unit_cost
            total_cost = Decimal(suggested_qty) * unit_cost
            total_value += total_cost

            suggestions.append(OrderSuggestion(
                item_id=product.item_id,
                product_name=product.product_name,
                current_stock=metrics["current_stock"],
                forecasted_demand_30d=metrics.get("forecasted_demand_30d") or Decimal("0"),
                dir=metrics.get("dir") or Decimal("0"),
                stockout_risk=metrics.get("stockout_risk") or Decimal("0"),
                suggested_quantity=suggested_qty,
                supplier_id=supplier.id,
                supplier_name=supplier.name,
                moq=condition.moq,
                lead_time_days=condition.lead_time_days,
                unit_cost=unit_cost,
                total_cost=total_cost,
                reason=f"Stockout risk: {metrics.get('stockout_risk', 0):.1f}%"
            ))

    return OrderSuggestionsResponse(
        suggestions=suggestions,
        total_suggestions=len(suggestions),
        total_value=total_value
    )


# ============================================================================
# Recommendations API
# ============================================================================

@router.get("/recommendations")
async def get_recommendations(
    type: Optional[str] = Query(None, alias="type"),
    role: Optional[str] = Query(None),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get AI-powered recommendations.

    Types: REORDER, URGENT, REDUCE_ORDER, DEAD_STOCK, PROMOTE
    Role: CEO, PROCUREMENT, MARKETING (filters by role-based rules)
    """
    service = RecommendationsService(db)

    recommendations = await service.get_recommendations(
        client_id=client.client_id,
        recommendation_type=type,
        role=role
    )

    return {"recommendations": recommendations, "total": len(recommendations)}


@router.post("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    recommendation_id: str,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Dismiss a recommendation (don't show again).

    Note: This is a placeholder - in production, you'd store dismissed recommendations
    in a database table.
    """
    # TODO: Store dismissed recommendations in database
    return {"message": "Recommendation dismissed", "recommendation_id": recommendation_id}

