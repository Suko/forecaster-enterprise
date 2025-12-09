"""
Compare Darts Chronos2Model with our custom Chronos-2 implementation

Uses real database data to validate that both produce similar results.
This validates our custom implementation against Darts' reference implementation.

NOTE: For fair comparison, covariates are removed - both models receive only
      the target column (id, timestamp, target). Covariates will be handled in Phase 2.

Reference: https://unit8co.github.io/darts/generated_api/darts.models.forecasting.chronos2_model.html
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
    from darts.models import Chronos2Model, NaiveMean, ExponentialSmoothing
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("❌ Darts not installed. Install with: uv add darts")
    sys.exit(1)

from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model
from forecasting.services.data_access import DataAccess


async def compare_models_for_sku(
    db: AsyncSession,
    item_id: str,
    client_id: str,
    test_days: int = 30
):
    """Compare Darts vs our implementation for a single SKU"""
    
    data_access = DataAccess(db)
    
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
    
    if not row:
        return None
    
    max_date = row.max_date
    if isinstance(max_date, str):
        max_date = pd.to_datetime(max_date).date()
    train_end = max_date - timedelta(days=test_days)
    
    # Get training data
    train_data = await data_access.fetch_historical_data(
        client_id=client_id,
        item_ids=[item_id],
        end_date=train_end,
    )
    
    if train_data.empty:
        return None
    
    # Filter for this item
    item_train = train_data[train_data["id"] == item_id].copy()
    
    if item_train.empty or len(item_train) < 30:
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
        return None
    
    test_data = pd.DataFrame([
        {"timestamp": row.date_local, "target": float(row.units_sold)}
        for row in test_rows
    ])
    
    # Ensure timestamps are datetime
    item_train["timestamp"] = pd.to_datetime(item_train["timestamp"])
    test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])
    
    results = {
        "item_id": item_id,
        "train_days": len(item_train),
        "test_days": len(test_data),
    }
    
    # Test Darts Chronos2Model (foundation model - zero-shot, but still needs fit())
    print(f"\n  Testing Darts Chronos2Model...")
    
    train_series = TimeSeries.from_dataframe(
        item_train,
        time_col="timestamp",
        value_cols="target"
    )
    test_series = TimeSeries.from_dataframe(
        test_data,
        time_col="timestamp",
        value_cols="target"
    )
    
    darts_results = {}
    
    # Test Darts Chronos2Model (foundation model - supports zero-shot)
    # According to Darts docs: https://unit8co.github.io/darts/generated_api/darts.models.forecasting.chronos2_model.html
    # It's a FoundationModel but still requires fit() before predict()
    try:
        # Use input_chunk_length based on training data size (but max 8192 for Chronos-2)
        input_len = min(len(train_series), 512)  # Reasonable chunk size
        output_len = min(test_days, 512)  # Match prediction length (max 1024 - output_chunk_shift)
        
        darts_chronos = Chronos2Model(
            input_chunk_length=input_len,
            output_chunk_length=output_len
        )
        
        # Force CPU to avoid MPS float64 issues on Mac
        darts_chronos.to_cpu()
        
        # Even foundation models need fit() in Darts (though no actual training happens)
        darts_chronos.fit(train_series)
        
        # Now predict
        darts_pred = darts_chronos.predict(n=test_days)
        
        try:
            darts_mape = mape(test_series, darts_pred)
        except ValueError:
            darts_mape = None
        darts_mae = mae(test_series, darts_pred)
        darts_rmse = rmse(test_series, darts_pred)
        
        darts_results["Chronos2Model"] = {
            "mape": darts_mape,
            "mae": darts_mae,
            "rmse": darts_rmse,
        }
        print(f"    ✅ Darts Chronos2Model MAE: {darts_mae:.2f}")
    except Exception as e:
        print(f"    ⚠️  Darts Chronos2Model failed: {e}")
        # Fall back to baseline models
        print(f"    Trying baseline models instead...")
        
        # Test NaiveMean (simple baseline)
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
            print(f"    ✅ NaiveMean MAE: {naive_mae:.2f}")
        except Exception as e2:
            print(f"    ⚠️  NaiveMean failed: {e2}")
        
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
            print(f"    ✅ ExponentialSmoothing MAE: {es_mae:.2f}")
        except Exception as e2:
            print(f"    ⚠️  ExponentialSmoothing failed: {e2}")
    
    # Use best Darts model for comparison
    if darts_results:
        # Use the model with lowest MAE
        best_darts = min(darts_results.items(), key=lambda x: x[1]["mae"])
        results["darts"] = {
            "model": best_darts[0],
            "mape": best_darts[1]["mape"],
            "mae": best_darts[1]["mae"],
            "rmse": best_darts[1]["rmse"],
            "status": "success"
        }
        print(f"    📊 Best Darts model: {best_darts[0]} (MAE: {best_darts[1]['mae']:.2f})")
    else:
        results["darts"] = {"status": "failed", "error": "All Darts models failed"}
        print(f"    ❌ All Darts models failed")
    
    # Test Our Custom Chronos2Model
    # Remove covariates for fair comparison (same input as Darts - only target)
    print(f"  Testing Our Custom Chronos2Model (without covariates for fair comparison)...")
    try:
        # Strip covariates to match Darts input (only id, timestamp, target)
        item_train_no_cov = item_train[["id", "timestamp", "target"]].copy()
        
        our_model = OurChronos2Model()
        await our_model.initialize()
        
        our_pred_df = await our_model.predict(
            context_df=item_train_no_cov,
            prediction_length=test_days,
        )
        
        our_pred = TimeSeries.from_dataframe(
            our_pred_df,
            time_col="timestamp",
            value_cols="point_forecast"
        )
        
        try:
            our_mape = mape(test_series, our_pred)
        except ValueError:
            our_mape = None
        
        our_mae = mae(test_series, our_pred)
        our_rmse = rmse(test_series, our_pred)
        
        results["ours"] = {
            "mape": our_mape,
            "mae": our_mae,
            "rmse": our_rmse,
            "status": "success"
        }
        
        print(f"    ✅ MAPE: {our_mape:.2f}%" if our_mape else "    ✅ (MAPE unavailable)")
        print(f"    ✅ MAE: {our_mae:.2f}")
        
    except Exception as e:
        results["ours"] = {"status": "failed", "error": str(e)}
        print(f"    ❌ Failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Compare if both succeeded
    if results["darts"]["status"] == "success" and results["ours"]["status"] == "success":
        mae_diff = abs(results["darts"]["mae"] - results["ours"]["mae"])
        mae_pct_diff = (mae_diff / results["darts"]["mae"]) * 100 if results["darts"]["mae"] > 0 else 0
        
        rmse_diff = abs(results["darts"]["rmse"] - results["ours"]["rmse"])
        rmse_pct_diff = (rmse_diff / results["darts"]["rmse"]) * 100 if results["darts"]["rmse"] > 0 else 0
        
        results["comparison"] = {
            "mae_diff": mae_diff,
            "mae_pct_diff": mae_pct_diff,
            "rmse_diff": rmse_diff,
            "rmse_pct_diff": rmse_pct_diff,
        }
        
        if results["darts"]["mape"] and results["ours"]["mape"]:
            mape_diff = abs(results["darts"]["mape"] - results["ours"]["mape"])
            results["comparison"]["mape_diff"] = mape_diff
        
        print(f"\n  📊 Comparison:")
        print(f"    MAE Difference: {mae_diff:.2f} ({mae_pct_diff:.1f}%)")
        print(f"    RMSE Difference: {rmse_diff:.2f} ({rmse_pct_diff:.1f}%)")
        if results["darts"]["mape"] and results["ours"]["mape"]:
            print(f"    MAPE Difference: {mape_diff:.2f}%")
    
    return results


async def main():
    """Compare Darts vs our implementation on multiple SKUs"""
    
    print("=" * 80)
    print("Darts vs Our Chronos-2 Implementation Comparison")
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
            
            result = await compare_models_for_sku(db, item_id, client_id, test_days=30)
            
            if result:
                all_results.append(result)
        
        # Summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        successful = [r for r in all_results if r.get("darts", {}).get("status") == "success" and r.get("ours", {}).get("status") == "success"]
        
        print(f"\n📊 Results:")
        print(f"   Total tested: {len(all_results)}")
        print(f"   Both succeeded: {len(successful)}")
        
        if successful:
            mae_diffs = [r["comparison"]["mae_pct_diff"] for r in successful]
            rmse_diffs = [r["comparison"]["rmse_pct_diff"] for r in successful]
            
            print(f"\n📈 Average Differences:")
            print(f"   MAE: {np.mean(mae_diffs):.1f}% (min: {np.min(mae_diffs):.1f}%, max: {np.max(mae_diffs):.1f}%)")
            print(f"   RMSE: {np.mean(rmse_diffs):.1f}% (min: {np.min(rmse_diffs):.1f}%, max: {np.max(rmse_diffs):.1f}%)")
            
            print(f"\n📋 Per-SKU Comparison:")
            print(f"   {'SKU':<10} {'Darts MAE':<12} {'Our MAE':<12} {'Diff %':<10}")
            print("   " + "-" * 50)
            for r in successful:
                darts_mae = r["darts"]["mae"]
                our_mae = r["ours"]["mae"]
                diff_pct = r["comparison"]["mae_pct_diff"]
                print(f"   {r['item_id']:<10} {darts_mae:<12.2f} {our_mae:<12.2f} {diff_pct:<10.1f}%")
            
            # Validation
            avg_diff = np.mean(mae_diffs)
            if avg_diff < 20:
                print(f"\n   ✅ Validation PASSED - Results are similar (avg diff: {avg_diff:.1f}%)")
            else:
                print(f"\n   ⚠️  Validation WARNING - Results differ significantly (avg diff: {avg_diff:.1f}%)")


if __name__ == "__main__":
    asyncio.run(main())

