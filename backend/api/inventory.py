"""
Inventory API Routes

API endpoints for inventory management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID
from decimal import Decimal

from models.database import get_db
from models.client import Client
from auth.dependencies import get_current_client
from services.inventory_service import InventoryService
from services.dashboard_service import DashboardService
from services.dashboard_service import DashboardService
from schemas.inventory import (
    ProductListResponse,
    ProductDetailResponse,
    ProductMetrics,
    ProductFilters,
    ProductSupplierResponse,
    ProductSupplierCreate,
    ProductSupplierUpdate,
    DashboardResponse,
)

router = APIRouter(prefix="/api/v1", tags=["inventory"])


@router.get("/products", response_model=ProductListResponse)
async def get_products(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
    category: Optional[str] = None,
    supplier_id: Optional[UUID] = None,
    location_id: Optional[str] = None,
    status: Optional[str] = None,
    min_dir: Optional[float] = None,
    max_dir: Optional[float] = None,
    min_risk: Optional[float] = None,
    max_risk: Optional[float] = None,
    min_stock: Optional[int] = None,
    max_stock: Optional[int] = None,
    sort: Optional[str] = None,
    order: str = Query("asc", pattern="^(asc|desc)$"),
):
    """
    Get paginated list of products with filtering and sorting.
    
    Supports data table requirements:
    - Filterable columns (text, numeric, categorical)
    - Sortable columns
    - Pagination
    """
    service = InventoryService(db)
    
    # Build filters
    filters = ProductFilters(
        search=search,
        category=category,
        supplier_id=supplier_id,
        location_id=location_id,
        status=status,
        min_dir=Decimal(str(min_dir)) if min_dir else None,
        max_dir=Decimal(str(max_dir)) if max_dir else None,
        min_risk=Decimal(str(min_risk)) if min_risk else None,
        max_risk=Decimal(str(max_risk)) if max_risk else None,
        min_stock=min_stock,
        max_stock=max_stock,
    )
    
    result = await service.get_products(
        client_id=client.client_id,
        filters=filters,
        page=page,
        page_size=page_size,
        sort=sort,
        order=order
    )
    
    return ProductListResponse(**result)


@router.get("/products/{item_id}", response_model=ProductDetailResponse)
async def get_product(
    item_id: str,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get product details by item_id.
    
    Includes product information and computed metrics (DIR, risk, etc.).
    """
    service = InventoryService(db)
    
    product = await service.get_product(client.client_id, item_id)
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Product with item_id {item_id} not found")
    
    return product


