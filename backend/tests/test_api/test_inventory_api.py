"""
Tests for Inventory API endpoints

Tests Products, Dashboard, and Product-Supplier APIs.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from datetime import date, timedelta

from models.product import Product
from models.stock import StockLevel
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.inventory_metrics import InventoryMetric
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_stock_level,
    create_test_product_supplier_condition,
    create_test_inventory_data_batch
)


@pytest.mark.asyncio
async def test_get_products(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test GET /api/v1/products - List products"""
    # Create test products
    product1 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        product_name="Test Product 1"
    )
    product2 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-002",
        product_name="Test Product 2"
    )
    db_session.add_all([product1, product2])
    await db_session.commit()

    # Make request
    response = await test_client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 2


@pytest.mark.asyncio
async def test_get_products_with_filters(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test GET /api/v1/products with filters"""
    # Create products in different categories
    product1 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        category="Electronics"
    )
    product2 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-002",
        category="Clothing"
    )
    db_session.add_all([product1, product2])
    await db_session.commit()

    # Filter by category
    response = await test_client.get(
        "/api/v1/products?category=Electronics",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert all(item["category"] == "Electronics" for item in data["items"])


@pytest.mark.asyncio
async def test_get_products_metric_filters(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str,
    populate_test_data
):
    """Metric filters: min_stock, min_dir, status."""
    # Create products
    under_item = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="FILTER-UNDER",
        product_name="Understocked"
    )
    over_item = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="FILTER-OVER",
        product_name="Overstocked"
    )
    db_session.add_all([under_item, over_item])

    # Stock levels
    db_session.add_all([
        create_test_stock_level(client_id=test_client_obj.client_id, item_id=under_item.item_id, current_stock=5),
        create_test_stock_level(client_id=test_client_obj.client_id, item_id=over_item.item_id, current_stock=1000),
    ])

    # Minimal sales history to compute DIR / status
    from sqlalchemy import text
    today = date.today()
    for i in range(10):
        day = today - timedelta(days=i)
        await db_session.execute(
            text("""
                INSERT INTO ts_demand_daily
                (client_id, item_id, location_id, date_local, units_sold, promotion_flag, holiday_flag, is_weekend, marketing_spend)
                VALUES (:client_id, :item_id, 'UNSPECIFIED', :date_local, :units_sold, false, false, false, 0)
                ON CONFLICT (client_id, item_id, location_id, date_local) DO NOTHING
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": under_item.item_id,
                "date_local": day,
                "units_sold": 10,  # High demand → low DIR given low stock
            }
        )
        await db_session.execute(
            text("""
                INSERT INTO ts_demand_daily
                (client_id, item_id, location_id, date_local, units_sold, promotion_flag, holiday_flag, is_weekend, marketing_spend)
                VALUES (:client_id, :item_id, 'UNSPECIFIED', :date_local, :units_sold, false, false, false, 0)
                ON CONFLICT (client_id, item_id, location_id, date_local) DO NOTHING
            """),
            {
                "client_id": str(test_client_obj.client_id),
                "item_id": over_item.item_id,
                "date_local": day,
                "units_sold": 5,  # Lower demand → high DIR given high stock
            }
        )
    await db_session.commit()

    # Precomputed metrics used by API-side filtering (latest per item_id)
    metric_under = InventoryMetric(
        client_id=test_client_obj.client_id,
        item_id=under_item.item_id,
        location_id="UNSPECIFIED",
        date=today,
        current_stock=5,
        dir=Decimal("2.0"),
        stockout_risk=Decimal("0.90"),
        forecasted_demand_30d=Decimal("200"),
        inventory_value=Decimal("50"),
        status="understocked",
    )
    metric_over = InventoryMetric(
        client_id=test_client_obj.client_id,
        item_id=over_item.item_id,
        location_id="UNSPECIFIED",
        date=today,
        current_stock=1000,
        dir=Decimal("200"),
        stockout_risk=Decimal("0.10"),
        forecasted_demand_30d=Decimal("50"),
        inventory_value=Decimal("2000"),
        status="overstocked",
    )
    db_session.add_all([metric_under, metric_over])
    await db_session.commit()

    # min_stock should only return the high-stock item
    resp_stock = await test_client.get(
        "/api/v1/products?min_stock=100",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    assert resp_stock.status_code == 200
    items_stock = {p["item_id"] for p in resp_stock.json()["items"]}
    assert "FILTER-OVER" in items_stock
    assert "FILTER-UNDER" not in items_stock

    # min_dir should return the high-DIR item (overstocked)
    resp_dir = await test_client.get(
        "/api/v1/products?min_dir=50",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    assert resp_dir.status_code == 200
    items_dir = {p["item_id"] for p in resp_dir.json()["items"]}
    assert "FILTER-OVER" in items_dir
    assert "FILTER-UNDER" not in items_dir

    # status=understocked should only return the low-stock/high-demand item
    resp_status = await test_client.get(
        "/api/v1/products?status=understocked",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    assert resp_status.status_code == 200
    items_status = {p["item_id"] for p in resp_status.json()["items"]}
    assert "FILTER-UNDER" in items_status
    assert "FILTER-OVER" not in items_status


@pytest.mark.asyncio
async def test_get_product_detail(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test GET /api/v1/products/{item_id} - Get product details"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        product_name="Test Product"
    )
    db_session.add(product)
    await db_session.commit()

    response = await test_client.get(
        f"/api/v1/products/{product.item_id}",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["item_id"] == product.item_id
    assert data["product_name"] == "Test Product"


@pytest.mark.asyncio
async def test_get_product_metrics(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str,
    populate_test_data
):
    """Test GET /api/v1/products/{item_id}/metrics"""
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

    response = await test_client.get(
        f"/api/v1/products/{product.item_id}/metrics",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "dir" in data
    assert "stockout_risk" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_get_dashboard(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str,
    populate_test_data
):
    """Test GET /api/v1/dashboard"""
    # Create test data
    batch = create_test_inventory_data_batch(
        client_id=test_client_obj.client_id,
        num_products=3
    )
    db_session.add_all(batch["products"])
    db_session.add_all(batch["stock_levels"])
    await db_session.commit()

    response = await test_client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "top_understocked" in data
    assert "top_overstocked" in data


@pytest.mark.asyncio
async def test_get_product_suppliers(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test GET /api/v1/products/{item_id}/suppliers"""
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add_all([product, supplier])
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id
    )
    db_session.add(condition)
    await db_session.commit()

    # Refresh to ensure timestamps are set
    await db_session.refresh(condition)

    response = await test_client.get(
        f"/api/v1/products/{product.item_id}/suppliers",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    # Verify supplier info is included
    assert "supplier" in data[0]


@pytest.mark.asyncio
async def test_add_product_supplier(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test POST /api/v1/products/{item_id}/suppliers"""
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

    response = await test_client.post(
        f"/api/v1/products/{product.item_id}/suppliers",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "supplier_id": str(supplier.id),
            "moq": 10,
            "lead_time_days": 14,
            "supplier_cost": "10.00",
            "is_primary": True
        }
    )

    if response.status_code != 200:
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")

    assert response.status_code == 200
    data = response.json()
    assert data["supplier_id"] == str(supplier.id)
    assert data["moq"] == 10


@pytest.mark.asyncio
async def test_get_products_unauthorized(test_client: AsyncClient):
    """Test GET /api/v1/products without authentication"""
    response = await test_client.get("/api/v1/products")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_products_wrong_client(
    test_client: AsyncClient,
    db_session: AsyncSession,
    test_client_obj,
    test_jwt_token: str
):
    """Test multi-tenant isolation - products from other clients not visible"""
    import uuid

    # Create product for different client
    other_client_id = uuid.uuid4()
    other_product = create_test_product(
        client_id=other_client_id,
        item_id="OTHER-001"
    )
    db_session.add(other_product)
    await db_session.commit()

    # Request products for test_client
    response = await test_client.get(
        "/api/v1/products",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    # Should not see other client's products
    assert not any(item["item_id"] == "OTHER-001" for item in data["items"])
