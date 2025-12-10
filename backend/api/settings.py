"""
Settings API Routes

API endpoints for client settings and configuration.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from models.database import get_db
from models.client import Client
from models.settings import ClientSettings
from auth.dependencies import get_current_client
from schemas.settings import (
    ClientSettingsResponse,
    ClientSettingsUpdate,
    RecommendationRulesUpdate,
)
from sqlalchemy import select

router = APIRouter(prefix="/api/v1", tags=["settings"])


@router.get("/settings", response_model=ClientSettingsResponse)
async def get_settings(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get client settings"""
    result = await db.execute(
        select(ClientSettings).where(ClientSettings.client_id == client.client_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Return default settings
        return ClientSettingsResponse(
            client_id=client.client_id,
            safety_buffer_days=7,
            understocked_threshold=14,
            overstocked_threshold=90,
            dead_stock_days=90,
            recommendation_rules={
                "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
                "role_rules": {
                    "CEO": ["URGENT", "DEAD_STOCK"],
                    "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
                    "MARKETING": ["PROMOTE", "DEAD_STOCK"]
                },
                "min_inventory_value": 0,
                "min_risk_score": 0
            }
        )
    
    return ClientSettingsResponse(
        client_id=settings.client_id,
        safety_buffer_days=settings.safety_buffer_days,
        understocked_threshold=settings.understocked_threshold,
        overstocked_threshold=settings.overstocked_threshold,
        dead_stock_days=settings.dead_stock_days,
        recommendation_rules=settings.recommendation_rules or {}
    )


@router.put("/settings", response_model=ClientSettingsResponse)
async def update_settings(
    data: ClientSettingsUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update client settings"""
    result = await db.execute(
        select(ClientSettings).where(ClientSettings.client_id == client.client_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings
        settings = ClientSettings(
            client_id=client.client_id,
            safety_buffer_days=data.safety_buffer_days or 7,
            understocked_threshold=data.understocked_threshold or 14,
            overstocked_threshold=data.overstocked_threshold or 90,
            dead_stock_days=data.dead_stock_days or 90
        )
        db.add(settings)
    else:
        # Update existing settings
        if data.safety_buffer_days is not None:
            settings.safety_buffer_days = data.safety_buffer_days
        if data.understocked_threshold is not None:
            settings.understocked_threshold = data.understocked_threshold
        if data.overstocked_threshold is not None:
            settings.overstocked_threshold = data.overstocked_threshold
        if data.dead_stock_days is not None:
            settings.dead_stock_days = data.dead_stock_days
    
    await db.commit()
    await db.refresh(settings)
    
    return ClientSettingsResponse(
        client_id=settings.client_id,
        safety_buffer_days=settings.safety_buffer_days,
        understocked_threshold=settings.understocked_threshold,
        overstocked_threshold=settings.overstocked_threshold,
        dead_stock_days=settings.dead_stock_days,
        recommendation_rules=settings.recommendation_rules or {}
    )


@router.get("/settings/recommendation-rules", response_model=dict)
async def get_recommendation_rules(
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Get recommendation rules"""
    result = await db.execute(
        select(ClientSettings).where(ClientSettings.client_id == client.client_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.recommendation_rules:
        return {
            "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
            "role_rules": {
                "CEO": ["URGENT", "DEAD_STOCK"],
                "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
                "MARKETING": ["PROMOTE", "DEAD_STOCK"]
            },
            "min_inventory_value": 0,
            "min_risk_score": 0
        }
    
    return settings.recommendation_rules


@router.put("/settings/recommendation-rules", response_model=dict)
async def update_recommendation_rules(
    data: RecommendationRulesUpdate,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db),
):
    """Update recommendation rules"""
    result = await db.execute(
        select(ClientSettings).where(ClientSettings.client_id == client.client_id)
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings with default values
        default_rules = {
            "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
            "role_rules": {
                "CEO": ["URGENT", "DEAD_STOCK"],
                "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
                "MARKETING": ["PROMOTE", "DEAD_STOCK"]
            },
            "min_inventory_value": 0,
            "min_risk_score": 0
        }
        settings = ClientSettings(
            client_id=client.client_id,
            recommendation_rules=default_rules
        )
        db.add(settings)
    else:
        # Update existing rules
        if not settings.recommendation_rules:
            settings.recommendation_rules = {}
        
        if data.enabled_types is not None:
            settings.recommendation_rules["enabled_types"] = data.enabled_types
        if data.role_rules is not None:
            settings.recommendation_rules["role_rules"] = data.role_rules
        if data.min_inventory_value is not None:
            settings.recommendation_rules["min_inventory_value"] = data.min_inventory_value
        if data.min_risk_score is not None:
            settings.recommendation_rules["min_risk_score"] = data.min_risk_score
    
    await db.commit()
    await db.refresh(settings)
    
    return settings.recommendation_rules or {}

