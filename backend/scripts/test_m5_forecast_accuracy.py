#!/usr/bin/env python3
"""
Test Forecast Accuracy for M5 SKUs

Tests forecast accuracy and compares with expected MAPE ranges from classifications.
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
from uuid import uuid4


async def test_m5_forecast_accuracy():
    """Test forecast accuracy for M5 SKUs and compare with expected ranges"""

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
        print("M5 Forecast Accuracy Test")
        print("=" * 80)

        # Get M5 SKUs with classifications
        result = await db.execute(
            select(SKUClassification).where(
                SKUClassification.item_id.like('M5_%')
            ).limit(10)
        )
        classifications = result.scalars().all()

        if not classifications:
            print("❌ No M5 classifications found")
            return

        print(f"\n📦 Testing {len(classifications)} M5 SKUs\n")

        # Get user
        result = await db.execute(
            select(User).where(User.email == "test@example.com").limit(1)
        )
        user = result.scalar_one_or_none()

        if not user:
            print("❌ Test user not found")
            return

        service = ForecastService(db)
        test_days = 30
        prediction_length = 7

        results = []

        for classification in classifications:
            item_id = classification.item_id
            client_id = str(classification.client_id)

            print(f"Testing {item_id} ({classification.abc_class}-{classification.xyz_class}, {classification.demand_pattern})...")

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
                print(f"  ⚠️  No data found")
                continue

            max_date = row.max_date
            test_start = max_date - timedelta(days=test_days - 1)
            train_end = test_start - timedelta(days=1)

            # Generate forecast
            try:
                forecast_run = await service.generate_forecast(
                    client_id=client_id,
                    user_id=user.id,
                    item_ids=[item_id],
                    prediction_length=prediction_length,
                    primary_model="chronos-2",
                    include_baseline=True,
                    training_end_date=train_end,
                )

                if forecast_run.status != "completed":
                    print(f"  ❌ Forecast failed: {forecast_run.error_message}")
                    continue

                # Get predictions
                predictions = await service.get_forecast_results(
                    forecast_run_id=forecast_run.forecast_run_id,
                    method=forecast_run.recommended_method or forecast_run.primary_model,
                )

                if item_id not in predictions:
                    print(f"  ⚠️  No predictions found")
                    continue

                pred_data = predictions[item_id]

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
                    print(f"  ⚠️  Insufficient actuals ({len(actuals)} < {prediction_length})")
                    continue

                # Calculate metrics using QualityCalculator
                actual_values = [float(row.units_sold) for row in actuals[:prediction_length]]
                pred_values = [float(p['point_forecast']) for p in pred_data[:prediction_length]]

                quality_calc = QualityCalculator(db)

                # Use QualityCalculator methods
                mape = quality_calc.calculate_mape(actual_values, pred_values)
                mae = quality_calc.calculate_mae(actual_values, pred_values)
                rmse = quality_calc.calculate_rmse(actual_values, pred_values)
                bias = quality_calc.calculate_bias(actual_values, pred_values)

                # Additional metrics
                # WMAPE (Weighted MAPE) - better for low-volume items
                total_actual = sum(actual_values)
                if total_actual > 0:
                    wmape = (sum(abs(a - p) for a, p in zip(actual_values, pred_values)) / total_actual) * 100
                else:
                    wmape = None

                # Directional Accuracy
                if len(actual_values) > 1 and len(pred_values) > 1:
                    actual_changes = [actual_values[i] - actual_values[i-1] for i in range(1, len(actual_values))]
                    pred_changes = [pred_values[i] - pred_values[i-1] for i in range(1, len(pred_values))]
                    correct_directions = sum(
                        (a > 0 and p > 0) or (a < 0 and p < 0) or (a == 0 and p == 0)
                        for a, p in zip(actual_changes, pred_changes)
                    )
                    directional_accuracy = (correct_directions / len(actual_changes)) * 100 if actual_changes else None
                else:
                    directional_accuracy = None

                # R² (Coefficient of Determination)
                if len(actual_values) > 1:
                    mean_actual = np.mean(actual_values)
                    ss_res = sum((a - p) ** 2 for a, p in zip(actual_values, pred_values))
                    ss_tot = sum((a - mean_actual) ** 2 for a in actual_values)
                    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else None
                else:
                    r_squared = None

                # MAE
                mae = np.mean(np.abs(np.array(actual_values) - np.array(pred_values)))

                # Check if within expected range
                expected_min = float(classification.expected_mape_min) if classification.expected_mape_min else 0
                expected_max = float(classification.expected_mape_max) if classification.expected_mape_max else 200
                within_range = expected_min <= mape <= expected_max

                results.append({
                    "item_id": item_id,
                    "abc_xyz": f"{classification.abc_class}-{classification.xyz_class}",
                    "pattern": classification.demand_pattern,
                    "recommended": classification.recommended_method,
                    "expected_mape_min": expected_min,
                    "expected_mape_max": expected_max,
                    "actual_mape": mape,
                    "mae": mae,
                    "rmse": rmse,
                    "bias": bias,
                    "wmape": wmape,
                    "directional_accuracy": directional_accuracy,
                    "r_squared": r_squared,
                    "within_range": within_range,
                })

                status = "✅" if within_range else "⚠️"
                print(f"  {status} MAPE: {mape:.1f}% | MAE: {mae:.2f} | RMSE: {rmse:.2f} | Bias: {bias:.2f}")
                if wmape:
                    print(f"      WMAPE: {wmape:.1f}% | Dir Acc: {directional_accuracy:.1f}% | R²: {r_squared:.3f}" if directional_accuracy and r_squared else f"      WMAPE: {wmape:.1f}%")

            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)

        if not results:
            print("❌ No results to summarize")
            return

        df = pd.DataFrame(results)

        within_range_count = df['within_range'].sum()
        total = len(df)

        print(f"\n📊 Accuracy vs Expected Ranges:")
        print(f"   Within range: {within_range_count}/{total} ({within_range_count/total*100:.1f}%)")
        print(f"   Outside range: {total - within_range_count}/{total} ({(total-within_range_count)/total*100:.1f}%)")

        print(f"\n📊 Average MAPE by Classification:")
        for combo in df['abc_xyz'].unique():
            subset = df[df['abc_xyz'] == combo]
            avg_mape = subset['actual_mape'].mean()
            avg_expected = (subset['expected_mape_min'].mean() + subset['expected_mape_max'].mean()) / 2
            print(f"   {combo}: {avg_mape:.1f}% (expected: {avg_expected:.1f}%)")

        print(f"\n📊 Average MAPE by Pattern:")
        for pattern in df['pattern'].unique():
            subset = df[df['pattern'] == pattern]
            avg_mape = subset['actual_mape'].mean()
            avg_mae = subset['mae'].mean()
            avg_rmse = subset['rmse'].mean()
            print(f"   {pattern}: MAPE {avg_mape:.1f}% | MAE {avg_mae:.2f} | RMSE {avg_rmse:.2f}")

        print(f"\n📊 Additional Metrics Summary:")
        if df['wmape'].notna().any():
            avg_wmape = df['wmape'].mean()
            print(f"   Average WMAPE: {avg_wmape:.1f}%")
        if df['directional_accuracy'].notna().any():
            avg_dir_acc = df['directional_accuracy'].mean()
            print(f"   Average Directional Accuracy: {avg_dir_acc:.1f}%")
        if df['r_squared'].notna().any():
            avg_r2 = df['r_squared'].mean()
            print(f"   Average R²: {avg_r2:.3f}")

        print(f"\n📋 Detailed Results:")
        for _, row in df.iterrows():
            status = "✅" if row['within_range'] else "⚠️"
            metrics_str = f"MAPE: {row['actual_mape']:.1f}% | MAE: {row['mae']:.2f} | RMSE: {row['rmse']:.2f}"
            if pd.notna(row.get('wmape')):
                metrics_str += f" | WMAPE: {row['wmape']:.1f}%"
            print(f"   {status} {row['item_id']}: {metrics_str}")
            print(f"      ({row['abc_xyz']}, {row['pattern']}, expected MAPE: {row['expected_mape_min']:.0f}-{row['expected_mape_max']:.0f}%)")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_m5_forecast_accuracy())

