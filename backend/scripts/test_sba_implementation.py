#!/usr/bin/env python3
"""
Test SBA Implementation

Tests SBA model on lumpy demand SKUs and compares with MA7 to measure improvement.
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


async def test_sba_implementation():
    """Test SBA on lumpy demand SKUs"""
    
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
        print("SBA Implementation Test")
        print("=" * 80)
        
        # Get lumpy demand SKUs
        result = await db.execute(
            select(SKUClassification).where(
                SKUClassification.demand_pattern == "lumpy"
            )
        )
        lumpy_skus = result.scalars().all()
        
        if not lumpy_skus:
            print("❌ No lumpy demand SKUs found")
            return
        
        print(f"\n📦 Found {len(lumpy_skus)} lumpy demand SKUs")
        
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
        
        print(f"\n🧪 Testing SBA vs MA7 on {len(lumpy_skus)} lumpy demand SKUs...")
        print(f"   Test period: Last {test_days} days")
        print(f"   Prediction length: {prediction_length} days\n")
        
        results = []
        
        for idx, classification in enumerate(lumpy_skus, 1):
            item_id = classification.item_id
            client_id = str(classification.client_id)
            
            print(f"[{idx}/{len(lumpy_skus)}] {item_id} ({classification.abc_class}-{classification.xyz_class})")
            
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
            
            # Test SBA
            try:
                forecast_run_sba = await service.generate_forecast(
                    client_id=client_id,
                    user_id=user.id,
                    item_ids=[item_id],
                    prediction_length=prediction_length,
                    primary_model="sba",
                    include_baseline=False,
                    training_end_date=train_end,
                )
                
                if forecast_run_sba.status != "completed":
                    print(f"  ⚠️  SBA failed: {forecast_run_sba.status} - {forecast_run_sba.error_message}")
                    continue
                
                predictions_sba = await service.get_forecast_results(
                    forecast_run_id=forecast_run_sba.forecast_run_id,
                    method="sba",
                )
                
                if item_id not in predictions_sba:
                    print(f"  ⚠️  No SBA predictions found for {item_id}")
                    continue
                
                pred_data_sba = predictions_sba[item_id]
                
                # Test MA7 for comparison (force MA7, bypass routing)
                # We'll compare with previous MA7 results from comprehensive comparison
                # For now, just test SBA and we'll compare with historical MA7 data
                try:
                    forecast_run_ma7 = await service.generate_forecast(
                        client_id=client_id,
                        user_id=user.id,
                        item_ids=[item_id],
                        prediction_length=prediction_length,
                        primary_model="statistical_ma7",
                        include_baseline=False,
                        training_end_date=train_end,
                    )
                    
                    if forecast_run_ma7.status == "completed":
                        predictions_ma7 = await service.get_forecast_results(
                            forecast_run_id=forecast_run_ma7.forecast_run_id,
                            method="statistical_ma7",
                        )
                        
                        if item_id in predictions_ma7:
                            pred_data_ma7 = predictions_ma7[item_id]
                        else:
                            # Skip MA7 comparison for this SKU
                            pred_data_ma7 = None
                    else:
                        pred_data_ma7 = None
                except Exception as e:
                    # Skip MA7 if it fails
                    pred_data_ma7 = None
                
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
                    continue
                
                # Calculate metrics
                actual_values = [float(row.units_sold) for row in actuals[:prediction_length]]
                pred_values_sba = [float(p['point_forecast']) for p in pred_data_sba[:prediction_length]]
                
                mape_sba = quality_calc.calculate_mape(actual_values, pred_values_sba)
                
                # Compare with MA7 if available
                if pred_data_ma7:
                    pred_values_ma7 = [float(p['point_forecast']) for p in pred_data_ma7[:prediction_length]]
                    mape_ma7 = quality_calc.calculate_mape(actual_values, pred_values_ma7)
                    improvement = mape_ma7 - mape_sba
                    improvement_pct = (improvement / mape_ma7 * 100) if mape_ma7 > 0 else 0
                    
                    results.append({
                        "item_id": item_id,
                        "mape_sba": mape_sba,
                        "mape_ma7": mape_ma7,
                        "improvement": improvement,
                        "improvement_pct": improvement_pct,
                    })
                    
                    status = "✅" if mape_sba < mape_ma7 else "⚠️"
                    print(f"  {status} SBA: {mape_sba:.1f}% | MA7: {mape_ma7:.1f}% | Improvement: {improvement:.1f}% ({improvement_pct:.1f}%)")
                else:
                    # Just SBA results
                    results.append({
                        "item_id": item_id,
                        "mape_sba": mape_sba,
                        "mape_ma7": None,
                        "improvement": None,
                        "improvement_pct": None,
                    })
                    
                    # Check if within expected range (50-90%)
                    target_min, target_max = 50, 90
                    in_range = target_min <= mape_sba <= target_max
                    status = "✅" if in_range else "⚠️"
                    print(f"  {status} SBA: {mape_sba:.1f}% (Expected: {target_min}-{target_max}%)")
                
            except Exception as e:
                print(f"  ⚠️  Error: {e}")
                continue
        
        # Summary
        if not results:
            print("\n❌ No results to analyze")
            return
        
        df = pd.DataFrame(results)
        
        print("\n" + "=" * 80)
        print("Results Summary")
        print("=" * 80)
        
        print(f"\n📊 Overall Performance:")
        print(f"   SBA Average MAPE: {df['mape_sba'].mean():.1f}%")
        
        # MA7 comparison if available
        if df['mape_ma7'].notna().any():
            print(f"   MA7 Average MAPE: {df['mape_ma7'].mean():.1f}%")
            print(f"   Average Improvement: {df['improvement'].mean():.1f} percentage points")
            print(f"   Average Improvement %: {df['improvement_pct'].mean():.1f}%")
            
            print(f"\n📊 Improvement Distribution:")
            better = (df['mape_sba'] < df['mape_ma7']).sum()
            worse = (df['mape_sba'] > df['mape_ma7']).sum()
            same = (df['mape_sba'] == df['mape_ma7']).sum()
            print(f"   SBA Better: {better}/{len(df)} ({better/len(df)*100:.1f}%)")
            print(f"   MA7 Better: {worse}/{len(df)} ({worse/len(df)*100:.1f}%)")
            print(f"   Same: {same}/{len(df)} ({same/len(df)*100:.1f}%)")
        else:
            print(f"   (MA7 comparison not available - using previous results)")
        
        print(f"\n📊 Target Achievement:")
        target_min, target_max = 50, 90
        within_target = ((df['mape_sba'] >= target_min) & (df['mape_sba'] <= target_max)).sum()
        print(f"   Within Expected Range ({target_min}-{target_max}%): {within_target}/{len(df)} ({within_target/len(df)*100:.1f}%)")
        
        # Save results
        output_file = backend_dir / "reports" / f"sba_test_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "=" * 80)
        print("✅ Test Complete!")
        print("=" * 80)
        
        return df


if __name__ == "__main__":
    asyncio.run(test_sba_implementation())

