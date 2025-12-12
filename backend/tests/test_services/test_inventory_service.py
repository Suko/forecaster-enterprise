"""
Unit tests for InventoryService

Tests product retrieval, filtering, supplier management, etc.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from services.inventory_service import InventoryService
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition
)


@pytest.mark.asyncio
async def test_get_products_pagination(db_session, test_client_obj):
    """Test product listing with pagination"""
    service = InventoryService(db_session)

    # Create multiple products
    products = []
    for i in range(15):
        product = create_test_product(
            client_id=test_client_obj.client_id,
            item_id=f"TEST-{i+1:03d}"
        )
        products.append(product)
    db_session.add_all(products)
    await db_session.commit()

    # Get first page
    result = await service.get_products(
        client_id=test_client_obj.client_id,
        page=1,
        page_size=10
    )

    assert len(result["items"]) == 10
    assert result["total"] == 15
    assert result["page"] == 1
    assert result["page_size"] == 10
    assert result["total_pages"] == 2


@pytest.mark.asyncio
async def test_get_products_filter_by_category(db_session, test_client_obj):
    """Test filtering products by category"""
    service = InventoryService(db_session)

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

    from schemas.inventory import ProductFilters

    # Filter by category
    filters = ProductFilters(category="Electronics")
    result = await service.get_products(
        client_id=test_client_obj.client_id,
        filters=filters
    )

    assert len(result["items"]) == 1
    assert result["items"][0]["category"] == "Electronics"


@pytest.mark.asyncio
async def test_get_product_not_found(db_session, test_client_obj):
    """Test getting non-existent product"""
    service = InventoryService(db_session)

    product = await service.get_product(
        client_id=test_client_obj.client_id,
        item_id="NONEXISTENT"
    )

    assert product is None


@pytest.mark.asyncio
async def test_add_product_supplier(db_session, test_client_obj):
    """Test adding supplier to product"""
    service = InventoryService(db_session)

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

    # Add supplier condition
    condition = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=10,
        lead_time_days=14,
        supplier_cost=Decimal("10.00")
    )

    assert condition is not None
    assert condition.moq == 10
    assert condition.lead_time_days == 14


@pytest.mark.asyncio
async def test_add_product_supplier_duplicate(db_session, test_client_obj):
    """Test adding duplicate supplier (should update existing)"""
    service = InventoryService(db_session)

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

    # Add first time
    condition1 = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=10,
        lead_time_days=14
    )

    # Add again (should update)
    condition2 = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=20,  # Different MOQ
        lead_time_days=21  # Different lead time
    )

    # Should be the same record, updated
    assert condition1.id == condition2.id
    assert condition2.moq == 20
    assert condition2.lead_time_days == 21


@pytest.mark.asyncio
async def test_get_product_suppliers(db_session, test_client_obj):
    """Test getting all suppliers for a product"""
    service = InventoryService(db_session)

    # Create product and multiple suppliers
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001"
    )
    supplier1 = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier 1"
    )
    supplier2 = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier 2"
    )
    db_session.add_all([product, supplier1, supplier2])
    await db_session.flush()

    # Add conditions
    condition1 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier1.id
    )
    condition2 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier2.id
    )
    db_session.add_all([condition1, condition2])
    await db_session.commit()

    # Get suppliers
    suppliers = await service.get_product_suppliers(
        client_id=test_client_obj.client_id,
        item_id=product.item_id
    )

    assert len(suppliers) == 2


@pytest.mark.asyncio
async def test_remove_product_supplier(db_session, test_client_obj):
    """Test removing supplier from product"""
    service = InventoryService(db_session)

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
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id
    )
    db_session.add(condition)
    await db_session.commit()

    # Remove supplier
    await service.remove_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id
    )

    await db_session.commit()

    # Verify removed
    suppliers = await service.get_product_suppliers(
        client_id=test_client_obj.client_id,
        item_id=product.item_id
    )

    assert len(suppliers) == 0


# ============================================================================
# Tests for Effective Value Helpers (MOQ, Lead Time, Buffer)
# ============================================================================

@pytest.mark.asyncio
async def test_get_effective_moq_from_condition(db_session, test_client_obj):
    """Test effective MOQ uses product-supplier condition when available"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 50  # Supplier default
    db_session.add_all([product, supplier])
    await db_session.flush()

    # Create condition with explicit MOQ
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100  # Explicit override
    )
    db_session.add(condition)
    await db_session.commit()

    # Should use condition MOQ (100), not supplier default (50)
    effective_moq = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective_moq == 100


