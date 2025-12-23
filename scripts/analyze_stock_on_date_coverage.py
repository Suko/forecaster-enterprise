#!/usr/bin/env python3
"""
Analyze stock_on_date coverage in ts_demand_daily table.

This script investigates how often stock_on_date is NULL, which affects
the simulation's ability to use real historical stock data vs calculated fallback.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict
from decimal import Decimal

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

# Load environment variables if .env exists
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, func
from models.database import get_async_session_local
from models.product import Product
import pandas as pd


async def analyze_stock_coverage(client_id: str, item_ids: list = None):
    """Analyze stock_on_date coverage for a client"""
    
    async_session = get_async_session_local()
    
    async with async_session() as db:
        # Overall statistics
        print("=" * 80)
        print("STOCK_ON_DATE COVERAGE ANALYSIS")
        print("=" * 80)
        print()
        
        # 1. Overall coverage statistics
        query = text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(stock_on_date) as records_with_stock,
                COUNT(*) - COUNT(stock_on_date) as records_null,
                ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
            FROM ts_demand_daily
            WHERE client_id = :client_id
        """)
        
        result = await db.execute(query, {"client_id": client_id})
        row = result.one()
        
        print("📊 OVERALL STATISTICS")
        print("-" * 80)
        print(f"Total records:           {row.total_records:,}")
        print(f"Records with stock_on_date: {row.records_with_stock:,}")
        print(f"Records with NULL:       {row.records_null:,}")
        print(f"Coverage:                {row.coverage_pct}%")
        print()
        
        # 2. Coverage by item_id
        if item_ids:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as total_records,
                    COUNT(stock_on_date) as records_with_stock,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct,
                    MIN(date_local) as first_date,
                    MAX(date_local) as last_date
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = ANY(:item_ids)
                GROUP BY item_id
                ORDER BY coverage_pct ASC, records_null DESC
            """)
            params = {"client_id": client_id, "item_ids": item_ids}
        else:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as total_records,
                    COUNT(stock_on_date) as records_with_stock,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct,
                    MIN(date_local) as first_date,
                    MAX(date_local) as last_date
                FROM ts_demand_daily
                WHERE client_id = :client_id
                GROUP BY item_id
                ORDER BY coverage_pct ASC, records_null DESC
            """)
            params = {"client_id": client_id}
        
        result = await db.execute(query, params)
        rows = result.all()
        
        print("📦 COVERAGE BY ITEM_ID")
        print("-" * 80)
        print(f"{'Item ID':<30} {'Total':<10} {'With Stock':<12} {'NULL':<10} {'Coverage':<12} {'Date Range':<20}")
        print("-" * 80)
        
        for row in rows:
            date_range = f"{row.first_date} to {row.last_date}"
            print(f"{row.item_id:<30} {row.total_records:<10} {row.records_with_stock:<12} {row.records_null:<10} {row.coverage_pct:<12}% {date_range:<20}")
        
        print()
        
        # 3. Coverage by date range (monthly breakdown)
        if item_ids:
            query = text("""
                SELECT 
                    DATE_TRUNC('month', date_local) as month,
                    COUNT(*) as total_records,
                    COUNT(stock_on_date) as records_with_stock,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = ANY(:item_ids)
                GROUP BY DATE_TRUNC('month', date_local)
                ORDER BY month ASC
            """)
            params = {"client_id": client_id, "item_ids": item_ids}
        else:
            query = text("""
                SELECT 
                    DATE_TRUNC('month', date_local) as month,
                    COUNT(*) as total_records,
                    COUNT(stock_on_date) as records_with_stock,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
                FROM ts_demand_daily
                WHERE client_id = :client_id
                GROUP BY DATE_TRUNC('month', date_local)
                ORDER BY month ASC
            """)
            params = {"client_id": client_id}
        
        result = await db.execute(query, params)
        rows = result.all()
        
        print("📅 COVERAGE BY MONTH")
        print("-" * 80)
        print(f"{'Month':<15} {'Total':<10} {'With Stock':<12} {'NULL':<10} {'Coverage':<12}")
        print("-" * 80)
        
        for row in rows:
            month_str = str(row.month)[:7]  # YYYY-MM
            print(f"{month_str:<15} {row.total_records:<10} {row.records_with_stock:<12} {row.records_null:<10} {row.coverage_pct:<12}%")
        
        print()
        
        # 4. Items with worst coverage (top 10)
        if item_ids:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as total_records,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id = ANY(:item_ids)
                GROUP BY item_id
                HAVING COUNT(*) - COUNT(stock_on_date) > 0
                ORDER BY records_null DESC
                LIMIT 10
            """)
            params = {"client_id": client_id, "item_ids": item_ids}
        else:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as total_records,
                    COUNT(*) - COUNT(stock_on_date) as records_null,
                    ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
                FROM ts_demand_daily
                WHERE client_id = :client_id
                GROUP BY item_id
                HAVING COUNT(*) - COUNT(stock_on_date) > 0
                ORDER BY records_null DESC
                LIMIT 10
            """)
            params = {"client_id": client_id}
        
        result = await db.execute(query, params)
        rows = result.all()
        
        if rows:
            print("⚠️  TOP 10 ITEMS WITH MOST NULL VALUES")
            print("-" * 80)
            print(f"{'Item ID':<30} {'Total Records':<15} {'NULL Records':<15} {'Coverage':<12}")
            print("-" * 80)
            
            for row in rows:
                print(f"{row.item_id:<30} {row.total_records:<15} {row.records_null:<15} {row.coverage_pct:<12}%")
            print()
        
        # 5. Date range analysis (first and last dates with NULL)
        if item_ids:
            query = text("""
                SELECT 
                    MIN(date_local) as first_null_date,
                    MAX(date_local) as last_null_date,
                    COUNT(DISTINCT date_local) as distinct_dates_with_null
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND stock_on_date IS NULL
                  AND item_id = ANY(:item_ids)
            """)
            params = {"client_id": client_id, "item_ids": item_ids}
        else:
            query = text("""
                SELECT 
                    MIN(date_local) as first_null_date,
                    MAX(date_local) as last_null_date,
                    COUNT(DISTINCT date_local) as distinct_dates_with_null
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND stock_on_date IS NULL
            """)
            params = {"client_id": client_id}
        
        result = await db.execute(query, params)
        row = result.one()
        
        if row.first_null_date:
            print("📆 NULL VALUE DATE RANGE")
            print("-" * 80)
            print(f"First NULL date:         {row.first_null_date}")
            print(f"Last NULL date:          {row.last_null_date}")
            print(f"Distinct dates with NULL: {row.distinct_dates_with_null}")
            print()
        
        # 6. Summary recommendations
        # Get overall coverage from first query
        query = text("""
            SELECT 
                ROUND(100.0 * COUNT(stock_on_date) / COUNT(*), 2) as coverage_pct
            FROM ts_demand_daily
            WHERE client_id = :client_id
        """)
        result = await db.execute(query, {"client_id": client_id})
        overall_coverage = float(result.one().coverage_pct)
        
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        if overall_coverage >= 90:
            print("✅ Excellent coverage! Real stock data is available for most days.")
        elif overall_coverage >= 75:
            print("⚠️  Good coverage, but ~25% of days use calculated fallback.")
            print("   Consider: This may affect simulation accuracy for those days.")
        elif overall_coverage >= 50:
            print("⚠️  Moderate coverage. ~50% of days use calculated fallback.")
            print("   Consider: Simulation may have limited accuracy for real stock comparison.")
        else:
            print("❌ Low coverage. Most days use calculated fallback.")
            print("   Consider: Simulation real stock comparison may be unreliable.")
        
        # 7. Find products with zero stock_on_date (not NULL, but 0)
        if item_ids:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as zero_stock_days,
                    MIN(date_local) as first_zero_date,
                    MAX(date_local) as last_zero_date,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ts_demand_daily WHERE client_id = :client_id AND item_id = t.item_id), 2) as zero_stock_pct
                FROM ts_demand_daily t
                WHERE client_id = :client_id
                  AND stock_on_date = 0
                  AND item_id = ANY(:item_ids)
                GROUP BY item_id
                ORDER BY zero_stock_days DESC
            """)
            params = {"client_id": client_id, "item_ids": item_ids}
        else:
            query = text("""
                SELECT 
                    item_id,
                    COUNT(*) as zero_stock_days,
                    MIN(date_local) as first_zero_date,
                    MAX(date_local) as last_zero_date,
                    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM ts_demand_daily WHERE client_id = :client_id AND item_id = t.item_id), 2) as zero_stock_pct
                FROM ts_demand_daily t
                WHERE client_id = :client_id
                  AND stock_on_date = 0
                GROUP BY item_id
                ORDER BY zero_stock_days DESC
            """)
            params = {"client_id": client_id}
        
        result = await db.execute(query, params)
        rows = result.all()
        
        if rows:
            print("📉 PRODUCTS WITH ZERO STOCK (stock_on_date = 0)")
            print("-" * 80)
            print(f"{'Item ID':<30} {'Zero Stock Days':<18} {'% of Total':<12} {'First Zero':<15} {'Last Zero':<15}")
            print("-" * 80)
            
            for row in rows:
                print(f"{row.item_id:<30} {row.zero_stock_days:<18} {row.zero_stock_pct:<12}% {str(row.first_zero_date):<15} {str(row.last_zero_date):<15}")
            print()
            
            # Summary
            total_zero_days = sum(r.zero_stock_days for r in rows)
            print(f"Total days with zero stock: {total_zero_days:,}")
            print(f"Products with at least one zero stock day: {len(rows)}")
            print()
        else:
            print("✅ No products found with zero stock_on_date")
            print()
        
        print()
        print("=" * 80)


async def find_clients(db: AsyncSession):
    """Find all clients with data in ts_demand_daily"""
    query = text("""
        SELECT DISTINCT client_id, COUNT(*) as record_count
        FROM ts_demand_daily
        GROUP BY client_id
        ORDER BY record_count DESC
    """)
    
    result = await db.execute(query)
    return result.all()


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze stock_on_date coverage")
    parser.add_argument("--client-id", help="Client ID to analyze (if not provided, will list available clients)")
    parser.add_argument("--item-ids", nargs="+", help="Optional: specific item IDs to analyze")
    parser.add_argument("--list-clients", action="store_true", help="List all available clients and exit")
    
    args = parser.parse_args()
    
    async_session = get_async_session_local()
    
    async with async_session() as db:
        if args.list_clients or not args.client_id:
            print("=" * 80)
            print("AVAILABLE CLIENTS")
            print("=" * 80)
            clients = await find_clients(db)
            
            if not clients:
                print("❌ No clients found in ts_demand_daily table")
                return
            
            print(f"{'Client ID':<40} {'Records':<15}")
            print("-" * 80)
            for row in clients:
                print(f"{str(row.client_id):<40} {row.record_count:<15,}")
            print()
            print(f"Total clients: {len(clients)}")
            print()
            print("Usage: python scripts/analyze_stock_on_date_coverage.py --client-id <uuid>")
            
            if not args.client_id:
                return
        
        await analyze_stock_coverage(args.client_id, args.item_ids)


if __name__ == "__main__":
    asyncio.run(main())

