"""
Tests for Supplier Update with apply_to_existing functionality
"""
import pytest
from uuid import UUID
from decimal import Decimal

from services.supplier_service import SupplierService
from models.product_supplier import ProductSupplierCondition
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition
)


@pytest.mark.asyncio
async def test_update_supplier_defaults_without_apply(db_session, test_client_obj):
    """Test updating supplier defaults without applying to existing products"""
    service = SupplierService(db_session)

    # Create supplier with defaults
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A",
        default_moq=100,
        default_lead_time_days=14
    )
    db_session.add(supplier)
    await db_session.flush()

    # Create product-supplier condition using supplier defaults
    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    db_session.add(product)
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100,  # Matches supplier default
        lead_time_days=14,  # Matches supplier default
    )
    db_session.add(condition)
    await db_session.commit()

    # Update supplier defaults without applying
    updated = await service.update_supplier(
        client_id=test_client_obj.client_id,
        supplier_id=supplier.id,
        default_moq=150,
        default_lead_time_days=21,
        apply_to_existing=False,
    )

    assert updated.default_moq == 150
    assert updated.default_lead_time_days == 21

    # Condition should remain unchanged
    await db_session.refresh(condition)
    assert condition.moq == 100  # Old value
    assert condition.lead_time_days == 14  # Old value


@pytest.mark.asyncio
async def test_update_supplier_defaults_with_apply(db_session, test_client_obj):
    """Test updating supplier defaults and applying to existing products that match"""
    service = SupplierService(db_session)

    # Create supplier with defaults
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A",
        default_moq=100,
        default_lead_time_days=14
    )
    db_session.add(supplier)
    await db_session.flush()

    # Create products
    product1 = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    product2 = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-002")
    product3 = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-003")
    db_session.add_all([product1, product2, product3])
    await db_session.flush()

    # Condition 1: Uses supplier default MOQ (should be updated)
    condition1 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product1.item_id,
        supplier_id=supplier.id,
        moq=100,  # Matches supplier default
        lead_time_days=14,  # Matches supplier default
    )

    # Condition 2: Uses supplier default MOQ but different lead time (MOQ should be updated)
    condition2 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product2.item_id,
        supplier_id=supplier.id,
        moq=100,  # Matches supplier default
        lead_time_days=21,  # Explicit override - should NOT be updated
    )

    # Condition 3: Explicit override for both (should NOT be updated)
    condition3 = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product3.item_id,
        supplier_id=supplier.id,
        moq=200,  # Explicit override - should NOT be updated
        lead_time_days=30,  # Explicit override - should NOT be updated
    )

    db_session.add_all([condition1, condition2, condition3])
    await db_session.commit()

    # Update supplier defaults and apply to existing
    updated = await service.update_supplier(
        client_id=test_client_obj.client_id,
        supplier_id=supplier.id,
        default_moq=150,
        default_lead_time_days=21,
        apply_to_existing=True,
    )

    assert updated.default_moq == 150
    assert updated.default_lead_time_days == 21

    # Refresh conditions
    await db_session.refresh(condition1)
    await db_session.refresh(condition2)
    await db_session.refresh(condition3)

    # Condition 1: Both should be updated (matched old defaults)
    assert condition1.moq == 150
    assert condition1.lead_time_days == 21

    # Condition 2: MOQ updated (matched), lead time unchanged (was override)
    assert condition2.moq == 150
    assert condition2.lead_time_days == 21  # This matched old default, so updated

    # Condition 3: Both unchanged (were explicit overrides)
    assert condition3.moq == 200
    assert condition3.lead_time_days == 30


@pytest.mark.asyncio
async def test_update_only_moq_with_apply(db_session, test_client_obj):
    """Test updating only MOQ and applying to existing products"""
    service = SupplierService(db_session)

    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A",
        default_moq=100,
        default_lead_time_days=14
    )
    db_session.add(supplier)
    await db_session.flush()

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    db_session.add(product)
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100,  # Matches supplier default
        lead_time_days=14,  # Matches supplier default
    )
    db_session.add(condition)
    await db_session.commit()

    # Update only MOQ
    updated = await service.update_supplier(
        client_id=test_client_obj.client_id,
        supplier_id=supplier.id,
        default_moq=150,
        apply_to_existing=True,
    )

    assert updated.default_moq == 150
    assert updated.default_lead_time_days == 14  # Unchanged

    await db_session.refresh(condition)
    assert condition.moq == 150  # Updated
    assert condition.lead_time_days == 14  # Unchanged (wasn't in update)


@pytest.mark.asyncio
async def test_update_only_lead_time_with_apply(db_session, test_client_obj):
    """Test updating only lead time and applying to existing products"""
    service = SupplierService(db_session)

    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Supplier A",
        default_moq=100,
        default_lead_time_days=14
    )
    db_session.add(supplier)
    await db_session.flush()

    product = create_test_product(client_id=test_client_obj.client_id, item_id="TEST-001")
    db_session.add(product)
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        moq=100,  # Matches supplier default
        lead_time_days=14,  # Matches supplier default
    )
    db_session.add(condition)
    await db_session.commit()

    # Update only lead time
    updated = await service.update_supplier(
        client_id=test_client_obj.client_id,
        supplier_id=supplier.id,
        default_lead_time_days=21,
        apply_to_existing=True,
    )

    assert updated.default_moq == 100  # Unchanged
    assert updated.default_lead_time_days == 21

    await db_session.refresh(condition)
    assert condition.moq == 100  # Unchanged (wasn't in update)
    assert condition.lead_time_days == 21  # Updated

