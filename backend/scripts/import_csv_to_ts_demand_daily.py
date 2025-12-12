#!/usr/bin/env python3
"""
Import CSV data into ts_demand_daily table

Development script for importing test/demo data.
Production will use proper ETL pipelines.

Usage:
    uv run python backend/scripts/import_csv_to_ts_demand_daily.py \
        --csv data/synthetic_data/synthetic_ecom_chronos2_demo.csv \
        --client-id <uuid> \
        [--clear-existing]
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local, get_engine
from models.client import Client


async def validate_client_id(client_id: str) -> bool:
    """Validate that client_id exists in clients table"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("SELECT EXISTS(SELECT 1 FROM clients WHERE client_id = :client_id)"),
            {"client_id": client_id}
        )
        exists = result.scalar()
        return exists


async def check_table_exists() -> bool:
    """Check if ts_demand_daily table exists"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'ts_demand_daily'
                )
            """)
        )
        return result.scalar()


async def import_csv_to_ts_demand_daily(
    csv_path: Path,
    client_id: str,
    clear_existing: bool = False,
    default_location_id: str = "UNSPECIFIED"
) -> dict:
    """
    Import CSV data into ts_demand_daily table

    Args:
        csv_path: Path to CSV file
        client_id: Client UUID (must exist in clients table)
        clear_existing: If True, delete existing data for this client first

    Returns:
        dict with import statistics
    """
    # Check if table exists
    if not await check_table_exists():
        raise ValueError(
            "ts_demand_daily table does not exist. "
            "Please run migrations first: alembic upgrade head"
        )

    # Validate client_id
    if not await validate_client_id(client_id):
        raise ValueError(f"Client ID {client_id} does not exist in clients table")

    # Load CSV
    print(f"Loading CSV: {csv_path}")
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df):,} rows from CSV")

    # Validate required columns
    required_columns = ['date', 'sku', 'sales_qty']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # Transform date column
    df['date'] = pd.to_datetime(df['date']).dt.date

    # Prepare data for insertion
    rows_to_insert = []
    for _, row in df.iterrows():
        rows_to_insert.append({
            'item_id': str(row['sku']),
            'location_id': str(row['location_id']) if 'location_id' in df.columns else default_location_id,
            'date_local': row['date'],
            'units_sold': float(row.get('sales_qty', 0)),
            'client_id': client_id,
            'promotion_flag': bool(row.get('promo_flag', False)),
            'holiday_flag': bool(row.get('holiday_flag', False)),
            'is_weekend': bool(row.get('is_weekend', False)),
            'marketing_spend': float(row.get('marketing_index', 0)) * 100,  # Scale index to spend
        })

    # Import to database
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        try:
            # Clear existing data if requested
            if clear_existing:
                print(f"Clearing existing data for client {client_id}...")
                await session.execute(
                    text("DELETE FROM ts_demand_daily WHERE client_id = :client_id"),
                    {"client_id": client_id}
                )
                await session.commit()
                print("Existing data cleared")

            # Insert data
            print(f"Inserting {len(rows_to_insert):,} rows...")
            insert_query = text("""
                INSERT INTO ts_demand_daily
                (item_id, location_id, date_local, units_sold, client_id, promotion_flag, holiday_flag, is_weekend, marketing_spend)
                VALUES (:item_id, :location_id, :date_local, :units_sold, :client_id, :promotion_flag, :holiday_flag, :is_weekend, :marketing_spend)
                ON CONFLICT (item_id, location_id, date_local, client_id) DO UPDATE
                SET units_sold = EXCLUDED.units_sold,
                    promotion_flag = EXCLUDED.promotion_flag,
                    holiday_flag = EXCLUDED.holiday_flag,
                    is_weekend = EXCLUDED.is_weekend,
                    marketing_spend = EXCLUDED.marketing_spend
            """)

            inserted_count = 0
            error_count = 0

            for row_data in rows_to_insert:
                try:
                    await session.execute(insert_query, row_data)
                    inserted_count += 1
                    if inserted_count % 1000 == 0:
                        print(f"  Inserted {inserted_count:,} rows...")
                        await session.commit()
                except Exception as e:
                    error_count += 1
                    if error_count <= 10:  # Print first 10 errors
                        print(f"  Error inserting row: {e}")

            await session.commit()

            # Get statistics
            result = await session.execute(
                text("""
                    SELECT
                        COUNT(*) as total_rows,
                        COUNT(DISTINCT item_id) as unique_items,
                        MIN(date_local) as min_date,
                        MAX(date_local) as max_date
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                """),
                {"client_id": client_id}
            )
            stats = result.fetchone()

            return {
                'success': True,
                'rows_processed': len(rows_to_insert),
                'rows_inserted': inserted_count,
                'errors': error_count,
                'total_rows_in_table': stats[0] if stats else 0,
                'unique_items': stats[1] if stats else 0,
                'date_range': (stats[2], stats[3]) if stats and stats[2] and stats[3] else None,
            }

        except Exception as e:
            await session.rollback()
            raise


async def main():
    parser = argparse.ArgumentParser(
        description='Import CSV data into ts_demand_daily table (development use only)'
    )
    parser.add_argument(
        '--csv',
        type=str,
        required=True,
        help='Path to CSV file'
    )
    parser.add_argument(
        '--client-id',
        type=str,
        required=True,
        help='Client UUID (must exist in clients table)'
    )
    parser.add_argument(
        '--clear-existing',
        action='store_true',
        help='Clear existing data for this client before importing'
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)

    try:
        result = await import_csv_to_ts_demand_daily(
            csv_path=csv_path,
            client_id=args.client_id,
            clear_existing=args.clear_existing
        )

        print("\n" + "="*60)
        print("Import Complete!")
        print("="*60)
        print(f"Rows processed: {result['rows_processed']:,}")
        print(f"Rows inserted: {result['rows_inserted']:,}")
        if result['errors'] > 0:
            print(f"Errors: {result['errors']}")
        print(f"Total rows in table: {result['total_rows_in_table']:,}")
        print(f"Unique items: {result['unique_items']}")
        if result['date_range']:
            print(f"Date range: {result['date_range'][0]} to {result['date_range'][1]}")
        print("="*60)

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())
