"""
API tests for Purchase Orders endpoints

Tests purchase order creation, listing, and status updates.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition
)


@pytest.mark.asyncio
async def test_create_purchase_order(test_client, test_jwt_token, test_client_obj, db_session):
    """Test creating purchase order"""
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
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Create PO
    response = await test_client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "items": [
                {
                    "item_id": product.item_id,
                    "quantity": 10,
                    "unit_cost": "10.00"
                }
            ]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert data["supplier_id"] == str(supplier.id)
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_purchase_orders(test_client, test_jwt_token, test_client_obj, db_session):
    """Test listing purchase orders"""
    # Create supplier
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    
    # Create a PO first
    await test_client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "items": []
        }
    )
    
    # List POs
    response = await test_client.get(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_get_purchase_order_detail(test_client, test_jwt_token, test_client_obj, db_session):
    """Test getting purchase order details"""
    # Create supplier
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    
    # Create a PO
    create_response = await test_client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "items": []
        }
    )
    po_id = create_response.json()["id"]
    
    # Get PO details
    response = await test_client.get(
        f"/api/v1/purchase-orders/{po_id}",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == po_id
    assert data["supplier_id"] == str(supplier.id)


@pytest.mark.asyncio
async def test_update_po_status(test_client, test_jwt_token, test_client_obj, db_session):
    """Test updating purchase order status"""
    # Create supplier
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add(supplier)
    await db_session.commit()
    await db_session.refresh(supplier)
    
    # Create a PO
    create_response = await test_client.post(
        "/api/v1/purchase-orders",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "items": []
        }
    )
    po_id = create_response.json()["id"]
    
    # Update status
    response = await test_client.patch(
        f"/api/v1/purchase-orders/{po_id}/status",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={"status": "confirmed"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "confirmed"


@pytest.mark.asyncio
async def test_create_po_from_cart(test_client, test_jwt_token, test_client_obj, db_session):
    """Test creating purchase order from cart"""
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
        supplier_id=supplier.id
    )
    db_session.add(condition)
    await db_session.commit()
    
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
    
    # Create PO from cart
    response = await test_client.post(
        "/api/v1/purchase-orders/from-cart",
        headers={"Authorization": f"Bearer {test_jwt_token}", "X-Session-ID": "test-session"},
        json={
            "supplier_id": str(supplier.id)
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "pending"
    assert len(data["items"]) == 1

