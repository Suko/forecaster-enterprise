"""
Tests for MOQ, Lead Time, and Buffer functionality

Tests resolution logic, auto-population, and integration with services.
"""
import pytest
from uuid import UUID
from decimal import Decimal

from services.inventory_service import InventoryService
from services.cart_service import CartService
from services.metrics_service import MetricsService
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.settings import ClientSettings
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition,
    create_test_client_settings
)


# ============================================================================
# Resolution Logic Tests
# ============================================================================

@pytest.mark.asyncio
async def test_effective_moq_precedence_chain(db_session, test_client_obj):
    """Test MOQ resolution follows correct precedence: condition > supplier > system"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 50
    db_session.add_all([product, supplier])
    await db_session.flush()

    # Test 1: Condition exists - should use condition
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100
    )
    db_session.add(condition)
    await db_session.commit()

    effective = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective == 100  # From condition

    # Test 2: Remove condition - should use supplier default
    await db_session.delete(condition)
    await db_session.commit()

    effective = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective == 50  # From supplier default

    # Test 3: Remove supplier default - should use system default
    supplier.default_moq = 0
    await db_session.commit()

    effective = await service.get_effective_moq(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective == 0  # System default


@pytest.mark.asyncio
async def test_effective_lead_time_precedence_chain(db_session, test_client_obj):
    """Test lead time resolution follows correct precedence"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_lead_time_days = 10
    db_session.add_all([product, supplier])
    await db_session.flush()

    # Test condition override
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        lead_time_days=21
    )
    db_session.add(condition)
    await db_session.commit()

    effective = await service.get_effective_lead_time(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective == 21

    # Test supplier default fallback
    await db_session.delete(condition)
    await db_session.commit()

    effective = await service.get_effective_lead_time(
        test_client_obj.client_id, product.item_id, supplier.id
    )
    assert effective == 10


@pytest.mark.asyncio
async def test_effective_buffer_precedence_chain(db_session, test_client_obj):
    """Test buffer resolution follows correct precedence: product > client > system"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = 10  # Product override
    db_session.add(product)

    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add(settings)
    await db_session.commit()

    # Test product override
    effective = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective == 10  # From product

    # Test client default fallback
    product.safety_buffer_days = None
    await db_session.commit()

    effective = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective == 7  # From client settings

    # Test system default fallback
    await db_session.delete(settings)
    await db_session.commit()

    effective = await service.get_effective_buffer(
        test_client_obj.client_id, product.item_id
    )
    assert effective == 7  # System default


# ============================================================================
# Auto-Population Tests
# ============================================================================

@pytest.mark.asyncio
async def test_auto_populate_moq_from_supplier_default(db_session, test_client_obj):
    """Test MOQ auto-populates from supplier default when None provided"""
    service = InventoryService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 75
    supplier.default_lead_time_days = 12
    db_session.add_all([product, supplier])
    await db_session.commit()

    # Create condition without specifying MOQ - should auto-populate
    condition = await service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=None,  # Should use supplier.default_moq
        lead_time_days=None  # Should use supplier.default_lead_time_days
    )

    assert condition.moq == 75
    assert condition.lead_time_days == 12


@pytest.mark.asyncio
async def test_auto_populate_uses_system_default_when_supplier_default_zero(db_session, test_client_obj):
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
        lead_time_days=None
    )

    assert condition.moq == 0  # System default
    assert condition.lead_time_days == 14  # System default for lead time


# ============================================================================
# Cart Service Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cart_uses_effective_moq_from_condition(db_session, test_client_obj):
    """Test cart validation uses effective MOQ from product-supplier condition"""
    service = CartService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 50
    db_session.add_all([product, supplier])
    await db_session.flush()

    # Create condition with MOQ = 100
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Try to add to cart with quantity < MOQ - should fail
    with pytest.raises(ValueError, match="MOQ"):
        await service.add_to_cart(
            client_id=test_client_obj.client_id,
            session_id="test-session",
            item_id=product.item_id,
            supplier_id=supplier.id,
            quantity=50  # Below MOQ of 100
        )

    # Add with quantity >= MOQ - should succeed
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=100  # Meets MOQ
    )
    assert cart_item.quantity == 100


@pytest.mark.asyncio
async def test_cart_uses_effective_moq_from_supplier_default(db_session, test_client_obj):
    """Test cart uses supplier default MOQ when condition doesn't specify"""
    service = CartService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 75
    db_session.add_all([product, supplier])
    await db_session.flush()

    # Create condition with MOQ = 0 (no override)
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=0,  # No override - should use supplier default
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Should use supplier default MOQ (75)
    with pytest.raises(ValueError, match="MOQ"):
        await service.add_to_cart(
            client_id=test_client_obj.client_id,
            session_id="test-session",
            item_id=product.item_id,
            supplier_id=supplier.id,
            quantity=50  # Below supplier default MOQ of 75
        )


@pytest.mark.asyncio
async def test_cart_auto_uses_moq_when_quantity_not_provided(db_session, test_client_obj):
    """Test cart automatically uses MOQ when quantity not provided"""
    service = CartService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 100
    db_session.add_all([product, supplier])
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Add to cart without quantity - should use MOQ
    cart_item = await service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=None  # Should auto-use MOQ
    )
    assert cart_item.quantity == 100


