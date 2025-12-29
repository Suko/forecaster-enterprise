"""
Unit tests for PurchaseOrderService

Tests purchase order creation, listing, status updates.
"""
import pytest
from uuid import UUID
from decimal import Decimal
from datetime import date, timedelta

from services.purchase_order_service import PurchaseOrderService
from models.product import Product
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.order_cart import OrderCartItem
from schemas.order import PurchaseOrderCreate, PurchaseOrderItemCreate
from tests.fixtures.test_inventory_data import (
    create_test_product,
    create_test_supplier,
    create_test_product_supplier_condition
)


@pytest.mark.asyncio
async def test_create_purchase_order(db_session, test_client_obj):
    """Test creating purchase order from items"""
    service = PurchaseOrderService(db_session)

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
    await db_session.flush()

    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Create PO
    po_data = PurchaseOrderCreate(
        supplier_id=supplier.id,
        items=[
            PurchaseOrderItemCreate(
                item_id=product.item_id,
                quantity=10,
                unit_cost=Decimal("10.00")
            )
        ]
    )

    po = await service.create_purchase_order(
        client_id=test_client_obj.client_id,
        data=po_data,
        created_by="test@example.com"
    )

    assert po is not None
    assert po.status == "pending"
    assert po.supplier_id == supplier.id
    assert po.total_amount == Decimal("100.00")  # 10 * 10.00


@pytest.mark.asyncio
async def test_get_purchase_orders(db_session, test_client_obj):
    """Test listing purchase orders"""
    service = PurchaseOrderService(db_session)

    # Create supplier
    supplier = create_test_supplier(
        client_id=test_client_obj.client_id,
        name="Test Supplier"
    )
    db_session.add(supplier)
    await db_session.commit()

    # Create product first
    product = create_test_product(
        client_id=test_client_obj.client_id,
        item_id="TEST-001",
        unit_cost=Decimal("10.00")
    )
    db_session.add(product)
    await db_session.commit()

    # Create product-supplier condition
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Create multiple POs
    for i in range(3):
        po_data = PurchaseOrderCreate(
            supplier_id=supplier.id,
            items=[
                PurchaseOrderItemCreate(
                    item_id=product.item_id,
                    quantity=10 + i,
                    unit_cost=Decimal("10.00")
                )
            ]
        )
        po = await service.create_purchase_order(
            client_id=test_client_obj.client_id,
            data=po_data,
            created_by="test@example.com"
        )

    # List POs
    pos = await service.get_purchase_orders(
        client_id=test_client_obj.client_id
    )

    assert len(pos) >= 3


@pytest.mark.asyncio
async def test_update_po_status(db_session, test_client_obj):
    """Test updating purchase order status"""
    service = PurchaseOrderService(db_session)

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

    # Create product-supplier condition
    condition = create_test_product_supplier_condition(
        client_id=test_client_obj.client_id,
        item_id=product.item_id,
        supplier_id=supplier.id,
        supplier_cost=Decimal("10.00")
    )
    db_session.add(condition)
    await db_session.commit()

    # Create PO with items
    po_data = PurchaseOrderCreate(
        supplier_id=supplier.id,
        items=[
            PurchaseOrderItemCreate(
                item_id=product.item_id,
                quantity=10,
                unit_cost=Decimal("10.00")
            )
        ]
    )

    po = await service.create_purchase_order(
        client_id=test_client_obj.client_id,
        data=po_data,
        created_by="test@example.com"
    )

    assert po.status == "pending"

    # Update status
    updated = await service.update_purchase_order_status(
        client_id=test_client_obj.client_id,
        po_id=po.id,
        status="confirmed"
    )

    assert updated.status == "confirmed"

