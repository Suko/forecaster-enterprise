"""
Monitoring API Endpoints

Provides endpoints to view performance metrics and monitoring data.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from core.monitoring import get_monitor
from auth.dependencies import get_current_user

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


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

