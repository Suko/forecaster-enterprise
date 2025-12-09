"""Test forecast accuracy on real data - standalone script

Tests multiple SKUs and generates comprehensive reports.
"""
import asyncio
import sys
from datetime import date, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import numpy as np
from uuid import uuid4
import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Load environment
load_dotenv()

# Import models - adjust path since we're now in tests/ folder
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from models.database import get_db
from models.forecast import ForecastRun, ForecastResult
from models.client import Client
from models.user import User
from forecasting.services.forecast_service import ForecastService


async def test_single_sku(
    db: AsyncSession,
    forecast_service: ForecastService,
    item_id: str,
    client_id: str,
    user_id: str,
    test_days: int,
    prediction_length: int,
    min_date: date,
    max_date: date,
) -> Dict[str, Any]:
    """Test forecast accuracy for a single SKU"""
    
    result = {
        "item_id": item_id,
        "status": "pending",
        "error": None,
        "data_info": {},
        "forecast_run_id": None,
        "metrics": {},
        "validation": {},
    }
    
    try:
        # Calculate train/test split
        test_start_date = max_date - timedelta(days=test_days - 1)
        train_end_date = test_start_date - timedelta(days=1)
        train_days = (train_end_date - min_date).days + 1
        
        # Get actual values for test period
        actuals_result = await db.execute(
            text("""
                SELECT date_local, units_sold 
                FROM ts_demand_daily 
                WHERE item_id = :item_id 
                AND client_id = :client_id
                AND date_local >= :test_start
                AND date_local <= :test_end
                ORDER BY date_local
            """),
            {
                "item_id": item_id,
                "client_id": client_id,
                "test_start": test_start_date,
                "test_end": max_date,
            }
        )
        
        actuals = actuals_result.fetchall()
        actual_values = [float(row.units_sold) for row in actuals]
        actual_dates = [row.date_local for row in actuals]
        
        if len(actual_values) < test_days:
            result["status"] = "insufficient_test_data"
            result["error"] = f"Only {len(actual_values)} days in test period (need {test_days})"
            return result
        
        # Store data info
        actual_arr = np.array(actual_values)
        result["data_info"] = {
            "total_days": (max_date - min_date).days + 1,
            "train_days": train_days,
            "test_days": len(actual_values),
            "test_start": str(test_start_date),
            "test_end": str(max_date),
            "actual_mean": float(np.mean(actual_arr)),
            "actual_std": float(np.std(actual_arr)),
            "actual_min": float(np.min(actual_arr)),
            "actual_max": float(np.max(actual_arr)),
            "actual_cv": float(np.std(actual_arr) / np.mean(actual_arr) * 100) if np.mean(actual_arr) > 0 else 0,
        }
        
        # Generate forecast
        forecast_run = await forecast_service.generate_forecast(
            client_id=client_id,
            user_id=user_id,
            item_ids=[item_id],
            prediction_length=prediction_length,
            primary_model="chronos-2",
            include_baseline=True,
            training_end_date=train_end_date,
        )
        
        # Refresh to get latest status
        await db.refresh(forecast_run)
        
        result["forecast_run_id"] = str(forecast_run.forecast_run_id)
        result["status"] = forecast_run.status
        
        # Check if forecast failed
        if forecast_run.status == "failed":
            result["status"] = "forecast_failed"
            result["error"] = forecast_run.error_message or "Forecast generation failed"
            return result
        
        # Get audit metadata if available
        if forecast_run.audit_metadata:
            result["validation"] = forecast_run.audit_metadata
        
        # Get predictions - need to flush/refresh to see committed data
        await db.flush()
        predictions_result = await db.execute(
            select(ForecastResult)
            .where(ForecastResult.forecast_run_id == forecast_run.forecast_run_id)
            .where(ForecastResult.item_id == item_id)
            .order_by(ForecastResult.method, ForecastResult.horizon_day)
        )
        
        all_predictions = predictions_result.scalars().all()
        if not all_predictions:
            result["status"] = "no_predictions"
            result["error"] = f"No predictions found for forecast_run_id {forecast_run.forecast_run_id}, status: {forecast_run.status}"
            return result
        
        # Group by method
        methods = set(p.method for p in all_predictions)
        result["metrics"] = {}
        
        for method in methods:
            method_predictions = [p for p in all_predictions if p.method == method]
            pred_by_date = {p.date: float(p.point_forecast) for p in method_predictions}
            
            # Match predictions to actuals by date
            pred_values = []
            matched_dates = []
            for actual_date, actual_val in zip(actual_dates, actual_values):
                if actual_date in pred_by_date:
                    pred_values.append(pred_by_date[actual_date])
                    matched_dates.append(actual_date)
            
            if len(pred_values) == 0:
                continue
            
            # Calculate metrics
            pred_arr = np.array(pred_values)
            actual_matched = np.array([actual_values[actual_dates.index(d)] for d in matched_dates])
            
            # MAPE (handle zeros)
            non_zero_mask = actual_matched != 0
            if non_zero_mask.sum() > 0:
                mape = float(np.mean(np.abs((actual_matched[non_zero_mask] - pred_arr[non_zero_mask]) / actual_matched[non_zero_mask])) * 100)
            else:
                mape = 0.0
            
            mae = float(np.mean(np.abs(actual_matched - pred_arr)))
            rmse = float(np.sqrt(np.mean((actual_matched - pred_arr) ** 2)))
            bias = float(np.mean(pred_arr - actual_matched))
            
            result["metrics"][method] = {
                "mape": mape,
                "mae": mae,
                "rmse": rmse,
                "bias": bias,
                "predicted_mean": float(np.mean(pred_arr)),
                "actual_mean": float(np.mean(actual_matched)),
                "matched_days": len(pred_values),
            }
        
        result["status"] = "success"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        import traceback
        result["traceback"] = traceback.format_exc()
    
    return result


