#!/usr/bin/env python3
"""
Check Inventory Data for DIR Calculation

Diagnostic script to verify that all required data exists for calculating:
- DIR (Days of Inventory Remaining)
- Stockout Risk
- Status

Usage:
    uv run python scripts/check_inventory_data.py [--client-id <uuid>]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from models.product import Product
from models.stock import StockLevel
from models.settings import ClientSettings
from sqlalchemy import select, func, text
from services.metrics_service import MetricsService


async def check_data(client_id: str = None):
    """Check all required data for inventory metrics"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Get client
        if client_id:
            result = await session.execute(
                select(Client).where(Client.client_id == UUID(client_id))
            )
            client = result.scalar_one_or_none()
        else:
            result = await session.execute(select(Client).limit(1))
            client = result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found in database")
            return
        
        client_id = str(client.client_id)
        print(f"📊 Checking data for client: {client.name} ({client_id})\n")
        
        # 1. Check Products
        result = await session.execute(
            select(func.count(Product.id)).where(Product.client_id == UUID(client_id))
        )
        product_count = result.scalar() or 0
        print(f"1. Products: {product_count}")
        
        if product_count == 0:
            print("   ❌ No products found - cannot calculate metrics")
            return
        
        # Get sample product
        result = await session.execute(
            select(Product).where(Product.client_id == UUID(client_id)).limit(1)
        )
        sample_product = result.scalar_one()
        print(f"   Sample: {sample_product.item_id} - {sample_product.product_name}")
        
        # 2. Check Stock Levels
        result = await session.execute(
            select(func.count(StockLevel.id)).where(StockLevel.client_id == UUID(client_id))
        )
        stock_count = result.scalar() or 0
        print(f"\n2. Stock Levels: {stock_count}")
        
        if stock_count == 0:
            print("   ❌ No stock levels found - DIR cannot be calculated")
        else:
            # Check stock for sample product
            result = await session.execute(
                select(StockLevel).where(
                    StockLevel.client_id == UUID(client_id),
                    StockLevel.item_id == sample_product.item_id
                )
            )
            stock_levels = result.scalars().all()
            total_stock = sum(sl.current_stock for sl in stock_levels)
            print(f"   Sample product stock: {total_stock} units")
            if total_stock == 0:
                print("   ⚠️  Stock is 0 - DIR will be 0")
        
        # 3. Check Sales Data (ts_demand_daily)
        result = await session.execute(
            text("""
                SELECT 
                    COUNT(DISTINCT item_id) as item_count,
                    COUNT(*) as total_records,
                    MIN(date_local) as earliest_date,
                    MAX(date_local) as latest_date,
                    SUM(units_sold) as total_units_sold
                FROM ts_demand_daily
                WHERE client_id = :client_id
            """),
            {"client_id": client_id}
        )
        sales_data = result.fetchone()
        
        print(f"\n3. Sales Data (ts_demand_daily):")
        if sales_data and sales_data[0]:
            print(f"   Items with sales data: {sales_data[0]}")
            print(f"   Total records: {sales_data[1]}")
            print(f"   Date range: {sales_data[2]} to {sales_data[3]}")
            print(f"   Total units sold: {sales_data[4]}")
            
            # Check last 30 days for sample product
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            result = await session.execute(
                text("""
                    SELECT 
                        COUNT(*) as days_with_sales,
                        SUM(units_sold) as total_units,
                        AVG(units_sold) as avg_daily
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                """),
                {
                    "client_id": client_id,
                    "item_id": sample_product.item_id,
                    "start_date": start_date,
                    "end_date": end_date
                }
            )
            recent_sales = result.fetchone()
            
            if recent_sales and recent_sales[0]:
                print(f"\n   Sample product ({sample_product.item_id}) - Last 30 days:")
                print(f"   Days with sales: {recent_sales[0]}")
                print(f"   Total units: {recent_sales[1]}")
                print(f"   Avg daily: {recent_sales[2]:.2f}")
                
                if recent_sales[2] and recent_sales[2] > 0:
                    print("   ✅ Has sales data for DIR calculation")
                else:
                    print("   ❌ No average daily demand - DIR will be None")
            else:
                print(f"   ❌ No sales data for sample product in last 30 days")
        else:
            print("   ❌ No sales data found - DIR cannot be calculated")
        
        # 4. Check Client Settings
        result = await session.execute(
            select(ClientSettings).where(ClientSettings.client_id == UUID(client_id))
        )
        settings = result.scalar_one_or_none()
        
        print(f"\n4. Client Settings:")
        if settings:
            print(f"   ✅ Settings exist")
            print(f"   Safety buffer: {settings.safety_buffer_days} days")
            print(f"   Understocked threshold: {settings.understocked_threshold} days")
            print(f"   Overstocked threshold: {settings.overstocked_threshold} days")
        else:
            print("   ⚠️  No settings found - will use defaults")
        
        # 5. Test DIR Calculation
        print(f"\n5. Testing DIR Calculation:")
        metrics_service = MetricsService(session)
        
        metrics = await metrics_service.compute_product_metrics(
            client_id=UUID(client_id),
            item_id=sample_product.item_id
        )
        
        print(f"   Product: {sample_product.item_id}")
        print(f"   Current Stock: {metrics.get('current_stock', 0)}")
        print(f"   DIR: {metrics.get('dir')}")
        print(f"   Stockout Risk: {metrics.get('stockout_risk')}")
        print(f"   Status: {metrics.get('status')}")
        print(f"   Inventory Value: {metrics.get('inventory_value')}")
        
        if metrics.get('dir') is None:
            print("\n   ❌ DIR is None - likely no sales data or stock is 0")
        elif metrics.get('dir') == 0:
            print("\n   ⚠️  DIR is 0 - stock is 0 or demand is very high")
        else:
            print(f"\n   ✅ DIR calculated: {metrics.get('dir')} days")
        
        # 6. Summary
        print(f"\n{'='*60}")
        print("SUMMARY:")
        print(f"{'='*60}")
        
        issues = []
        if product_count == 0:
            issues.append("❌ No products")
        if stock_count == 0:
            issues.append("❌ No stock levels")
        if not sales_data or not sales_data[0]:
            issues.append("❌ No sales data")
        if metrics.get('dir') is None:
            issues.append("❌ DIR calculation returns None")
        
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  {issue}")
            print("\n💡 To fix:")
            print("  1. Run: uv run python scripts/setup_test_data.py")
            print("  2. Or import sales data: uv run python scripts/setup_demo_client.py --csv <file>")
        else:
            print("✅ All data looks good!")
            if metrics.get('dir') == 0:
                print("⚠️  But DIR is 0 - check if stock levels are > 0")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check inventory data for DIR calculation")
    parser.add_argument("--client-id", help="Client ID to check (optional)")
    args = parser.parse_args()
    
    asyncio.run(check_data(args.client_id))

