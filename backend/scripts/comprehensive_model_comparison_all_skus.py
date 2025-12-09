#!/usr/bin/env python3
"""
Comprehensive Model Comparison - All SKUs

Compares ALL available models (Chronos-2, MA7) across ALL SKUs in database
to understand which models work best for which patterns BEFORE implementing new methods.

This helps us:
1. See actual performance data
2. Decide which methods to implement first
3. Validate our classification recommendations
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd
import numpy as np
from collections import defaultdict

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


async def compare_all_models_all_skus():
    """Compare all models across all SKUs"""
    
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
        print("Comprehensive Model Comparison - All SKUs")
        print("=" * 80)
        
        # Get all SKUs with sufficient data
        result = await db.execute(
            text("""
                SELECT DISTINCT item_id, client_id
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 60
                ORDER BY item_id
            """)
        )
        all_skus = result.fetchall()
        
        if not all_skus:
            print("❌ No SKUs found with sufficient data")
            return
        
        print(f"\n📦 Found {len(all_skus)} SKUs with sufficient data")
        
        # Get classifications
        result = await db.execute(
            select(SKUClassification)
        )
        classifications = {c.item_id: c for c in result.scalars().all()}
        
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
        
        # Available models to test
        models_to_test = ["chronos-2", "statistical_ma7"]
        
        # Results storage
        all_results = []
        
        print(f"\n🧪 Testing {len(models_to_test)} models on {len(all_skus)} SKUs...")
        print(f"   Models: {', '.join(models_to_test)}")
        print(f"   Test period: Last {test_days} days")
        print(f"   Prediction length: {prediction_length} days\n")
        
        for idx, (item_id, client_id) in enumerate(all_skus, 1):
            client_id_str = str(client_id)
            
            # Get classification if available
            classification = classifications.get(item_id)
            abc_xyz = f"{classification.abc_class}-{classification.xyz_class}" if classification else "Unknown"
            pattern = classification.demand_pattern if classification else "unknown"
            recommended = classification.recommended_method if classification else "none"
            
            print(f"[{idx}/{len(all_skus)}] {item_id} ({abc_xyz}, {pattern}, recommends: {recommended})")
            
            # Get date range
            result = await db.execute(
                text("""
                    SELECT MIN(date_local) as min_date, MAX(date_local) as max_date
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                """),
                {"item_id": item_id, "client_id": client_id_str}
            )
            row = result.fetchone()
            
            if not row or not row.min_date:
                print(f"  ⚠️  No data found")
                continue
            
            max_date = row.max_date
            test_start = max_date - timedelta(days=test_days - 1)
            train_end = test_start - timedelta(days=1)
            
            # Test each model
            for model_id in models_to_test:
                try:
                    # Generate forecast
                    forecast_run = await service.generate_forecast(
                        client_id=client_id_str,
                        user_id=user.id,
                        item_ids=[item_id],
                        prediction_length=prediction_length,
                        primary_model=model_id,
                        include_baseline=False,
                        training_end_date=train_end,
                    )
                    
                    if forecast_run.status != "completed":
                        continue
                    
                    # Get predictions
                    predictions = await service.get_forecast_results(
                        forecast_run_id=forecast_run.forecast_run_id,
                        method=model_id,
                    )
                    
                    if item_id not in predictions:
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
                        {"item_id": item_id, "client_id": client_id_str, "test_start": test_start, "max_date": max_date}
                    )
                    actuals = result.fetchall()
                    
                    if len(actuals) < prediction_length:
                        continue
                    
                    # Calculate metrics
                    actual_values = [float(row.units_sold) for row in actuals[:prediction_length]]
                    pred_values = [float(p['point_forecast']) for p in pred_data[:prediction_length]]
                    
                    mape = quality_calc.calculate_mape(actual_values, pred_values)
                    mae = quality_calc.calculate_mae(actual_values, pred_values)
                    rmse = quality_calc.calculate_rmse(actual_values, pred_values)
                    bias = quality_calc.calculate_bias(actual_values, pred_values)
                    
                    all_results.append({
                        "item_id": item_id,
                        "model": model_id,
                        "abc_xyz": abc_xyz,
                        "pattern": pattern,
                        "recommended": recommended,
                        "mape": mape,
                        "mae": mae,
                        "rmse": rmse,
                        "bias": bias,
                    })
                    
                except Exception as e:
                    print(f"  ⚠️  {model_id} failed: {e}")
                    continue
            
            # Progress update
            if idx % 5 == 0:
                print(f"  Progress: {idx}/{len(all_skus)} SKUs tested...")
        
        # Analysis
        if not all_results:
            print("\n❌ No results to analyze")
            return
        
        df = pd.DataFrame(all_results)
        
        print("\n" + "=" * 80)
        print("Results Analysis")
        print("=" * 80)
        
        # Overall comparison
        print(f"\n📊 Overall Performance by Model:")
        for model in models_to_test:
            model_df = df[df['model'] == model]
            if not model_df.empty:
                print(f"\n   {model}:")
                print(f"      Average MAPE: {model_df['mape'].mean():.1f}%")
                print(f"      Average MAE: {model_df['mae'].mean():.2f}")
                print(f"      Average RMSE: {model_df['rmse'].mean():.2f}")
                print(f"      Average Bias: {model_df['bias'].mean():.2f}")
                print(f"      SKUs tested: {len(model_df)}")
        
        # By classification
        print(f"\n📊 Performance by ABC-XYZ Classification:")
        for combo in sorted(df['abc_xyz'].unique()):
            combo_df = df[df['abc_xyz'] == combo]
            if combo_df.empty:
                continue
            print(f"\n   {combo}:")
            for model in models_to_test:
                model_df = combo_df[combo_df['model'] == model]
                if not model_df.empty:
                    print(f"      {model}: MAPE {model_df['mape'].mean():.1f}% (n={len(model_df)})")
        
        # By pattern
        print(f"\n📊 Performance by Demand Pattern:")
        for pattern in sorted(df['pattern'].unique()):
            pattern_df = df[df['pattern'] == pattern]
            if pattern_df.empty:
                continue
            print(f"\n   {pattern}:")
            for model in models_to_test:
                model_df = pattern_df[pattern_df['model'] == model]
                if not model_df.empty:
                    print(f"      {model}: MAPE {model_df['mape'].mean():.1f}% (n={len(model_df)})")
        
        # Best model per SKU
        print(f"\n📊 Best Model per SKU:")
        best_model_counts = defaultdict(int)
        for item_id in df['item_id'].unique():
            item_df = df[df['item_id'] == item_id]
            if len(item_df) < 2:  # Need at least 2 models to compare
                continue
            # Find model with lowest MAPE for this SKU
            best_idx = item_df['mape'].idxmin()
            best = item_df.loc[best_idx]
            best_model_counts[best['model']] += 1
        
        print(f"   Chronos-2 best: {best_model_counts.get('chronos-2', 0)} SKUs")
        print(f"   MA7 best: {best_model_counts.get('statistical_ma7', 0)} SKUs")
        
        # Show SKUs where both models were tested
        both_tested = []
        for item_id in df['item_id'].unique():
            item_df = df[df['item_id'] == item_id]
            models_tested = set(item_df['model'].unique())
            if len(models_tested) >= 2:
                both_tested.append(item_id)
        
        if both_tested:
            print(f"\n   SKUs with both models tested: {len(both_tested)}")
            print(f"   (See CSV for detailed comparison)")
        
        # Save results
        output_file = backend_dir / "reports" / f"model_comparison_all_skus_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        print("\n" + "=" * 80)
        print("✅ Comparison Complete!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(compare_all_models_all_skus())

