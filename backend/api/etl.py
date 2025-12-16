"""
ETL API Routes

Endpoints for data synchronization from external sources.
"""
from typing import Optional
from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.dependencies import get_current_client
from models.client import Client
from models.database import get_db
from schemas.etl import (
    SyncSalesHistoryRequest,
    SyncProductsRequest,
    SyncStockLevelsRequest,
    SyncLocationsRequest,
    SyncResponse
)
from schemas.monitoring import ValidationRequest, ValidationReport
from services.etl import ETLService
from services.etl.connectors import BigQueryConnector, SQLConnector, ETLConnector
from services.data_validation_service import DataValidationService


router = APIRouter(prefix="/api/v1/etl", tags=["ETL"])


def get_connector(connector_type: str, config: dict) -> ETLConnector:
    """Factory function to create connector instance"""
    if connector_type == "bigquery":
        return BigQueryConnector(
            project_id=config.get("project_id"),
            credentials_path=config.get("credentials_path")
        )
    elif connector_type == "sql":
        return SQLConnector(
            connection_string=config.get("connection_string"),
            driver=config.get("driver", "postgresql")
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported connector type: {connector_type}"
        )


@router.post("/sync/sales-history", response_model=SyncResponse)
async def sync_sales_history(
    request: SyncSalesHistoryRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync sales history from external source to ts_demand_daily table

    Requires authentication and client context.
    """
    try:
        connector = get_connector(request.connector_type, request.connector_config)
        service = ETLService(db)

        result = await service.sync_sales_history(
            client_id=client.client_id,
            connector=connector,
            start_date=request.start_date,
            end_date=request.end_date,
            replace=request.replace
        )

        return SyncResponse(
            success=result["success"],
            rows_fetched=result["rows_fetched"],
            rows_inserted=result["rows_inserted"],
            rows_updated=result["rows_updated"],
            errors=result.get("errors", []),
            message=f"Synced {result['rows_inserted']} rows from external source"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/products", response_model=SyncResponse)
async def sync_products(
    request: SyncProductsRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync products from external source

    Requires authentication and client context.
    """
    try:
        connector = get_connector(request.connector_type, request.connector_config)
        service = ETLService(db)

        result = await service.sync_products(
            client_id=client.client_id,
            connector=connector
        )

        return SyncResponse(
            success=result["success"],
            rows_fetched=result["rows_fetched"],
            rows_inserted=result["rows_inserted"],
            rows_updated=result["rows_updated"],
            errors=result.get("errors", []),
            message=f"Synced {result['rows_inserted']} new products, updated {result['rows_updated']} existing"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/stock-levels", response_model=SyncResponse)
async def sync_stock_levels(
    request: SyncStockLevelsRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync stock levels from external source

    Requires authentication and client context.
    """
    try:
        connector = get_connector(request.connector_type, request.connector_config)
        service = ETLService(db)

        result = await service.sync_stock_levels(
            client_id=client.client_id,
            connector=connector,
            replace=request.replace
        )

        return SyncResponse(
            success=result["success"],
            rows_fetched=result["rows_fetched"],
            rows_inserted=result["rows_inserted"],
            rows_updated=result["rows_updated"],
            errors=result.get("errors", []),
            message=f"Synced {result['rows_inserted']} stock levels"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/sync/locations", response_model=SyncResponse)
async def sync_locations(
    request: SyncLocationsRequest,
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Sync locations from external source

    Requires authentication and client context.
    Preserves app-managed locations (is_synced = false).
    """
    try:
        connector = get_connector(request.connector_type, request.connector_config)
        service = ETLService(db)

        result = await service.sync_locations(
            client_id=client.client_id,
            connector=connector
        )

        return SyncResponse(
            success=result["success"],
            rows_fetched=result["rows_fetched"],
            rows_inserted=result["rows_inserted"],
            rows_updated=result["rows_updated"],
            errors=result.get("errors", []),
            message=f"Synced {result['rows_inserted']} new locations, updated {result['rows_updated']} existing"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}"
        )


@router.post("/validate", response_model=ValidationReport)
async def validate_data(
    request: ValidationRequest = ValidationRequest(),
    client: Client = Depends(get_current_client),
    db: AsyncSession = Depends(get_db)
):
    """
    Validate data quality, completeness, and computed metrics

    Requires authentication and client context.
    Returns comprehensive validation report.
    """
    try:
        service = DataValidationService(db)
        report = await service.validate_all(
            client_id=client.client_id,
            include_computed_metrics=request.include_computed_metrics,
            include_frontend_consistency=request.include_frontend_consistency
        )
        return ValidationReport(**report)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )
