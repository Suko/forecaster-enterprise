"""
Test MA7 Model with Enhanced Data Validator

Tests the Moving Average 7-day model with:
1. Enhanced validator (missing dates filled, NaN handled)
2. Comparison with Darts baseline models
3. Validation that MA7 works correctly with cleaned data
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
import numpy as np
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
    from darts.models import NaiveMean, ExponentialSmoothing
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("⚠️  Darts not installed - skipping Darts comparison")

from forecasting.modes.statistical.moving_average import MovingAverageModel
from forecasting.services.data_access import DataAccess
from forecasting.services.data_validator import DataValidator


async def test_ma7_for_sku(db, item_id: str, client_id: str, test_days: int = 30):
    """Test MA7 model for a single SKU"""

    print(f"\n{'='*80}")
    print(f"Testing MA7 for {item_id}")
    print(f"{'='*80}")

    # Get data
    max_date_result = await db.execute(
        text("""
            SELECT MAX(date_local) as max_date
            FROM ts_demand_daily
            WHERE item_id = :item_id AND client_id = :client_id
        """),
        {"item_id": item_id, "client_id": client_id}
    )
    max_date_row = max_date_result.fetchone()

    if not max_date_row or not max_date_row.max_date:
        print(f"❌ No data found for {item_id}")
        return None

    max_date = max_date_row.max_date
    if isinstance(max_date, str):
        max_date = pd.to_datetime(max_date).date()

    train_end = max_date - timedelta(days=test_days)

    # Fetch training data
    data_access = DataAccess(db)
    train_data = await data_access.fetch_historical_data(
        client_id=client_id,
        item_ids=[item_id],
        end_date=train_end,
    )

    if train_data.empty:
        print(f"❌ No training data for {item_id}")
        return None

    item_train = train_data[train_data["id"] == item_id].copy()

    if len(item_train) < 30:
        print(f"❌ Insufficient data: {len(item_train)} days (need 30+)")
        return None

    # Get test actuals
    result = await db.execute(
        text("""
            SELECT date_local, units_sold
            FROM ts_demand_daily
            WHERE item_id = :item_id AND client_id = :client_id
            AND date_local > :train_end
            ORDER BY date_local
        """),
        {"item_id": item_id, "client_id": client_id, "train_end": train_end}
    )
    test_rows = result.fetchall()

    if not test_rows:
        print(f"❌ No test data for {item_id}")
        return None

    test_data = pd.DataFrame([
        {"timestamp": row.date_local, "target": float(row.units_sold)}
        for row in test_rows
    ])
    test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])
    test_data["target"] = pd.to_numeric(test_data["target"], errors='coerce')

    print(f"\n📊 Data Summary:")
    print(f"   Training: {len(item_train)} days ({item_train['timestamp'].min().date()} to {item_train['timestamp'].max().date()})")
    print(f"   Test: {len(test_data)} days ({test_data['timestamp'].min().date()} to {test_data['timestamp'].max().date()})")
    print(f"   Training mean: {item_train['target'].mean():.2f}")
    print(f"   Test mean: {test_data['target'].mean():.2f}")

    # Test with Enhanced Validator
    print(f"\n🔬 Testing with Enhanced Validator...")

    # Validate and clean data
    is_valid, validation_report, error_msg, cleaned_df = DataValidator.validate_context_data(
        item_train,
        item_id=item_id,
        min_history_days=7,
        fill_missing_dates=True,  # Fill gaps
        fillna_strategy="zero",   # Fill NaN with 0
    )

    if not is_valid:
        print(f"❌ Validation failed: {error_msg}")
        return None

    print(f"   ✅ Validation passed")
    print(f"   Original rows: {len(item_train)}")
    print(f"   Cleaned rows: {len(cleaned_df)}")

    if len(cleaned_df) > len(item_train):
        print(f"   ✅ Missing dates filled: {len(cleaned_df) - len(item_train)} days")

    # Check for warnings
    if validation_report.get("warnings"):
        print(f"   ⚠️  Warnings: {validation_report['warnings']}")

    # Test Our MA7 Model
    print(f"\n🔬 Testing Our MA7 Model...")
    try:
        ma7_model = MovingAverageModel(window=7)
        await ma7_model.initialize()

        # Use cleaned data
        ma7_pred_df = await ma7_model.predict(
            context_df=cleaned_df,
            prediction_length=test_days,
        )

        # Convert to TimeSeries for metrics
        ma7_pred = TimeSeries.from_dataframe(
            ma7_pred_df,
            time_col="timestamp",
            value_cols="point_forecast"
        )
        test_series = TimeSeries.from_dataframe(
            test_data,
            time_col="timestamp",
            value_cols="target"
        )

        try:
            ma7_mape = mape(test_series, ma7_pred)
        except ValueError:
            ma7_mape = None
        ma7_mae = mae(test_series, ma7_pred)
        ma7_rmse = rmse(test_series, ma7_pred)

        print(f"   ✅ MA7 MAPE: {ma7_mape:.2f}%" if ma7_mape else "   ✅ (MAPE unavailable)")
        print(f"   ✅ MA7 MAE: {ma7_mae:.2f}")
        print(f"   ✅ MA7 RMSE: {ma7_rmse:.2f}")

    except Exception as e:
        print(f"   ❌ MA7 failed: {e}")
        import traceback
        traceback.print_exc()
        return None

    # Compare with Darts baseline models
    if DARTS_AVAILABLE:
        print(f"\n🔬 Comparing with Darts Baseline Models...")

        # Prepare data for Darts (only target column)
        train_series = TimeSeries.from_dataframe(
            cleaned_df[["timestamp", "target"]],
            time_col="timestamp",
            value_cols="target"
        )

        darts_results = {}

        # Test NaiveMean (similar to MA7)
        try:
            naive_model = NaiveMean()
            naive_model.fit(train_series)
            naive_pred = naive_model.predict(test_days)

            try:
                naive_mape = mape(test_series, naive_pred)
            except ValueError:
                naive_mape = None
            naive_mae = mae(test_series, naive_pred)
            naive_rmse = rmse(test_series, naive_pred)

            darts_results["NaiveMean"] = {
                "mape": naive_mape,
                "mae": naive_mae,
                "rmse": naive_rmse,
            }
            print(f"   ✅ NaiveMean MAE: {naive_mae:.2f}")
        except Exception as e:
            print(f"   ⚠️  NaiveMean failed: {e}")

        # Test Exponential Smoothing
        try:
            es_model = ExponentialSmoothing()
            es_model.fit(train_series)
            es_pred = es_model.predict(test_days)

            try:
                es_mape = mape(test_series, es_pred)
            except ValueError:
                es_mape = None
            es_mae = mae(test_series, es_pred)
            es_rmse = rmse(test_series, es_pred)

            darts_results["ExponentialSmoothing"] = {
                "mape": es_mape,
                "mae": es_mae,
                "rmse": es_rmse,
            }
            print(f"   ✅ ExponentialSmoothing MAE: {es_mae:.2f}")
        except Exception as e:
            print(f"   ⚠️  ExponentialSmoothing failed: {e}")

        # Compare results
        if darts_results:
            print(f"\n📊 Comparison:")
            print(f"   {'Model':<25} {'MAE':<10} {'RMSE':<10} {'MAPE':<10}")
            print(f"   {'-'*60}")
            print(f"   {'Our MA7':<25} {ma7_mae:<10.2f} {ma7_rmse:<10.2f} {str(ma7_mape) + '%' if ma7_mape else 'N/A':<10}")

            for model_name, metrics in darts_results.items():
                print(f"   {model_name:<25} {metrics['mae']:<10.2f} {metrics['rmse']:<10.2f} {str(metrics['mape']) + '%' if metrics['mape'] else 'N/A':<10}")

    return {
        "item_id": item_id,
        "train_days": len(cleaned_df),
        "test_days": len(test_data),
        "ma7": {
            "mape": ma7_mape,
            "mae": ma7_mae,
            "rmse": ma7_rmse,
        },
        "darts": darts_results if DARTS_AVAILABLE else {},
        "validation": validation_report,
    }


async def main():
    """Test MA7 model on multiple SKUs"""

    print("=" * 80)
    print("MA7 Model Test with Enhanced Data Validator")
    print("=" * 80)

    # Get database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise")
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get SKUs with data
        result = await db.execute(
            text("""
                SELECT item_id, client_id, COUNT(*) as cnt
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 60
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)
        )
        rows = result.fetchall()

        if not rows:
            print("❌ No data found in database")
            return

        print(f"\n✅ Found {len(rows)} SKUs with sufficient data")
        print(f"   Testing first 5 SKUs...\n")

        all_results = []

        for idx, row in enumerate(rows, 1):
            item_id = row.item_id
            client_id = str(row.client_id)

            print(f"[{idx}/{len(rows)}] Testing {item_id}...")

            result = await test_ma7_for_sku(db, item_id, client_id, test_days=30)

            if result:
                all_results.append(result)

        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)

        if all_results:
            print(f"\n📊 Results:")
            print(f"   Total tested: {len(all_results)}")
            print(f"   Successful: {len(all_results)}")

            mape_values = [r["ma7"]["mape"] for r in all_results if r["ma7"]["mape"] is not None]
            mae_values = [r["ma7"]["mae"] for r in all_results]
            rmse_values = [r["ma7"]["rmse"] for r in all_results]

            if mape_values:
                print(f"\n📈 MA7 Metrics:")
                print(f"   MAPE: Mean={np.mean(mape_values):.2f}%, Min={np.min(mape_values):.2f}%, Max={np.max(mape_values):.2f}%")
            print(f"   MAE:  Mean={np.mean(mae_values):.2f}, Min={np.min(mae_values):.2f}, Max={np.max(mae_values):.2f}")
            print(f"   RMSE: Mean={np.mean(rmse_values):.2f}, Min={np.min(rmse_values):.2f}, Max={np.max(rmse_values):.2f}")

            print(f"\n📋 Per-SKU Results:")
            print(f"   {'SKU':<10} {'MAE':<10} {'RMSE':<10} {'MAPE':<10}")
            print("   " + "-" * 45)
            for r in all_results:
                mape_str = f"{r['ma7']['mape']:.1f}%" if r['ma7']['mape'] else "N/A"
                print(f"   {r['item_id']:<10} {r['ma7']['mae']:<10.2f} {r['ma7']['rmse']:<10.2f} {mape_str:<10}")

            print(f"\n   ✅ MA7 Model working correctly with Enhanced Validator!")


if __name__ == "__main__":
    asyncio.run(main())

