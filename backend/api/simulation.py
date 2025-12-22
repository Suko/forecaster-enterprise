"""
Simulation API Endpoints

Endpoints for running historical simulations to validate system effectiveness.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

from models import get_db
from models.client import Client
from auth.dependencies import get_current_client
from schemas.simulation import SimulationRequest, SimulationResponse
from services.simulation_service import SimulationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["simulation"])


@router.post("/simulation/run", response_model=SimulationResponse, status_code=status.HTTP_201_CREATED)
async def run_simulation(
    request: SimulationRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """
    Run historical simulation to validate system effectiveness.
    
    Simulates the system running over a historical period (e.g., 12 months),
    automatically following system recommendations, and compares outcomes
    against real historical data.
    
    **Authentication:** Requires JWT token (user calls)
    
    **What it does:**
    1. Starts from `start_date` with initial stock levels
    2. For each day until `end_date`:
       - Generates forecast using data up to that day
       - Calculates inventory recommendations
       - Automatically places orders when reorder point is triggered
       - Tracks simulated stock levels
       - Compares with real stock levels
    
    **Returns:**
    - Overall metrics (stockout rate, inventory value, service level)
    - Improvement metrics vs baseline
    - Daily comparisons
    - Item-level results
    
    **Example:**
    ```json
    {
      "client_id": "123e4567-e89b-12d3-a456-426614174000",
      "start_date": "2024-01-01",
      "end_date": "2024-12-22",
      "item_ids": ["SKU001", "SKU002"],
      "simulation_config": {
        "auto_place_orders": true,
        "lead_time_buffer_days": 0,
        "min_order_quantity": 1,
        "service_level": 0.95
      }
    }
    ```
    """
    # Validate client_id matches authenticated client
    if request.client_id != client.client_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client ID in request does not match authenticated client"
        )
    
    # Validate date range
    if request.start_date >= request.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be before end_date"
        )
    
    # Validate date range is reasonable (max 2 years)
    total_days = (request.end_date - request.start_date).days + 1
    if total_days > 730:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation period cannot exceed 2 years (730 days)"
        )
    
    if total_days < 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Simulation period must be at least 30 days"
        )
    
    try:
        service = SimulationService(db)
        result = await service.run_simulation(request)
        
        if result.status == "failed":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Simulation failed: {result.error_message}"
            )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Simulation endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Simulation failed: {str(e)}"
        )

