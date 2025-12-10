#!/usr/bin/env python3
"""
Populate Historical Stock Data

Calculates historical stock levels (`stock_on_date`) by working backwards
from current stock levels using sales data.

IMPORTANT:
- stock_levels table: Has location_id (each location has its own stock)
- ts_demand_daily table: NO location_id (aggregated at SKU level)
- stock_on_date: Should be SUM of stock across ALL locations for that SKU

Strategy:
1. Get current stock (SUM across all locations) from stock_levels table
2. For each date (working backwards from today):
   - stock_on_date = stock_next_day + units_sold_today - restocking_today
   - Restocking happens weekly (simulate based on average sales)
3. Update stock_on_date in ts_demand_daily (one value per SKU per date)

This enables:
- Historical inventory visibility (aggregated across locations)
- Stockout detection (stock_on_date = 0)
- Analysis of stock levels over time
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional, List
from datetime import date, timedelta
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.product import Product
from models.stock import StockLevel
from sqlalchemy import select, text


async def populate_historical_stock(
    client_id: str,
    item_ids: Optional[List[str]] = None,
    days_back: int = 365,
    reference_date: Optional[date] = None
) -> dict:
    """
    Populate stock_on_date for historical dates by calculating backwards from current stock.
    
    Args:
        client_id: Client UUID string
        item_ids: List of item_ids (if None, uses all products)
        days_back: Number of days to populate (default: 365)
        reference_date: Reference date (default: today)
    
    Returns:
        dict with counts of records updated
    """
    if reference_date is None:
        reference_date = date.today()
    
    start_date = reference_date - timedelta(days=days_back)
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Get item_ids if not provided
        if item_ids is None:
            result = await session.execute(
                select(Product.item_id).where(
                    Product.client_id == uuid.UUID(client_id)
                )
            )
            item_ids = [row[0] for row in result.fetchall()]
        
        if not item_ids:
            return {"error": "No products found", "records_updated": 0}
        
        records_updated = 0
        
        for item_id in item_ids:
            # Get current stock (SUM across all locations)
            # ts_demand_daily is aggregated at SKU level (no location_id),
            # so stock_on_date should be total stock across all locations
            stock_result = await session.execute(
                text("""
                    SELECT COALESCE(SUM(current_stock), 0) as total_stock
                    FROM stock_levels
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                """),
                {
                    "client_id": client_id,
                    "item_id": item_id
                }
            )
            current_stock = int(stock_result.scalar() or 0)
            
            if current_stock == 0:
                # No stock, set all to 0
                await session.execute(
                    text("""
                        UPDATE ts_demand_daily
                        SET stock_on_date = 0
                        WHERE client_id = :client_id
                          AND item_id = :item_id
                          AND date_local >= :start_date
                          AND date_local <= :end_date
                    """),
                    {
                        "client_id": client_id,
                        "item_id": item_id,
                        "start_date": start_date,
                        "end_date": reference_date
                    }
                )
                continue
            
            # Get sales data for this period (ordered by date DESC)
            sales_result = await session.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND item_id = :item_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                    ORDER BY date_local DESC
                """),
                {
                    "client_id": client_id,
                    "item_id": item_id,
                    "start_date": start_date,
                    "end_date": reference_date
                }
            )
            sales_data = {row.date_local: float(row.units_sold) for row in sales_result}
            
            if not sales_data:
                continue
            
            # Calculate average weekly sales for restocking simulation
            recent_sales = [
                sales_data.get(reference_date - timedelta(days=i), 0)
                for i in range(min(30, days_back))
            ]
            avg_weekly_sales = sum(recent_sales) / max(1, len(recent_sales) / 7) if recent_sales else 0
            
            # Calculate stock backwards from today
            stock = current_stock
            stock_levels = {}
            
            for day_offset in range(days_back):
                sale_date = reference_date - timedelta(days=day_offset)
                units_sold = sales_data.get(sale_date, 0)
                
                # Stock at end of day = stock at start of day - units_sold + restocking
                # Working backwards: stock_yesterday = stock_today + units_sold_today - restocking_today
                
                # Weekly restocking (simulate - happens on Mondays)
                restocking = 0
                if sale_date.weekday() == 0 and day_offset > 0:  # Monday
                    # Restock based on average weekly sales
                    restocking = int(avg_weekly_sales * 1.2)  # Restock 120% of weekly average
                
                # Calculate stock for this day (working backwards)
                stock = stock + units_sold - restocking
                stock = max(0, stock)  # Can't be negative
                
                stock_levels[sale_date] = int(stock)
            
            # Update stock_on_date for all dates
            for sale_date, stock_value in stock_levels.items():
                await session.execute(
                    text("""
                        UPDATE ts_demand_daily
                        SET stock_on_date = :stock
                        WHERE client_id = :client_id
                          AND item_id = :item_id
                          AND date_local = :date_local
                    """),
                    {
                        "client_id": client_id,
                        "item_id": item_id,
                        "date_local": sale_date,
                        "stock": stock_value
                    }
                )
                records_updated += 1
        
        await session.commit()
        
        return {
            "records_updated": records_updated,
            "products": len(item_ids),
            "start_date": start_date.isoformat(),
            "end_date": reference_date.isoformat(),
            "days_back": days_back
        }


async def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Populate historical stock data (stock_on_date) from current stock"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        required=True,
        help="Client ID (UUID)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=365,
        help="Number of days to populate (default: 365)"
    )
    
    args = parser.parse_args()
    
    try:
        result = await populate_historical_stock(
            client_id=args.client_id,
            days_back=args.days_back
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"\n✅ Populated {result['records_updated']} historical stock records")
        print(f"   Products: {result['products']}")
        print(f"   Date range: {result['start_date']} to {result['end_date']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
