#!/usr/bin/env python3
"""
Generate Recent Sales Data (from today backwards)

Generates synthetic sales data from today backwards to fill the gap
between historical data (M5 dataset 2015-2024) and current date.

This ensures:
- DIR calculations work (need last 30 days)
- Status classifications work (need recent data)
- Recommendations generate properly

Strategy:
- Keep all existing historical data (M5, synthetic, etc.)
- Generate data from TODAY backwards for specified days
- Only fill dates that don't already have data
- Use patterns based on historical averages
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
import random
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.product import Product
from sqlalchemy import select, text


def is_weekend(sale_date: date) -> bool:
    """Check if date is weekend"""
    return sale_date.weekday() >= 5


def is_holiday(sale_date: date) -> bool:
    """Check if date is a holiday (simplified - can be enhanced)"""
    # Simple holiday detection: New Year, Christmas, etc.
    holidays = [
        (1, 1),   # New Year
        (12, 25), # Christmas
        (12, 31), # New Year's Eve
    ]
    return (sale_date.month, sale_date.day) in holidays


def calculate_daily_sales(
    item_id: str,
    sale_date: date,
    historical_avg: Optional[float] = None,
    pattern: str = "normal"
) -> Decimal:
    """
    Calculate units sold for a specific day based on pattern and historical data.
    
    Args:
        item_id: Product identifier
        sale_date: Date for calculation
        historical_avg: Average daily sales from historical data (if available)
        pattern: Sales pattern type (normal, high_volume, low_volume, dead_stock)
    
    Returns:
        Units sold for this day
    """
    # Use historical average if available, otherwise use pattern defaults
    if historical_avg and historical_avg > 0:
        base = historical_avg
    else:
        # Pattern-based defaults
        if pattern == "high_volume":
            base = random.randint(50, 200)
        elif pattern == "low_volume":
            base = random.randint(1, 10)
        elif pattern == "dead_stock":
            # Dead stock: no sales for 60+ days, occasional small sales
            days_since_start = (date.today() - sale_date).days
            if days_since_start < 60:
                return Decimal("0.00")
            else:
                return Decimal(str(random.randint(0, 5)))
        else:  # normal
            base = random.randint(10, 50)
    
    # Weekend effect (-30%)
    if is_weekend(sale_date):
        base = int(base * 0.7)
    
    # Holiday effect (+20%)
    if is_holiday(sale_date):
        base = int(base * 1.2)
    
    # Weekly pattern (higher mid-week)
    day_of_week = sale_date.weekday()
    if day_of_week in [1, 2, 3]:  # Tue, Wed, Thu
        base = int(base * 1.1)
    elif day_of_week == 0:  # Monday
        base = int(base * 0.9)
    
    # Promotion effect (random 1-2 per month)
    # Use item_id hash to make promotions consistent per SKU
    item_hash = hash(f"{item_id}{sale_date.year}{sale_date.month}") % 100
    is_promotion = item_hash < 5  # ~5% chance = ~1-2 per month
    if is_promotion:
        base = int(base * 1.5)  # +50% during promotions
    
    # Add small random variation (-10% to +10%)
    variation = random.randint(-int(base * 0.1), int(base * 0.1))
    units = max(0, base + variation)
    
    return Decimal(str(units))


async def get_historical_average_daily_sales(
    client_id: str,
    item_id: str,
    session
) -> Optional[float]:
    """
    Get average daily sales from historical data (last 90 days of historical data).
    This helps maintain realistic patterns based on M5 or other historical data.
    """
    result = await session.execute(
        text("""
            SELECT AVG(daily_total) as avg_demand
            FROM (
                SELECT date_local, SUM(units_sold) as daily_total
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = :item_id
                  AND date_local < CURRENT_DATE
                  AND date_local >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY date_local
            ) daily_totals
        """),
        {"client_id": client_id, "item_id": item_id}
    )
    row = result.fetchone()
    if row and row[0]:
        return float(row[0])
    return None


async def classify_product_pattern(
    client_id: str,
    item_id: str,
    session
) -> str:
    """
    Classify product into sales pattern based on historical data.
    """
    result = await session.execute(
        text("""
            SELECT AVG(units_sold) as avg_sales, COUNT(*) as days_with_sales
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND item_id = :item_id
              AND date_local < CURRENT_DATE
              AND date_local >= CURRENT_DATE - INTERVAL '90 days'
        """),
        {"client_id": client_id, "item_id": item_id}
    )
    row = result.fetchone()
    
    if not row or not row[0]:
        return "normal"  # Default if no historical data
    
    avg_sales = float(row[0]) if row[0] else 0
    days_with_sales = int(row[1]) if row[1] else 0
    
    # Classify based on average sales
    if avg_sales > 50:
        return "high_volume"
    elif avg_sales < 5:
        return "low_volume"
    elif days_with_sales < 10:  # Less than 10 days with sales in 90 days
        return "dead_stock"
    else:
        return "normal"


async def generate_recent_sales_data(
    client_id: str,
    item_ids: Optional[List[str]] = None,
    days_back: int = 30,
    reference_date: Optional[date] = None,
    clear_existing_recent: bool = False
) -> dict:
    """
    Generate synthetic sales data from reference_date backwards.
    
    Strategy:
    - Keep all historical data (M5 2015-2024, etc.)
    - Only generate data for dates >= reference_date - days_back
    - Only fill dates that don't already have data
    - Use historical patterns to maintain realism
    
    Args:
        client_id: Client UUID string
        item_ids: List of item_ids (if None, uses all products for client)
        days_back: Number of days to generate from reference_date backwards
        reference_date: Reference date (default: today)
        clear_existing_recent: If True, clear existing recent data first
    
    Returns:
        dict with counts of records created
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
            return {"error": "No products found", "records_created": 0}
        
        # Clear existing recent data if requested
        if clear_existing_recent:
            await session.execute(
                text("""
                    DELETE FROM ts_demand_daily
                    WHERE client_id = :client_id
                      AND date_local >= :start_date
                      AND date_local <= :end_date
                """),
                {
                    "client_id": client_id,
                    "start_date": start_date,
                    "end_date": reference_date
                }
            )
            await session.commit()
            print(f"   Cleared existing data from {start_date} to {reference_date}")
        
        records_created = 0
        records_skipped = 0
        
        # Generate data for each product
        for item_id in item_ids:
            # Get historical average for this product
            historical_avg = await get_historical_average_daily_sales(
                client_id, item_id, session
            )
            
            # Classify product pattern
            pattern = await classify_product_pattern(client_id, item_id, session)
            
            # Generate daily sales
            for day_offset in range(days_back):
                sale_date = reference_date - timedelta(days=day_offset)
                
                # Skip if data already exists
                existing = await session.execute(
                    text("""
                        SELECT 1 FROM ts_demand_daily
                        WHERE client_id = :client_id
                          AND item_id = :item_id
                          AND date_local = :date_local
                    """),
                    {
                        "client_id": client_id,
                        "item_id": item_id,
                        "date_local": sale_date
                    }
                )
                if existing.fetchone():
                    records_skipped += 1
                    continue
                
                # Calculate units sold
                units_sold = calculate_daily_sales(
                    item_id, sale_date, historical_avg, pattern
                )
                
                # Determine flags
                is_weekend_flag = is_weekend(sale_date)
                is_holiday_flag = is_holiday(sale_date)
                
                # Promotion flag (consistent per SKU per month)
                item_hash = hash(f"{item_id}{sale_date.year}{sale_date.month}") % 100
                is_promotion = item_hash < 5
                
                # Marketing spend (higher during promotions)
                marketing_spend = Decimal("0.00")
                if is_promotion:
                    marketing_spend = Decimal(str(random.randint(50, 200)))
                elif random.random() < 0.1:  # 10% chance of marketing on non-promo days
                    marketing_spend = Decimal(str(random.randint(10, 50)))
                
                # Insert record
                await session.execute(
                    text("""
                        INSERT INTO ts_demand_daily
                        (item_id, date_local, units_sold, client_id,
                         promotion_flag, holiday_flag, is_weekend, marketing_spend)
                        VALUES (:item_id, :date_local, :units_sold, :client_id,
                                :promo_flag, :holiday_flag, :is_weekend, :marketing_spend)
                        ON CONFLICT (item_id, date_local, client_id) DO NOTHING
                    """),
                    {
                        "item_id": item_id,
                        "date_local": sale_date,
                        "units_sold": float(units_sold),
                        "client_id": client_id,
                        "promo_flag": is_promotion,
                        "holiday_flag": is_holiday_flag,
                        "is_weekend": is_weekend_flag,
                        "marketing_spend": float(marketing_spend)
                    }
                )
                records_created += 1
        
        await session.commit()
        
        return {
            "records_created": records_created,
            "records_skipped": records_skipped,
            "products": len(item_ids),
            "start_date": start_date.isoformat(),
            "end_date": reference_date.isoformat(),
            "days_back": days_back
        }


async def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate recent sales data from today backwards"
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
        default=30,
        help="Number of days to generate from today backwards (default: 30)"
    )
    parser.add_argument(
        "--clear-existing",
        action="store_true",
        help="Clear existing recent data before generating"
    )
    
    args = parser.parse_args()
    
    try:
        result = await generate_recent_sales_data(
            client_id=args.client_id,
            days_back=args.days_back,
            clear_existing_recent=args.clear_existing
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        print(f"\n✅ Generated {result['records_created']} sales records")
        print(f"   Skipped {result['records_skipped']} existing records")
        print(f"   Products: {result['products']}")
        print(f"   Date range: {result['start_date']} to {result['end_date']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
