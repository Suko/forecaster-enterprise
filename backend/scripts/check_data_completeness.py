"""
Check Data Completeness for A-Y SKUs

Analyzes:
1. Date range coverage (expected vs actual)
2. Missing days in the time series
3. Zero-demand days vs missing days
4. Data gaps that could affect forecasting
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.forecast import SKUClassification
from config import settings


async def main():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get A-Y SKUs
        result = await db.execute(
            select(SKUClassification).where(
                SKUClassification.abc_class == "A",
                SKUClassification.xyz_class == "Y"
            )
        )
        ay_skus = result.scalars().all()
        
        if not ay_skus:
            print("❌ No A-Y SKUs found")
            return
        
        print("=" * 80)
        print("A-Y DATA COMPLETENESS CHECK")
        print("=" * 80)
        print(f"\nFound {len(ay_skus)} A-Y SKUs")
        print("\nChecking for:")
        print("  - Missing days in time series")
        print("  - Date range gaps")
        print("  - ETL data pull issues")
        print("=" * 80)
        
        for sku in ay_skus:
            print(f"\n{'='*80}")
            print(f"SKU: {sku.item_id}")
            print(f"Classification: {sku.abc_class}-{sku.xyz_class} ({sku.demand_pattern})")
            print(f"History used: {sku.history_days_used} days")
            print("=" * 80)
            
            # Get all data for this SKU
            result = await db.execute(
                text("""
                    SELECT date_local as date, units_sold
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                    ORDER BY date_local
                """),
                {"item_id": sku.item_id, "client_id": sku.client_id}
            )
            records = result.fetchall()
            
            if not records:
                print("❌ No data found")
                continue
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                'date': pd.to_datetime(r.date),
                'quantity': float(r.units_sold)
            } for r in records])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Expected date range (continuous)
            min_date = df['date'].min()
            max_date = df['date'].max()
            expected_days = (max_date - min_date).days + 1
            actual_days = len(df)
            
            print(f"\n📅 DATE RANGE ANALYSIS")
            print(f"   First date: {min_date.date()}")
            print(f"   Last date: {max_date.date()}")
            print(f"   Expected days (continuous): {expected_days}")
            print(f"   Actual days (in database): {actual_days}")
            
            missing_days = expected_days - actual_days
            completeness = (actual_days / expected_days * 100) if expected_days > 0 else 0
            
            print(f"   Missing days: {missing_days} ({100 - completeness:.1f}%)")
            print(f"   Completeness: {completeness:.1f}%")
            
            if missing_days > 0:
                print(f"   ⚠️  DATA GAPS DETECTED!")
            
            # Find missing dates
            if missing_days > 0:
                date_range = pd.date_range(start=min_date, end=max_date, freq='D')
                missing_dates = set(date_range) - set(df['date'])
                missing_dates_sorted = sorted(missing_dates)
                
                print(f"\n📋 MISSING DATES ({len(missing_dates_sorted)} days)")
                if len(missing_dates_sorted) <= 20:
                    for missing_date in missing_dates_sorted:
                        print(f"   - {missing_date.date()}")
                else:
                    print(f"   First 10 missing dates:")
                    for missing_date in missing_dates_sorted[:10]:
                        print(f"   - {missing_date.date()}")
                    print(f"   ... and {len(missing_dates_sorted) - 10} more")
                
                # Check for gaps (consecutive missing days)
                gaps = []
                if len(missing_dates_sorted) > 1:
                    gap_start = missing_dates_sorted[0]
                    gap_end = missing_dates_sorted[0]
                    
                    for i in range(1, len(missing_dates_sorted)):
                        if (missing_dates_sorted[i] - missing_dates_sorted[i-1]).days == 1:
                            gap_end = missing_dates_sorted[i]
                        else:
                            if gap_start == gap_end:
                                gaps.append((gap_start, gap_end, 1))
                            else:
                                gaps.append((gap_start, gap_end, (gap_end - gap_start).days + 1))
                            gap_start = missing_dates_sorted[i]
                            gap_end = missing_dates_sorted[i]
                    
                    # Add last gap
                    if gap_start == gap_end:
                        gaps.append((gap_start, gap_end, 1))
                    else:
                        gaps.append((gap_start, gap_end, (gap_end - gap_start).days + 1))
                
                if gaps:
                    print(f"\n🔍 GAP ANALYSIS")
                    print(f"   Total gaps: {len(gaps)}")
                    for gap_start, gap_end, gap_length in gaps[:10]:
                        if gap_length == 1:
                            print(f"   - Single missing day: {gap_start.date()}")
                        else:
                            print(f"   - Gap: {gap_start.date()} to {gap_end.date()} ({gap_length} days)")
                    if len(gaps) > 10:
                        print(f"   ... and {len(gaps) - 10} more gaps")
            
            # Zero-demand days
            zero_days = (df['quantity'] == 0).sum()
            zero_pct = zero_days / len(df) * 100
            
            print(f"\n📊 DATA QUALITY")
            print(f"   Total records: {len(df)}")
            print(f"   Zero-demand days: {zero_days} ({zero_pct:.1f}%)")
            print(f"   Non-zero days: {len(df) - zero_days} ({100 - zero_pct:.1f}%)")
            
            # Check for test period specifically
            test_days = 30
            if len(df) >= test_days:
                train_df = df.iloc[:-test_days]
                test_df = df.iloc[-test_days:]
                
                # Check if test period has missing days
                test_min = test_df['date'].min()
                test_max = test_df['date'].max()
                test_expected = (test_max - test_min).days + 1
                test_actual = len(test_df)
                test_missing = test_expected - test_actual
                
                print(f"\n🧪 TEST PERIOD ANALYSIS (last {test_days} days)")
                print(f"   Test period: {test_min.date()} to {test_max.date()}")
                print(f"   Expected days: {test_expected}")
                print(f"   Actual days: {test_actual}")
                print(f"   Missing days: {test_missing}")
                
                if test_missing > 0:
                    print(f"   ⚠️  TEST PERIOD HAS MISSING DAYS!")
                    print(f"      This could significantly affect MAPE calculation!")
                
                # Check training period
                train_min = train_df['date'].min()
                train_max = train_df['date'].max()
                train_expected = (train_max - train_min).days + 1
                train_actual = len(train_df)
                train_missing = train_expected - train_actual
                
                print(f"\n📚 TRAINING PERIOD ANALYSIS")
                print(f"   Training period: {train_min.date()} to {train_max.date()}")
                print(f"   Expected days: {train_expected}")
                print(f"   Actual days: {train_actual}")
                print(f"   Missing days: {train_missing}")
                print(f"   Completeness: {(train_actual / train_expected * 100):.1f}%")
                
                if train_missing > 0:
                    print(f"   ⚠️  TRAINING PERIOD HAS MISSING DAYS!")
                    print(f"      This could affect model training!")
            
            # Summary diagnosis
            print(f"\n{'='*80}")
            print("📋 DIAGNOSIS")
            print("=" * 80)
            
            issues = []
            if missing_days > 0:
                issues.append(f"Missing {missing_days} days ({100 - completeness:.1f}% incomplete)")
            if missing_days > expected_days * 0.05:  # More than 5% missing
                issues.append("Significant data gaps (>5%)")
            if test_missing > 0:
                issues.append(f"Test period missing {test_missing} days")
            if train_missing > train_expected * 0.05:
                issues.append(f"Training period missing {train_missing} days (>5%)")
            
            if issues:
                print("⚠️  DATA QUALITY ISSUES DETECTED:")
                for issue in issues:
                    print(f"   - {issue}")
                print("\n💡 IMPACT:")
                print("   - Missing days can cause:")
                print("     • Model training on incomplete data")
                print("     • MAPE calculation errors (wrong date alignment)")
                print("     • Forecast accuracy degradation")
                print("\n🔧 RECOMMENDATION:")
                print("   - Check ETL process for data pull")
                print("   - Verify date range coverage")
                print("   - Consider filling missing days with 0 or interpolation")
            else:
                print("✅ Data completeness looks good")
                print("   No significant gaps detected")
        
        print(f"\n{'='*80}")
        print("SUMMARY")
        print("=" * 80)
        print("\nIf missing days are found:")
        print("  → Check ETL script for date range coverage")
        print("  → Verify data source has complete date range")
        print("  → Consider if missing days should be filled with 0")
        print("  → Missing days in test period will affect MAPE calculation")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