@router.get("/products/{item_id}/metrics", response_model=ProductMetrics)
async def get_product_metrics(
    item_id: str,
    location_id: Optional[str] = None,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get product metrics (DIR, stockout risk, forecasted demand, inventory value).
    
    Computed on-the-fly or from inventory_metrics table.
    """
    service = InventoryService(db)
    
    metrics = await service.get_product_metrics(
        client_id=client.client_id,
        item_id=item_id,
        location_id=location_id
    )
    
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail=f"Metrics not found for product {item_id}"
        )
    
    return metrics


@router.get("/products/{item_id}/suppliers", response_model=list[ProductSupplierResponse])
async def get_product_suppliers(
    item_id: str,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all suppliers for a product with conditions (MOQ, lead time, etc.).
    """
    service = InventoryService(db)
    
    conditions = await service.get_product_suppliers(client.client_id, item_id)
    
    # Convert to response format (need to load supplier info)
    from sqlalchemy import select
    from models.supplier import Supplier
    from schemas.inventory import SupplierInfo
    
    result_list = []
    for condition in conditions:
        # Get supplier info
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == condition.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        
        # Build response
        supplier_info = SupplierInfo.model_validate(supplier)
        
        # Build response dict with supplier info
        response_dict = {
            "id": condition.id,
            "client_id": condition.client_id,
            "item_id": condition.item_id,
            "supplier_id": condition.supplier_id,
            "supplier": supplier_info,
            "moq": condition.moq,
            "lead_time_days": condition.lead_time_days,
            "supplier_cost": condition.supplier_cost,
            "packaging_unit": condition.packaging_unit,
            "packaging_qty": condition.packaging_qty,
            "is_primary": condition.is_primary,
            "notes": condition.notes,
            "created_at": condition.created_at,
            "updated_at": condition.updated_at,
        }
        response = ProductSupplierResponse.model_validate(response_dict)
        
        result_list.append(response)
    
    return result_list


@router.post("/products/{item_id}/suppliers", response_model=ProductSupplierResponse)
async def add_product_supplier(
    item_id: str,
    data: ProductSupplierCreate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Link product to supplier with conditions (MOQ, lead time, packaging).
    """
    service = InventoryService(db)
    
    try:
        condition = await service.add_product_supplier(
            client_id=client.client_id,
            item_id=item_id,
            supplier_id=data.supplier_id,
            moq=data.moq,
            lead_time_days=data.lead_time_days,
            supplier_cost=data.supplier_cost,
            packaging_unit=data.packaging_unit,
            packaging_qty=data.packaging_qty,
            is_primary=data.is_primary,
            notes=data.notes
        )
        
        # Refresh to get updated timestamps
        await db.refresh(condition)
        
        # Get supplier info for response
        from sqlalchemy import select
        from models.supplier import Supplier
        from schemas.inventory import SupplierInfo
        
        supplier_result = await db.execute(
            select(Supplier).where(Supplier.id == condition.supplier_id)
        )
        supplier = supplier_result.scalar_one()
        supplier_info = SupplierInfo.model_validate(supplier)
        
        # Build response with supplier info
        response_dict = {
            "id": condition.id,
            "client_id": condition.client_id,
            "item_id": condition.item_id,
            "supplier_id": condition.supplier_id,
            "supplier": supplier_info,
            "moq": condition.moq,
            "lead_time_days": condition.lead_time_days,
            "supplier_cost": condition.supplier_cost,
            "packaging_unit": condition.packaging_unit,
            "packaging_qty": condition.packaging_qty,
            "is_primary": condition.is_primary,
            "notes": condition.notes,
            "created_at": condition.created_at,
            "updated_at": condition.updated_at,
        }
        response = ProductSupplierResponse.model_validate(response_dict)
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/products/{item_id}/suppliers/{supplier_id}", response_model=ProductSupplierResponse)
async def update_product_supplier(
    item_id: str,
    supplier_id: UUID,
    data: ProductSupplierUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Update product-supplier conditions (MOQ, lead time, packaging).
    """
    service = InventoryService(db)
    
    condition = await service.update_product_supplier(
        client_id=client.client_id,
        item_id=item_id,
        supplier_id=supplier_id,
        moq=data.moq,
        lead_time_days=data.lead_time_days,
        supplier_cost=data.supplier_cost,
        packaging_unit=data.packaging_unit,
        packaging_qty=data.packaging_qty,
        is_primary=data.is_primary,
        notes=data.notes
    )
    
    if not condition:
        raise HTTPException(
            status_code=404,
            detail=f"Product-supplier condition not found"
        )
    
    # Get supplier info for response
    from sqlalchemy import select
    from models.supplier import Supplier
    from schemas.inventory import SupplierInfo
    
    supplier_result = await db.execute(
        select(Supplier).where(Supplier.id == condition.supplier_id)
    )
    supplier = supplier_result.scalar_one()
    supplier_info = SupplierInfo.model_validate(supplier)
    
    response = ProductSupplierResponse.model_validate(condition)
    response.supplier = supplier_info
    
    return response


@router.delete("/products/{item_id}/suppliers/{supplier_id}")
async def remove_product_supplier(
    item_id: str,
    supplier_id: UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove product-supplier link.
    """
    service = InventoryService(db)
    
    success = await service.remove_product_supplier(
        client_id=client.client_id,
        item_id=item_id,
        supplier_id=supplier_id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Product-supplier condition not found"
        )
    
    return {"message": "Product-supplier condition removed successfully"}


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Get dashboard data:
    - Overall metrics (total SKUs, inventory value, understocked/overstocked counts)
    - Top understocked products (by risk and value)
    - Top overstocked products (by value)
    """
    service = DashboardService(db)
    
    dashboard_data = await service.get_dashboard_data(client.client_id)
    
    return dashboard_data
