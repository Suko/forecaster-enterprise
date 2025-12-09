"""
Settings Schemas

Pydantic models for client settings and configuration.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from uuid import UUID


class ClientSettingsResponse(BaseModel):
    """Client settings response"""
    client_id: UUID
    safety_buffer_days: int
    understocked_threshold: int
    overstocked_threshold: int
    dead_stock_days: int
    recommendation_rules: Dict
    
    class Config:
        from_attributes = True


class ClientSettingsUpdate(BaseModel):
    """Schema for updating client settings"""
    safety_buffer_days: Optional[int] = Field(None, ge=0)
    understocked_threshold: Optional[int] = Field(None, ge=0)
    overstocked_threshold: Optional[int] = Field(None, ge=0)
    dead_stock_days: Optional[int] = Field(None, ge=0)


class RecommendationRulesUpdate(BaseModel):
    """Schema for updating recommendation rules"""
    enabled_types: Optional[List[str]] = None
    role_rules: Optional[Dict[str, List[str]]] = None
    min_inventory_value: Optional[float] = None
    min_risk_score: Optional[float] = None

