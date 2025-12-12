"""
API Tests for Supplier Defaults (MOQ, Lead Time)

Tests API endpoints for managing supplier defaults.
"""
import pytest
from httpx import AsyncClient
from decimal import Decimal

from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier
)


@pytest.mark.asyncio
async def test_get_supplier_includes_defaults(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test GET /api/v1/suppliers/{id} includes default_moq and default_lead_time_days"""
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add(supplier)
    await db_session.commit()

    response = await test_client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["default_moq"] == 100
    assert data["default_lead_time_days"] == 14


@pytest.mark.asyncio
async def test_supplier_list_includes_defaults(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test GET /api/v1/suppliers includes defaults in response"""
    supplier1 = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A"
    )
    supplier1.default_moq = 50
    supplier1.default_lead_time_days = 10

    supplier2 = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier B"
    )
    supplier2.default_moq = 100
    supplier2.default_lead_time_days = 21

    db_session.add_all([supplier1, supplier2])
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/suppliers",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 2

    # Find our suppliers
    suppliers_dict = {s["name"]: s for s in data["items"]}
    assert suppliers_dict["Supplier A"]["default_moq"] == 50
    assert suppliers_dict["Supplier A"]["default_lead_time_days"] == 10
    assert suppliers_dict["Supplier B"]["default_moq"] == 100
    assert suppliers_dict["Supplier B"]["default_lead_time_days"] == 21


@pytest.mark.asyncio
async def test_add_product_supplier_auto_populates_from_supplier_defaults(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test POST /api/v1/products/{item_id}/suppliers auto-populates MOQ/lead time"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A"
    )
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add_all([product, supplier])
    await db_session.commit()

    # Add supplier without specifying MOQ/lead_time
    response = await test_client.post(
        f"/api/v1/products/{product.item_id}/suppliers",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "moq": None,  # Should auto-populate from supplier.default_moq
            "lead_time_days": None,  # Should auto-populate from supplier.default_lead_time_days
            "supplier_cost": "10.00",
            "is_primary": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["moq"] == 100  # Auto-populated
    assert data["lead_time_days"] == 14  # Auto-populated


@pytest.mark.asyncio
async def test_add_product_supplier_manual_override(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test manual override of supplier defaults when creating product-supplier link"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A"
    )
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add_all([product, supplier])
    await db_session.commit()

    # Add supplier with explicit values - should override defaults
    response = await test_client.post(
        f"/api/v1/products/{product.item_id}/suppliers",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "moq": 150,  # Manual override
            "lead_time_days": 21,  # Manual override
            "supplier_cost": "10.00",
            "is_primary": True
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["moq"] == 150  # Manual value, not supplier default
    assert data["lead_time_days"] == 21


@pytest.mark.asyncio
async def test_get_product_includes_safety_buffer(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test GET /api/v1/products/{item_id} includes safety_buffer_days"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    product.safety_buffer_days = 10  # Product override
    db_session.add(product)
    await db_session.commit()

    response = await test_client.get(
        f"/api/v1/products/{product.item_id}",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["safety_buffer_days"] == 10


@pytest.mark.asyncio
async def test_get_product_shows_null_buffer_when_using_client_default(
    test_client: AsyncClient,
    test_jwt_token: str,
    test_client_obj,
    db_session
):
    """Test GET /api/v1/products/{item_id} shows null buffer when using client default"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    product.safety_buffer_days = None  # Using client default
    db_session.add(product)
    await db_session.commit()

    response = await test_client.get(
        f"/api/v1/products/{product.item_id}",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["safety_buffer_days"] is None  # Using client default