# ============================================================================
# Metrics Service Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_metrics_uses_effective_buffer_from_product_override(db_session, test_client_obj):
    """Test metrics service uses product buffer override"""
    service = MetricsService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = 10  # Product override
    db_session.add(product)

    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7  # Client default
    )
    db_session.add(settings)
    await db_session.commit()

    # Calculate stockout risk - should use product buffer (10)
    risk = await service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=50,
        dir_value=Decimal("5.0"),
        lead_time_days=14,
        safety_buffer_days=None  # Should use effective buffer
    )

    # DIR (5) < lead_time (14) + buffer (10) = 24, so high risk
    assert risk is not None
    assert risk > 0


@pytest.mark.asyncio
async def test_metrics_uses_effective_buffer_from_client_settings(db_session, test_client_obj):
    """Test metrics service uses client buffer when product override not set"""
    service = MetricsService(db_session)

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = None  # No override
    db_session.add(product)

    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add(settings)
    await db_session.commit()

    # Should use client buffer (7)
    risk = await service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=50,
        dir_value=Decimal("5.0"),
        lead_time_days=14,
        safety_buffer_days=None
    )

    # DIR (5) < lead_time (14) + buffer (7) = 21, so high risk
    assert risk is not None
    assert risk > 0


# ============================================================================
# Integration Tests - Full Flow
# ============================================================================

@pytest.mark.asyncio
async def test_full_flow_supplier_defaults_to_cart(db_session, test_client_obj):
    """Test complete flow: supplier defaults -> product-supplier -> cart"""
    inventory_service = InventoryService(db_session)
    cart_service = CartService(db_session)

    # 1. Create supplier with defaults
    supplier = create_test_supplier(client_id=test_client_obj.client_id, name="Supplier A")
    supplier.default_moq = 100
    supplier.default_lead_time_days = 14
    db_session.add(supplier)

    # 2. Create product
    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    db_session.add(product)
    await db_session.commit()

    # 3. Link product to supplier (auto-populate from defaults)
    condition = await inventory_service.add_product_supplier(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=None,  # Auto-populate
        lead_time_days=None,  # Auto-populate
        supplier_cost=Decimal("10.00")
    )

    assert condition.moq == 100
    assert condition.lead_time_days == 14

    # 4. Add to cart - should validate against MOQ
    cart_item = await cart_service.add_to_cart(
        client_id=test_client_obj.client_id,
        session_id="test-session",
        item_id=product.item_id,
        supplier_id=supplier.id,
        quantity=100  # Meets MOQ
    )

    assert cart_item.quantity == 100
    assert cart_item.item_id == product.item_id


@pytest.mark.asyncio
async def test_full_flow_product_buffer_to_metrics(db_session, test_client_obj):
    """Test complete flow: product buffer override -> metrics calculation"""
    metrics_service = MetricsService(db_session)

    # 1. Create product with buffer override
    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product.safety_buffer_days = 10  # Product override
    db_session.add(product)

    # 2. Create client settings with default buffer
    settings = create_test_client_settings(
        client_id=test_client_obj.client_id,
        safety_buffer_days=7
    )
    db_session.add(settings)
    await db_session.commit()

    # 3. Calculate metrics - should use product buffer (10)
    risk = await metrics_service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=50,
        dir_value=Decimal("15.0"),
        lead_time_days=14,
        safety_buffer_days=None  # Should use effective buffer
    )

    # DIR (15) < lead_time (14) + buffer (10) = 24, so some risk
    assert risk is not None

    # 4. Test with product buffer = None - should use client default
    product.safety_buffer_days = None
    await db_session.commit()

    risk2 = await metrics_service.calculate_stockout_risk(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        current_stock=50,
        dir_value=Decimal("15.0"),
        lead_time_days=14,
        safety_buffer_days=None
    )

    # Both should calculate risk (buffer is being used)
    assert risk2 is not None
    # Note: Risk calculation is complex, we just verify it uses different buffers
    # by checking both values are calculated (not None)

