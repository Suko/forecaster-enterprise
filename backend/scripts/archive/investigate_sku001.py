"""
Investigate SKU001 - Why is there a 34.6% difference between Darts and our implementation?

Checks:
1. Zero sales days handling
2. Data format differences
3. Prediction value differences
4. Data quality issues
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
    from darts.models import Chronos2Model
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("❌ Darts not installed")
    sys.exit(1)

from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model
from forecasting.services.data_access import DataAccess


async def investigate_sku001():
    """Deep dive into SKU001 to find the difference"""

    print("=" * 80)
    print("SKU001 Investigation - Darts vs Our Implementation")
    print("=" * 80)

    # Get database connection
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise")
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")

    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get SKU001 data
        result = await db.execute(
            text("""
                SELECT item_id, client_id, MIN(date_local) as min_date, MAX(date_local) as max_date, COUNT(*) as cnt
                FROM ts_demand_daily
                WHERE item_id = 'SKU001'
                GROUP BY item_id, client_id
                LIMIT 1
            """)
        )
        row = result.fetchone()

        if not row:
            print("❌ SKU001 not found")
            return

        item_id = row.item_id
        client_id = str(row.client_id)
        max_date = row.max_date
        if isinstance(max_date, str):
            max_date = pd.to_datetime(max_date).date()
        train_end = max_date - timedelta(days=30)

        print(f"\n📊 SKU001 Data Summary:")
        print(f"   Total days: {row.cnt}")
        print(f"   Date range: {row.min_date} to {max_date}")
        print(f"   Training up to: {train_end}")
        print(f"   Test period: {train_end + timedelta(days=1)} to {max_date}")

        # Get training data
        data_access = DataAccess(db)
        train_data = await data_access.fetch_historical_data(
            client_id=client_id,
            item_ids=[item_id],
            end_date=train_end,
        )
        train_data = train_data[train_data["id"] == item_id].copy()

        # Convert target to numeric to avoid Decimal issues
        train_data["target"] = pd.to_numeric(train_data["target"], errors='coerce')

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
        test_data = pd.DataFrame([
            {"timestamp": row.date_local, "target": float(row.units_sold)}
            for row in test_rows
        ])
        test_data["target"] = pd.to_numeric(test_data["target"], errors='coerce')
        test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])

        # Analyze training data
        print(f"\n📈 Training Data Analysis:")
        print(f"   Total days: {len(train_data)}")
        print(f"   Zero sales days: {(train_data['target'] == 0).sum()} ({(train_data['target'] == 0).sum() / len(train_data) * 100:.1f}%)")
        print(f"   Mean sales: {train_data['target'].mean():.2f}")
        print(f"   Std sales: {train_data['target'].std():.2f}")
        print(f"   Min: {train_data['target'].min()}, Max: {train_data['target'].max()}")
        print(f"   CV: {train_data['target'].std() / train_data['target'].mean() * 100:.1f}%")

        # Analyze test data
        print(f"\n📈 Test Data Analysis:")
        print(f"   Total days: {len(test_data)}")
        print(f"   Zero sales days: {(test_data['target'] == 0).sum()} ({(test_data['target'] == 0).sum() / len(test_data) * 100:.1f}%)")
        print(f"   Mean sales: {test_data['target'].mean():.2f}")
        print(f"   Std sales: {test_data['target'].std():.2f}")
        print(f"   Min: {test_data['target'].min()}, Max: {test_data['target'].max()}")

        # Check for data quality issues
        print(f"\n🔍 Data Quality Checks:")

        # Check for missing dates
        train_data["timestamp"] = pd.to_datetime(train_data["timestamp"])
        date_range = pd.date_range(start=train_data["timestamp"].min(), end=train_data["timestamp"].max(), freq='D')
        missing_dates = len(date_range) - len(train_data)
        if missing_dates > 0:
            print(f"   ⚠️  Missing dates in training: {missing_dates} days")

        # Check for negative values
        negative_count = (train_data['target'] < 0).sum()
        if negative_count > 0:
            print(f"   ⚠️  Negative values: {negative_count}")

        # Check for nulls
        null_count = train_data['target'].isna().sum()
        if null_count > 0:
            print(f"   ⚠️  Null values: {null_count}")

        # Convert to TimeSeries
        train_series = TimeSeries.from_dataframe(
            train_data,
            time_col="timestamp",
            value_cols="target"
        )
        test_series = TimeSeries.from_dataframe(
            test_data,
            time_col="timestamp",
            value_cols="target"
        )

        # Test Darts Chronos2Model
        print(f"\n🔬 Testing Darts Chronos2Model...")
        try:
            input_len = min(len(train_series), 512)
            output_len = 30

            darts_model = Chronos2Model(
                input_chunk_length=input_len,
                output_chunk_length=output_len
            )
            darts_model.to_cpu()
            darts_model.fit(train_series)
            darts_pred = darts_model.predict(n=30)

            darts_vals = darts_pred.values().flatten()
            darts_mae = mae(test_series, darts_pred)

            print(f"   ✅ Darts MAE: {darts_mae:.2f}")
            print(f"   ✅ Darts predictions - Mean: {np.mean(darts_vals):.2f}, Min: {np.min(darts_vals):.2f}, Max: {np.max(darts_vals):.2f}")
            print(f"   ✅ Darts predictions - Zeros: {(darts_vals == 0).sum()}")
            print(f"   ✅ Darts predictions - Negatives: {(darts_vals < 0).sum()}")

        except Exception as e:
            print(f"   ❌ Darts failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Test Our Custom Chronos2Model - WITH covariates (current behavior)
        print(f"\n🔬 Testing Our Custom Chronos2Model (WITH covariates)...")
        try:
            our_model = OurChronos2Model()
            await our_model.initialize()
            our_pred_df = await our_model.predict(
                context_df=train_data,
                prediction_length=30,
            )

            our_vals_with_cov = our_pred_df["point_forecast"].values
            our_pred_with_cov = TimeSeries.from_dataframe(
                our_pred_df,
                time_col="timestamp",
                value_cols="point_forecast"
            )
            our_mae_with_cov = mae(test_series, our_pred_with_cov)

            print(f"   ✅ Our MAE (WITH covariates): {our_mae_with_cov:.2f}")
            print(f"   ✅ Our predictions - Mean: {np.mean(our_vals_with_cov):.2f}, Min: {np.min(our_vals_with_cov):.2f}, Max: {np.max(our_vals_with_cov):.2f}")
            print(f"   ✅ Our predictions - Zeros: {(our_vals_with_cov == 0).sum()}")
            print(f"   ✅ Our predictions - Negatives: {(our_vals_with_cov < 0).sum()}")

        except Exception as e:
            print(f"   ❌ Our model failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Test Our Custom Chronos2Model - WITHOUT covariates (like Darts)
        print(f"\n🔬 Testing Our Custom Chronos2Model (WITHOUT covariates - like Darts)...")
        try:
            # Remove covariates to match Darts
            train_data_no_cov = train_data[["id", "timestamp", "target"]].copy()

            our_model_no_cov = OurChronos2Model()
            await our_model_no_cov.initialize()
            our_pred_df_no_cov = await our_model_no_cov.predict(
                context_df=train_data_no_cov,
                prediction_length=30,
            )

            our_vals_no_cov = our_pred_df_no_cov["point_forecast"].values
            our_pred_no_cov = TimeSeries.from_dataframe(
                our_pred_df_no_cov,
                time_col="timestamp",
                value_cols="point_forecast"
            )
            our_mae_no_cov = mae(test_series, our_pred_no_cov)

            print(f"   ✅ Our MAE (WITHOUT covariates): {our_mae_no_cov:.2f}")
            print(f"   ✅ Our predictions - Mean: {np.mean(our_vals_no_cov):.2f}, Min: {np.min(our_vals_no_cov):.2f}, Max: {np.max(our_vals_no_cov):.2f}")
            print(f"   ✅ Our predictions - Zeros: {(our_vals_no_cov == 0).sum()}")
            print(f"   ✅ Our predictions - Negatives: {(our_vals_no_cov < 0).sum()}")

            # Compare with Darts
            print(f"\n   📊 Comparison:")
            print(f"      Darts MAE: {darts_mae:.2f}")
            print(f"      Our MAE (with covariates): {our_mae_with_cov:.2f}")
            print(f"      Our MAE (without covariates): {our_mae_no_cov:.2f}")
            print(f"      Difference (with cov): {abs(darts_mae - our_mae_with_cov):.2f} ({abs(darts_mae - our_mae_with_cov)/darts_mae*100:.1f}%)")
            print(f"      Difference (without cov): {abs(darts_mae - our_mae_no_cov):.2f} ({abs(darts_mae - our_mae_no_cov)/darts_mae*100:.1f}%)")

            # Use the no-covariates version for comparison
            our_vals = our_vals_no_cov
            our_mae = our_mae_no_cov
            our_pred = our_pred_no_cov

        except Exception as e:
            print(f"   ❌ Our model (no covariates) failed: {e}")
            import traceback
            traceback.print_exc()
            # Fall back to with-covariates version
            our_vals = our_vals_with_cov
            our_mae = our_mae_with_cov
            our_pred = our_pred_with_cov

            our_vals = our_pred_df["point_forecast"].values
            our_pred = TimeSeries.from_dataframe(
                our_pred_df,
                time_col="timestamp",
                value_cols="point_forecast"
            )
            our_mae = mae(test_series, our_pred)

            print(f"   ✅ Our MAE: {our_mae:.2f}")
            print(f"   ✅ Our predictions - Mean: {np.mean(our_vals):.2f}, Min: {np.min(our_vals):.2f}, Max: {np.max(our_vals):.2f}")
            print(f"   ✅ Our predictions - Zeros: {(our_vals == 0).sum()}")
            print(f"   ✅ Our predictions - Negatives: {(our_vals < 0).sum()}")

        except Exception as e:
            print(f"   ❌ Our model failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # Compare predictions day-by-day
        print(f"\n📊 Day-by-Day Comparison:")
        print(f"   {'Day':<6} {'Actual':<10} {'Darts':<10} {'Ours':<10} {'Darts Err':<12} {'Our Err':<12} {'Diff':<10}")
        print("   " + "-" * 80)

        actual_vals = test_data["target"].values
        for i in range(min(30, len(actual_vals), len(darts_vals), len(our_vals))):
            actual = actual_vals[i]
            darts_pred_val = darts_vals[i]
            our_pred_val = our_vals[i]
            darts_err = abs(actual - darts_pred_val)
            our_err = abs(actual - our_pred_val)
            diff = abs(darts_pred_val - our_pred_val)

            print(f"   {i+1:<6} {actual:<10.2f} {darts_pred_val:<10.2f} {our_pred_val:<10.2f} {darts_err:<12.2f} {our_err:<12.2f} {diff:<10.2f}")

        # Analyze differences
        print(f"\n🔍 Difference Analysis:")
        pred_diff = np.abs(darts_vals - our_vals)
        print(f"   Mean absolute prediction difference: {np.mean(pred_diff):.2f}")
        print(f"   Max absolute prediction difference: {np.max(pred_diff):.2f}")
        print(f"   Correlation: {np.corrcoef(darts_vals, our_vals)[0, 1]:.4f}")

        # Check where differences are largest
        large_diff_indices = np.where(pred_diff > np.percentile(pred_diff, 75))[0]
        if len(large_diff_indices) > 0:
            print(f"\n   ⚠️  Largest differences on days: {large_diff_indices[:5]}")
            for idx in large_diff_indices[:5]:
                if idx < len(actual_vals):
                    print(f"      Day {idx+1}: Actual={actual_vals[idx]:.2f}, Darts={darts_vals[idx]:.2f}, Ours={our_vals[idx]:.2f}, Diff={pred_diff[idx]:.2f}")

        # Check if zeros are the issue
        zero_actual_indices = np.where(actual_vals == 0)[0]
        if len(zero_actual_indices) > 0:
            print(f"\n   🔍 Zero Sales Days Analysis:")
            print(f"      Zero sales days in test: {len(zero_actual_indices)}")
            for idx in zero_actual_indices[:5]:
                if idx < len(darts_vals) and idx < len(our_vals):
                    print(f"      Day {idx+1} (zero actual): Darts={darts_vals[idx]:.2f}, Ours={our_vals[idx]:.2f}, Diff={pred_diff[idx]:.2f}")

        # Check data format differences
        print(f"\n🔍 Data Format Check:")
        print(f"   Training data columns: {list(train_data.columns)}")
        print(f"   Training data dtypes:")
        for col in train_data.columns:
            print(f"      {col}: {train_data[col].dtype}")

        # Check if our model receives different data
        print(f"\n   Our model receives:")
        print(f"      Rows: {len(train_data)}")
        print(f"      Target range: {train_data['target'].min():.2f} to {train_data['target'].max():.2f}")
        print(f"      Target mean: {train_data['target'].mean():.2f}")

        # Check Chronos-2 pipeline input
        print(f"\n   Checking what we send to Chronos-2 pipeline...")
        chronos_df = train_data.copy()
        if "id" in chronos_df.columns and "item_id" not in chronos_df.columns:
            chronos_df = chronos_df.rename(columns={"id": "item_id"})

        print(f"      Columns sent to pipeline: {list(chronos_df.columns)}")
        print(f"      item_id values: {chronos_df['item_id'].unique()}")
        print(f"      Timestamp type: {chronos_df['timestamp'].dtype}")
        print(f"      Target type: {chronos_df['target'].dtype}")
        print(f"      Target has nulls: {chronos_df['target'].isna().sum()}")
        print(f"      Target has zeros: {(chronos_df['target'] == 0).sum()}")


if __name__ == "__main__":
    asyncio.run(investigate_sku001())