@pytest.mark.asyncio
async def test_get_effective_moq_from_supplier_default(db_session, test_client_obj):
    """Test effective MOQ falls back to supplier default when condition doesn't exist"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 75  # Supplier default
    db_session.add_all([product, supplier])
    await db_session.commit()

    # No condition exists - should use supplier default
    effective_moq = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective_moq == 75


@pytest.mark.asyncio
async def test_get_effective_moq_system_default(db_session, test_client_obj):
    """Test effective MOQ falls back to system default (0) when no defaults set"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 0  # No default set
    db_session.add_all([product, supplier])
    await db_session.commit()

    effective_moq = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective_moq == 0


@pytest.mark.asyncio
async def test_get_effective_lead_time_from_condition(db_session, test_client_obj):
    """Test effective lead time uses product-supplier condition when available"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_lead_time_days = 10  # Supplier default
    db_session.add_all([product, supplier])
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        lead_time_days=21  # Explicit override
    )
    db_session.add(condition)
    await db_session.commit()

    effective_lead_time = await service.get_effective_lead_time(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective_lead_time == 21


@pytest.mark.asyncio
async def test_get_effective_lead_time_from_supplier_default(db_session, test_client_obj):
    """Test effective lead time falls back to supplier default"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_lead_time_days = 14
    db_session.add_all([product, supplier])
    await db_session.commit()

    effective_lead_time = await service.get_effective_lead_time(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective_lead_time == 14


@pytest.mark.asyncio
async def test_get_effective_buffer_from_product_override(db_session, test_client_obj):
    """Test effective buffer uses product override when set"""
    from models.settings import ClientSettings

    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = 10  # Product override
    db_session.add(product)

    # Create client settings with default buffer
    settings = ClientSettings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7  # Client default
    )
    db_session.add(settings)
    await db_session.commit()

    effective_buffer = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective_buffer == 10  # Should use product override


@pytest.mark.asyncio
async def test_get_effective_buffer_from_client_settings(db_session, test_client_obj):
    """Test effective buffer falls back to client settings"""
    from models.settings import ClientSettings

    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = None  # No product override
    db_session.add(product)

    settings = ClientSettings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add(settings)
    await db_session.commit()

    effective_buffer = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective_buffer == 7


@pytest.mark.asyncio
async def test_get_effective_buffer_system_default(db_session, test_client_obj):
    """Test effective buffer falls back to system default (7)"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = None
    db_session.add(product)
    await db_session.commit()

    # No client settings - should use system default
    effective_buffer = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective_buffer == 7


# ============================================================================
# Tests for Auto-Population on Product-Supplier Creation
# ============================================================================

@pytest.mark.asyncio
async def test_add_product_supplier_auto_populate_from_supplier_defaults(db_session, test_client_obj):
    """Test that MOQ and lead_time_days are auto-populated from supplier defaults"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add_all([product, supplier])
    await db_session.commit()

    # Add supplier without specifying MOQ/lead_time - should auto-populate
    condition = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=None,  # Not provided - should use supplier.default_moq
        lead_time_days=None,  # Not provided - should use supplier.default_lead_time_days
    )

    assert condition.moq == 100
    assert condition.lead_time_days == 14


@pytest.mark.asyncio
async def test_add_product_supplier_manual_override(db_session, test_client_obj):
    """Test that manual MOQ/lead_time override supplier defaults"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add_all([product, supplier])
    await db_session.commit()

    # Add supplier with explicit values - should override defaults
    condition = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=150,  # Manual override
        lead_time_days=21,  # Manual override
    )

    assert condition.moq == 150  # Should use manual value, not supplier default
    assert condition.lead_time_days == 21


@pytest.mark.asyncio
async def test_add_product_supplier_auto_populate_system_defaults(db_session, test_client_obj):
    """Test that system defaults are used when supplier defaults are 0"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 0  # No default
    supplier.default_lead_time_days = 0  # No default
    db_session.add_all([product, supplier])
    await db_session.commit()

    condition = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=None,
        lead_time_days=None,
    )

    assert condition.moq == 0  # System default
    assert condition.lead_time_days == 14  # System default for lead time

