"""
Cart Service Tests

Tests for CartService - business-critical service that manages:
1. Adding items to cart with MOQ validation
2. Cart item updates with quantity validation
3. Multi-tenant isolation for cart data
4. Cart → Purchase Order flow
"""
import pytest
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.cart_service import CartService
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition,
)


# ============================================================================
# add_to_cart Tests
# ============================================================================


@pytest.mark.asyncio
async def test_add_to_cart_success(db_session: AsyncSession, test_client_obj):
    """Test adding item to cart successfully"""
    service = CartService(db_session)
    
    # Create product, supplier, and condition
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-001",
        unit_cost=Decimal("25.00")
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier",
        default_moq=10
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-001",
        supplier_id=supplier.id,
        moq=10,
        lead_time_days=7
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add to cart
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-001",
        supplier_id=supplier.id,
        quantity=20
    )
    
    assert cart_item is not None
    assert cart_item.item_id == "CART-001"
    assert cart_item.quantity == 20
    # unit_cost comes from condition.supplier_cost (10.00) not product.unit_cost (25.00)
    assert cart_item.unit_cost == Decimal("10.00")
    assert cart_item.total_price == Decimal("200.00")


@pytest.mark.asyncio
async def test_add_to_cart_uses_moq_when_no_quantity(db_session: AsyncSession, test_client_obj):
    """Test that cart uses MOQ when no quantity is provided"""
    service = CartService(db_session)
    
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-MOQ-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="MOQ Supplier",
        default_moq=50
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-MOQ-001",
        supplier_id=supplier.id,
        moq=50
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add without specifying quantity
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-MOQ-001",
        supplier_id=supplier.id,
        quantity=None  # Should use MOQ
    )
    
    assert cart_item.quantity == 50


@pytest.mark.asyncio
async def test_add_to_cart_below_moq_fails(db_session: AsyncSession, test_client_obj):
    """Test that adding below MOQ raises an error"""
    service = CartService(db_session)
    
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-MOQ-FAIL"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Strict MOQ Supplier",
        default_moq=100
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-MOQ-FAIL",
        supplier_id=supplier.id,
        moq=100
    )
    db_session.add(condition)
    await db_session.commit()
    
    with pytest.raises(ValueError, match="less than MOQ"):
        await service.add_to_cart(
            client_id=test_client_obj.client_id,
            session_id="test-session",
            item_id="CART-MOQ-FAIL",
            supplier_id=supplier.id,
            quantity=50  # Below MOQ of 100
        )


@pytest.mark.asyncio
async def test_add_to_cart_product_not_found(db_session: AsyncSession, test_client_obj):
    """Test that adding non-existent product raises error"""
    service = CartService(db_session)
    
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add(supplier)
    await db_session.commit()
    
    with pytest.raises(ValueError, match="not found"):
        await service.add_to_cart(
            client_id=test_client_obj.client_id,
            session_id="test-session",
            item_id="NONEXISTENT-001",
            supplier_id=supplier.id,
            quantity=10
        )


@pytest.mark.asyncio
async def test_add_to_cart_updates_existing_item(db_session: AsyncSession, test_client_obj):
    """Test that adding same item again updates quantity"""
    service = CartService(db_session)
    
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-UPDATE-001",
        unit_cost=Decimal("10.00")
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Update Supplier",
        default_moq=5
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-UPDATE-001",
        supplier_id=supplier.id,
        moq=5
    )
    db_session.add(condition)
    await db_session.commit()
    
    # First add
    cart_item1 = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-UPDATE-001",
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Second add (should update)
    cart_item2 = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-UPDATE-001",
        supplier_id=supplier.id,
        quantity=20
    )
    
    assert cart_item1.id == cart_item2.id
    assert cart_item2.quantity == 20
    assert cart_item2.total_price == Decimal("200.00")


# ============================================================================
# get_cart Tests
# ============================================================================


@pytest.mark.asyncio
async def test_get_cart_empty(db_session: AsyncSession, test_client_obj):
    """Test getting empty cart"""
    service = CartService(db_session)
    
    items = await service.get_cart(
        client_id=test_client_obj.client_id,
        session_id="empty-session"
    )
    
    assert items == []


@pytest.mark.asyncio
async def test_get_cart_multi_tenant_isolation(db_session: AsyncSession, test_client_obj):
    """Test that cart only returns items for the correct client"""
    service = CartService(db_session)
    
    # Create product and supplier for test client
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-TENANT-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Tenant Supplier"
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-TENANT-001",
        supplier_id=supplier.id
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add item to cart
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="shared-session",
        item_id="CART-TENANT-001",
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Create another client and try to access
    from models.client import Client
    other_client = Client(name="Other Client")
    db_session.add(other_client)
    await db_session.commit()
    
    # Other client should see empty cart
    other_items = await service.get_cart(
        client_id=other_client.client_id,
        session_id="shared-session"  # Same session ID
    )
    
    assert len(other_items) == 0
    
    # Original client should still see their item
    items = await service.get_cart(
        client_id=test_client_obj.client_id,
        session_id="shared-session"
    )
    
    assert len(items) == 1


# ============================================================================
# remove_from_cart Tests
# ============================================================================


@pytest.mark.asyncio
async def test_remove_from_cart_success(db_session: AsyncSession, test_client_obj):
    """Test removing item from cart"""
    service = CartService(db_session)
    
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-REMOVE-001"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Remove Supplier"
    )
    db_session.add_all([product, supplier])
    await db_session.flush()
    
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-REMOVE-001",
        supplier_id=supplier.id
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add item
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-REMOVE-001",
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Verify it's in cart
    items = await service.get_cart(test_client_obj.client_id, "test-session")
    assert len(items) == 1
    
    # Remove it
    removed = await service.remove_from_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-REMOVE-001",
        supplier_id=supplier.id
    )
    
    assert removed is True
    
    # Verify cart is empty
    items = await service.get_cart(test_client_obj.client_id, "test-session")
    assert len(items) == 0


@pytest.mark.asyncio
async def test_remove_nonexistent_item_returns_false(db_session: AsyncSession, test_client_obj):
    """Test removing non-existent item returns False"""
    service = CartService(db_session)
    
    from uuid import uuid4
    
    removed = await service.remove_from_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="NONEXISTENT-001",
        supplier_id=uuid4()
    )
    
    assert removed is False


# ============================================================================
# clear_cart Tests
# ============================================================================


@pytest.mark.asyncio
async def test_clear_cart(db_session: AsyncSession, test_client_obj):
    """Test clearing entire cart"""
    service = CartService(db_session)
    
    # Create 2 products
    product1 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-CLEAR-001"
    )
    product2 = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="CART-CLEAR-002"
    )
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Clear Supplier"
    )
    db_session.add_all([product1, product2, supplier])
    await db_session.flush()
    
    condition1 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-CLEAR-001",
        supplier_id=supplier.id
    )
    condition2 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id="CART-CLEAR-002",
        supplier_id=supplier.id
    )
    db_session.add_all([condition1, condition2])
    await db_session.commit()
    
    # Add both items
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-CLEAR-001",
        supplier_id=supplier.id,
        quantity=10
    )
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id="CART-CLEAR-002",
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Verify items in cart
    items = await service.get_cart(test_client_obj.client_id, "test-session")
    assert len(items) == 2
    
    # Clear cart
    count = await service.clear_cart(test_client_obj.client_id, "test-session")
    
    assert count == 2
    
    # Verify cart is empty
    items = await service.get_cart(test_client_obj.client_id, "test-session")
    assert len(items) == 0
