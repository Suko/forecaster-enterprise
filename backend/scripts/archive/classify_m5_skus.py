#!/usr/bin/env python3
"""
Classify M5 SKUs

Generates forecasts for M5 SKUs to trigger automatic classification.
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from uuid import uuid4

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from models.user import User
from forecasting.services.forecast_service import ForecastService


async def classify_m5_skus():
    """Generate forecasts for M5 SKUs to trigger classification"""

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
        print("Classify M5 SKUs")
        print("=" * 80)

        # Get M5 SKUs
        result = await db.execute(
            text("""
                SELECT DISTINCT item_id, client_id
                FROM ts_demand_daily
                WHERE item_id LIKE 'M5_%'
                LIMIT 20
            """)
        )
        m5_skus = result.fetchall()

        if not m5_skus:
            print("❌ No M5 SKUs found in database")
            return

        print(f"\n📦 Found {len(m5_skus)} M5 SKUs")

        # Get client_id and user
        client_id = str(m5_skus[0][1])

        # Get or create user
        result = await db.execute(
            select(User).where(User.email == "test@example.com").limit(1)
        )
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=str(uuid4()),
                email="test@example.com",
                hashed_password="test",
                client_id=client_id,
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        user_id = user.id

        # Get item_ids
        item_ids = [row[0] for row in m5_skus]

        print(f"\n🔮 Generating forecasts for {len(item_ids)} M5 SKUs...")
        print("   This will trigger automatic classification")

        # Generate forecast (will classify automatically)
        service = ForecastService(db)

        try:
            forecast_run = await service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=item_ids,
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=True,
            )

            print(f"\n✅ Forecast generated: {forecast_run.forecast_run_id}")
            print(f"   Status: {forecast_run.status}")

            # Check classifications
            if hasattr(forecast_run, 'sku_classifications_data') and forecast_run.sku_classifications_data:
                print(f"\n📊 Classifications created: {len(forecast_run.sku_classifications_data)} SKUs")

                # Show sample classifications
                for idx, (item_id, classification) in enumerate(list(forecast_run.sku_classifications_data.items())[:5], 1):
                    print(f"\n[{idx}] {item_id}")
                    print(f"    ABC: {classification.get('abc_class', 'N/A')}")
                    print(f"    XYZ: {classification.get('xyz_class', 'N/A')}")
                    print(f"    Pattern: {classification.get('demand_pattern', 'N/A')}")
                    print(f"    Forecastability: {classification.get('forecastability_score', 0):.2f}")
                    print(f"    Recommended: {classification.get('recommended_method', 'N/A')}")
            else:
                print("\n⚠️  No classifications found in forecast run")

        except Exception as e:
            print(f"\n❌ Forecast generation failed: {e}")
            import traceback
            traceback.print_exc()

        print("\n" + "=" * 80)
        print("✅ Classification Complete!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(classify_m5_skus())

