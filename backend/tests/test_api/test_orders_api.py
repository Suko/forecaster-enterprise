"""
API tests for Order Planning endpoints

Tests cart, suggestions, and recommendations APIs.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition,
    create_test_stock_level
)


@pytest.mark.asyncio
async def test_add_to_cart(test_client, test_jwt_token, test_client_obj, db_session):
    """Test adding item to cart"""
    # Create product and supplier
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
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
        moq=10
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add to cart
    response = await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "item_id": product.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 20
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == product.item_id
    assert data["quantity"] == 20


@pytest.mark.asyncio
async def test_add_to_cart_below_moq(test_client, test_jwt_token, test_client_obj, db_session):
    """Test adding item below MOQ (should fail)"""
    # Create product and supplier
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
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
        moq=10  # MOQ is 10
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Try to add below MOQ
    response = await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "item_id": product.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 5  # Below MOQ
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_cart(test_client, test_jwt_token, test_client_obj, db_session):
    """Test getting cart items"""
    # Create products and supplier
    product1 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    product2 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-002"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    from models.database import get_async_session_local
    async with get_async_session_local()() as db:
        db.add_all([product1, product2, supplier])
        await db.commit()
        await db.refresh(supplier)
        
        condition1 = create_test_product_supplier_condition(
            client_id=test_client_obj.client_id,
            item_id=product1.item_id,
            supplier_id=supplier.id
        )
        condition2 = create_test_product_supplier_condition(
            client_id=test_client_obj.client_id,
            item_id=product2.item_id,
            supplier_id=supplier.id
        )
        db.add_all([condition1, condition2])
        await db.commit()
    
    # Use JWT token
    
    # Add items to cart
    await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={
            "item_id": product1.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 10
        }
    )
    await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={
            "item_id": product2.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 20
        }
    )
    
    # Get cart
    response = await test_client.get(
        "/api/v1/order-planning/cart",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "test-session"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_update_cart_item(test_client, test_jwt_token, test_client_obj, db_session):
    """Test updating cart item quantity"""
    # Create product and supplier
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    from models.database import get_async_session_local
    async with get_async_session_local()() as db:
        db.add_all([product, supplier])
        await db.commit()
        await db.refresh(supplier)
        
        condition = create_test_product_supplier_condition(
            client_id=test_client_obj.client_id,
            item_id=product.item_id,
            supplier_id=supplier.id,
            moq=10
        )
        db.add(condition)
        await db.commit()
    
    # Use JWT token
    
    # Add to cart
    await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={
            "item_id": product.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 10
        }
    )
    
    # Update quantity
    response = await test_client.put(
        f"/api/v1/order-planning/cart/{product.item_id}",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={"quantity": 30}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 30


@pytest.mark.asyncio
async def test_remove_from_cart(test_client, test_jwt_token, test_client_obj, db_session):
    """Test removing item from cart"""
    # Create product and supplier
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    from models.database import get_async_session_local
    async with get_async_session_local()() as db:
        db.add_all([product, supplier])
        await db.commit()
        await db.refresh(supplier)
        
        condition = create_test_product_supplier_condition(
            client_id=test_client_obj.client_id,
            item_id=product.item_id,
            supplier_id=supplier.id
        )
        db.add(condition)
        await db.commit()
    
    # Use JWT token
    
    # Add to cart
    await test_client.post(
        "/api/v1/order-planning/cart/add",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={
            "item_id": product.item_id,
            "supplier_id": str(supplier.id),
            "quantity": 10
        }
    )
    
    # Remove from cart
    response = await test_client.delete(
        f"/api/v1/order-planning/cart/{product.item_id}",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "test-session"}
    )
    
    assert response.status_code == 200
    
    # Verify removed
    cart_response = await test_client.get(
        "/api/v1/order-planning/cart",
        headers={"Authorization": f"Bearer {token}", "X-Session-ID": "test-session"}
    )
    data = cart_response.json()
    assert len(data["items"]) == 0


@pytest.mark.asyncio
async def test_get_order_suggestions(test_client, test_jwt_token, test_client_obj, db_session, populate_test_data):
    """Test getting order suggestions"""
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
    
    # Use JWT token
    
    # Get suggestions
    response = await test_client.get(
        "/api/v1/order-planning/suggestions",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["suggestions"], list)


@pytest.mark.asyncio
async def test_get_recommendations(test_client, test_jwt_token, test_client_obj, populate_test_data):
    """Test getting recommendations"""
    # Use JWT token
    
    # Get recommendations
    response = await test_client.get(
        "/api/v1/order-planning/recommendations",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_recommendations_by_type(test_client, test_jwt_token, test_client_obj, populate_test_data):
    """Test filtering recommendations by type"""
    # Use JWT token
    
    # Get REORDER recommendations
    response = await test_client.get(
        "/api/v1/order-planning/recommendations?recommendation_type=REORDER",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # All items should be REORDER type (if any)
    for item in data:
        assert item.get("type") == "REORDER"

