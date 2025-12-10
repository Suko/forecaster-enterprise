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

