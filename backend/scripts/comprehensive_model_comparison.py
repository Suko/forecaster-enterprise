"""
Comprehensive Model Comparison - All SKUs, All Models

Uses Darts for consistent comparison across:
- Our MA7 (Moving Average 7-day)
- Darts NaiveMean
- Darts ExponentialSmoothing
- Our Chronos-2
- Darts Chronos2Model (optional, slower)

Tests all 20 SKUs and generates comprehensive comparison report.
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
import json
from datetime import datetime

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

load_dotenv()

try:
    from darts import TimeSeries
    from darts.models import NaiveMean, ExponentialSmoothing, Chronos2Model
    from darts.metrics import mape, mae, rmse
    DARTS_AVAILABLE = True
except ImportError:
    DARTS_AVAILABLE = False
    print("❌ Darts not installed")
    sys.exit(1)

from forecasting.modes.statistical.moving_average import MovingAverageModel
from forecasting.modes.ml.chronos2 import Chronos2Model as OurChronos2Model
from forecasting.services.data_access import DataAccess
from forecasting.services.data_validator import DataValidator


async def test_models_for_sku(
    db,
    item_id: str,
    client_id: str,
    test_days: int = 30,
    include_darts_chronos: bool = False,  # Skip by default (slow)
):
    """Test all models for a single SKU"""
    
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
        return None
    
    item_train = train_data[train_data["id"] == item_id].copy()
    
    if len(item_train) < 30:
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
    test_data["timestamp"] = pd.to_datetime(test_data["timestamp"])
    test_data["target"] = pd.to_numeric(test_data["target"], errors='coerce')
    
    # Validate and clean data (Enhanced Validator)
    is_valid, validation_report, error_msg, cleaned_df = DataValidator.validate_context_data(
        item_train,
        item_id=item_id,
        min_history_days=7,
        fill_missing_dates=True,
        fillna_strategy="zero",
    )
    
    if not is_valid:
        return None
    
    # Prepare data for Darts (only target column for fair comparison)
    train_series = TimeSeries.from_dataframe(
        cleaned_df[["timestamp", "target"]],
        time_col="timestamp",
        value_cols="target"
    )
    test_series = TimeSeries.from_dataframe(
        test_data,
        time_col="timestamp",
        value_cols="target"
    )
    
    results = {
        "item_id": item_id,
        "train_days": len(cleaned_df),
        "test_days": len(test_data),
        "models": {},
    }
    
    # Test Our MA7
    try:
        ma7_model = MovingAverageModel(window=7)
        await ma7_model.initialize()
        ma7_pred_df = await ma7_model.predict(
            context_df=cleaned_df,
            prediction_length=test_days,
        )
        ma7_pred = TimeSeries.from_dataframe(
            ma7_pred_df,
            time_col="timestamp",
            value_cols="point_forecast"
        )
        
        try:
            ma7_mape = mape(test_series, ma7_pred)
        except ValueError:
            ma7_mape = None
        ma7_mae = mae(test_series, ma7_pred)
        ma7_rmse = rmse(test_series, ma7_pred)
        
        results["models"]["Our_MA7"] = {
            "mape": ma7_mape,
            "mae": ma7_mae,
            "rmse": ma7_rmse,
            "status": "success",
        }
    except Exception as e:
        results["models"]["Our_MA7"] = {"status": "failed", "error": str(e)}
    
    # Test Darts NaiveMean
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
        
        results["models"]["Darts_NaiveMean"] = {
            "mape": naive_mape,
            "mae": naive_mae,
            "rmse": naive_rmse,
            "status": "success",
        }
    except Exception as e:
        results["models"]["Darts_NaiveMean"] = {"status": "failed", "error": str(e)}
    
    # Test Darts ExponentialSmoothing
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
        
        results["models"]["Darts_ExponentialSmoothing"] = {
            "mape": es_mape,
            "mae": es_mae,
            "rmse": es_rmse,
            "status": "success",
        }
    except Exception as e:
        results["models"]["Darts_ExponentialSmoothing"] = {"status": "failed", "error": str(e)}
    
    # Test Our Chronos-2
    try:
        our_chronos = OurChronos2Model()
        await our_chronos.initialize()
        our_chronos_pred_df = await our_chronos.predict(
            context_df=cleaned_df[["id", "timestamp", "target"]],  # No covariates for fair comparison
            prediction_length=test_days,
        )
        our_chronos_pred = TimeSeries.from_dataframe(
            our_chronos_pred_df,
            time_col="timestamp",
            value_cols="point_forecast"
        )
        
        try:
            our_chronos_mape = mape(test_series, our_chronos_pred)
        except ValueError:
            our_chronos_mape = None
        our_chronos_mae = mae(test_series, our_chronos_pred)
        our_chronos_rmse = rmse(test_series, our_chronos_pred)
        
        results["models"]["Our_Chronos2"] = {
            "mape": our_chronos_mape,
            "mae": our_chronos_mae,
            "rmse": our_chronos_rmse,
            "status": "success",
        }
    except Exception as e:
        results["models"]["Our_Chronos2"] = {"status": "failed", "error": str(e)}
    
    # Test Darts Chronos2Model (optional, slow)
    if include_darts_chronos:
        try:
            input_len = min(len(train_series), 512)
            output_len = min(test_days, 512)
            
            darts_chronos = Chronos2Model(
                input_chunk_length=input_len,
                output_chunk_length=output_len
            )
            darts_chronos.to_cpu()
            darts_chronos.fit(train_series)
            darts_chronos_pred = darts_chronos.predict(test_days)
            
            try:
                darts_chronos_mape = mape(test_series, darts_chronos_pred)
            except ValueError:
                darts_chronos_mape = None
            darts_chronos_mae = mae(test_series, darts_chronos_pred)
            darts_chronos_rmse = rmse(test_series, darts_chronos_pred)
            
            results["models"]["Darts_Chronos2Model"] = {
                "mape": darts_chronos_mape,
                "mae": darts_chronos_mae,
                "rmse": darts_chronos_rmse,
                "status": "success",
            }
        except Exception as e:
            results["models"]["Darts_Chronos2Model"] = {"status": "failed", "error": str(e)}
    
    return results


async def main(max_skus: int = 20, test_days: int = 30, include_darts_chronos: bool = False):
    """Run comprehensive model comparison on all SKUs"""
    
    print("=" * 80)
    print("Comprehensive Model Comparison - All SKUs")
    print("=" * 80)
    print(f"\nModels to test:")
    print(f"  ✅ Our MA7")
    print(f"  ✅ Darts NaiveMean")
    print(f"  ✅ Darts ExponentialSmoothing")
    print(f"  ✅ Our Chronos-2")
    if include_darts_chronos:
        print(f"  ✅ Darts Chronos2Model (slow)")
    else:
        print(f"  ⏭️  Darts Chronos2Model (skipped - use --darts-chronos to include)")
    print(f"\nTesting {max_skus} SKUs with {test_days} day test period...\n")
    
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
                LIMIT :max_skus
            """),
            {"max_skus": max_skus}
        )
        rows = result.fetchall()
        
        if not rows:
            print("❌ No data found in database")
            return
        
        print(f"✅ Found {len(rows)} SKUs with sufficient data\n")
        
        all_results = []
        
        # Test each SKU (can be parallelized in future)
        for idx, row in enumerate(rows, 1):
            item_id = row.item_id
            client_id = str(row.client_id)
            
            print(f"[{idx}/{len(rows)}] Testing {item_id}...", end=" ", flush=True)
            
            result = await test_models_for_sku(
                db, item_id, client_id, test_days, include_darts_chronos
            )
            
            if result:
                all_results.append(result)
                # Count successful models
                successful = sum(1 for m in result["models"].values() if m.get("status") == "success")
                print(f"✅ ({successful}/{len(result['models'])} models)")
            else:
                print("❌ Failed")
        
        # Generate summary
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        if not all_results:
            print("❌ No successful tests")
            return
        
        print(f"\n📊 Results:")
        print(f"   Total SKUs tested: {len(all_results)}")
        
        # Aggregate metrics by model
        model_metrics = {}
        for result in all_results:
            for model_name, model_result in result["models"].items():
                if model_result.get("status") == "success":
                    if model_name not in model_metrics:
                        model_metrics[model_name] = {
                            "mape": [],
                            "mae": [],
                            "rmse": [],
                            "count": 0,
                        }
                    
                    if model_result.get("mape") is not None:
                        model_metrics[model_name]["mape"].append(model_result["mape"])
                    model_metrics[model_name]["mae"].append(model_result["mae"])
                    model_metrics[model_name]["rmse"].append(model_result["rmse"])
                    model_metrics[model_name]["count"] += 1
        
        # Print summary table
        print(f"\n📈 Model Performance Summary:")
        print(f"   {'Model':<30} {'Count':<8} {'MAPE (mean)':<15} {'MAE (mean)':<15} {'RMSE (mean)':<15}")
        print("   " + "-" * 85)
        
        for model_name, metrics in sorted(model_metrics.items()):
            mape_str = f"{np.mean(metrics['mape']):.2f}%" if metrics['mape'] else "N/A"
            mae_str = f"{np.mean(metrics['mae']):.2f}"
            rmse_str = f"{np.mean(metrics['rmse']):.2f}"
            print(f"   {model_name:<30} {metrics['count']:<8} {mape_str:<15} {mae_str:<15} {rmse_str:<15}")
        
        # Per-SKU comparison table
        print(f"\n📋 Per-SKU Comparison (showing best model by MAE):")
        print(f"   {'SKU':<10} {'Best Model':<30} {'MAE':<10} {'MAPE':<10}")
        print("   " + "-" * 65)
        
        for result in all_results:
            item_id = result["item_id"]
            best_model = None
            best_mae = float('inf')
            
            for model_name, model_result in result["models"].items():
                if model_result.get("status") == "success":
                    mae_val = model_result.get("mae", float('inf'))
                    if mae_val < best_mae:
                        best_mae = mae_val
                        best_model = model_name
            
            if best_model:
                best_result = result["models"][best_model]
                mape_str = f"{best_result['mape']:.1f}%" if best_result.get('mape') else "N/A"
                print(f"   {item_id:<10} {best_model:<30} {best_mae:<10.2f} {mape_str:<10}")
        
        # Save detailed report
        report_dir = Path(backend_dir) / "reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"comprehensive_model_comparison_{timestamp}.json"
        
        report_data = {
            "test_config": {
                "test_days": test_days,
                "max_skus": max_skus,
                "include_darts_chronos": include_darts_chronos,
                "timestamp": timestamp,
            },
            "summary": {
                "total_tested": len(all_results),
                "models_tested": list(model_metrics.keys()),
            },
            "model_metrics": {
                name: {
                    "count": m["count"],
                    "mape_mean": float(np.mean(m["mape"])) if m["mape"] else None,
                    "mae_mean": float(np.mean(m["mae"])),
                    "rmse_mean": float(np.mean(m["rmse"])),
                }
                for name, m in model_metrics.items()
            },
            "results": all_results,
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        print("\n" + "=" * 80)
        print("✅ Test complete!")
        print("=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive model comparison using Darts")
    parser.add_argument("--max-skus", type=int, default=20, help="Maximum SKUs to test (default: 20)")
    parser.add_argument("--test-days", type=int, default=30, help="Test period in days (default: 30)")
    parser.add_argument("--darts-chronos", action="store_true", help="Include Darts Chronos2Model (slow)")
    
    args = parser.parse_args()
    
    asyncio.run(main(
        max_skus=args.max_skus,
        test_days=args.test_days,
        include_darts_chronos=args.darts_chronos,
    ))

