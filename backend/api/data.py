"""
Data API Routes

Lightweight endpoints for simple data queries.
No forecasting imports to avoid PyTorch initialization overhead.
"""
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date

from models import get_db
from auth.service_auth import get_client_id_from_request_or_token

router = APIRouter(prefix="/api/v1", tags=["data"])


@router.get("/forecast/date-range")
async def get_date_range(
    request_obj: Request,
    item_id: Optional[str] = Query(None, description="Optional item ID to get date range for"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the date range of available historical data.
    
    Lightweight endpoint - no forecasting imports to avoid PyTorch initialization.
    
    Authentication (choose one):
    - JWT token (user calls): client_id from user's JWT token
    - Service API key (system calls): X-API-Key header
    
    Returns min/max dates and total days of data.
    """
    from sqlalchemy import text

    # Get client_id from JWT token OR service API key
    client_id = await get_client_id_from_request_or_token(
        request_obj,
        client_id=None,
        x_api_key=request_obj.headers.get("X-API-Key"),
        db=db,
    )

    # Build query using raw SQL (ts_demand_daily has no SQLAlchemy model)
    if item_id:
        query = text("""
            SELECT
                MIN(date_local) as min_date,
                MAX(date_local) as max_date,
                COUNT(DISTINCT date_local) as total_days
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
        """)
        params = {"client_id": client_id, "item_id": item_id}
    else:
        query = text("""
            SELECT
                MIN(date_local) as min_date,
                MAX(date_local) as max_date,
                COUNT(DISTINCT date_local) as total_days
            FROM ts_demand_daily
            WHERE client_id = :client_id
        """)
        params = {"client_id": client_id}

    result = await db.execute(query, params)
    row = result.one()

    return {
        "min_date": row.min_date.isoformat() if row.min_date else None,
        "max_date": row.max_date.isoformat() if row.max_date else None,
        "total_days": row.total_days or 0,
    }

