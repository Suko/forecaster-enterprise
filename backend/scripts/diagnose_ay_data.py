"""
Diagnose A-Y SKU Data Quality

Before concluding A-Y performance is a limitation, verify the test data is appropriate.
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
        print("A-Y DATA QUALITY DIAGNOSTIC")
        print("=" * 80)
        print(f"\nFound {len(ay_skus)} A-Y SKUs")

        for sku in ay_skus:
            print(f"\n{'='*80}")
            print(f"SKU: {sku.item_id}")
            print(f"Classification: {sku.abc_class}-{sku.xyz_class} ({sku.demand_pattern})")
            print(f"CV: {float(sku.coefficient_of_variation):.2f} | ADI: {float(sku.average_demand_interval):.2f}")
            print(f"Method: {sku.recommended_method} | History: {sku.history_days_used} days")
            print("=" * 80)

            # Get all data for this SKU using raw SQL
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
                'date': r.date,
                'quantity': r.units_sold
            } for r in records])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')

            # Basic stats
            print(f"\n📊 BASIC STATISTICS")
            print(f"   Total days: {len(df)}")
            print(f"   Date range: {df['date'].min().date()} to {df['date'].max().date()}")
            print(f"   Mean: {df['quantity'].mean():.2f}")
            print(f"   Std: {df['quantity'].std():.2f}")
            print(f"   CV (calculated): {df['quantity'].std() / df['quantity'].mean():.2f}")
            print(f"   Min: {df['quantity'].min():.0f}")
            print(f"   Max: {df['quantity'].max():.0f}")
            print(f"   Median: {df['quantity'].median():.2f}")

            # Zero days
            zero_days = (df['quantity'] == 0).sum()
            zero_pct = zero_days / len(df) * 100
            print(f"\n📉 ZERO-DEMAND DAYS")
            print(f"   Zero days: {zero_days} ({zero_pct:.1f}%)")
            if zero_pct > 20:
                print(f"   ⚠️ HIGH ZERO RATE - may indicate intermittent demand")

            # Outlier detection (IQR method)
            Q1 = df['quantity'].quantile(0.25)
            Q3 = df['quantity'].quantile(0.75)
            IQR = Q3 - Q1
            outliers = df[(df['quantity'] < Q1 - 1.5*IQR) | (df['quantity'] > Q3 + 1.5*IQR)]
            print(f"\n🔍 OUTLIERS (IQR method)")
            print(f"   Q1: {Q1:.2f}, Q3: {Q3:.2f}, IQR: {IQR:.2f}")
            print(f"   Outliers: {len(outliers)} ({len(outliers)/len(df)*100:.1f}%)")
            if len(outliers) > 0:
                print(f"   Outlier values: {sorted(outliers['quantity'].values)}")

            # Trend analysis
            df['day_num'] = range(len(df))
            correlation = df['day_num'].corr(df['quantity'])
            print(f"\n📈 TREND ANALYSIS")
            print(f"   Time correlation: {correlation:.3f}")
            if abs(correlation) > 0.3:
                trend = "increasing" if correlation > 0 else "decreasing"
                print(f"   ⚠️ SIGNIFICANT {trend.upper()} TREND")
            else:
                print(f"   ✅ No strong trend")

            # Split analysis (training vs test period)
            test_days = 30
            train_df = df.iloc[:-test_days]
            test_df = df.iloc[-test_days:]

            print(f"\n🔀 TRAIN/TEST SPLIT ANALYSIS")
            print(f"   Training: {len(train_df)} days ({train_df['date'].min().date()} to {train_df['date'].max().date()})")
            print(f"   Test: {len(test_df)} days ({test_df['date'].min().date()} to {test_df['date'].max().date()})")

            train_mean = train_df['quantity'].mean()
            test_mean = test_df['quantity'].mean()
            mean_shift = (test_mean - train_mean) / train_mean * 100 if train_mean > 0 else 0

            print(f"\n   Training mean: {train_mean:.2f}")
            print(f"   Test mean: {test_mean:.2f}")
            print(f"   Mean shift: {mean_shift:+.1f}%")

            if abs(mean_shift) > 30:
                print(f"   ⚠️ SIGNIFICANT MEAN SHIFT between train and test")
                print(f"      This could explain high MAPE!")

            train_cv = train_df['quantity'].std() / train_df['quantity'].mean() if train_df['quantity'].mean() > 0 else 0
            test_cv = test_df['quantity'].std() / test_df['quantity'].mean() if test_df['quantity'].mean() > 0 else 0

            print(f"\n   Training CV: {train_cv:.2f}")
            print(f"   Test CV: {test_cv:.2f}")

            # Seasonality check (day of week)
            df['dow'] = df['date'].dt.dayofweek
            dow_mean = df.groupby('dow')['quantity'].mean()
            dow_cv = dow_mean.std() / dow_mean.mean() if dow_mean.mean() > 0 else 0

            print(f"\n📅 DAY-OF-WEEK PATTERN")
            print(f"   Day-of-week CV: {dow_cv:.2f}")
            for day, mean in dow_mean.items():
                day_name = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][day]
                print(f"      {day_name}: {mean:.1f}")

            if dow_cv > 0.3:
                print(f"   ⚠️ STRONG DAY-OF-WEEK PATTERN - may need seasonality model")

            # Recent volatility
            recent_30 = df.tail(60).head(30)  # 30 days before test
            recent_cv = recent_30['quantity'].std() / recent_30['quantity'].mean() if recent_30['quantity'].mean() > 0 else 0
            print(f"\n📊 RECENT VOLATILITY (30 days before test)")
            print(f"   Recent CV: {recent_cv:.2f}")
            print(f"   Overall CV: {df['quantity'].std() / df['quantity'].mean():.2f}")

            # Diagnosis
            print(f"\n{'='*80}")
            print("📋 DIAGNOSIS")
            print("=" * 80)

            issues = []
            if zero_pct > 20:
                issues.append("High zero-demand rate (intermittent pattern)")
            if abs(mean_shift) > 30:
                issues.append(f"Large mean shift in test period ({mean_shift:+.1f}%)")
            if len(outliers) > len(df) * 0.1:
                issues.append("Many outliers (>10% of data)")
            if abs(correlation) > 0.3:
                issues.append(f"Strong trend ({correlation:.2f})")
            if dow_cv > 0.3:
                issues.append("Strong day-of-week pattern")
            if len(df) < 90:
                issues.append(f"Limited history ({len(df)} days)")

            if issues:
                print("⚠️ POTENTIAL ISSUES:")
                for issue in issues:
                    print(f"   - {issue}")
            else:
                print("✅ No obvious data quality issues detected")

            # Recommendation
            print(f"\n💡 RECOMMENDATION:")
            if abs(mean_shift) > 30:
                print("   The test period has significantly different demand than training.")
                print("   This is a DISTRIBUTION SHIFT problem, not a model problem.")
                print("   Options:")
                print("   1. Use shorter training window (more recent data)")
                print("   2. Add covariates to explain the shift (Phase 3)")
                print("   3. Accept higher MAPE for this SKU type")
            elif dow_cv > 0.3:
                print("   Strong weekly seasonality detected.")
                print("   Consider: Seasonal models or weekly aggregation")
            elif zero_pct > 20:
                print("   May be incorrectly classified as 'regular' demand.")
                print("   Should potentially be 'intermittent' pattern.")
            else:
                print("   Data looks appropriate for forecasting.")
                print("   A-Y classification may inherently have higher MAPE.")

        print(f"\n{'='*80}")
        print("SUMMARY")
        print("=" * 80)
        print("\nKey question: Is 111.9% MAPE due to:")
        print("  A) Bad test data? → Fix data or test setup")
        print("  B) Distribution shift? → Need covariates (Phase 3)")
        print("  C) Inherent difficulty? → Adjust expectations for A-Y")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

