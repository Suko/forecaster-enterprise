"""
Diagnostic script to test Chronos-2 using Darts library

This helps debug why our custom Chronos-2 wrapper isn't working.
Uses Darts' Chronos2Model which has better error handling.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

load_dotenv()

try:
    from darts import TimeSeries
    from darts.models import Chronos2Model
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("❌ Darts not installed. Install with: pip install darts")
    print("   This script uses Darts to diagnose Chronos-2 issues.")
    sys.exit(1)


async def test_with_darts():
    """Test Chronos-2 using Darts library"""

    # Get database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise")
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get one SKU with data
        result = await db.execute(
            text("""
                SELECT item_id, client_id, MIN(date_local) as min_date, MAX(date_local) as max_date
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 60
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)
        )
        row = result.fetchone()

        if not row:
            print("❌ No data found in database")
            return

        item_id = row.item_id
        client_id = str(row.client_id)
        max_date = row.max_date
        train_end = max_date - timedelta(days=30)

        print(f"📊 Testing with SKU: {item_id}")
        print(f"   Data range: {row.min_date} to {max_date}")
        print(f"   Training up to: {train_end}")
        print()

        # Fetch historical data
        result = await db.execute(
            text("""
                SELECT date_local, units_sold
                FROM ts_demand_daily
                WHERE item_id = :item_id
                AND client_id = :client_id
                AND date_local <= :train_end
                ORDER BY date_local
            """),
            {
                "item_id": item_id,
                "client_id": client_id,
                "train_end": train_end,
            }
        )

        rows = result.fetchall()
        if not rows:
            print("❌ No training data found")
            return

        # Convert to DataFrame
        df = pd.DataFrame([
            {"date": row.date_local, "target": float(row.units_sold)}
            for row in rows
        ])

        print(f"✅ Loaded {len(df)} days of training data")
        print(f"   Mean: {df['target'].mean():.2f}")
        print(f"   Std: {df['target'].std():.2f}")
        print()

        # Convert to Darts TimeSeries
        try:
            series = TimeSeries.from_dataframe(
                df,
                time_col="date",
                value_cols="target"
            )
            print("✅ Created Darts TimeSeries")
        except Exception as e:
            print(f"❌ Failed to create TimeSeries: {e}")
            return

        # Test Chronos-2 with Darts
        print("\n🔬 Testing Chronos-2 via Darts...")
        try:
            model = Chronos2Model()
            print("✅ Model initialized")

            # Predict (no training needed for Chronos-2)
            prediction = model.predict(series=series, n=30)
            print(f"✅ Prediction generated: {len(prediction)} points")
            print(f"   Mean forecast: {prediction.values().mean():.2f}")
            print(f"   Date range: {prediction.start_time()} to {prediction.end_time()}")

            # Convert to DataFrame for inspection
            pred_df = prediction.pd_dataframe()
            print(f"\n📈 Sample predictions (first 5):")
            print(pred_df.head())

            return True

        except Exception as e:
            print(f"❌ Chronos-2 prediction failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_our_wrapper():
    """Test our custom Chronos-2 wrapper for comparison"""
    print("\n" + "="*60)
    print("Testing Our Custom Chronos-2 Wrapper")
    print("="*60)

    from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model

    # Get database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise")
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get one SKU
        result = await db.execute(
            text("""
                SELECT item_id, client_id, MAX(date_local) as max_date
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 60
                LIMIT 1
            """)
        )
        row = result.fetchone()

        if not row:
            return False

        item_id = row.item_id
        client_id = str(row.client_id)
        train_end = row.max_date - timedelta(days=30)

        # Fetch data using our data access
        from forecasting.services.data_access import DataAccess
        data_access = DataAccess(db)

        context_df = await data_access.fetch_historical_data(
            client_id=client_id,
            item_ids=[item_id],
            end_date=train_end,
        )

        if context_df.empty:
            print("❌ No data from DataAccess")
            return False

        print(f"✅ Loaded {len(context_df)} rows via DataAccess")
        print(f"   Columns: {list(context_df.columns)}")

        # Test our model
        try:
            model = OurChronos2Model()
            await model.initialize()
            print("✅ Our model initialized")

            # Filter for this item
            item_context = context_df[context_df["id"] == item_id].copy()
            print(f"✅ Filtered to {len(item_context)} rows for {item_id}")

            predictions_df = await model.predict(
                context_df=item_context,
                prediction_length=30,
            )

            print(f"✅ Our model prediction generated")
            print(f"   Shape: {predictions_df.shape}")
            print(f"   Columns: {list(predictions_df.columns)}")
            if not predictions_df.empty:
                print(f"   Sample:\n{predictions_df.head()}")
            else:
                print("   ⚠️  Empty DataFrame!")

            return not predictions_df.empty

        except Exception as e:
            print(f"❌ Our model failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    print("="*60)
    print("Chronos-2 Diagnostic Tool")
    print("="*60)
    print()

    # Test with Darts first (reference implementation)
    print("Step 1: Testing with Darts Chronos2Model (reference)")
    print("-"*60)
    darts_works = await test_with_darts()

    # Test our wrapper
    print("\n")
    our_works = await test_our_wrapper()

    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    print(f"Darts Chronos2Model: {'✅ Works' if darts_works else '❌ Failed'}")
    print(f"Our Custom Wrapper:  {'✅ Works' if our_works else '❌ Failed'}")

    if darts_works and not our_works:
        print("\n💡 Recommendation: Consider using Darts Chronos2Model")
        print("   Our wrapper has issues that Darts handles correctly.")
    elif not darts_works:
        print("\n⚠️  Both implementations failed - issue may be with:")
        print("   - Chronos-2 model installation")
        print("   - Data format")
        print("   - Model initialization")


if __name__ == "__main__":
    asyncio.run(main())

