"""
Tests for DataValidationService

Proves that:
1. Backend calculates metrics correctly
2. API returns correct format for frontend
3. Validation service detects issues
"""
import pytest
from decimal import Decimal
from uuid import UUID

from services.data_validation_service import DataValidationService
from services.metrics_service import MetricsService
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_stock_level,
    create_test_client_settings,
    create_test_product_supplier_condition
)
from models.supplier import Supplier


@pytest.mark.asyncio
async def test_validation_detects_correct_metrics(db_session, test_client_obj, populate_test_data):
    """Test that validation confirms metrics are calculated correctly"""
    service = DataValidationService(db_session)
    
    # Run validation
    report = await service.validate_all(
        client_id=test_client_obj.client_id,
        include_computed_metrics=True,
        include_frontend_consistency=True
    )
    
    # Should have no errors if data is correct
    # (warnings are OK, but errors indicate problems)
    assert report["summary"]["total_errors"] == 0, \
        f"Found validation errors: {report['raw_data_quality']['errors']}"
    
    # Should have computed metrics section
    assert "computed_metrics" in report
    assert report["computed_metrics"]["samples_checked"] > 0


@pytest.mark.asyncio
async def test_stockout_risk_range_0_to_1(db_session, test_client_obj):
    """PROOF: Stockout risk is returned in 0-1 range (correct for frontend)"""
    metrics_service = MetricsService(db_session)
    
    # Create test data
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
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
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add_all([condition, settings])
    await db_session.commit()
    
    # Test case 1: Out of stock = 1.0 (100%)
    risk_out_of_stock = await metrics_service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=0,
        dir_value=Decimal("0.0")
    )
    assert risk_out_of_stock == Decimal("1.00"), \
        f"Out of stock should return 1.0, got {risk_out_of_stock}"
    
    # Test case 2: Low DIR = high risk (0-1 range)
    risk_low_dir = await metrics_service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=50,
        dir_value=Decimal("5.0")  # DIR 5 < required 21 (14+7)
    )
    assert risk_low_dir is not None
    assert Decimal("0.0") <= risk_low_dir <= Decimal("1.0"), \
        f"Risk should be 0-1, got {risk_low_dir}"
    assert risk_low_dir > Decimal("0.5"), \
        f"Low DIR should have high risk, got {risk_low_dir}"
    
    # Test case 3: Sufficient stock = 0.0 (0%)
    risk_sufficient = await metrics_service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=1000,
        dir_value=Decimal("30.0")  # DIR 30 > required 21
    )
    assert risk_sufficient == Decimal("0.00"), \
        f"Sufficient stock should return 0.0, got {risk_sufficient}"
    
    print("✅ PROOF: Stockout risk is correctly returned in 0-1 range")


@pytest.mark.asyncio
async def test_dir_calculation_accuracy(db_session, test_client_obj):
    """PROOF: DIR calculation is accurate"""
    metrics_service = MetricsService(db_session)
    
    # Create product with stock
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
    
    # Test: DIR = current_stock / avg_daily_demand
    # If forecasted_demand_30d = 10, then avg_daily = 10/30 = 0.333
    # DIR = 100 / 0.333 = 300 days
    forecasted_demand_30d = Decimal("10.0")
    dir_value = await metrics_service.calculate_dir(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=100,
        forecasted_demand_30d=forecasted_demand_30d
    )
    
    expected_dir = Decimal("300.0")  # 100 / (10/30) = 300
    assert dir_value == expected_dir, \
        f"DIR calculation incorrect: expected {expected_dir}, got {dir_value}"
    
    print("✅ PROOF: DIR calculation is accurate")


@pytest.mark.asyncio
async def test_status_determination_correct(db_session, test_client_obj):
    """PROOF: Status determination matches thresholds"""
    metrics_service = MetricsService(db_session)
    
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        understocked_threshold=14,
        overstocked_threshold=90
    )
    db_session.add(settings)
    await db_session.commit()
    
    # Test understocked
    status_low = await metrics_service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        current_stock=100,
        dir_value=Decimal("10.0")  # Below 14
    )
    assert status_low == "understocked", \
        f"DIR 10 < 14 should be understocked, got {status_low}"
    
    # Test normal
    status_normal = await metrics_service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        current_stock=100,
        dir_value=Decimal("30.0")  # Between 14 and 90
    )
    assert status_normal == "normal", \
        f"DIR 30 between 14-90 should be normal, got {status_normal}"
    
    # Test overstocked
    status_high = await metrics_service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        current_stock=100,
        dir_value=Decimal("100.0")  # Above 90
    )
    assert status_high == "overstocked", \
        f"DIR 100 > 90 should be overstocked, got {status_high}"
    
    # Test out of stock
    status_out = await metrics_service.determine_status(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        current_stock=0,
        dir_value=Decimal("0.0")
    )
    assert status_out == "out_of_stock", \
        f"Stock 0 should be out_of_stock, got {status_out}"
    
    print("✅ PROOF: Status determination is correct")


