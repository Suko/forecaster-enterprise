#!/usr/bin/env python3
"""
Setup Test Data for Inventory Management

Creates test data for MVP development:
- Products (from existing ts_demand_daily item_ids)
- Locations
- Suppliers
- Product-Supplier conditions (MOQ, lead time)
- Stock levels
- Client settings

Usage:
    uv run python backend/scripts/setup_test_data.py \
        [--client-id <uuid>] \
        [--client-name "Demo Client"] \
        [--clear-existing]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional, List
import uuid
from datetime import date, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from models.product import Product
from models.location import Location
from models.stock import StockLevel
from models.supplier import Supplier
from models.product_supplier import ProductSupplierCondition
from models.settings import ClientSettings
from sqlalchemy import select, text


async def get_or_create_client(client_id: Optional[str] = None, client_name: str = "Demo Client") -> str:
    """Get existing client or create new one"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if client_id:
            result = await session.execute(
                select(Client).where(Client.client_id == uuid.UUID(client_id))
            )
            client = result.scalar_one_or_none()
            if client:
                print(f"Using existing client: {client.name} ({client.client_id})")
                return str(client.client_id)
            else:
                raise ValueError(f"Client with ID {client_id} not found")
        
        # Check if client with this name exists
        result = await session.execute(
            select(Client).where(Client.name == client_name)
        )
        existing_client = result.scalar_one_or_none()
        
        if existing_client:
            print(f"Using existing client: {existing_client.name} ({existing_client.client_id})")
            return str(existing_client.client_id)
        
        # Create new client
        new_client = Client(
            name=client_name,
            timezone="UTC",
            currency="EUR",
            is_active=True
        )
        session.add(new_client)
        await session.commit()
        await session.refresh(new_client)
        
        print(f"Created new client: {new_client.name} ({new_client.client_id})")
        return str(new_client.client_id)


async def get_existing_item_ids(client_id: str) -> List[str]:
    """Get item_ids from existing ts_demand_daily data"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT DISTINCT item_id 
                FROM ts_demand_daily 
                WHERE client_id = :client_id
                ORDER BY item_id
                LIMIT 50
            """),
            {"client_id": client_id}
        )
        item_ids = [row[0] for row in result.fetchall()]
        return item_ids


