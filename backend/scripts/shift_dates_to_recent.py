#!/usr/bin/env python3
"""
Shift Sales Data Dates to Recent

Instead of generating synthetic data, simply shift all existing sales data
dates forward so the most recent data is today (or recent).

This preserves:
- Real M5 sales patterns
- Historical relationships
- Actual demand patterns

Strategy:
1. Find max date in existing data
2. Calculate offset to today
3. Update all dates by that offset
4. All data becomes "recent" relative to today
"""
import asyncio
import sys
from pathlib import Path
from typing import Optional
from datetime import date, timedelta
import uuid

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from sqlalchemy import text


async def shift_dates_to_recent(
    client_id: str,
    target_max_date: Optional[date] = None,
    days_back_from_target: int = 0
) -> dict:
    """
    Shift all sales data dates forward so max date is target_max_date.
    
    Args:
        client_id: Client UUID string
        target_max_date: Target maximum date (default: today)
        days_back_from_target: If set, target_max_date will be this many days before target
    
    Returns:
        dict with shift details
    """
    if target_max_date is None:
        target_max_date = date.today()
    
    if days_back_from_target > 0:
        target_max_date = target_max_date - timedelta(days=days_back_from_target)
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Find current max date
        result = await session.execute(
            text("""
                SELECT MAX(date_local) as max_date, MIN(date_local) as min_date
                FROM ts_demand_daily
                WHERE client_id = :client_id
            """),
            {"client_id": client_id}
        )
        row = result.fetchone()
        
        if not row or not row[0]:
            return {
                "error": "No sales data found",
                "records_updated": 0
            }
        
        current_max_date = row[0]
        current_min_date = row[1] if row[1] else current_max_date
        
        # Calculate offset
        date_offset = (target_max_date - current_max_date).days
        
        if date_offset == 0:
            return {
                "message": "Dates already up to date",
                "current_max_date": current_max_date.isoformat(),
                "target_max_date": target_max_date.isoformat(),
                "records_updated": 0
            }
        
        # Get count of records to update
        count_result = await session.execute(
            text("""
                SELECT COUNT(*) as cnt
                FROM ts_demand_daily
                WHERE client_id = :client_id
            """),
            {"client_id": client_id}
        )
        record_count = count_result.scalar() or 0
        
        # Update all dates (PostgreSQL: date + interval = date)
        # Use a temporary column approach to avoid unique constraint violations
        # Strategy: Add offset to create new dates, then update in batches
        offset_days = date_offset
        
        # First, add a temporary column with new dates
        await session.execute(
            text("""
                ALTER TABLE ts_demand_daily 
                ADD COLUMN IF NOT EXISTS date_local_new DATE
            """)
        )
        
        # Calculate new dates
        await session.execute(
            text("""
                UPDATE ts_demand_daily
                SET date_local_new = date_local + (CAST(:offset_days AS INTEGER) || ' days')::interval
                WHERE client_id = :client_id
            """),
            {
                "client_id": client_id,
                "offset_days": offset_days
            }
        )
        
        # Delete records that would create duplicates
        await session.execute(
            text("""
                DELETE FROM ts_demand_daily t1
                USING ts_demand_daily t2
                WHERE t1.client_id = :client_id
                  AND t2.client_id = :client_id
                  AND t1.location_id = t2.location_id
                  AND t1.date_local_new = t2.date_local
                  AND t1.item_id = t2.item_id
                  AND t1.date_local < t2.date_local
            """),
            {"client_id": client_id}
        )
        
        # Update date_local with new dates
        await session.execute(
            text("""
                UPDATE ts_demand_daily
                SET date_local = date_local_new
                WHERE client_id = :client_id
                  AND date_local_new IS NOT NULL
            """),
            {"client_id": client_id}
        )
        
        # Drop temporary column
        await session.execute(
            text("ALTER TABLE ts_demand_daily DROP COLUMN IF EXISTS date_local_new")
        )
        
        await session.commit()
        
        new_min_date = current_min_date + timedelta(days=date_offset)
        new_max_date = current_max_date + timedelta(days=date_offset)
        
        return {
            "records_updated": record_count,
            "date_offset_days": date_offset,
            "old_date_range": {
                "min": current_min_date.isoformat(),
                "max": current_max_date.isoformat()
            },
            "new_date_range": {
                "min": new_min_date.isoformat(),
                "max": new_max_date.isoformat()
            },
            "target_max_date": target_max_date.isoformat()
        }


async def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Shift all sales data dates to recent (preserves patterns)"
    )
    parser.add_argument(
        "--client-id",
        type=str,
        required=True,
        help="Client ID (UUID)"
    )
    parser.add_argument(
        "--target-date",
        type=str,
        help="Target maximum date (YYYY-MM-DD, default: today)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=0,
        help="Days back from target date (default: 0 = target date is max)"
    )
    
    args = parser.parse_args()
    
    target_date = None
    if args.target_date:
        target_date = date.fromisoformat(args.target_date)
    
    try:
        result = await shift_dates_to_recent(
            client_id=args.client_id,
            target_max_date=target_date,
            days_back_from_target=args.days_back
        )
        
        if "error" in result:
            print(f"❌ Error: {result['error']}")
            sys.exit(1)
        
        if "message" in result:
            print(f"ℹ️  {result['message']}")
            print(f"   Current max date: {result['current_max_date']}")
            print(f"   Target max date: {result['target_max_date']}")
        else:
            print(f"\n✅ Shifted {result['records_updated']} records")
            print(f"   Date offset: {result['date_offset_days']} days")
            print(f"   Old range: {result['old_date_range']['min']} to {result['old_date_range']['max']}")
            print(f"   New range: {result['new_date_range']['min']} to {result['new_date_range']['max']}")
            print(f"   Target max: {result['target_max_date']}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
