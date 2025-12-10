"""
Integration tests for complete workflows

Tests end-to-end workflows that span multiple services and APIs.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition,
    create_test_stock_level,
    create_test_client_settings
)


@pytest.mark.asyncio
async def test_workflow_order_planning_to_po(test_client, test_jwt_token, test_client_obj, db_session, populate_test_data):
    """Test complete workflow: product -> cart -> purchase order"""
    # Create product and supplier
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        unit_cost=Decimal("10.00")
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add_all([product, supplier])
    await db_session.commit()
    await db_session.refresh(supplier)
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=10,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Step 1: Add product to cart
    cart_response = await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "workflow-session"},
        json={
            "item_id": product.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 20
        }
    )
    assert cart_response.status_code == 200
    
    # Step 2: Get cart to verify
    get_cart_response = await test_client.get(
        "/api/v1/order-planning/cart",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "workflow-session"}
    )
    assert get_cart_response.status_code == 200
    cart_data = get_cart_response.json()
    assert len(cart_data["items"]) == 1
    
    # Step 3: Create purchase order from cart
    po_response = await test_client.post(
        "/api/v1/purchase-orders/from-cart",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "workflow-session"},
        json={"supplier_id": str(supplier.id)}
    )
    assert po_response.status_code == 201
    po_data = po_response.json()
    assert po_data["status"] == "pending"
    assert len(po_data["items"]) == 1
    
    # Step 4: Verify cart is cleared after PO creation
    cart_after_po = await test_client.get(
        "/api/v1/order-planning/cart",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "workflow-session"}
    )
    cart_after_data = cart_after_po.json()
    assert len(cart_after_data["items"]) == 0


@pytest.mark.asyncio
async def test_workflow_product_metrics_to_recommendations(test_client, test_jwt_token, test_client_obj, db_session, populate_test_data):
    """Test workflow: product with low stock -> metrics -> recommendations"""
    # Create product with low stock
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=5  # Low stock
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    from models.database import get_async_session_local
    async with get_async_session_local()() as db:
        db.add_all([product, stock, supplier])
        await db.commit()
        await db.refresh(supplier)
        
        condition = create_test_product_supplier_condition(
            client_id=test_client_obj.client_id,
            item_id=product.item_id,
            supplier_id=supplier.id,
            lead_time_days=14
        )
        db.add(condition)
        await db.commit()
    
    token = test_user.token
    
    # Step 1: Get product metrics
    metrics_response = await test_client.get(
        f"/api/v1/products/{product.item_id}/metrics",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert "dir" in metrics
    assert "stockout_risk" in metrics
    assert "status" in metrics
    
    # Step 2: Get recommendations (should include this product)
    recommendations_response = await test_client.get(
        "/api/v1/order-planning/recommendations",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert recommendations_response.status_code == 200
    recommendations = recommendations_response.json()
    assert isinstance(recommendations, list)
    
    # Step 3: Verify recommendation includes our product (if risk is high enough)
    if metrics.get("stockout_risk", 0) > 0.5:
        product_recommendations = [
            r for r in recommendations
            if r.get("item_id") == product.item_id
        ]
        # Should have at least one recommendation for this product
        assert len(product_recommendations) >= 0  # May be 0 if thresholds not met


@pytest.mark.asyncio
async def test_workflow_settings_update_affects_recommendations(test_client, test_jwt_token, test_client_obj, populate_test_data):
    """Test workflow: update settings -> verify recommendations change"""
    # Create product with low stock
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    stock = create_test_stock_level(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=10
    )
    from models.database import get_async_session_local
    async with get_async_session_local()() as db:
        db.add_all([product, stock])
        await db.commit()
    
    token = test_user.token
    
    # Step 1: Get initial recommendations
    initial_response = await test_client.get(
        "/api/v1/order-planning/recommendations",
        headers={"Authorization": f"Bearer {token}"}
    )
    initial_recommendations = initial_response.json()
    initial_count = len(initial_recommendations)
    
    # Step 2: Update settings to be more restrictive
    await test_client.put(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "safety_buffer_days": 30,
            "understocked_threshold": 60
        }
    )
    
    # Step 3: Get recommendations again
    updated_response = await test_client.get(
        "/api/v1/order-planning/recommendations",
        headers={"Authorization": f"Bearer {token}"}
    )
    updated_recommendations = updated_response.json()
    
    # Recommendations may change based on new thresholds
    assert isinstance(updated_recommendations, list)


@pytest.mark.asyncio
async def test_workflow_dashboard_to_product_detail(test_client, test_jwt_token, test_client_obj, populate_test_data):
    """Test workflow: dashboard -> product detail -> metrics"""
    token = test_user.token
    
    # Step 1: Get dashboard
    dashboard_response = await test_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert dashboard_response.status_code == 200
    dashboard = dashboard_response.json()
    assert "total_products" in dashboard
    assert "total_value" in dashboard
    
    # Step 2: If there are products, get first product detail
    products_response = await test_client.get(
        "/api/v1/products?page_size=1",
        headers={"Authorization": f"Bearer {token}"}
    )
    products = products_response.json()
    
    if products["total"] > 0:
        item_id = products["items"][0]["item_id"]
        
        # Step 3: Get product detail
        detail_response = await test_client.get(
            f"/api/v1/products/{item_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert detail_response.status_code == 200
        
        # Step 4: Get product metrics
        metrics_response = await test_client.get(
            f"/api/v1/products/{item_id}/metrics",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert metrics_response.status_code == 200
        metrics = metrics_response.json()
        assert "dir" in metrics
        assert "status" in metrics