async def test_forecast_accuracy(test_days: int = 30, prediction_length: int = None, max_skus: int = 20):
    """
    Test forecast accuracy for multiple SKUs and generate comprehensive report
    
    Args:
        test_days: Number of days to use as test period (default: 30)
        prediction_length: How many days ahead to forecast (default: same as test_days)
        max_skus: Maximum number of SKUs to test (default: 20)
    """
    if prediction_length is None:
        prediction_length = test_days
    
    # Get database URL
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/forecaster_enterprise")
    if not db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
    
    engine = create_async_engine(db_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # 1. Find SKUs with sufficient data
        print("=" * 80)
        print("Step 1: Finding SKUs with sufficient data")
        print("=" * 80)
        
        result = await db.execute(
            text("""
                SELECT 
                    MIN(date_local) as min_date,
                    MAX(date_local) as max_date,
                    COUNT(*) as count,
                    item_id,
                    client_id
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= :min_days
                ORDER BY COUNT(*) DESC
                LIMIT :max_skus
            """),
            {"min_days": test_days + 30, "max_skus": max_skus}  # Need at least test_days + 30 for training
        )
        
        all_skus = result.fetchall()
        
        if not all_skus:
            print("❌ No SKUs found with sufficient data")
            return
        
        print(f"✅ Found {len(all_skus)} SKUs with sufficient data")
        
        # Get client_id (assuming all same client)
        client_id = str(all_skus[0].client_id)
        
        # Find or create test user
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
        
        # 2. Test each SKU
        print("\n" + "=" * 80)
        print(f"Step 2: Testing {len(all_skus)} SKUs")
        print("=" * 80)
        
        forecast_service = ForecastService(db=db)
        all_results = []
        
        for idx, sku_row in enumerate(all_skus, 1):
            item_id = sku_row.item_id
            min_date = sku_row.min_date
            max_date = sku_row.max_date
            total_days = sku_row.count
            
            print(f"\n[{idx}/{len(all_skus)}] Testing {item_id}...")
            print(f"   Data: {total_days} days ({min_date} to {max_date})")
            
            # Rollback any previous failed transaction before starting new test
            try:
                await db.rollback()
            except:
                pass
            
            sku_result = await test_single_sku(
                db=db,
                forecast_service=forecast_service,
                item_id=item_id,
                client_id=client_id,
                user_id=user_id,
                test_days=test_days,
                prediction_length=prediction_length,
                min_date=min_date,
                max_date=max_date,
            )
            
            all_results.append(sku_result)
            
            # Print quick status
            if sku_result["status"] == "success":
                if "chronos-2" in sku_result["metrics"]:
                    mape = sku_result["metrics"]["chronos-2"]["mape"]
                    print(f"   ✅ Success - MAPE: {mape:.2f}%")
                else:
                    print(f"   ✅ Success - No chronos-2 metrics")
            else:
                error_msg = sku_result.get('error', 'Unknown error')
                # Truncate long error messages
                if len(error_msg) > 100:
                    error_msg = error_msg[:97] + "..."
                print(f"   ❌ {sku_result['status']}: {error_msg}")
        
        # 3. Generate summary report
        print("\n" + "=" * 80)
        print("Step 3: Summary Report")
        print("=" * 80)
        
        successful = [r for r in all_results if r["status"] == "success"]
        failed = [r for r in all_results if r["status"] != "success"]
        
        print(f"\n📊 Overall Statistics:")
        print(f"   Total SKUs tested: {len(all_results)}")
        print(f"   ✅ Successful: {len(successful)}")
        print(f"   ❌ Failed: {len(failed)}")
        
        if successful:
            # Chronos-2 metrics
            chronos_results = [
                r["metrics"]["chronos-2"] 
                for r in successful 
                if "chronos-2" in r["metrics"]
            ]
            
            if chronos_results:
                mape_values = [m["mape"] for m in chronos_results]
                mae_values = [m["mae"] for m in chronos_results]
                rmse_values = [m["rmse"] for m in chronos_results]
                
                print(f"\n📈 Chronos-2 Accuracy Metrics (n={len(chronos_results)}):")
                print(f"   MAPE:  Mean={np.mean(mape_values):.2f}%,  Min={np.min(mape_values):.2f}%,  Max={np.max(mape_values):.2f}%")
                print(f"   MAE:   Mean={np.mean(mae_values):.2f},   Min={np.min(mae_values):.2f},   Max={np.max(mae_values):.2f}")
                print(f"   RMSE:  Mean={np.mean(rmse_values):.2f},  Min={np.min(rmse_values):.2f},  Max={np.max(rmse_values):.2f}")
            
            # MA7 metrics
            ma7_results = [
                r["metrics"]["statistical_ma7"] 
                for r in successful 
                if "statistical_ma7" in r["metrics"]
            ]
            
            if ma7_results:
                mape_values_ma7 = [m["mape"] for m in ma7_results]
                print(f"\n📊 MA7 Baseline Metrics (n={len(ma7_results)}):")
                print(f"   MAPE:  Mean={np.mean(mape_values_ma7):.2f}%,  Min={np.min(mape_values_ma7):.2f}%,  Max={np.max(mape_values_ma7):.2f}%")
        
        # 4. Save detailed report to JSON
        report_dir = Path(backend_dir) / "reports"
        report_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"forecast_accuracy_report_{timestamp}.json"
        
        report_data = {
            "test_config": {
                "test_days": test_days,
                "prediction_length": prediction_length,
                "max_skus": max_skus,
                "timestamp": timestamp,
            },
            "summary": {
                "total_tested": len(all_results),
                "successful": len(successful),
                "failed": len(failed),
            },
            "results": all_results,
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\n💾 Detailed report saved to: {report_file}")
        
        # 5. Print per-SKU summary table
        print("\n" + "=" * 80)
        print("Step 4: Per-SKU Summary")
        print("=" * 80)
        
        print(f"\n{'SKU':<12} {'Status':<12} {'MAPE (C2)':<12} {'MAPE (MA7)':<12} {'Days':<8} {'CV%':<8}")
        print("-" * 80)
        
        for r in all_results:
            item_id = r["item_id"][:11]  # Truncate if long
            status = r["status"][:11]
            
            mape_c2 = "-"
            if "chronos-2" in r["metrics"]:
                mape_c2 = f"{r['metrics']['chronos-2']['mape']:.1f}%"
            
            mape_ma7 = "-"
            if "statistical_ma7" in r["metrics"]:
                mape_ma7 = f"{r['metrics']['statistical_ma7']['mape']:.1f}%"
            
            days = r.get("data_info", {}).get("total_days", "-")
            cv = "-"
            if "data_info" in r and "actual_cv" in r["data_info"]:
                cv = f"{r['data_info']['actual_cv']:.1f}%"
            
            print(f"{item_id:<12} {status:<12} {mape_c2:<12} {mape_ma7:<12} {days:<8} {cv:<8}")
        
        print("\n" + "=" * 80)
        print("✅ Test complete!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_forecast_accuracy())
