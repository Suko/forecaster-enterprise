"""
Order Planning Schemas

Pydantic models for order planning and purchase orders.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from uuid import UUID


# ============================================================================
# Cart Schemas
# ============================================================================

class CartItemBase(BaseModel):
    """Base cart item schema"""
    item_id: str = Field(..., description="Product identifier (matches forecasting engine)")
    supplier_id: UUID
    quantity: int = Field(..., ge=1)
    notes: Optional[str] = None


class CartItemCreate(CartItemBase):
    """Schema for adding item to cart"""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item"""
    quantity: Optional[int] = Field(None, ge=1)
    notes: Optional[str] = None


class CartItemResponse(CartItemBase):
    """Schema for cart item response"""
    id: UUID
    session_id: str
    unit_cost: Decimal
    total_price: Decimal
    packaging_unit: Optional[str] = None
    packaging_qty: Optional[int] = None
    product_name: str
    supplier_name: str
    moq: int = Field(0, description="Minimum Order Quantity for this product-supplier combination")
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    """Cart response with items grouped by supplier"""
    items: List[CartItemResponse]
    total_items: int
    total_value: Decimal
    suppliers: List[dict]  # List of suppliers with their items


# ============================================================================
# Purchase Order Schemas
# ============================================================================

class PurchaseOrderItemCreate(BaseModel):
    """Schema for purchase order item"""
    item_id: str = Field(..., description="Product identifier (matches forecasting engine)")
    quantity: int = Field(..., ge=1)
    unit_cost: Decimal
    packaging_unit: Optional[str] = None
    packaging_qty: Optional[int] = None


class PurchaseOrderCreate(BaseModel):
    """Schema for creating purchase order"""
    supplier_id: UUID
    items: List[PurchaseOrderItemCreate] = Field(..., min_length=1)
    shipping_method: Optional[str] = None
    shipping_unit: Optional[str] = None
    notes: Optional[str] = None
    expected_delivery_date: Optional[date] = None


class PurchaseOrderItemResponse(BaseModel):
    """Purchase order item response"""
    id: UUID
    item_id: str
    product_name: str
    quantity: int
    unit_cost: Decimal
    total_price: Decimal
    packaging_unit: Optional[str] = None
    packaging_qty: Optional[int] = None

    class Config:
        from_attributes = True


class PurchaseOrderResponse(BaseModel):
    """Purchase order response"""
    id: UUID
    po_number: str
    supplier_id: UUID
    supplier_name: str
    status: str
    order_date: date
    expected_delivery_date: Optional[date] = None
    total_amount: Decimal
    shipping_method: Optional[str] = None
    shipping_unit: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[str] = None
    items: List[PurchaseOrderItemResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PurchaseOrderStatusUpdate(BaseModel):
    """Schema for updating purchase order status"""
    status: str = Field(..., pattern="^(pending|confirmed|shipped|received|cancelled)$")


# ============================================================================
# Order Suggestions Schemas
# ============================================================================

class OrderSuggestion(BaseModel):
    """Order suggestion for a product"""
    item_id: str
    product_name: str
    current_stock: int
    forecasted_demand_30d: Decimal
    dir: Decimal
    stockout_risk: Decimal
    suggested_quantity: int
    supplier_id: UUID
    supplier_name: str
    moq: int
    lead_time_days: int
    unit_cost: Decimal
    total_cost: Decimal
    reason: str  # Why this suggestion (e.g., "Stockout risk > 70%")


class OrderSuggestionsResponse(BaseModel):
    """Order suggestions response"""
    suggestions: List[OrderSuggestion]
    total_suggestions: int
    total_value: Decimal

