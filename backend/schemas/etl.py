"""
ETL Schemas

Pydantic models for ETL API requests and responses.
"""
from typing import Optional, List, Dict, Any
from datetime import date
from pydantic import BaseModel, Field


class SyncSalesHistoryRequest(BaseModel):
    """Request schema for sales history sync"""
    connector_type: str = Field(..., description="Connector type: 'bigquery' or 'sql'")
    connector_config: Dict[str, Any] = Field(..., description="Connector configuration")
    start_date: Optional[date] = Field(None, description="Start date filter")
    end_date: Optional[date] = Field(None, description="End date filter")
    replace: bool = Field(False, description="Replace existing data instead of upserting")


class SyncProductsRequest(BaseModel):
    """Request schema for products sync"""
    connector_type: str = Field(..., description="Connector type: 'bigquery' or 'sql'")
    connector_config: Dict[str, Any] = Field(..., description="Connector configuration")


class SyncStockLevelsRequest(BaseModel):
    """Request schema for stock levels sync"""
    connector_type: str = Field(..., description="Connector type: 'bigquery' or 'sql'")
    connector_config: Dict[str, Any] = Field(..., description="Connector configuration")
    replace: bool = Field(True, description="Replace all stock levels")


class SyncLocationsRequest(BaseModel):
    """Request schema for locations sync"""
    connector_type: str = Field(..., description="Connector type: 'bigquery' or 'sql'")
    connector_config: Dict[str, Any] = Field(..., description="Connector configuration")


class SyncResponse(BaseModel):
    """Response schema for sync operations"""
    success: bool
    rows_fetched: int
    rows_inserted: int
    rows_updated: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    message: Optional[str] = None

