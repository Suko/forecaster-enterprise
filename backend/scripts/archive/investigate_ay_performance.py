#!/usr/bin/env python3
"""
Investigate A-Y Performance Issue

Deep dive into A-Y SKUs showing high MAPE (111.9%) with Chronos-2.
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd
import numpy as np

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from models.forecast import SKUClassification
from forecasting.services.quality_calculator import QualityCalculator


async def investigate_ay_performance():
    """Investigate A-Y SKU performance"""

    # Get database URL
    database_url = os.getenv("DATABASE_URL", settings.database_url)

    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        print("=" * 80)
        print("A-Y Performance Investigation")
        print("=" * 80)

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

        print(f"\n📦 Found {len(ay_skus)} A-Y SKUs\n")

        quality_calc = QualityCalculator(db)

        for sku in ay_skus:
            item_id = sku.item_id
            client_id = str(sku.client_id)

            print(f"🔍 Analyzing: {item_id}")
            print(f"   Classification: {sku.abc_class}-{sku.xyz_class}")
            print(f"   Pattern: {sku.demand_pattern}")
            print(f"   CV: {sku.coefficient_of_variation:.2f}")
            print(f"   ADI: {sku.average_demand_interval:.2f}")
            print(f"   Expected MAPE: {sku.expected_mape_min:.1f}% - {sku.expected_mape_max:.1f}%")

            # Get historical data
            result = await db.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                    ORDER BY date_local
                """),
                {"item_id": item_id, "client_id": client_id}
            )
            data = result.fetchall()

            if not data:
                print("   ⚠️  No data found\n")
                continue

            df = pd.DataFrame([{"date": row.date_local, "units_sold": float(row.units_sold)} for row in data])
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date")

            # Data statistics
            print(f"\n   📊 Data Statistics:")
            print(f"      Total days: {len(df)}")
            print(f"      Mean: {df['units_sold'].mean():.2f}")
            print(f"      Std: {df['units_sold'].std():.2f}")
            print(f"      Min: {df['units_sold'].min():.2f}")
            print(f"      Max: {df['units_sold'].max():.2f}")
            print(f"      Zero days: {(df['units_sold'] == 0).sum()} ({(df['units_sold'] == 0).sum()/len(df)*100:.1f}%)")

            # Check for outliers
            q1 = df['units_sold'].quantile(0.25)
            q3 = df['units_sold'].quantile(0.75)
            iqr = q3 - q1
            outliers = df[(df['units_sold'] < q1 - 1.5*iqr) | (df['units_sold'] > q3 + 1.5*iqr)]
            print(f"      Outliers: {len(outliers)} ({len(outliers)/len(df)*100:.1f}%)")

            # Check for missing dates
            date_range = pd.date_range(start=df['date'].min(), end=df['date'].max(), freq='D')
            missing_dates = len(date_range) - len(df)
            print(f"      Missing dates: {missing_dates} ({missing_dates/len(date_range)*100:.1f}%)")

            # Recent trend
            recent_30 = df.tail(30)
            older_30 = df.iloc[-60:-30] if len(df) >= 60 else df.iloc[:-30] if len(df) > 30 else df.head(0)

            if len(older_30) > 0:
                recent_mean = recent_30['units_sold'].mean()
                older_mean = older_30['units_sold'].mean()
                trend = ((recent_mean - older_mean) / older_mean * 100) if older_mean > 0 else 0
                print(f"      Trend (last 30 vs previous 30): {trend:+.1f}%")

            print()

        print("=" * 80)
        print("Investigation Complete")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(investigate_ay_performance())

