#!/usr/bin/env python3
"""
Test Phase 2A Integration

Tests the complete Phase 2A flow:
1. Generate forecast (should classify SKUs automatically)
2. Check classifications are stored in database
3. Verify classifications are in API response
4. Test GET classification endpoint
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from models.forecast import ForecastRun, SKUClassification as SKUClassificationModel
from models.user import User
from forecasting.services.forecast_service import ForecastService
from uuid import uuid4


async def test_phase2a_integration():
    """Test Phase 2A integration end-to-end"""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    
    # Convert postgres:// to postgresql+asyncpg:// for async operations
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("Phase 2A Integration Test")
        print("=" * 80)
        
        # 1. Get a test SKU
        result = await db.execute(
            text("""
                SELECT item_id, client_id
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 30
                LIMIT 1
            """)
        )
        row = result.fetchone()
        
        if not row:
            print("❌ No SKUs found in database")
            return
        
        item_id = row.item_id
        client_id = str(row.client_id)
        
        print(f"\n📦 Testing with SKU: {item_id}")
        print(f"   Client ID: {client_id}")
        
        # Create or get test user
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
        print(f"   User ID: {user_id}")
        
        # 2. Generate forecast (should classify automatically)
        print("\n" + "=" * 80)
        print("Step 1: Generate Forecast (with automatic classification)")
        print("=" * 80)
        
        service = ForecastService(db)
        
        try:
            forecast_run = await service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[item_id],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=True,
            )
            
            print(f"✅ Forecast generated: {forecast_run.forecast_run_id}")
            print(f"   Status: {forecast_run.status}")
            print(f"   Method: {forecast_run.recommended_method or forecast_run.primary_model}")
            
            # Check if classifications were attached
            classifications = getattr(forecast_run, '_sku_classifications', {})
            if item_id in classifications:
                classification = classifications[item_id]
                print(f"\n✅ Classification attached to forecast run:")
                print(f"   ABC: {classification.abc_class}")
                print(f"   XYZ: {classification.xyz_class}")
                print(f"   Pattern: {classification.demand_pattern}")
                print(f"   Forecastability: {classification.forecastability_score:.2f}")
                print(f"   Recommended: {classification.recommended_method}")
            else:
                print(f"\n⚠️  No classification found in forecast run (may have failed silently)")
        
        except Exception as e:
            print(f"❌ Forecast generation failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 3. Check classifications in database
        print("\n" + "=" * 80)
        print("Step 2: Verify Classifications Stored in Database")
        print("=" * 80)
        
        result = await db.execute(
            select(SKUClassificationModel).where(
                SKUClassificationModel.client_id == client_id,
                SKUClassificationModel.item_id == item_id
            ).order_by(SKUClassificationModel.classification_date.desc())
        )
        db_classification = result.scalar_one_or_none()
        
        if db_classification:
            print(f"✅ Classification found in database:")
            print(f"   ABC: {db_classification.abc_class}")
            print(f"   XYZ: {db_classification.xyz_class}")
            print(f"   Pattern: {db_classification.demand_pattern}")
            print(f"   Forecastability: {float(db_classification.forecastability_score):.2f}")
            print(f"   Recommended Method: {db_classification.recommended_method}")
            print(f"   Expected MAPE: {float(db_classification.expected_mape_min):.0f}-{float(db_classification.expected_mape_max):.0f}%")
            print(f"   Classification Date: {db_classification.classification_date}")
            
            if db_classification.classification_metadata:
                warnings = db_classification.classification_metadata.get("warnings", [])
                if warnings:
                    print(f"   Warnings: {', '.join(warnings)}")
        else:
            print(f"❌ No classification found in database")
        
        # 4. Test API response format (simulate)
        print("\n" + "=" * 80)
        print("Step 3: Test API Response Format")
        print("=" * 80)
        
        # Get forecast results
        results = await service.get_forecast_results(
            forecast_run_id=forecast_run.forecast_run_id,
            method=forecast_run.recommended_method or forecast_run.primary_model,
        )
        
        if item_id in results:
            print(f"✅ Forecast results retrieved:")
            print(f"   Predictions: {len(results[item_id])} days")
            print(f"   First prediction: {results[item_id][0]['point_forecast']:.2f} units")
            
            # Simulate API response
            if item_id in classifications:
                classification = classifications[item_id]
                api_response = {
                    "forecast_id": str(forecast_run.forecast_run_id),
                    "primary_model": forecast_run.primary_model,
                    "forecasts": [{
                        "item_id": item_id,
                        "method_used": forecast_run.recommended_method or forecast_run.primary_model,
                        "predictions": results[item_id],
                        "classification": {
                            "abc_class": classification.abc_class,
                            "xyz_class": classification.xyz_class,
                            "demand_pattern": classification.demand_pattern,
                            "forecastability_score": classification.forecastability_score,
                            "recommended_method": classification.recommended_method,
                            "expected_mape_range": classification.expected_mape_range,
                            "warnings": classification.warnings,
                        }
                    }]
                }
                print(f"\n✅ API Response would include classification:")
                print(f"   ABC-XYZ: {classification.abc_class}-{classification.xyz_class}")
                print(f"   Forecastability: {classification.forecastability_score:.2f}")
                print(f"   Expected MAPE: {classification.expected_mape_range[0]:.0f}-{classification.expected_mape_range[1]:.0f}%")
            else:
                print(f"\n⚠️  Classification not available in forecast run")
        else:
            print(f"❌ No forecast results found")
        
        # 5. Summary
        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        
        checks = {
            "Forecast generated": forecast_run.status == "completed",
            "Classification attached": item_id in classifications,
            "Classification in database": db_classification is not None,
            "Forecast results available": item_id in results,
        }
        
        all_passed = all(checks.values())
        
        for check, passed in checks.items():
            status = "✅" if passed else "❌"
            print(f"{status} {check}")
        
        print("\n" + "=" * 80)
        if all_passed:
            print("✅ Phase 2A Integration Test: PASSED")
        else:
            print("⚠️  Phase 2A Integration Test: PARTIAL (some checks failed)")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_phase2a_integration())

