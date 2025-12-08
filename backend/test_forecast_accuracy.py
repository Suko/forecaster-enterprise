"""Test forecast accuracy on real data - standalone script"""
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

# Load environment
load_dotenv()

# Import models
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from models.database import get_db
from models.forecast import ForecastRun, ForecastResult
from models.client import Client
from models.user import User
from forecasting.services.forecast_service import ForecastService

async def test_forecast_accuracy(test_days: int = 30, prediction_length: int = None):
    """
    Test forecast accuracy by splitting data into train/test
    
    Args:
        test_days: Number of days to use as test period (default: 30)
        prediction_length: How many days ahead to forecast (default: same as test_days)
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
        # 1. Find a SKU with sufficient data
        print("=" * 60)
        print("Step 1: Finding SKU with data")
        print("=" * 60)
        
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
                HAVING COUNT(*) >= 60
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)
        )
        
        sku_data = result.first()
        
        if not sku_data:
            print("❌ No SKU found with sufficient data (need 60+ days)")
            return
        
        item_id = sku_data.item_id
        min_date = sku_data.min_date
        max_date = sku_data.max_date
        total_days = sku_data.count
        client_id = str(sku_data.client_id)
        
        print(f"✅ Found SKU: {item_id}")
        print(f"   Date range: {min_date} to {max_date}")
        print(f"   Total days: {total_days}")
        print(f"   Client ID: {client_id}")
        
        # Find or create a test user
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
        print(f"   Using user_id: {user_id}")
        
        # 2. Split data: last N days = test, rest = train
        print("\n" + "=" * 60)
        print("Step 2: Splitting data (train/test)")
        print("=" * 60)
        
        test_start_date = max_date - timedelta(days=test_days - 1)  # Last N days
        train_end_date = test_start_date - timedelta(days=1)
        train_days = (train_end_date - min_date).days + 1
        
        print(f"📊 Data Split Configuration:")
        print(f"   Total data: {total_days} days ({min_date} to {max_date})")
        print(f"   Training period: {train_days} days ({min_date} to {train_end_date})")
        print(f"   Test period: {test_days} days ({test_start_date} to {max_date})")
        print(f"   Prediction horizon: {prediction_length} days ahead")
        print(f"   Train/Test ratio: {train_days}/{test_days} = {train_days/test_days:.1f}:1")
        
        # 3. Get actual values for test period
        result = await db.execute(
            text("""
                SELECT date_local, units_sold 
                FROM ts_demand_daily 
                WHERE item_id = :item_id 
                AND client_id = :client_id
                AND date_local >= :test_start
                AND date_local <= :test_end
                ORDER BY date_local
            """),
            {"item_id": item_id, "client_id": client_id, "test_start": test_start_date, "test_end": max_date}
        )
        
        actuals = result.fetchall()
        actual_values = [float(row.units_sold) for row in actuals]
        actual_dates = [row.date_local for row in actuals]
        
        print(f"\n✅ Test period actuals: {len(actual_values)} days")
        if len(actual_values) > 0:
            actual_arr = np.array(actual_values)
            print(f"   Mean: {np.mean(actual_arr):.2f}")
            print(f"   Std: {np.std(actual_arr):.2f}")
            print(f"   Min: {np.min(actual_arr):.2f}, Max: {np.max(actual_arr):.2f}")
            print(f"   CV (Coefficient of Variation): {np.std(actual_arr)/np.mean(actual_arr)*100:.1f}%")
            print(f"   Sample values: {actual_values[:5]}...")
        
        # 4. Run forecast
        print("\n" + "=" * 60)
        print("Step 3: Running forecast")
        print("=" * 60)
        
        forecast_service = ForecastService(db=db)
        
        print(f"\nGenerating forecast for {item_id}...")
        print(f"   Using training data up to: {train_end_date}")
        print(f"   Will predict for: {test_start_date} onwards")
        
        # CRITICAL: Limit training data to train_end_date so model doesn't see test period
        forecast_run = await forecast_service.generate_forecast(
            client_id=client_id,
            user_id=user_id,
            item_ids=[item_id],
            prediction_length=prediction_length,
            primary_model="chronos-2",
            include_baseline=True,
            training_end_date=train_end_date,  # Only use data up to train_end_date
        )
        
        print(f"✅ Forecast generated: Run ID {forecast_run.forecast_run_id}")
        
        # 5. Get predictions for all methods
        print("\n" + "=" * 60)
        print("Step 4: Comparing predictions vs actuals")
        print("=" * 60)
        
        result = await db.execute(
            select(ForecastResult)
            .where(ForecastResult.forecast_run_id == forecast_run.forecast_run_id)
            .where(ForecastResult.item_id == item_id)
            .order_by(ForecastResult.method, ForecastResult.horizon_day)
        )
        
        all_predictions = result.scalars().all()
        if not all_predictions:
            print("❌ No predictions found")
            return
        
        methods = set(p.method for p in all_predictions)
        print(f"   Methods found: {methods}")
        
        # Compare all methods - match by date, not just order
        results_by_method = {}
        for method in methods:
            method_predictions = [p for p in all_predictions if p.method == method]
            # Create a dict by date for easy lookup
            pred_by_date = {p.date: float(p.point_forecast) for p in method_predictions}
            
            # Match predictions to actuals by date
            method_pred_values = []
            for actual_date in actual_dates:
                if actual_date in pred_by_date:
                    method_pred_values.append(pred_by_date[actual_date])
                else:
                    # If date doesn't match, skip this actual
                    pass
            
            if len(method_pred_values) > 0 and len(method_pred_values) == len(actual_values):
                results_by_method[method] = method_pred_values
            elif len(method_pred_values) > 0:
                # If counts don't match, take what we have
                min_len = min(len(method_pred_values), len(actual_values))
                method_pred_values = method_pred_values[:min_len]
                if min_len > 0:
                    results_by_method[method] = method_pred_values
        
        # 6. Calculate accuracy metrics for each method
        print("\n" + "=" * 60)
        print("Step 5: Calculating accuracy metrics")
        print("=" * 60)
        
        actual_arr = np.array(actual_values)
        
        for method, pred_values in results_by_method.items():
            pred_arr = np.array(pred_values)
            
            # Filter out zeros for MAPE calculation
            non_zero_mask = actual_arr != 0
            if non_zero_mask.sum() > 0:
                mape = np.mean(np.abs((actual_arr[non_zero_mask] - pred_arr[non_zero_mask]) / actual_arr[non_zero_mask])) * 100
            else:
                mape = 0
            
            mae = np.mean(np.abs(actual_arr - pred_arr))
            rmse = np.sqrt(np.mean((actual_arr - pred_arr) ** 2))
            bias = np.mean(pred_arr - actual_arr)
            
            print(f"\n📊 {method.upper()} Results for {item_id}:")
            print(f"   MAPE: {mape:.2f}%")
            print(f"   MAE: {mae:.2f}")
            print(f"   RMSE: {rmse:.2f}")
            print(f"   Bias: {bias:.2f} ({'over' if bias > 0 else 'under'}-forecasting)")
            print(f"   Predicted mean: {np.mean(pred_arr):.2f} (actual: {np.mean(actual_arr):.2f})")
        
        # Show comparison table for primary method
        primary_method = "chronos-2" if "chronos-2" in results_by_method else list(results_by_method.keys())[0]
        pred_values = results_by_method[primary_method]
        
        print(f"\n📈 Sample Comparison - {primary_method.upper()} (first 10 days):")
        print(f"   Date       | Actual | Predicted | Error | % Error")
        print(f"   {'-' * 55}")
        for i in range(min(10, len(actual_values))):
            error = actual_values[i] - pred_values[i]
            pct_error = (error / actual_values[i] * 100) if actual_values[i] != 0 else 0
            print(f"   {actual_dates[i]} | {actual_values[i]:7.2f} | {pred_values[i]:9.2f} | {error:6.2f} | {pct_error:6.1f}%")
        
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_forecast_accuracy())
