#!/usr/bin/env python3
"""
Complete Test Data Reset

Completely deletes all test data for a client and repopulates it fresh.

This script:
1. Deletes ALL test data (products, locations, suppliers, stock, sales, etc.)
2. Re-imports sales data (if M5/synthetic data exists)
3. Re-creates all test data structures
4. Shifts dates to recent
5. Populates historical stock

Usage:
    uv run python backend/scripts/reset_test_data.py \
        --client-id <uuid> \
        [--keep-sales-data]  # Don't delete ts_demand_daily
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from sqlalchemy import text
from scripts.setup_test_data import setup_test_data


async def clear_all_test_data(
    client_id: str,
    keep_sales_data: bool = False
) -> dict:
    """
    Delete all test data for a client.
    
    Args:
        client_id: Client UUID string
        keep_sales_data: If True, don't delete ts_demand_daily (preserve M5/synthetic data)
    
    Returns:
        dict with counts of deleted records
    """
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        deleted_counts = {}
        
        # Delete in order (respecting foreign keys)
        tables = [
            ("order_cart_items", "Order cart items"),
            ("purchase_order_items", "Purchase order items"),
            ("purchase_orders", "Purchase orders"),
            ("product_supplier_conditions", "Product-supplier conditions"),
            ("stock_levels", "Stock levels"),
            ("products", "Products"),
            ("suppliers", "Suppliers"),
            ("locations", "Locations"),
            ("client_settings", "Client settings"),
        ]
        
        for table_name, display_name in tables:
            result = await session.execute(
                text(f"DELETE FROM {table_name} WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            deleted_counts[table_name] = result.rowcount
            print(f"   Deleted {result.rowcount} {display_name}")
        
        # Optionally delete sales data
        if not keep_sales_data:
            result = await session.execute(
                text("DELETE FROM ts_demand_daily WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            deleted_counts["ts_demand_daily"] = result.rowcount
            print(f"   Deleted {result.rowcount} sales records (ts_demand_daily)")
        else:
            # Count existing records
            count_result = await session.execute(
                text("SELECT COUNT(*) FROM ts_demand_daily WHERE client_id = :client_id"),
                {"client_id": client_id}
            )
            existing_count = count_result.scalar() or 0
            deleted_counts["ts_demand_daily"] = 0
            print(f"   Kept sales data (ts_demand_daily) - {existing_count} records preserved")
        
        await session.commit()
        
        return deleted_counts


async def reset_test_data(
    client_id: Optional[str] = None,
    client_name: str = "Demo Client",
    keep_sales_data: bool = False,
    days_back: int = 30
) -> dict:
    """
    Complete reset: delete all test data and repopulate.
    
    Args:
        client_id: Client UUID (if None, uses client_name to find/create)
        client_name: Client name (if creating new)
        keep_sales_data: If True, preserve ts_demand_daily data
        days_back: Days of recent data to ensure (for date shifting)
    
    Returns:
        dict with reset results
    """
    print("="*60)
    print("COMPLETE TEST DATA RESET")
    print("="*60)
    
    # Step 1: Get client
    from scripts.setup_test_data import get_or_create_client
    client_id = await get_or_create_client(client_id, client_name)
    
    # Step 2: Clear all existing test data
    print(f"\n🗑️  Step 1: Clearing all existing test data...")
    deleted_counts = await clear_all_test_data(client_id, keep_sales_data)
    
    total_deleted = sum(deleted_counts.values())
    print(f"\n   ✅ Deleted {total_deleted} total records")
    
    # Step 3: Check if we need to re-import sales data
    if not keep_sales_data:
        print(f"\n⚠️  WARNING: Sales data (ts_demand_daily) was deleted.")
        print(f"   This includes:")
        print(f"   - M5 dataset (if imported)")
        print(f"   - Synthetic CSV data (if imported)")
        print(f"   - All historical sales records")
        print(f"\n   You need to re-import sales data before running setup_test_data.py")
        print(f"   Options:")
        print(f"   1. M5 Dataset: python backend/scripts/download_m5_data.py --client-id {client_id}")
        print(f"   2. CSV Import: python backend/scripts/import_csv_to_ts_demand_daily.py --csv <file> --client-id {client_id}")
        print(f"\n   After importing, run:")
        print(f"   python backend/scripts/setup_test_data.py --client-id {client_id}")
        print(f"\n   OR use setup_demo_client.py for complete workflow:")
        print(f"   python backend/scripts/setup_demo_client.py --client-name '{client_name}' --csv <file>")
        return {
            "client_id": client_id,
            "deleted": deleted_counts,
            "status": "sales_data_deleted",
            "next_step": "import_sales_data"
        }
    
    # Step 4: Re-populate test data
    print(f"\n🔄 Step 2: Re-populating test data...")
    setup_result = await setup_test_data(
        client_id=client_id,
        client_name=None,  # Don't create new client
        clear_existing=False,  # Already cleared
        days_back=days_back,
        skip_recent_sales=False
    )
    
    if "error" in setup_result:
        return {
            "client_id": client_id,
            "deleted": deleted_counts,
            "error": setup_result.get("error"),
            "status": "setup_failed"
        }
    
    print("\n" + "="*60)
    print("✅ RESET COMPLETE!")
    print("="*60)
    print(f"Client ID: {client_id}")
    print(f"Deleted: {total_deleted} records")
    print(f"Created:")
    print(f"  - Products: {setup_result.get('products', 0)}")
    print(f"  - Locations: {setup_result.get('locations', 0)}")
    print(f"  - Suppliers: {setup_result.get('suppliers', 0)}")
    print(f"  - Conditions: {setup_result.get('conditions', 0)}")
    print(f"  - Stock Levels: {setup_result.get('stock_levels', 0)}")
    print(f"  - Sales Records Updated: {setup_result.get('sales_records_updated', 0)}")
    print(f"  - Historical Stock Records: {setup_result.get('historical_stock_records', 0)}")
    
    return {
        "client_id": client_id,
        "deleted": deleted_counts,
        "created": setup_result,
        "status": "complete"
    }


async def main():
    parser = argparse.ArgumentParser(
        description="Complete test data reset (delete all and repopulate)"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        help="Client ID (UUID). If not provided, uses --client-name"
    )
    parser.add_argument(
        "--client-name",
        type=str,
        default="Demo Client",
        help="Client name (if creating new or finding existing)"
    )
    parser.add_argument(
        "--keep-sales-data",
        action="store_true",
        help="Keep ts_demand_daily data (preserves M5, synthetic, and all sales history)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Days of recent data to ensure (default: 30)"
    )
    
    args = parser.parse_args()
    
    try:
        result = await reset_test_data(
            client_id=args.client_id,
            client_name=args.client_name,
            keep_sales_data=args.keep_sales_data,
            days_back=args.days_back
        )
        
        if result.get("status") == "sales_data_deleted":
            print("\n⚠️  Next step: Import sales data, then run setup_test_data.py")
            sys.exit(0)
        elif result.get("status") == "setup_failed":
            print(f"\n❌ Setup failed: {result.get('error')}")
            sys.exit(1)
        elif result.get("status") == "complete":
            print("\n✅ Reset completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠️  Unexpected status: {result.get('status')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
