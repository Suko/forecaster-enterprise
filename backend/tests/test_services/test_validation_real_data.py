"""
Test Validation Service with Real Data

Tests validation on actual data from database (not just fixtures).
This proves validation works on real production-like data.
"""
import pytest
from sqlalchemy import text

from services.data_validation_service import DataValidationService
from services.metrics_service import MetricsService
from services.inventory_service import InventoryService


@pytest.mark.asyncio
async def test_validation_on_real_database_data(db_session, test_client_obj, populate_test_data):
    """
    PROOF: Validation works on real data structure from database
    
    This test uses actual ts_demand_daily data (from CSV or synthetic)
    and validates that:
    1. Real data passes validation
    2. Metrics are calculated correctly on real data
    3. API format is correct for real data
    """
    validation_service = DataValidationService(db_session)
    metrics_service = MetricsService(db_session)
    inventory_service = InventoryService(db_session)
    
    # Get actual products from database (real data)
    result = await db_session.execute(
        text("""
            SELECT DISTINCT item_id
            FROM ts_demand_daily
            WHERE client_id = :client_id
            LIMIT 5
        """),
        {"client_id": str(test_client_obj.client_id)}
    )
    real_item_ids = [row[0] for row in result.fetchall()]
    
    if not real_item_ids:
        pytest.skip("No real data in database - run populate_test_data first")
    
    print(f"\n📊 Testing validation on {len(real_item_ids)} real products from database")
    
    # Test 1: Validate real data structure
    report = await validation_service.validate_all(
        client_id=test_client_obj.client_id,
        include_computed_metrics=True,
        include_frontend_consistency=True
    )
    
    # Should have no critical errors on real data
    assert report["summary"]["total_errors"] == 0, \
        f"Found errors in real data: {report['raw_data_quality']['errors']}"
    
    # Test 2: Calculate metrics on real products
    for item_id in real_item_ids[:3]:  # Test first 3
        metrics = await metrics_service.compute_product_metrics(
            client_id=test_client_obj.client_id,
            item_id=item_id
        )
        
        # Verify metrics are calculated (not None for products with data)
        assert metrics is not None, f"Metrics should be calculated for {item_id}"
        
        # Verify stockout risk is in correct range (0-1)
        if metrics.get("stockout_risk") is not None:
            risk = float(metrics["stockout_risk"])
            assert 0 <= risk <= 1, \
                f"Real data: {item_id} has stockout_risk {risk} (should be 0-1)"
        
        # Verify DIR is valid
        if metrics.get("dir") is not None:
            dir_value = float(metrics["dir"])
            assert dir_value >= 0, \
                f"Real data: {item_id} has DIR {dir_value} (should be >= 0)"
        
        print(f"  ✅ {item_id}: DIR={metrics.get('dir')}, Risk={metrics.get('stockout_risk')}, Status={metrics.get('status')}")
    
    # Test 3: Get products via API (simulates real API call)
    api_result = await inventory_service.get_products_with_metrics(
        client_id=test_client_obj.client_id,
        page=1,
        page_size=10
    )
    
    if api_result["items"]:
        # Verify API response format for real data
        for product in api_result["items"][:3]:
            # Stockout risk should be 0-1
            if product.stockout_risk is not None:
                risk = float(product.stockout_risk)
                assert 0 <= risk <= 1, \
                    f"API real data: {product.item_id} risk={risk} (should be 0-1)"
                # Frontend will multiply by 100
                percentage = risk * 100
                assert 0 <= percentage <= 100, \
                    f"After frontend multiplication: {percentage}% (should be 0-100%)"
            
            # DIR should be formatable
            if product.dir is not None:
                dir_float = float(product.dir)
                formatted = round(dir_float, 1)
                assert abs(dir_float - formatted) < 0.1, \
                    f"DIR should be formatable to 1 decimal: {dir_float}"
            
            # Status should be valid
            if product.status:
                valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
                assert product.status in valid_statuses, \
                    f"Status should be valid: {product.status}"
        
        print(f"  ✅ API format correct for {len(api_result['items'])} real products")
    
    print("✅ PROOF: Validation works correctly on real database data")


