"""
Suppliers API Routes

API endpoints for supplier views.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from models.database import get_db
from models.client import Client
from auth.dependencies import get_current_client
from services.supplier_service import SupplierService
from schemas.supplier import SupplierListResponse, SupplierResponse


router = APIRouter(prefix="/api/v1", tags=["suppliers"])


@router.get("/suppliers", response_model=SupplierListResponse)
async def get_suppliers(
    search: Optional[str] = None,
    supplier_type: Optional[str] = Query(None, description="PO | WO"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of suppliers"""
    service = SupplierService(db)
    result = await service.get_suppliers(
        client_id=client.client_id,
        search=search,
        supplier_type=supplier_type,
        page=page,
        page_size=page_size,
    )
    return SupplierListResponse(**result)


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
async def get_supplier(
    supplier_id: UUID,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get supplier detail"""
    service = SupplierService(db)
    supplier = await service.get_supplier(client.client_id, supplier_id)
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return SupplierResponse.model_validate(supplier)

