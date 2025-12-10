"""
Unit tests for CartService

Tests cart operations: add, get, update, remove, clear.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from services.cart_service import CartService
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition
)


@pytest.mark.asyncio
async def test_add_to_cart(db_session, test_client_obj):
    """Test adding item to cart"""
    service = CartService(db_session)
    
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
        supplier_id=supplier.id,
        moq=10
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add to cart
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=20
    )
    
    assert cart_item is not None
    assert cart_item.quantity == 20
    assert cart_item.item_id == product.item_id


@pytest.mark.asyncio
async def test_add_to_cart_below_moq(db_session, test_client_obj):
    """Test adding item below MOQ (should fail)"""
    service = CartService(db_session)
    
    # Create product and supplier with MOQ
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
        supplier_id=supplier.id,
        moq=10  # MOQ is 10
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Try to add below MOQ
    with pytest.raises(ValueError, match="MOQ"):
        await service.add_to_cart(
            client_id=test_client_obj.client_id,
            session_id="test-session",
            item_id=product.item_id,
            supplier_id=supplier.id,
            quantity=5  # Below MOQ
        )


@pytest.mark.asyncio
async def test_get_cart(db_session, test_client_obj):
    """Test getting cart items"""
    service = CartService(db_session)
    
    # Create products and suppliers
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
    db_session.add_all([product1, product2, supplier])
    await db_session.flush()
    
    # Add conditions
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
    db_session.add_all([condition1, condition2])
    await db_session.commit()
    
    # Add items to cart
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product1.item_id,
        supplier_id=supplier.id,
        quantity=10
    )
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product2.item_id,
        supplier_id=supplier.id,
        quantity=20
    )
    
    # Get cart
    cart_items = await service.get_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session"
    )
    
    assert len(cart_items) == 2


@pytest.mark.asyncio
async def test_update_cart_item(db_session, test_client_obj):
    """Test updating cart item quantity"""
    service = CartService(db_session)
    
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
        supplier_id=supplier.id,
        moq=10
    )
    db_session.add(condition)
    await db_session.commit()
    
    # Add to cart
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Update quantity
    updated = await service.update_cart_item(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        quantity=30
    )
    
    assert updated.quantity == 30


@pytest.mark.asyncio
async def test_remove_from_cart(db_session, test_client_obj):
    """Test removing item from cart"""
    service = CartService(db_session)
    
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
    
    # Add to cart
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=10
    )
    
    # Remove from cart
    await service.remove_from_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id
    )
    
    # Verify removed
    cart_items = await service.get_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session"
    )
    
    assert len(cart_items) == 0


@pytest.mark.asyncio
async def test_clear_cart(db_session, test_client_obj):
    """Test clearing entire cart"""
    service = CartService(db_session)
    
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
    db_session.add_all([product1, product2, supplier])
    await db_session.flush()
    
    # Add conditions
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
    db_session.add_all([condition1, condition2])
    await db_session.commit()
    
    # Add items to cart
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product1.item_id,
        supplier_id=supplier.id,
        quantity=10
    )
    await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product2.item_id,
        supplier_id=supplier.id,
        quantity=20
    )
    
    # Clear cart
    await service.clear_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session"
    )
    
    # Verify cleared
    cart_items = await service.get_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session"
    )
    
    assert len(cart_items) == 0