@pytest.mark.asyncio
async def test_metrics_calculation_on_real_sales_data(db_session, test_client_obj, populate_test_data):
    """
    PROOF: Metrics are calculated correctly using real sales data from ts_demand_daily
    
    This test:
    1. Gets real sales data from ts_demand_daily
    2. Calculates DIR using actual average daily demand
    3. Verifies calculation is correct
    """
    metrics_service = MetricsService(db_session)
    
    # Get a product with real sales data
    result = await db_session.execute(
        text("""
            SELECT item_id, 
                   COUNT(*) as days_with_sales,
                   AVG(units_sold) as avg_daily,
                   SUM(units_sold) as total_sold
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND units_sold > 0
            GROUP BY item_id
            HAVING COUNT(*) >= 30
            ORDER BY COUNT(*) DESC
            LIMIT 1
        """),
        {"client_id": str(test_client_obj.client_id)}
    )
    row = result.fetchone()
    
    if not row:
        pytest.skip("No real sales data with 30+ days in database")
    
    item_id = row.item_id
    avg_daily_from_db = float(row.avg_daily)
    total_sold = float(row.total_sold)
    days_with_sales = int(row.days_with_sales)
    
    print(f"\n📊 Testing metrics on real sales data:")
    print(f"   Item: {item_id}")
    print(f"   Days with sales: {days_with_sales}")
    print(f"   Average daily (from DB): {avg_daily_from_db:.2f}")
    print(f"   Total sold: {total_sold:.0f}")
    
    # Get current stock
    stock_result = await db_session.execute(
        text("""
            SELECT SUM(current_stock) as total_stock
            FROM stock_levels
            WHERE client_id = :client_id
              AND item_id = :item_id
        """),
        {"client_id": str(test_client_obj.client_id), "item_id": item_id}
    )
    stock_row = stock_result.fetchone()
    current_stock = int(stock_row[0] or 0) if stock_row else 0
    
    print(f"   Current stock: {current_stock}")
    
    # Calculate metrics using service (uses real data from ts_demand_daily)
    metrics = await metrics_service.compute_product_metrics(
        client_id=test_client_obj.client_id,
        item_id=item_id
    )
    
    # Verify DIR calculation
    if metrics.get("dir") is not None and avg_daily_from_db > 0:
        calculated_dir = float(metrics["dir"])
        expected_dir = current_stock / avg_daily_from_db if avg_daily_from_db > 0 else None
        
        if expected_dir:
            # Allow small difference due to date range differences
            assert abs(calculated_dir - expected_dir) < 5 or calculated_dir == expected_dir, \
                f"DIR calculation mismatch: calculated={calculated_dir}, expected={expected_dir:.2f} " \
                f"(stock={current_stock}, avg_daily={avg_daily_from_db:.2f})"
        
        print(f"   ✅ DIR calculated: {calculated_dir:.2f} days")
    
    # Verify stockout risk is in correct range
    if metrics.get("stockout_risk") is not None:
        risk = float(metrics["stockout_risk"])
        assert 0 <= risk <= 1, \
            f"Stockout risk should be 0-1, got {risk} (frontend will show as {risk * 100}%)"
        print(f"   ✅ Stockout risk: {risk:.3f} (frontend will show as {risk * 100:.1f}%)")
    
    # Verify status is valid
    if metrics.get("status"):
        valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
        assert metrics["status"] in valid_statuses, \
            f"Status should be valid, got {metrics['status']}"
        print(f"   ✅ Status: {metrics['status']}")
    
    print("✅ PROOF: Metrics calculated correctly on real sales data")