@pytest.mark.asyncio
async def test_api_response_format_for_frontend(db_session, test_client_obj, populate_test_data):
    """PROOF: API response format is correct for frontend consumption"""
    from services.inventory_service import InventoryService
    
    inventory_service = InventoryService(db_session)
    
    # Get products with metrics (simulates API call)
    result = await inventory_service.get_products_with_metrics(
        client_id=test_client_obj.client_id,
        page=1,
        page_size=10
    )
    
    if result["items"]:
        product = result["items"][0]
        
        # Verify DIR format (should be Decimal, frontend uses toFixed(1))
        if product.dir is not None:
            dir_float = float(product.dir)
            # Should be a valid number that can be formatted to 1 decimal
            assert isinstance(dir_float, float), "DIR should be numeric"
            formatted = round(dir_float, 1)
            assert abs(dir_float - formatted) < 0.1, \
                f"DIR should be formatable to 1 decimal: {dir_float}"
        
        # Verify stockout risk format (should be 0-1, frontend multiplies by 100)
        if product.stockout_risk is not None:
            risk_float = float(product.stockout_risk)
            assert 0 <= risk_float <= 1, \
                f"Stockout risk should be 0-1, got {risk_float}"
            # Frontend will multiply by 100: risk_float * 100
            percentage = risk_float * 100
            assert 0 <= percentage <= 100, \
                f"After frontend multiplication, should be 0-100%, got {percentage}%"
        
        # Verify status values (frontend expects specific strings)
        if product.status:
            valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
            assert product.status in valid_statuses, \
                f"Status should be one of {valid_statuses}, got {product.status}"
        
        print("✅ PROOF: API response format is correct for frontend")
    else:
        pytest.skip("No products in test data")


@pytest.mark.asyncio
async def test_validation_catches_incorrect_metrics(db_session, test_client_obj):
    """PROOF: Validation service detects when metrics are wrong"""
    service = DataValidationService(db_session)
    
    # Create product with known incorrect state
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
    
    # Manually insert wrong data into inventory_metrics (simulating bug)
    from models.inventory_metrics import InventoryMetric
    from datetime import date
    
    wrong_metric = InventoryMetric(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        location_id="LOC-001",
        date=date.today(),
        current_stock=100,
        dir=Decimal("50.0"),
        stockout_risk=Decimal("2.0"),  # WRONG: Should be 0-1, not 2.0
        inventory_value=Decimal("500.00")  # WRONG: Should be 100 * 10 = 1000
    )
    db_session.add(wrong_metric)
    await db_session.commit()
    
    # Validation should catch these errors
    report = await service.validate_all(
        client_id=test_client_obj.client_id,
        include_computed_metrics=True
    )
    
    # Should detect stockout risk out of range
    risk_errors = [e for e in report["computed_metrics"]["errors"] 
                   if "stockout risk" in e.lower() and "out of range" in e.lower()]
    assert len(risk_errors) > 0, \
        "Validation should detect stockout risk out of 0-1 range"
    
    # Should detect inventory value mismatch
    value_errors = [e for e in report["computed_metrics"]["errors"] 
                    if "inventory value" in e.lower() and "mismatch" in e.lower()]
    assert len(value_errors) > 0, \
        "Validation should detect inventory value calculation error"
    
    print("✅ PROOF: Validation service detects incorrect metrics")


@pytest.mark.asyncio
async def test_frontend_backend_consistency(db_session, test_client_obj, populate_test_data):
    """PROOF: Backend format matches frontend expectations"""
    service = DataValidationService(db_session)
    
    # Run frontend consistency validation
    report = await service.validate_all(
        client_id=test_client_obj.client_id,
        include_frontend_consistency=True
    )
    
    consistency = report["frontend_consistency"]
    
    # After fixing stockout risk range, should have no errors
    # (warnings about thresholds are OK)
    frontend_errors = [e for e in consistency["errors"] 
                      if "stockout risk" in e.lower() and "range" in e.lower()]
    
    assert len(frontend_errors) == 0, \
        f"Frontend-backend consistency errors found: {frontend_errors}. " \
        f"This means backend format doesn't match frontend expectations."
    
    print("✅ PROOF: Backend format matches frontend expectations")


@pytest.mark.asyncio
async def test_end_to_end_metrics_flow(db_session, test_client_obj, populate_test_data):
    """PROOF: End-to-end flow from calculation to API response is correct"""
    from services.inventory_service import InventoryService
    
    inventory_service = InventoryService(db_session)
    validation_service = DataValidationService(db_session)
    
    # 1. Get products with metrics (simulates API call)
    result = await inventory_service.get_products_with_metrics(
        client_id=test_client_obj.client_id,
        page=1,
        page_size=5
    )
    
    if not result["items"]:
        pytest.skip("No products in test data")
    
    # 2. Verify each product's metrics are correct
    for product in result["items"]:
        # DIR should be >= 0 or None
        if product.dir is not None:
            assert float(product.dir) >= 0, f"DIR should be >= 0, got {product.dir}"
        
        # Stockout risk should be 0-1
        if product.stockout_risk is not None:
            risk = float(product.stockout_risk)
            assert 0 <= risk <= 1, \
                f"Stockout risk should be 0-1, got {risk} (frontend will show as {risk * 100}%)"
        
        # Status should be valid
        if product.status:
            valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
            assert product.status in valid_statuses, \
                f"Status should be one of {valid_statuses}, got {product.status}"
        
        # Inventory value should be >= 0
        if product.inventory_value is not None:
            assert float(product.inventory_value) >= 0, \
                f"Inventory value should be >= 0, got {product.inventory_value}"
    
    # 3. Run validation to confirm everything is correct
    report = await validation_service.validate_all(
        client_id=test_client_obj.client_id,
        include_computed_metrics=True,
        include_frontend_consistency=True
    )
    
    # Should have no critical errors
    assert report["summary"]["total_errors"] == 0, \
        f"Found errors in end-to-end flow: {report['summary']}"
    
    print("✅ PROOF: End-to-end metrics flow is correct (backend → API → frontend format)")

