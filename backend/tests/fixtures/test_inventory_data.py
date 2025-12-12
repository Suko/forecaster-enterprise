"""
Test Fixtures for Inventory Management

Reusable test data factories for unit tests.
"""
import uuid
from decimal import Decimal
from datetime import date, timedelta
from typing import Optional, List

from models.product import Product
from models.location import Location
from models.stock import StockLevel
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.settings import ClientSettings


def create_test_product(
    client_id: uuid.UUID,
    item_id: str,
    product_name: Optional[str] = None,
    category: str = "Test Category",
    unit_cost: Decimal = Decimal("10.00"),
    safety_buffer_days: Optional[int] = None
) -> Product:
    """Factory function to create a test product"""
    return Product(
        client_id=client_id,
        item_id=item_id,
        sku=item_id,
        product_name=product_name or f"Test Product {item_id}",
        category=category,
        unit_cost=unit_cost,
        safety_buffer_days=safety_buffer_days
    )


def create_test_location(
    client_id: uuid.UUID,
    location_id: str = "TEST-LOC-001",
    name: str = "Test Location",
    city: str = "Test City",
    country: str = "Test Country"
) -> Location:
    """Factory function to create a test location"""
    return Location(
        client_id=client_id,
        location_id=location_id,
        name=name,
        city=city,
        country=country,
        is_synced=False
    )


def create_test_supplier(
    client_id: uuid.UUID,
    name: str = "Test Supplier",
    contact_email: str = "test@supplier.com",
    supplier_type: str = "PO",
    default_moq: int = 0,
    default_lead_time_days: int = 14
) -> Supplier:
    """Factory function to create a test supplier"""
    return Supplier(
        client_id=client_id,
        name=name,
        contact_email=contact_email,
        supplier_type=supplier_type,
        default_moq=default_moq,
        default_lead_time_days=default_lead_time_days,
        is_synced=False
    )


def create_test_stock_level(
    client_id: uuid.UUID,
    item_id: str,
    location_id: str = "TEST-LOC-001",
    current_stock: int = 100
) -> StockLevel:
    """Factory function to create a test stock level"""
    return StockLevel(
        client_id=client_id,
        item_id=item_id,
        location_id=location_id,
        current_stock=current_stock
    )


def create_test_product_supplier_condition(
    client_id: uuid.UUID,
    item_id: str,
    supplier_id: uuid.UUID,
    moq: int = 10,
    lead_time_days: int = 14,
    supplier_cost: Decimal = Decimal("10.00"),
    is_primary: bool = True
) -> ProductSupplierCondition:
    """Factory function to create a test product-supplier condition"""
    return ProductSupplierCondition(
        client_id=client_id,
        item_id=item_id,
        supplier_id=supplier_id,
        moq=moq,
        lead_time_days=lead_time_days,
        supplier_cost=supplier_cost,
        packaging_unit="box",
        packaging_qty=12,
        is_primary=is_primary
    )


def create_test_client_settings(
    client_id: uuid.UUID,
    safety_buffer_days: int = 7,
    understocked_threshold: int = 14,
    overstocked_threshold: int = 90,
    dead_stock_days: int = 90
) -> ClientSettings:
    """Factory function to create test client settings"""
    return ClientSettings(
        client_id=client_id,
        safety_buffer_days=safety_buffer_days,
        understocked_threshold=understocked_threshold,
        overstocked_threshold=overstocked_threshold,
        dead_stock_days=dead_stock_days,
        recommendation_rules={
            "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
            "role_rules": {
                "CEO": ["URGENT", "DEAD_STOCK"],
                "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
                "MARKETING": ["PROMOTE", "DEAD_STOCK"]
            },
            "min_inventory_value": 0,
            "min_risk_score": 0
        }
    )


def create_test_inventory_data_batch(
    client_id: uuid.UUID,
    num_products: int = 5,
    num_locations: int = 2,
    num_suppliers: int = 2
) -> dict:
    """
    Create a batch of test inventory data for integration tests.

    Returns:
        dict with:
            - products: List[Product]
            - locations: List[Location]
            - suppliers: List[Supplier]
            - stock_levels: List[StockLevel]
            - conditions: List[ProductSupplierCondition]
            - settings: ClientSettings
    """
    products = []
    locations = []
    suppliers = []
    stock_levels = []
    conditions = []

    # Create products
    for i in range(num_products):
        item_id = f"TEST-ITEM-{i+1:03d}"
        products.append(create_test_product(
            client_id=client_id,
            item_id=item_id,
            category=f"Category {i % 3 + 1}",
            unit_cost=Decimal(f"{(i * 10) + 10}.00")
        ))

    # Create locations
    for i in range(num_locations):
        locations.append(create_test_location(
            client_id=client_id,
            location_id=f"TEST-LOC-{i+1:03d}",
            name=f"Test Location {i+1}"
        ))

    # Create suppliers
    for i in range(num_suppliers):
        suppliers.append(create_test_supplier(
            client_id=client_id,
            name=f"Test Supplier {i+1}",
            contact_email=f"supplier{i+1}@test.com"
        ))

    # Create stock levels (one per product per location)
    for product in products:
        for location in locations:
            stock_levels.append(create_test_stock_level(
                client_id=client_id,
                item_id=product.item_id,
                location_id=location.location_id,
                current_stock=(hash(f"{product.item_id}{location.location_id}") % 500)
            ))

    # Create product-supplier conditions (link each product to first supplier)
    if suppliers:
        for product in products:
            conditions.append(create_test_product_supplier_condition(
                client_id=client_id,
                item_id=product.item_id,
                supplier_id=suppliers[0].id if hasattr(suppliers[0], 'id') else uuid.uuid4(),
                moq=10,
                lead_time_days=14,
                is_primary=True
            ))

    # Create settings
    settings = create_test_client_settings(client_id=client_id)

    return {
        "products": products,
        "locations": locations,
        "suppliers": suppliers,
        "stock_levels": stock_levels,
        "conditions": conditions,
        "settings": settings
    }

