"""
Monitoring API Endpoints

Provides endpoints to view performance metrics and monitoring data.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from core.monitoring import get_monitor
from auth.dependencies import get_current_user, get_current_client
from models.client import Client
from models.database import get_db
from models.product import Product
from models.location import Location
from models.supplier import Supplier
from models.stock import StockLevel
from schemas.monitoring import SystemStatusResponse

router = APIRouter(prefix="/api/v1", tags=["monitoring"])


@router.get("/metrics")
async def get_metrics(
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get performance metrics summary.

    Requires authentication.
    """
    monitor = get_monitor()
    return monitor.get_summary()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint (no auth required).
    """
    return {"status": "healthy"}


@router.get("/system/status", response_model=SystemStatusResponse, tags=["system"])
async def get_system_status(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system initialization status

    Returns status of data tables and basic data quality metrics.
    Requires authentication and client context.
    """
    client_id = client.client_id

    # Check each table for existence of records
    has_products = False
    has_locations = False
    has_suppliers = False
    has_sales_data = False
    has_stock_levels = False

    # Check products
    result = await db.execute(
        select(func.count(Product.id)).where(Product.client_id == client_id)
    )
    has_products = (result.scalar() or 0) > 0

    # Check locations
    result = await db.execute(
        select(func.count(Location.id)).where(Location.client_id == client_id)
    )
    has_locations = (result.scalar() or 0) > 0

    # Check suppliers
    result = await db.execute(
        select(func.count(Supplier.id)).where(Supplier.client_id == client_id)
    )
    has_suppliers = (result.scalar() or 0) > 0

    # Check sales data (ts_demand_daily)
    result = await db.execute(
        text("""
            SELECT COUNT(*) as count
            FROM ts_demand_daily
            WHERE client_id = :client_id
        """),
        {"client_id": str(client_id)}
    )
    has_sales_data = (result.scalar() or 0) > 0

    # Check stock levels
    result = await db.execute(
        select(func.count(StockLevel.id)).where(StockLevel.client_id == client_id)
    )
    has_stock_levels = (result.scalar() or 0) > 0

    # Determine if initialized
    initialized = any([
        has_products,
        has_locations,
        has_suppliers,
        has_sales_data,
        has_stock_levels
    ])

    # Basic data quality metrics
    data_quality = None
    if initialized:
        # Count records per table
        data_quality = {
            "products_count": await db.execute(
                select(func.count(Product.id)).where(Product.client_id == client_id)
            ).scalar() or 0,
            "locations_count": await db.execute(
                select(func.count(Location.id)).where(Location.client_id == client_id)
            ).scalar() or 0,
            "suppliers_count": await db.execute(
                select(func.count(Supplier.id)).where(Supplier.client_id == client_id)
            ).scalar() or 0,
            "sales_records_count": await db.execute(
                text("SELECT COUNT(*) FROM ts_demand_daily WHERE client_id = :client_id"),
                {"client_id": str(client_id)}
            ).scalar() or 0,
            "stock_levels_count": await db.execute(
                select(func.count(StockLevel.id)).where(StockLevel.client_id == client_id)
            ).scalar() or 0
        }

    # Setup instructions
    setup_instructions = None
    if not initialized:
        setup_instructions = "No data found. Set up ETL sync to connect your data source."
    elif not has_sales_data:
        setup_instructions = "No sales data found. Configure ETL sync to import sales history."
    elif not has_products:
        setup_instructions = "No products found. Configure ETL sync to import your product catalog."

    return SystemStatusResponse(
        initialized=initialized,
        has_products=has_products,
        has_locations=has_locations,
        has_suppliers=has_suppliers,
        has_sales_data=has_sales_data,
        has_stock_levels=has_stock_levels,
        setup_instructions=setup_instructions,
        data_quality=data_quality
    )

