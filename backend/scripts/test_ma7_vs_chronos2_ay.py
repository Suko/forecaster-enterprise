#!/usr/bin/env python3
"""
Test MA7 vs Chronos-2 on A-Y SKUs

Compares MA7 and Chronos-2 performance on A-Y SKUs to determine best method.
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
from models.forecast import ForecastRun, ForecastResult, SKUClassification
from models.user import User
from forecasting.services.forecast_service import ForecastService
from forecasting.services.quality_calculator import QualityCalculator


async def test_ma7_vs_chronos2_ay():
    """Compare MA7 vs Chronos-2 on A-Y SKUs"""

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
        print("MA7 vs Chronos-2 Comparison - A-Y SKUs")
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

        print(f"\n📦 Found {len(ay_skus)} A-Y SKUs")

        # Get user
        result = await db.execute(
            select(User).where(User.email == "test@example.com").limit(1)
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Test user not found")
            return

        service = ForecastService(db)
        quality_calc = QualityCalculator(db)

        test_days = 30
        prediction_length = 7

        print(f"\n🧪 Testing MA7 vs Chronos-2 on {len(ay_skus)} A-Y SKUs...")
        print(f"   Test period: Last {test_days} days")
        print(f"   Prediction length: {prediction_length} days\n")

        results = []

        for idx, classification in enumerate(ay_skus, 1):
            item_id = classification.item_id
            client_id = str(classification.client_id)

            print(f"[{idx}/{len(ay_skus)}] {item_id}")
            print(f"   CV: {classification.coefficient_of_variation:.2f}, "
                  f"Expected MAPE: {classification.expected_mape_min:.1f}-{classification.expected_mape_max:.1f}%")

            # Get date range
            result = await db.execute(
                text("""
                    SELECT MIN(date_local) as min_date, MAX(date_local) as max_date
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                """),
                {"item_id": item_id, "client_id": client_id}
            )
            row = result.fetchone()

            if not row or not row.min_date:
                print(f"  ⚠️  No data found\n")
                continue

            max_date = row.max_date
            test_start = max_date - timedelta(days=test_days - 1)
            train_end = test_start - timedelta(days=1)

            # Test Chronos-2 (with baseline to get both methods)
            try:
                forecast_run_chronos = await service.generate_forecast(
                    client_id=client_id,
                    user_id=user.id,
                    item_ids=[item_id],
                    prediction_length=prediction_length,
                    primary_model="chronos-2",
                    include_baseline=True,  # This will add MA7 to methods_to_run
                    training_end_date=train_end,
                )

                if forecast_run_chronos.status != "completed":
                    print(f"  ⚠️  Chronos-2 failed: {forecast_run_chronos.error_message}\n")
                    continue

                predictions_chronos = await service.get_forecast_results(
                    forecast_run_id=forecast_run_chronos.forecast_run_id,
                    method="chronos-2",
                )

                if item_id not in predictions_chronos:
                    print(f"  ⚠️  No Chronos-2 predictions\n")
                    continue

                pred_data_chronos = predictions_chronos[item_id]

                # Get MA7 predictions from the same forecast run (since include_baseline=True)
                predictions_ma7 = await service.get_forecast_results(
                    forecast_run_id=forecast_run_chronos.forecast_run_id,
                    method="statistical_ma7",
                )

                if item_id not in predictions_ma7:
                    # Check what methods are available
                    result = await db.execute(
                        text("""
                            SELECT DISTINCT method
                            FROM forecast_results
                            WHERE forecast_run_id = :forecast_run_id
                        """),
                        {"forecast_run_id": str(forecast_run_chronos.forecast_run_id)}
                    )
                    available_methods = [row[0] for row in result.fetchall()]
                    print(f"  ⚠️  No MA7 predictions. Available methods: {available_methods}\n")
                    continue

                pred_data_ma7 = predictions_ma7[item_id]

            except Exception as e:
                print(f"  ⚠️  Error: {e}\n")
                continue

                if forecast_run_ma7.status != "completed":
                    print(f"  ⚠️  MA7 failed: {forecast_run_ma7.status} - {forecast_run_ma7.error_message}\n")
                    continue

                # Debug: Check what methods are stored
                result = await db.execute(
                    text("""
                        SELECT DISTINCT method
                        FROM forecast_results
                        WHERE forecast_run_id = :forecast_run_id
                    """),
                    {"forecast_run_id": str(forecast_run_ma7.forecast_run_id)}
                )
                stored_methods = [row[0] for row in result.fetchall()]
                print(f"  🔍 Stored methods: {stored_methods}")

                predictions_ma7 = await service.get_forecast_results(
                    forecast_run_id=forecast_run_ma7.forecast_run_id,
                    method="statistical_ma7",
                )

                if item_id not in predictions_ma7:
                    # Try without method filter to see what we have
                    all_predictions = await service.get_forecast_results(
                        forecast_run_id=forecast_run_ma7.forecast_run_id,
                        method=None,
                    )
                    print(f"  🔍 All predictions (no filter): {list(all_predictions.keys())}")
                    print(f"  ⚠️  No MA7 predictions for {item_id}\n")
                    continue

                pred_data_ma7 = predictions_ma7[item_id]

            except Exception as e:
                print(f"  ⚠️  MA7 error: {e}\n")
                continue

            # Get actuals
            result = await db.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                    AND date_local >= :test_start AND date_local <= :max_date
                    ORDER BY date_local
                """),
                {"item_id": item_id, "client_id": client_id, "test_start": test_start, "max_date": max_date}
            )
            actuals = result.fetchall()

            if len(actuals) < prediction_length:
                print(f"  ⚠️  Insufficient actuals ({len(actuals)} < {prediction_length})\n")
                continue

            # Calculate metrics
            actual_values = [float(row.units_sold) for row in actuals[:prediction_length]]
            pred_values_chronos = [float(p['point_forecast']) for p in pred_data_chronos[:prediction_length]]
            pred_values_ma7 = [float(p['point_forecast']) for p in pred_data_ma7[:prediction_length]]

            mape_chronos = quality_calc.calculate_mape(actual_values, pred_values_chronos)
            mape_ma7 = quality_calc.calculate_mape(actual_values, pred_values_ma7)

            mae_chronos = quality_calc.calculate_mae(actual_values, pred_values_chronos)
            mae_ma7 = quality_calc.calculate_mae(actual_values, pred_values_ma7)

            rmse_chronos = quality_calc.calculate_rmse(actual_values, pred_values_chronos)
            rmse_ma7 = quality_calc.calculate_rmse(actual_values, pred_values_ma7)

            # Determine winner
            if mape_ma7 < mape_chronos:
                winner = "MA7"
                improvement = mape_chronos - mape_ma7
                improvement_pct = (improvement / mape_chronos * 100) if mape_chronos > 0 else 0
            elif mape_chronos < mape_ma7:
                winner = "Chronos-2"
                improvement = mape_ma7 - mape_chronos
                improvement_pct = (improvement / mape_ma7 * 100) if mape_ma7 > 0 else 0
            else:
                winner = "Tie"
                improvement = 0
                improvement_pct = 0

            results.append({
                "item_id": item_id,
                "mape_chronos2": mape_chronos,
                "mape_ma7": mape_ma7,
                "mae_chronos2": mae_chronos,
                "mae_ma7": mae_ma7,
                "rmse_chronos2": rmse_chronos,
                "rmse_ma7": rmse_ma7,
                "winner": winner,
                "improvement": improvement,
                "improvement_pct": improvement_pct,
                "expected_mape_min": classification.expected_mape_min,
                "expected_mape_max": classification.expected_mape_max,
            })

            # Check if within expected range
            in_range_chronos = classification.expected_mape_min <= mape_chronos <= classification.expected_mape_max
            in_range_ma7 = classification.expected_mape_min <= mape_ma7 <= classification.expected_mape_max

            status_chronos = "✅" if in_range_chronos else "⚠️"
            status_ma7 = "✅" if in_range_ma7 else "⚠️"

            print(f"  {status_chronos} Chronos-2: {mape_chronos:.1f}% MAPE, {mae_chronos:.2f} MAE")
            print(f"  {status_ma7} MA7: {mape_ma7:.1f}% MAPE, {mae_ma7:.2f} MAE")
            print(f"  🏆 Winner: {winner} (improvement: {improvement:.1f}%, {improvement_pct:.1f}%)")
            print()

        # Summary
        if not results:
            print("\n❌ No results to analyze")
            return

        df = pd.DataFrame(results)

        print("=" * 80)
        print("Results Summary")
        print("=" * 80)

        print(f"\n📊 Overall Performance:")
        print(f"   Chronos-2 Average MAPE: {df['mape_chronos2'].mean():.1f}%")
        print(f"   MA7 Average MAPE: {df['mape_ma7'].mean():.1f}%")
        print(f"   Difference: {df['mape_chronos2'].mean() - df['mape_ma7'].mean():.1f} percentage points")

        print(f"\n📊 Winner Distribution:")
        winners = df['winner'].value_counts()
        for winner, count in winners.items():
            print(f"   {winner}: {count}/{len(df)} ({count/len(df)*100:.1f}%)")

        print(f"\n📊 Within Expected Range:")
        chronos_in_range = ((df['mape_chronos2'] >= df['expected_mape_min']) &
                           (df['mape_chronos2'] <= df['expected_mape_max'])).sum()
        ma7_in_range = ((df['mape_ma7'] >= df['expected_mape_min']) &
                       (df['mape_ma7'] <= df['expected_mape_max'])).sum()
        print(f"   Chronos-2: {chronos_in_range}/{len(df)} ({chronos_in_range/len(df)*100:.1f}%)")
        print(f"   MA7: {ma7_in_range}/{len(df)} ({ma7_in_range/len(df)*100:.1f}%)")

        print(f"\n📊 Average Improvement:")
        ma7_wins = df[df['winner'] == 'MA7']
        chronos_wins = df[df['winner'] == 'Chronos-2']
        if len(ma7_wins) > 0:
            print(f"   When MA7 wins: {ma7_wins['improvement'].mean():.1f}% improvement")
        if len(chronos_wins) > 0:
            print(f"   When Chronos-2 wins: {chronos_wins['improvement'].mean():.1f}% improvement")

        # Recommendation
        print(f"\n💡 Recommendation:")
        if df['mape_ma7'].mean() < df['mape_chronos2'].mean():
            improvement = df['mape_chronos2'].mean() - df['mape_ma7'].mean()
            print(f"   ✅ Use MA7 for A-Y SKUs")
            print(f"   📈 Average improvement: {improvement:.1f} percentage points")
            print(f"   🎯 Action: Update method recommendation for A-Y classification")
        else:
            improvement = df['mape_ma7'].mean() - df['mape_chronos2'].mean()
            print(f"   ✅ Keep Chronos-2 for A-Y SKUs")
            print(f"   📈 Chronos-2 is {improvement:.1f} percentage points better")
            print(f"   🔍 Action: Investigate why Chronos-2 MAPE is still high")

        # Save results
        output_file = backend_dir / "reports" / f"ma7_vs_chronos2_ay_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")

        print("\n" + "=" * 80)
        print("✅ Test Complete!")
        print("=" * 80)

        return df


if __name__ == "__main__":
    asyncio.run(test_ma7_vs_chronos2_ay())

