"""
Diagnose A-Y SKU Performance Using Darts Baselines

Uses Darts models (Chronos2Model, NaiveMean, ExponentialSmoothing) as baselines
to determine if the high MAPE is due to:
1. Our implementation issue
2. Data quality issue
3. Inherent difficulty of A-Y SKUs
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

try:
    from darts import TimeSeries
    from darts.models import Chronos2Model, NaiveMean, ExponentialSmoothing
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("⚠️  Darts not available. Install with: uv pip install darts")


async def main():
    if not DARTS_AVAILABLE:
        print("❌ Darts library not available. Cannot run diagnostic.")
        return

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
        print("A-Y PERFORMANCE DIAGNOSTIC (Using Darts Baselines)")
        print("=" * 80)
        print(f"\nFound {len(ay_skus)} A-Y SKUs")
        print("\nTesting with Darts models to determine if high MAPE is:")
        print("  A) Our implementation issue")
        print("  B) Data quality/distribution shift")
        print("  C) Inherent difficulty of A-Y SKUs")
        print("=" * 80)

        test_days = 30

        for sku in ay_skus:
            print(f"\n{'='*80}")
            print(f"SKU: {sku.item_id}")
            print(f"Classification: {sku.abc_class}-{sku.xyz_class} ({sku.demand_pattern})")
            print(f"CV: {float(sku.coefficient_of_variation):.2f} | ADI: {float(sku.average_demand_interval):.2f}")
            print(f"Expected MAPE: {float(sku.expected_mape_min):.1f}% - {float(sku.expected_mape_max):.1f}%")
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
                'date': r.date,
                'quantity': float(r.units_sold)  # Convert Decimal to float
            } for r in records])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)

            # Split train/test
            if len(df) < test_days + 30:
                print(f"⚠️  Insufficient data: {len(df)} days (need at least {test_days + 30})")
                continue

            train_df = df.iloc[:-test_days].copy()
            test_df = df.iloc[-test_days:].copy()

            print(f"\n📊 Data Split:")
            print(f"   Training: {len(train_df)} days ({train_df['date'].min().date()} to {train_df['date'].max().date()})")
            print(f"   Test: {len(test_df)} days ({test_df['date'].min().date()} to {test_df['date'].max().date()})")

            # Check for distribution shift
            train_mean = train_df['quantity'].mean()
            test_mean = test_df['quantity'].mean()
            mean_shift = (test_mean - train_mean) / train_mean * 100 if train_mean > 0 else 0

            print(f"\n📈 Distribution Check:")
            print(f"   Train mean: {train_mean:.2f}")
            print(f"   Test mean: {test_mean:.2f}")
            print(f"   Mean shift: {mean_shift:+.1f}%")

            if abs(mean_shift) > 30:
                print(f"   ⚠️  SIGNIFICANT DISTRIBUTION SHIFT!")

            # Convert to Darts TimeSeries
            train_series = TimeSeries.from_dataframe(
                train_df,
                time_col="date",
                value_cols="quantity"
            )
            test_series = TimeSeries.from_dataframe(
                test_df,
                time_col="date",
                value_cols="quantity"
            )

            results = {}

            # Test 1: NaiveMean (simplest baseline)
            print(f"\n🔬 Testing Darts NaiveMean (simplest baseline)...")
            try:
                naive_model = NaiveMean()
                naive_model.fit(train_series)
                naive_pred = naive_model.predict(n=test_days)

                naive_mae = mae(test_series, naive_pred)
                naive_rmse = rmse(test_series, naive_pred)
                try:
                    naive_mape = mape(test_series, naive_pred)
                except (ValueError, ZeroDivisionError):
                    # Calculate MAPE manually (skip zeros)
                    test_values = test_series.values().flatten()
                    pred_values = naive_pred.values().flatten()
                    mape_vals = [abs(a - p) / a * 100 for a, p in zip(test_values, pred_values) if a > 0]
                    naive_mape = sum(mape_vals) / len(mape_vals) if mape_vals else None

                results["NaiveMean"] = {
                    "mape": naive_mape,
                    "mae": naive_mae,
                    "rmse": naive_rmse
                }
                print(f"   ✅ NaiveMean MAE: {naive_mae:.2f}, RMSE: {naive_rmse:.2f}")
                if naive_mape:
                    print(f"   ✅ NaiveMean MAPE: {naive_mape:.1f}%")
            except Exception as e:
                print(f"   ❌ NaiveMean failed: {e}")
                results["NaiveMean"] = {"error": str(e)}

            # Test 2: ExponentialSmoothing (statistical baseline)
            print(f"\n🔬 Testing Darts ExponentialSmoothing (statistical baseline)...")
            try:
                es_model = ExponentialSmoothing()
                es_model.fit(train_series)
                es_pred = es_model.predict(n=test_days)

                es_mae = mae(test_series, es_pred)
                es_rmse = rmse(test_series, es_pred)
                try:
                    es_mape = mape(test_series, es_pred)
                except (ValueError, ZeroDivisionError):
                    # Calculate MAPE manually (skip zeros)
                    test_values = test_series.values().flatten()
                    pred_values = es_pred.values().flatten()
                    mape_vals = [abs(a - p) / a * 100 for a, p in zip(test_values, pred_values) if a > 0]
                    es_mape = sum(mape_vals) / len(mape_vals) if mape_vals else None

                results["ExponentialSmoothing"] = {
                    "mape": es_mape,
                    "mae": es_mae,
                    "rmse": es_rmse
                }
                print(f"   ✅ ExponentialSmoothing MAE: {es_mae:.2f}, RMSE: {es_rmse:.2f}")
                if es_mape:
                    print(f"   ✅ ExponentialSmoothing MAPE: {es_mape:.1f}%")
            except Exception as e:
                print(f"   ❌ ExponentialSmoothing failed: {e}")
                results["ExponentialSmoothing"] = {"error": str(e)}

            # Test 3: Darts Chronos2Model (same model, different implementation)
            print(f"\n🔬 Testing Darts Chronos2Model (reference implementation)...")
            try:
                input_len = min(len(train_series), 512)
                output_len = min(test_days, 512)

                darts_chronos = Chronos2Model(
                    input_chunk_length=input_len,
                    output_chunk_length=output_len
                )
                # Force CPU to avoid device issues
                try:
                    darts_chronos.to_cpu()
                except:
                    pass  # May not have to_cpu method

                darts_chronos.fit(train_series)
                darts_pred = darts_chronos.predict(n=test_days)

                darts_mae = mae(test_series, darts_pred)
                darts_rmse = rmse(test_series, darts_pred)
                try:
                    darts_mape = mape(test_series, darts_pred)
                except (ValueError, ZeroDivisionError):
                    # Calculate MAPE manually (skip zeros)
                    test_values = test_series.values().flatten()
                    pred_values = darts_pred.values().flatten()
                    mape_vals = [abs(a - p) / a * 100 for a, p in zip(test_values, pred_values) if a > 0]
                    darts_mape = sum(mape_vals) / len(mape_vals) if mape_vals else None

                results["Darts_Chronos2"] = {
                    "mape": darts_mape,
                    "mae": darts_mae,
                    "rmse": darts_rmse
                }
                print(f"   ✅ Darts Chronos2 MAE: {darts_mae:.2f}, RMSE: {darts_rmse:.2f}")
                if darts_mape:
                    print(f"   ✅ Darts Chronos2 MAPE: {darts_mape:.1f}%")
            except Exception as e:
                print(f"   ❌ Darts Chronos2 failed: {e}")
                results["Darts_Chronos2"] = {"error": str(e)}

            # Summary
            print(f"\n{'='*80}")
            print("📋 DIAGNOSIS SUMMARY")
            print("=" * 80)

            # Get our actual MAPE from database if available (calculate from actual_value and point_forecast)
            our_mape = None
            try:
                result = await db.execute(
                    text("""
                        SELECT fr.point_forecast, fr.actual_value, fr.date
                        FROM forecast_results fr
                        JOIN forecast_runs frun ON fr.forecast_run_id = frun.forecast_run_id
                        WHERE fr.item_id = :item_id
                        AND frun.client_id = :client_id
                        AND fr.method = 'chronos-2'
                        AND frun.status = 'completed'
                        AND fr.actual_value IS NOT NULL
                        AND fr.actual_value > 0
                        ORDER BY frun.created_at DESC, fr.date
                        LIMIT :test_days
                    """),
                    {"item_id": sku.item_id, "client_id": sku.client_id, "test_days": test_days}
                )
                rows = result.fetchall()
                if rows and len(rows) >= 10:  # Need at least 10 points for meaningful MAPE
                    actuals = [float(r.actual_value) for r in rows]
                    forecasts = [float(r.point_forecast) for r in rows]
                    # Calculate MAPE manually
                    mape_values = [abs(a - f) / a * 100 for a, f in zip(actuals, forecasts) if a > 0]
                    if mape_values:
                        our_mape = sum(mape_values) / len(mape_values)
            except Exception as e:
                pass  # Skip if query fails

            print(f"\n📊 Model Comparison (MAPE):")
            print(f"   Expected range: {float(sku.expected_mape_min):.1f}% - {float(sku.expected_mape_max):.1f}%")

            if our_mape:
                print(f"   Our Chronos-2: {our_mape:.1f}% {'❌' if our_mape > float(sku.expected_mape_max) else '✅'}")

            for model_name, model_results in results.items():
                if "error" not in model_results and model_results.get("mape"):
                    mape_val = model_results["mape"]
                    status = "✅" if mape_val <= float(sku.expected_mape_max) else "❌"
                    print(f"   {model_name}: {mape_val:.1f}% {status}")

            # Diagnosis
            print(f"\n💡 DIAGNOSIS:")

            # Check if all models struggle
            all_mape = [r.get("mape") for r in results.values() if "error" not in r and r.get("mape")]
            if all_mape and all([m > float(sku.expected_mape_max) for m in all_mape]):
                print("   🔴 ALL MODELS STRUGGLE - This is a DATA/DISTRIBUTION issue")
                print("      → Not an implementation problem")
                if abs(mean_shift) > 30:
                    print("      → Root cause: Distribution shift in test period")
                    print("      → Solution: Add covariates (Phase 3) or use shorter training window")
                else:
                    print("      → Root cause: Inherent difficulty of A-Y SKUs")
                    print("      → Solution: Adjust expectations or flag for manual review")
            elif our_mape and all_mape:
                # Compare our implementation vs Darts
                darts_chronos_mape = results.get("Darts_Chronos2", {}).get("mape")
                if darts_chronos_mape:
                    if abs(our_mape - darts_chronos_mape) < 20:
                        print("   🟡 Our implementation similar to Darts - likely data issue")
                    elif our_mape > darts_chronos_mape * 1.5:
                        print("   🔴 Our implementation worse than Darts - possible bug")
                    else:
                        print("   🟢 Our implementation better than Darts - good!")

            # Check if simple models do better
            naive_mape = results.get("NaiveMean", {}).get("mape")
            es_mape = results.get("ExponentialSmoothing", {}).get("mape")
            if naive_mape and our_mape and naive_mape < our_mape * 0.8:
                print("   ⚠️  Simple NaiveMean beats our model - investigate implementation")
            if es_mape and our_mape and es_mape < our_mape * 0.8:
                print("   ⚠️  ExponentialSmoothing beats our model - investigate implementation")

        print(f"\n{'='*80}")
        print("OVERALL CONCLUSION")
        print("=" * 80)
        print("\nIf ALL models (NaiveMean, ExponentialSmoothing, Darts Chronos2) struggle:")
        print("  → Problem is DATA QUALITY or DISTRIBUTION SHIFT")
        print("  → Not an implementation issue")
        print("  → Solution: Covariates (Phase 3) or adjust expectations")
        print("\nIf ONLY our implementation struggles:")
        print("  → Possible implementation bug")
        print("  → Investigate our Chronos-2 code")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

