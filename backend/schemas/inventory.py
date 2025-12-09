"""
Inventory Schemas

Pydantic models for inventory management API requests and responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import date
from uuid import UUID


# ============================================================================
# Product Schemas
# ============================================================================

class ProductBase(BaseModel):
    """Base product schema"""
    item_id: str = Field(..., description="Product identifier (matches forecasting engine)")
    sku: Optional[str] = Field(None, description="Optional SKU alias")
    product_name: str
    category: str = "Uncategorized"
    unit_cost: Decimal = Decimal("0.00")


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    product_name: Optional[str] = None
    category: Optional[str] = None
    unit_cost: Optional[Decimal] = None
    sku: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: UUID
    client_id: UUID
    created_at: date
    updated_at: date
    
    class Config:
        from_attributes = True


class ProductMetrics(BaseModel):
    """Product metrics (DIR, risk, etc.)"""
    item_id: str
    current_stock: int
    dir: Optional[Decimal] = None  # Days of Inventory Remaining
    stockout_risk: Optional[Decimal] = None  # Risk score 0-100
    forecasted_demand_30d: Optional[Decimal] = None
    inventory_value: Optional[Decimal] = None
    status: Optional[str] = None  # understocked, overstocked, normal


class ProductDetailResponse(ProductResponse):
    """Detailed product response with metrics"""
    metrics: Optional[ProductMetrics] = None


# ============================================================================
# Product List & Filtering
# ============================================================================

class ProductFilters(BaseModel):
    """Product list filters"""
    search: Optional[str] = None
    category: Optional[str] = None
    supplier_id: Optional[UUID] = None
    location_id: Optional[str] = None
    status: Optional[str] = None  # understocked, overstocked, normal
    min_dir: Optional[Decimal] = None
    max_dir: Optional[Decimal] = None
    min_risk: Optional[Decimal] = None
    max_risk: Optional[Decimal] = None
    min_stock: Optional[int] = None
    max_stock: Optional[int] = None


class ProductListResponse(BaseModel):
    """Paginated product list response"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Dashboard Schemas
# ============================================================================

class DashboardMetrics(BaseModel):
    """Dashboard KPIs"""
    total_skus: int
    total_inventory_value: Decimal
    understocked_count: int
    overstocked_count: int
    average_dir: Decimal
    understocked_value: Decimal
    overstocked_value: Decimal


class TopProduct(BaseModel):
    """Top product item for dashboard"""
    item_id: str
    product_name: str
    current_stock: int
    dir: Decimal
    stockout_risk: Decimal
    inventory_value: Decimal


class DashboardResponse(BaseModel):
    """Dashboard response"""
    metrics: DashboardMetrics
    top_understocked: List[TopProduct]
    top_overstocked: List[TopProduct]


# ============================================================================
# Product-Supplier Schemas
# ============================================================================

class ProductSupplierBase(BaseModel):
    """Base product-supplier condition schema"""
    moq: int = Field(..., ge=0, description="Minimum Order Quantity")
    lead_time_days: int = Field(..., ge=0, description="Lead time in days")
    supplier_cost: Optional[Decimal] = None
    packaging_unit: Optional[str] = None
    packaging_qty: Optional[int] = None
    is_primary: bool = False
    notes: Optional[str] = None


class ProductSupplierCreate(ProductSupplierBase):
    """Schema for creating product-supplier condition"""
    supplier_id: UUID


class ProductSupplierUpdate(BaseModel):
    """Schema for updating product-supplier condition"""
    moq: Optional[int] = Field(None, ge=0)
    lead_time_days: Optional[int] = Field(None, ge=0)
    supplier_cost: Optional[Decimal] = None
    packaging_unit: Optional[str] = None
    packaging_qty: Optional[int] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None


class SupplierInfo(BaseModel):
    """Supplier information"""
    id: UUID
    name: str
    contact_email: Optional[str] = None
    
    class Config:
        from_attributes = True


class ProductSupplierResponse(ProductSupplierBase):
    """Product-supplier condition response"""
    id: UUID
    item_id: str
    supplier_id: UUID
    supplier: SupplierInfo
    created_at: date
    updated_at: date
    
    class Config:
        from_attributes = True