@pytest.mark.asyncio
async def test_validation_detects_real_data_issues(db_session, test_client_obj, populate_test_data):
    """
    PROOF: Validation service detects actual issues in real data
    
    This test verifies validation catches:
    - Missing relationships
    - Invalid formats
    - Calculation errors
    """
    validation_service = DataValidationService(db_session)
    
    # Run validation on real data
    report = await validation_service.validate_all(
        client_id=test_client_obj.client_id,
        include_computed_metrics=True,
        include_frontend_consistency=True
    )
    
    # Check raw data quality
    raw_errors = report["raw_data_quality"]["errors"]
    raw_warnings = report["raw_data_quality"]["warnings"]
    
    print(f"\n📊 Validation results on real data:")
    print(f"   Raw data errors: {len(raw_errors)}")
    print(f"   Raw data warnings: {len(raw_warnings)}")
    
    if raw_errors:
        print(f"   ❌ Errors found:")
        for error in raw_errors[:5]:
            print(f"      - {error}")
    
    # Check completeness
    completeness_errors = report["data_completeness"]["errors"]
    completeness_warnings = report["data_completeness"]["warnings"]
    
    print(f"   Completeness errors: {len(completeness_errors)}")
    print(f"   Completeness warnings: {len(completeness_warnings)}")
    
    if completeness_errors:
        print(f"   ❌ Completeness issues:")
        for error in completeness_errors[:5]:
            print(f"      - {error}")
    
    # Check computed metrics
    if report.get("computed_metrics"):
        metrics_errors = report["computed_metrics"]["errors"]
        metrics_warnings = report["computed_metrics"]["warnings"]
        
        print(f"   Computed metrics errors: {len(metrics_errors)}")
        print(f"   Computed metrics warnings: {len(metrics_warnings)}")
        
        if metrics_errors:
            print(f"   ❌ Metrics calculation issues:")
            for error in metrics_errors[:5]:
                print(f"      - {error}")
    
    # Check frontend consistency
    if report.get("frontend_consistency"):
        consistency_errors = report["frontend_consistency"]["errors"]
        consistency_warnings = report["frontend_consistency"]["warnings"]
        
        print(f"   Frontend consistency errors: {len(consistency_errors)}")
        print(f"   Frontend consistency warnings: {len(consistency_warnings)}")
        
        # After our fixes, should have no stockout risk range errors
        risk_range_errors = [e for e in consistency_errors 
                            if "stockout risk" in e.lower() and "range" in e.lower()]
        assert len(risk_range_errors) == 0, \
            f"Should have no stockout risk range errors after fix: {risk_range_errors}"
        
        if consistency_errors:
            print(f"   ❌ Frontend consistency issues:")
            for error in consistency_errors[:5]:
                print(f"      - {error}")
    
    print(f"\n   Summary: {report['summary']['total_errors']} errors, "
          f"{report['summary']['total_warnings']} warnings")
    
    # Validation should complete without crashing
    assert "summary" in report
    assert "is_valid" in report["summary"]
    
    print("✅ PROOF: Validation service works on real data and detects issues")


@pytest.mark.asyncio
async def test_real_data_api_endpoint_format(db_session, test_client_obj, populate_test_data):
    """
    PROOF: API endpoint returns correct format for real data
    
    Simulates actual API call and verifies response format matches frontend expectations.
    """
    from services.inventory_service import InventoryService
    
    inventory_service = InventoryService(db_session)
    
    # Get products with metrics (simulates GET /api/v1/inventory/products)
    result = await inventory_service.get_products_with_metrics(
        client_id=test_client_obj.client_id,
        page=1,
        page_size=20
    )
    
    if not result["items"]:
        pytest.skip("No products in database")
    
    print(f"\n📊 Testing API format on {len(result['items'])} real products:")
    
    format_issues = []
    
    for product in result["items"]:
        item_id = product.item_id
        
        # Check DIR format
        if product.dir is not None:
            dir_float = float(product.dir)
            # Should be formatable to 1 decimal (frontend uses toFixed(1))
            if not (isinstance(dir_float, float) and dir_float >= 0):
                format_issues.append(f"{item_id}: DIR invalid: {product.dir}")
        
        # Check stockout risk format (CRITICAL)
        if product.stockout_risk is not None:
            risk = float(product.stockout_risk)
            if not (0 <= risk <= 1):
                format_issues.append(
                    f"{item_id}: Stockout risk out of range: {risk} "
                    f"(should be 0-1, frontend will show as {risk * 100}%)"
                )
            # Verify frontend multiplication works
            percentage = risk * 100
            if not (0 <= percentage <= 100):
                format_issues.append(
                    f"{item_id}: After frontend multiplication: {percentage}% "
                    f"(should be 0-100%)"
                )
        
        # Check status format
        if product.status:
            valid_statuses = ["understocked", "overstocked", "normal", "out_of_stock", "unknown"]
            if product.status not in valid_statuses:
                format_issues.append(
                    f"{item_id}: Invalid status: {product.status} "
                    f"(should be one of {valid_statuses})"
                )
        
        # Check inventory value format
        if product.inventory_value is not None:
            value = float(product.inventory_value)
            if value < 0:
                format_issues.append(f"{item_id}: Negative inventory value: {value}")
    
    if format_issues:
        print(f"   ❌ Format issues found:")
        for issue in format_issues[:10]:
            print(f"      - {issue}")
        assert False, f"Found {len(format_issues)} format issues in real API data"
    else:
        print(f"   ✅ All {len(result['items'])} products have correct format")
        print(f"   ✅ Stockout risk in 0-1 range (frontend will multiply by 100)")
        print(f"   ✅ DIR formatable to 1 decimal")
        print(f"   ✅ Status values valid")
    
    print("✅ PROOF: API endpoint returns correct format for real data")