async def create_products(client_id: str, item_ids: List[str], clear_existing: bool = False) -> int:
    """Create products from item_ids"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if clear_existing:
            await session.execute(
                text("DELETE FROM products WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
        
        created = 0
        categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Food", "Health"]
        
        for idx, item_id in enumerate(item_ids):
            # Check if product already exists
            result = await session.execute(
                select(Product).where(
                    Product.client_id == uuid.UUID(client_id),
                    Product.item_id == item_id
                )
            )
            if result.scalar_one_or_none():
                continue
            
            product = Product(
                client_id=uuid.UUID(client_id),
                item_id=item_id,
                sku=item_id,  # Use item_id as sku alias
                product_name=f"Product {item_id}",
                category=categories[idx % len(categories)],
                unit_cost=Decimal(f"{(idx % 100) + 10}.99")  # Random cost between 10.99 and 109.99
            )
            session.add(product)
            created += 1
        
        await session.commit()
        print(f"Created {created} products")
        return created


async def create_locations(client_id: str, clear_existing: bool = False) -> int:
    """Create sample locations"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if clear_existing:
            await session.execute(
                text("DELETE FROM locations WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
        
        locations_data = [
            {"location_id": "WH-001", "name": "Main Warehouse", "city": "Ljubljana", "country": "Slovenia"},
            {"location_id": "WH-002", "name": "Secondary Warehouse", "city": "Maribor", "country": "Slovenia"},
            {"location_id": "STORE-001", "name": "Retail Store 1", "city": "Ljubljana", "country": "Slovenia"},
        ]
        
        created = 0
        for loc_data in locations_data:
            result = await session.execute(
                select(Location).where(
                    Location.client_id == uuid.UUID(client_id),
                    Location.location_id == loc_data["location_id"]
                )
            )
            if result.scalar_one_or_none():
                continue
            
            location = Location(
                client_id=uuid.UUID(client_id),
                location_id=loc_data["location_id"],
                name=loc_data["name"],
                city=loc_data["city"],
                country=loc_data["country"],
                is_synced=False
            )
            session.add(location)
            created += 1
        
        await session.commit()
        print(f"Created {created} locations")
        return created


async def create_suppliers(client_id: str, clear_existing: bool = False) -> int:
    """Create sample suppliers"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if clear_existing:
            await session.execute(
                text("DELETE FROM suppliers WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
        
        suppliers_data = [
            {"name": "Supplier A", "contact_email": "contact@supplier-a.com", "supplier_type": "PO"},
            {"name": "Supplier B", "contact_email": "info@supplier-b.com", "supplier_type": "PO"},
            {"name": "Supplier C", "contact_email": "sales@supplier-c.com", "supplier_type": "PO"},
            {"name": "Manufacturing Partner", "contact_email": "prod@manufacturing.com", "supplier_type": "WO"},
        ]
        
        created = 0
        supplier_ids = {}
        
        for supp_data in suppliers_data:
            result = await session.execute(
                select(Supplier).where(
                    Supplier.client_id == uuid.UUID(client_id),
                    Supplier.name == supp_data["name"]
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                supplier_ids[supp_data["name"]] = existing.id
                continue
            
            supplier = Supplier(
                client_id=uuid.UUID(client_id),
                name=supp_data["name"],
                contact_email=supp_data["contact_email"],
                supplier_type=supp_data["supplier_type"],
                is_synced=False
            )
            session.add(supplier)
            await session.flush()
            supplier_ids[supp_data["name"]] = supplier.id
            created += 1
        
        await session.commit()
        print(f"Created {created} suppliers")
        return supplier_ids


async def create_product_supplier_conditions(
    client_id: str, 
    item_ids: List[str], 
    supplier_ids: dict,
    clear_existing: bool = False
) -> int:
    """Link products to suppliers with MOQ and lead time"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if clear_existing:
            await session.execute(
                text("DELETE FROM product_supplier_conditions WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
        
        created = 0
        supplier_names = list(supplier_ids.keys())
        
        for idx, item_id in enumerate(item_ids):
            # Assign each product to 1-2 suppliers
            num_suppliers = 1 if idx % 3 == 0 else 2
            selected_suppliers = supplier_names[:num_suppliers]
            
            for supp_idx, supp_name in enumerate(selected_suppliers):
                supplier_id = supplier_ids[supp_name]
                
                # Check if condition already exists
                result = await session.execute(
                    select(ProductSupplierCondition).where(
                        ProductSupplierCondition.client_id == uuid.UUID(client_id),
                        ProductSupplierCondition.item_id == item_id,
                        ProductSupplierCondition.supplier_id == supplier_id
                    )
                )
                if result.scalar_one_or_none():
                    continue
                
                condition = ProductSupplierCondition(
                    client_id=uuid.UUID(client_id),
                    item_id=item_id,
                    supplier_id=supplier_id,
                    moq=(idx % 10 + 1) * 10,  # MOQ between 10 and 100
                    lead_time_days=(idx % 14 + 7),  # Lead time between 7 and 21 days
                    supplier_cost=Decimal(f"{(idx % 50) + 5}.00"),
                    packaging_unit="box",
                    packaging_qty=12,
                    is_primary=(supp_idx == 0)  # First supplier is primary
                )
                session.add(condition)
                created += 1
        
        await session.commit()
        print(f"Created {created} product-supplier conditions")
        return created


async def create_stock_levels(
    client_id: str, 
    item_ids: List[str], 
    location_ids: List[str],
    clear_existing: bool = False
) -> int:
    """Create sample stock levels"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        if clear_existing:
            await session.execute(
                text("DELETE FROM stock_levels WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            await session.commit()
        
        created = 0
        
        for item_id in item_ids:
            for location_id in location_ids:
                # Check if stock level already exists
                result = await session.execute(
                    select(StockLevel).where(
                        StockLevel.client_id == uuid.UUID(client_id),
                        StockLevel.item_id == item_id,
                        StockLevel.location_id == location_id
                    )
                )
                if result.scalar_one_or_none():
                    continue
                
                # Random stock between 0 and 500
                stock = (hash(f"{item_id}{location_id}") % 500)
                
                stock_level = StockLevel(
                    client_id=uuid.UUID(client_id),
                    item_id=item_id,
                    location_id=location_id,
                    current_stock=stock
                )
                session.add(stock_level)
                created += 1
        
        await session.commit()
        print(f"Created {created} stock level records")
        return created


async def create_client_settings(client_id: str, clear_existing: bool = False) -> bool:
    """Create or update client settings"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(ClientSettings).where(ClientSettings.client_id == uuid.UUID(client_id))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            if not clear_existing:
                print("Client settings already exist, skipping")
                return False
            # Update existing
            existing.safety_buffer_days = 7
            existing.understocked_threshold = 14
            existing.overstocked_threshold = 90
            existing.dead_stock_days = 90
            existing.recommendation_rules = {
                "enabled_types": ["REORDER", "REDUCE_ORDER", "PROMOTE", "DEAD_STOCK", "URGENT"],
                "role_rules": {
                    "CEO": ["URGENT", "DEAD_STOCK"],
                    "PROCUREMENT": ["REORDER", "REDUCE_ORDER", "URGENT"],
                    "MARKETING": ["PROMOTE", "DEAD_STOCK"]
                },
                "min_inventory_value": 0,
                "min_risk_score": 0
            }
        else:
            # Create new
            settings = ClientSettings(
                client_id=uuid.UUID(client_id),
                safety_buffer_days=7,
                understocked_threshold=14,
                overstocked_threshold=90,
                dead_stock_days=90,
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
            session.add(settings)
        
        await session.commit()
        print("Created/updated client settings")
        return True


async def setup_test_data(
    client_id: Optional[str] = None,
    client_name: str = "Demo Client",
    clear_existing: bool = False,
    days_back: int = 30,
    skip_recent_sales: bool = False
) -> dict:
    """Complete test data setup"""
    print("="*60)
    print("Setting up Test Data for Inventory Management")
    print("="*60)
    
    # Step 1: Get or create client
    print(f"\n1. Getting/creating client...")
    client_id = await get_or_create_client(client_id, client_name)
    
    # Step 2: Get existing item_ids from ts_demand_daily
    print(f"\n2. Getting item_ids from ts_demand_daily...")
    item_ids = await get_existing_item_ids(client_id)
    if not item_ids:
        print("⚠️  WARNING: No item_ids found in ts_demand_daily. Please import sales data first.")
        print("   Run: python backend/scripts/import_csv_to_ts_demand_daily.py")
        return {"error": "No item_ids found"}
    
    print(f"   Found {len(item_ids)} item_ids")
    
    # Step 3: Create products
    print(f"\n3. Creating products...")
    products_created = await create_products(client_id, item_ids, clear_existing)
    
    # Step 4: Create locations
    print(f"\n4. Creating locations...")
    locations_created = await create_locations(client_id, clear_existing)
    
    # Get location_ids
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Location.location_id).where(Location.client_id == uuid.UUID(client_id))
        )
        location_ids = [row[0] for row in result.fetchall()]
    
    # Step 5: Create suppliers
    print(f"\n5. Creating suppliers...")
    supplier_ids = await create_suppliers(client_id, clear_existing)
    
    # Step 6: Create product-supplier conditions
    print(f"\n6. Creating product-supplier conditions...")
    conditions_created = await create_product_supplier_conditions(
        client_id, item_ids, supplier_ids, clear_existing
    )
    
    # Step 7: Create stock levels
    print(f"\n7. Creating stock levels...")
    stock_created = await create_stock_levels(client_id, item_ids, location_ids, clear_existing)
    
    # Step 8: Create client settings
    print(f"\n8. Creating client settings...")
    await create_client_settings(client_id, clear_existing)
    
    # Step 9: Ensure recent sales data (shifts dates to make data recent)
    # This makes all sales data "recent" relative to today so DIR calculations work
    sales_result = {"records_updated": 0}
    if not skip_recent_sales:
        print(f"\n9. Ensuring recent sales data (shifting dates to today)...")
        print(f"   This preserves all sales data (M5, synthetic) but makes dates recent")
        try:
            from scripts.shift_dates_to_recent import shift_dates_to_recent
            
            sales_result = await shift_dates_to_recent(
                client_id=client_id,
                target_max_date=None,  # Use today
                days_back_from_target=0  # Max date = today
            )
            
            if "error" not in sales_result:
                if "message" in sales_result:
                    print(f"   ℹ️  {sales_result['message']}")
                    print(f"   Sales data is already recent - no shift needed")
                else:
                    print(f"   ✅ Shifted {sales_result['records_updated']} sales records")
                    print(f"   Date offset: {sales_result['date_offset_days']} days")
                    print(f"   New date range: {sales_result['new_date_range']['min']} to {sales_result['new_date_range']['max']}")
                    print(f"   All sales data is now recent (max date = today)")
            else:
                print(f"   ⚠️  Warning: {sales_result.get('error', 'Unknown error')}")
                print(f"   This may affect DIR calculations (needs last 30 days of data)")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not shift dates: {e}")
            import traceback
            traceback.print_exc()
    
    # Step 10: Populate historical stock data (stock_on_date)
    print(f"\n10. Populating historical stock data...")
    try:
        from scripts.populate_historical_stock import populate_historical_stock
        
        stock_result = await populate_historical_stock(
            client_id=client_id,
            item_ids=item_ids,
            days_back=365,  # Populate last year
            reference_date=None  # Use today
        )
        
        if "error" not in stock_result:
            print(f"   Populated {stock_result['records_updated']} historical stock records")
            print(f"   Date range: {stock_result['start_date']} to {stock_result['end_date']}")
        else:
            print(f"   ⚠️  Warning: {stock_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"   ⚠️  Warning: Could not populate historical stock: {e}")
        import traceback
        traceback.print_exc()
        stock_result = {"records_updated": 0}
    
    print("\n" + "="*60)
    print("Test Data Setup Complete!")
    print("="*60)
    print(f"Client ID: {client_id}")
    print(f"Products: {products_created}")
    print(f"Locations: {locations_created}")
    print(f"Suppliers: {len(supplier_ids)}")
    print(f"Product-Supplier Conditions: {conditions_created}")
    print(f"Stock Levels: {stock_created}")
    print(f"Sales Records Updated: {sales_result.get('records_updated', 0)}")
    print(f"Historical Stock Records: {stock_result.get('records_updated', 0)}")
    
    return {
        "client_id": client_id,
        "products": products_created,
        "locations": locations_created,
        "suppliers": len(supplier_ids),
        "conditions": conditions_created,
        "stock_levels": stock_created,
        "sales_records_updated": sales_result.get("records_updated", 0),
        "historical_stock_records": stock_result.get("records_updated", 0)
    }


async def main():
    parser = argparse.ArgumentParser(description="Setup test data for inventory management")
    parser.add_argument("--client-id", type=str, help="Existing client ID (UUID)")
    parser.add_argument("--client-name", type=str, default="Demo Client", help="Client name (if creating new)")
    parser.add_argument("--clear-existing", action="store_true", help="Clear existing test data first")
    parser.add_argument("--days-back", type=int, default=30, help="Days of recent sales data to generate (default: 30)")
    parser.add_argument("--skip-recent-sales", action="store_true", help="Skip generating recent sales data")
    
    args = parser.parse_args()
    
    try:
        result = await setup_test_data(
            client_id=args.client_id,
            client_name=args.client_name,
            clear_existing=args.clear_existing,
            days_back=args.days_back,
            skip_recent_sales=args.skip_recent_sales
        )
        
        if "error" in result:
            sys.exit(1)
        
        print("\n✅ Setup completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

