#!/usr/bin/env python3
"""
Method Routing Validation

Validates that method routing is working correctly:
1. SKUs are routed to recommended methods
2. Routing improves accuracy vs always using Chronos-2
3. Correct methods are used for each classification
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


async def validate_method_routing():
    """Validate method routing end-to-end"""
    
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
        print("Method Routing Validation")
        print("=" * 80)
        
        # Get all classified SKUs
        result = await db.execute(select(SKUClassification))
        all_classifications = result.scalars().all()
        
        if not all_classifications:
            print("❌ No classified SKUs found")
            return
        
        print(f"\n📦 Found {len(all_classifications)} classified SKUs")
        
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
        
        print(f"\n🧪 Testing method routing on {len(all_classifications)} SKUs...")
        print(f"   Test period: Last {test_days} days")
        print(f"   Prediction length: {prediction_length} days\n")
        
        results = []
        routing_stats = defaultdict(lambda: {"correct": 0, "total": 0, "improvements": []})
        
        for idx, classification in enumerate(all_classifications, 1):
            item_id = classification.item_id
            client_id = str(classification.client_id)
            expected_method = classification.recommended_method
            
            # Map to actual method name
            method_mapping = {
                "chronos2": "chronos-2",
                "chronos-2": "chronos-2",
                "ma7": "statistical_ma7",
                "statistical_ma7": "statistical_ma7",
                "sba": "sba",
                "croston": "croston",
                "min_max": "min_max",
            }
            expected_actual_method = method_mapping.get(expected_method, "chronos-2")
            
            print(f"[{idx}/{len(all_classifications)}] {item_id}")
            print(f"   {classification.abc_class}-{classification.xyz_class}, {classification.demand_pattern}")
            print(f"   Expected: {expected_method} → {expected_actual_method}")
            
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
                print(f"  ⚠️  No data found\n")
                continue
            
            max_date = row.max_date
            test_start = max_date - timedelta(days=test_days - 1)
            train_end = test_start - timedelta(days=1)
            
            # Test with routing (use primary_model, routing will override)
            try:
                forecast_run_routed = await service.generate_forecast(
                    client_id=client_id,
                    user_id=user.id,
                    item_ids=[item_id],
                    prediction_length=prediction_length,
                    primary_model="chronos-2",  # Will be overridden by routing
                    include_baseline=False,
                    training_end_date=train_end,
                )
                
                if forecast_run_routed.status != "completed":
                    print(f"  ⚠️  Routed forecast failed: {forecast_run_routed.error_message}\n")
                    continue
                
                # Check what method was actually used
                actual_method = forecast_run_routed.recommended_method or forecast_run_routed.primary_model
                print(f"   Actual method used: {actual_method}")
                
                # Verify routing correctness
                routing_correct = (actual_method == expected_actual_method)
                routing_stats[f"{classification.abc_class}-{classification.xyz_class}"]["total"] += 1
                if routing_correct:
                    routing_stats[f"{classification.abc_class}-{classification.xyz_class}"]["correct"] += 1
                
                status = "✅" if routing_correct else "⚠️"
                print(f"   {status} Routing: {'Correct' if routing_correct else 'Incorrect'}")
                
                # Get predictions
                predictions_routed = await service.get_forecast_results(
                    forecast_run_id=forecast_run_routed.forecast_run_id,
                    method=actual_method,
                )
                
                if item_id not in predictions_routed:
                    print(f"  ⚠️  No predictions found\n")
                    continue
                
                pred_data_routed = predictions_routed[item_id]
                
                # Test without routing (force Chronos-2)
                # We'll compare routed method vs Chronos-2
                predictions_chronos = await service.get_forecast_results(
                    forecast_run_id=forecast_run_routed.forecast_run_id,
                    method="chronos-2",
                )
                
                # If Chronos-2 wasn't run, generate it separately
                if item_id not in predictions_chronos or actual_method == "chronos-2":
                    # Generate Chronos-2 forecast for comparison
                    forecast_run_chronos = await service.generate_forecast(
                        client_id=client_id,
                        user_id=user.id,
                        item_ids=[item_id],
                        prediction_length=prediction_length,
                        primary_model="chronos-2",
                        include_baseline=False,
                        training_end_date=train_end,
                    )
                    
                    if forecast_run_chronos.status == "completed":
                        predictions_chronos = await service.get_forecast_results(
                            forecast_run_id=forecast_run_chronos.forecast_run_id,
                            method="chronos-2",
                        )
                
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
                    print(f"  ⚠️  Insufficient actuals\n")
                    continue
                
                # Calculate metrics for routed method
                actual_values = [float(row.units_sold) for row in actuals[:prediction_length]]
                pred_values_routed = [float(p['point_forecast']) for p in pred_data_routed[:prediction_length]]
                
                mape_routed = quality_calc.calculate_mape(actual_values, pred_values_routed)
                
                # Compare with Chronos-2 if available
                if item_id in predictions_chronos and actual_method != "chronos-2":
                    pred_values_chronos = [float(p['point_forecast']) for p in predictions_chronos[item_id][:prediction_length]]
                    mape_chronos = quality_calc.calculate_mape(actual_values, pred_values_chronos)
                    
                    improvement = mape_chronos - mape_routed
                    improvement_pct = (improvement / mape_chronos * 100) if mape_chronos > 0 else 0
                    
                    results.append({
                        "item_id": item_id,
                        "classification": f"{classification.abc_class}-{classification.xyz_class}",
                        "pattern": classification.demand_pattern,
                        "expected_method": expected_method,
                        "actual_method": actual_method,
                        "routing_correct": routing_correct,
                        "mape_routed": mape_routed,
                        "mape_chronos2": mape_chronos,
                        "improvement": improvement,
                        "improvement_pct": improvement_pct,
                        "expected_mape_min": classification.expected_mape_min,
                        "expected_mape_max": classification.expected_mape_max,
                    })
                    
                    routing_stats[f"{classification.abc_class}-{classification.xyz_class}"]["improvements"].append(improvement)
                    
                    status_improvement = "✅" if improvement > 0 else "⚠️"
                    print(f"   {status_improvement} Routed: {mape_routed:.1f}% | Chronos-2: {mape_chronos:.1f}% | Improvement: {improvement:.1f}%")
                else:
                    # Only routed method available
                    results.append({
                        "item_id": item_id,
                        "classification": f"{classification.abc_class}-{classification.xyz_class}",
                        "pattern": classification.demand_pattern,
                        "expected_method": expected_method,
                        "actual_method": actual_method,
                        "routing_correct": routing_correct,
                        "mape_routed": mape_routed,
                        "mape_chronos2": None,
                        "improvement": None,
                        "improvement_pct": None,
                        "expected_mape_min": classification.expected_mape_min,
                        "expected_mape_max": classification.expected_mape_max,
                    })
                    
                    in_range = classification.expected_mape_min <= mape_routed <= classification.expected_mape_max
                    status = "✅" if in_range else "⚠️"
                    print(f"   {status} Routed method: {mape_routed:.1f}% (Expected: {classification.expected_mape_min:.1f}-{classification.expected_mape_max:.1f}%)")
                
                print()
                
            except Exception as e:
                print(f"  ⚠️  Error: {e}\n")
                continue
        
        # Summary
        if not results:
            print("\n❌ No results to analyze")
            return
        
        df = pd.DataFrame(results)
        
        print("=" * 80)
        print("Validation Results")
        print("=" * 80)
        
        # Routing correctness
        print(f"\n📊 Routing Correctness:")
        total_correct = df['routing_correct'].sum()
        total_skus = len(df)
        print(f"   Correct routing: {total_correct}/{total_skus} ({total_correct/total_skus*100:.1f}%)")
        
        # By classification
        print(f"\n📊 Routing Accuracy by Classification:")
        for classification in sorted(df['classification'].unique()):
            class_df = df[df['classification'] == classification]
            correct = class_df['routing_correct'].sum()
            total = len(class_df)
            print(f"   {classification}: {correct}/{total} ({correct/total*100:.1f}%)")
        
        # Method distribution
        print(f"\n📊 Methods Used:")
        method_counts = df['actual_method'].value_counts()
        for method, count in method_counts.items():
            print(f"   {method}: {count} SKUs ({count/len(df)*100:.1f}%)")
        
        # Performance comparison (where both methods available)
        comparison_df = df[df['mape_chronos2'].notna()]
        if len(comparison_df) > 0:
            print(f"\n📊 Performance Comparison (Routed vs Chronos-2):")
            print(f"   Routed Average MAPE: {comparison_df['mape_routed'].mean():.1f}%")
            print(f"   Chronos-2 Average MAPE: {comparison_df['mape_chronos2'].mean():.1f}%")
            print(f"   Average Improvement: {comparison_df['improvement'].mean():.1f} percentage points")
            
            better = (comparison_df['improvement'] > 0).sum()
            worse = (comparison_df['improvement'] < 0).sum()
            same = (comparison_df['improvement'] == 0).sum()
            print(f"\n   Routing Better: {better}/{len(comparison_df)} ({better/len(comparison_df)*100:.1f}%)")
            print(f"   Chronos-2 Better: {worse}/{len(comparison_df)} ({worse/len(comparison_df)*100:.1f}%)")
            print(f"   Same: {same}/{len(comparison_df)} ({same/len(comparison_df)*100:.1f}%)")
        
        # Within expected range
        print(f"\n📊 Within Expected MAPE Range:")
        in_range = ((df['mape_routed'] >= df['expected_mape_min']) & 
                   (df['mape_routed'] <= df['expected_mape_max'])).sum()
        print(f"   Routed method: {in_range}/{len(df)} ({in_range/len(df)*100:.1f}%)")
        
        # By classification
        print(f"\n📊 Within Range by Classification:")
        for classification in sorted(df['classification'].unique()):
            class_df = df[df['classification'] == classification]
            in_range = ((class_df['mape_routed'] >= class_df['expected_mape_min']) & 
                       (class_df['mape_routed'] <= class_df['expected_mape_max'])).sum()
            print(f"   {classification}: {in_range}/{len(class_df)} ({in_range/len(class_df)*100:.1f}%)")
        
        # Save results
        output_file = backend_dir / "reports" / f"method_routing_validation_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_file, index=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        # Overall assessment
        print(f"\n💡 Overall Assessment:")
        if total_correct / total_skus >= 0.95:
            print(f"   ✅ Routing is working correctly ({total_correct/total_skus*100:.1f}% accuracy)")
        else:
            print(f"   ⚠️  Routing needs improvement ({total_correct/total_skus*100:.1f}% accuracy)")
        
        if len(comparison_df) > 0:
            avg_improvement = comparison_df['improvement'].mean()
            if avg_improvement > 0:
                print(f"   ✅ Routing improves accuracy by {avg_improvement:.1f} percentage points on average")
            else:
                print(f"   ⚠️  Routing doesn't improve accuracy (avg: {avg_improvement:.1f} points)")
        
        print("\n" + "=" * 80)
        print("✅ Validation Complete!")
        print("=" * 80)
        
        return df


if __name__ == "__main__":
    asyncio.run(validate_method_routing())

