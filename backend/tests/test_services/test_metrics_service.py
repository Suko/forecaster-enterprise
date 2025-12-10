"""
Unit tests for MetricsService

Tests DIR calculation, stockout risk, status determination, etc.
"""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from uuid import UUID

from services.metrics_service import MetricsService
from models.settings import ClientSettings
from models.product import Product
from models.stock import StockLevel
from models.product_supplier import ProductSupplierCondition
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_stock_level,
    create_test_product_supplier_condition,
    create_test_client_settings
)


@pytest.mark.asyncio
async def test_calculate_dir_with_forecast(db_session, test_client_obj):
    """Test DIR calculation with forecasted demand"""
    service = MetricsService(db_session)
    
    # Create test data
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=100
    )
    db_session.add_all([product, stock])
    await db_session.commit()
    
    # Calculate DIR with forecasted demand
    forecasted_demand_30d = Decimal("10.0")  # 10 units total over 30 days
    dir_value = await service.calculate_dir(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=100,
        forecasted_demand_30d=forecasted_demand_30d
    )
    
    # DIR = (current_stock / forecasted_demand_30d) * 30
    # 100 / 10 * 30 = 300 days
    assert dir_value == Decimal("300.0")


@pytest.mark.asyncio
async def test_calculate_dir_zero_demand(db_session, test_client_obj):
    """Test DIR calculation with zero demand (should return high value)"""
    service = MetricsService(db_session)
    
    # Zero demand should result in very high DIR
    dir_value = await service.calculate_dir(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        current_stock=100,
        forecasted_demand_30d=Decimal("0")
    )
    
    # Should handle zero demand gracefully (return high value or None)
    assert dir_value is None or dir_value > Decimal("1000")


@pytest.mark.asyncio
async def test_calculate_stockout_risk(db_session, test_client_obj):
    """Test stockout risk calculation"""
    service = MetricsService(db_session)
    
    # Create settings
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add(settings)
    
    # Create product-supplier condition with lead time
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    from models.supplier import Supplier
    import uuid
    supplier = Supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        lead_time_days=14
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Calculate risk with low DIR (5 days) vs lead time (14) + buffer (7) = 21 days needed
    risk = await service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        dir_value=Decimal("5.0")
    )
    
    # DIR (5) < lead_time (14) + buffer (7) = 21, so high risk
    assert risk > Decimal("0.5")  # High risk


@pytest.mark.asyncio
async def test_determine_status_understocked(db_session, test_client_obj):
    """Test status determination for understocked product"""
    service = MetricsService(db_session)
    
    # Create settings
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        understocked_threshold=14
    )
    db_session.add(settings)
    await db_session.commit()
    
    # DIR below threshold = understocked
    status = await service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        dir_value=Decimal("10.0")  # Below 14 day threshold
    )
    
    assert status == "understocked"


@pytest.mark.asyncio
async def test_determine_status_overstocked(db_session, test_client_obj):
    """Test status determination for overstocked product"""
    service = MetricsService(db_session)
    
    # Create settings
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        overstocked_threshold=90
    )
    db_session.add(settings)
    await db_session.commit()
    
    # DIR above threshold = overstocked
    status = await service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        dir_value=Decimal("100.0")  # Above 90 day threshold
    )
    
    assert status == "overstocked"


@pytest.mark.asyncio
async def test_determine_status_normal(db_session, test_client_obj):
    """Test status determination for normal stock level"""
    service = MetricsService(db_session)
    
    # Create settings
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        understocked_threshold=14,
        overstocked_threshold=90
    )
    db_session.add(settings)
    await db_session.commit()
    
    # DIR between thresholds = normal
    status = await service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        dir_value=Decimal("30.0")  # Between 14 and 90
    )
    
    assert status == "normal"


@pytest.mark.asyncio
async def test_calculate_inventory_value(db_session, test_client_obj):
    """Test inventory value calculation"""
    service = MetricsService(db_session)
    
    # Create product with cost
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        unit_cost=Decimal("10.00")
    )
    db_session.add(product)
    await db_session.commit()
    
    # Calculate value: stock (100) * cost (10) = 1000
    value = await service.calculate_inventory_value(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=100
    )
    
    assert value == Decimal("1000.00")


@pytest.mark.asyncio
async def test_compute_product_metrics(db_session, test_client_obj, populate_test_data):
    """Test full product metrics computation"""
    service = MetricsService(db_session)
    
    # Create product and stock
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        unit_cost=Decimal("10.00")
    )
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=100
    )
    db_session.add_all([product, stock])
    await db_session.commit()
    
    # Compute all metrics
    metrics = await service.compute_product_metrics(
        client_id=test_client_obj.client_id,
        item_id=product.item_id
    )
    
    assert metrics is not None
    assert "dir" in metrics
    assert "stockout_risk" in metrics
    assert "status" in metrics
    assert "inventory_value" in metrics
    assert metrics["inventory_value"] == Decimal("1000.00")

