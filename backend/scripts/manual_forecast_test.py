"""
Manual Forecast Test Script

Run forecast on actual data and compare DIR/metrics before and after.
Shows how forecasts affect inventory metrics.

Usage:
    cd backend
    uv run python scripts/manual_forecast_test.py
"""
import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from uuid import UUID
from decimal import Decimal
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import get_async_session_local
from models.client import Client
from models.user import User
from forecasting.services.forecast_service import ForecastService
from services.inventory_service import InventoryService
from services.metrics_service import MetricsService


async def get_items_with_data(db: AsyncSession, client_id: UUID, limit: int = 5) -> list[str]:
    """Get item_ids that have sales data"""
    result = await db.execute(
        text("""
            SELECT item_id
            FROM ts_demand_daily
            WHERE client_id = :client_id
              AND units_sold > 0
            GROUP BY item_id
            HAVING COUNT(*) >= 30
            ORDER BY COUNT(*) DESC
            LIMIT :limit
        """),
        {"client_id": str(client_id), "limit": limit}
    )
    return [row[0] for row in result.fetchall()]


async def get_metrics_before_forecast(
    db: AsyncSession,
    client_id: UUID,
    item_id: str
) -> dict:
    """Get metrics using historical data (before forecast)"""
    metrics_service = MetricsService(db)
    
    # Get current stock
    stock_result = await db.execute(
        text("""
            SELECT SUM(current_stock) as total_stock
            FROM stock_levels
            WHERE client_id = :client_id
              AND item_id = :item_id
        """),
        {"client_id": str(client_id), "item_id": item_id}
    )
    stock_row = stock_result.fetchone()
    current_stock = int(stock_row[0] or 0) if stock_row else 0
    
    # Calculate metrics WITHOUT forecast (uses historical)
    metrics = await metrics_service.compute_product_metrics(
        client_id=client_id,
        item_id=item_id,
        forecasted_demand_30d=None  # Use historical
    )
    
    return {
        "item_id": item_id,
        "current_stock": current_stock,
        "dir": float(metrics["dir"]) if metrics.get("dir") else None,
        "stockout_risk": float(metrics["stockout_risk"]) if metrics.get("stockout_risk") else None,
        "status": metrics.get("status"),
        "inventory_value": float(metrics["inventory_value"]) if metrics.get("inventory_value") else None,
        "using_forecast": False,
        "data_source": "historical (last 30 days)"
    }


async def get_metrics_after_forecast(
    db: AsyncSession,
    client_id: UUID,
    item_id: str,
    forecast_run_id: UUID
) -> dict:
    """Get metrics using forecast data"""
    metrics_service = MetricsService(db)
    forecast_service = ForecastService(db)
    
    # Get forecast results
    results_by_item = await forecast_service.get_forecast_results(
        forecast_run_id=str(forecast_run_id)
    )
    
    # Calculate forecasted demand 30d
    forecasted_demand_30d = None
    if item_id in results_by_item and results_by_item[item_id]:
        predictions = results_by_item[item_id]
        total_forecast = sum(p["point_forecast"] for p in predictions)
        # Convert to Decimal (required by MetricsService)
        forecasted_demand_30d = Decimal(str(total_forecast))
    
    # Get current stock
    stock_result = await db.execute(
        text("""
            SELECT SUM(current_stock) as total_stock
            FROM stock_levels
            WHERE client_id = :client_id
              AND item_id = :item_id
        """),
        {"client_id": str(client_id), "item_id": item_id}
    )
    stock_row = stock_result.fetchone()
    current_stock = int(stock_row[0] or 0) if stock_row else 0
    
    # Calculate metrics WITH forecast
    metrics = await metrics_service.compute_product_metrics(
        client_id=client_id,
        item_id=item_id,
        forecasted_demand_30d=forecasted_demand_30d
    )
    
    return {
        "item_id": item_id,
        "current_stock": current_stock,
        "dir": float(metrics["dir"]) if metrics.get("dir") else None,
        "stockout_risk": float(metrics["stockout_risk"]) if metrics.get("stockout_risk") else None,
        "status": metrics.get("status"),
        "inventory_value": float(metrics["inventory_value"]) if metrics.get("inventory_value") else None,
        "using_forecast": True,
        "data_source": f"forecast (run_id: {forecast_run_id})",
        "forecasted_demand_30d": float(forecasted_demand_30d) if forecasted_demand_30d else None
    }


async def print_comparison(before: dict, after: dict):
    """Print before/after comparison"""
    print(f"\n{'='*80}")
    print(f"📊 COMPARISON: {before['item_id']}")
    print(f"{'='*80}")
    
    print(f"\n📦 Current Stock: {before['current_stock']} units")
    print(f"💰 Inventory Value: ${before['inventory_value']:.2f}")
    
    print(f"\n{'Metric':<20} {'Historical':<25} {'Forecast':<25} {'Change':<15}")
    print(f"{'-'*85}")
    
    # DIR comparison
    dir_before = before['dir']
    dir_after = after['dir']
    dir_change = ""
    if dir_before is not None and dir_after is not None:
        change = dir_after - dir_before
        pct_change = (change / dir_before * 100) if dir_before > 0 else 0
        dir_change = f"{change:+.1f} days ({pct_change:+.1f}%)"
    
    print(f"{'DIR (days)':<20} {str(dir_before or 'N/A'):<25} {str(dir_after or 'N/A'):<25} {dir_change:<15}")
    
    # Stockout Risk comparison
    risk_before = before['stockout_risk']
    risk_after = after['stockout_risk']
    risk_change = ""
    if risk_before is not None and risk_after is not None:
        change = risk_after - risk_before
        risk_before_pct = risk_before * 100
        risk_after_pct = risk_after * 100
        change_pct = change * 100
        risk_change = f"{change_pct:+.1f}% ({risk_after_pct:.1f}% vs {risk_before_pct:.1f}%)"
    
    print(f"{'Stockout Risk':<20} {f'{risk_before_pct:.1f}%' if risk_before else 'N/A':<25} {f'{risk_after_pct:.1f}%' if risk_after else 'N/A':<25} {risk_change:<15}")
    
    # Status comparison
    status_before = before['status']
    status_after = after['status']
    status_change = "✅ Same" if status_before == status_after else f"⚠️ {status_before} → {status_after}"
    print(f"{'Status':<20} {str(status_before or 'N/A'):<25} {str(status_after or 'N/A'):<25} {status_change:<15}")
    
    # Data source
    print(f"\n📊 Data Source:")
    print(f"   Before: {before['data_source']}")
    print(f"   After:  {after['data_source']}")
    
    if after.get('forecasted_demand_30d'):
        print(f"   Forecasted Demand (30d): {after['forecasted_demand_30d']:.2f} units")
    
    print(f"\n{'='*80}\n")


async def main():
    """Main test function"""
    print("🚀 Manual Forecast Test")
    print("="*80)
    print("This script will:")
    print("1. Find items with sales data")
    print("2. Get metrics BEFORE forecast (using historical data)")
    print("3. Generate forecast")
    print("4. Get metrics AFTER forecast (using forecast data)")
    print("5. Compare results")
    print("="*80)
    
    # Get database session
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as db:
        # Get first client (or specify client_id)
        client_result = await db.execute(select(Client).limit(1))
        client = client_result.scalar_one_or_none()
        
        if not client:
            print("❌ No client found in database")
            return
        
        client_id = client.client_id
        print(f"\n✅ Using client: {client_id}")
        
        # Get a user for this client (required for forecast_runs foreign key)
        user_result = await db.execute(
            select(User).where(User.client_id == client_id).limit(1)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            print("❌ No user found for this client")
            print("   Creating a test user...")
            # Create a test user
            from auth.security import get_password_hash
            import uuid
            test_user = User(
                id=str(uuid.uuid4()),
                email=f"test-forecast-{client_id}@example.com",
                name="Test Forecast User",
                hashed_password=get_password_hash("test-password"),
                client_id=client_id,
                is_active=True
            )
            db.add(test_user)
            await db.flush()
            user = test_user
            print(f"   ✅ Created test user: {user.id}")
        else:
            print(f"✅ Using user: {user.email} (id: {user.id})")
        
        user_id = user.id
        
        # Get items with data
        print("\n📋 Finding items with sales data...")
        item_ids = await get_items_with_data(db, client_id, limit=3)
        
        if not item_ids:
            print("❌ No items with sufficient sales data found")
            print("   Need at least 30 days of sales history")
            return
        
        print(f"✅ Found {len(item_ids)} items: {', '.join(item_ids)}")
        
        # Get metrics BEFORE forecast
        print("\n📊 Getting metrics BEFORE forecast (using historical data)...")
        metrics_before = {}
        for item_id in item_ids:
            metrics_before[item_id] = await get_metrics_before_forecast(db, client_id, item_id)
            print(f"   {item_id}: DIR={metrics_before[item_id]['dir']}, Risk={metrics_before[item_id]['stockout_risk']}")
        
        # Generate forecast
        print(f"\n🔮 Generating forecast for {len(item_ids)} items...")
        forecast_service = ForecastService(db)
        
        forecast_run = None
        try:
            forecast_run = await forecast_service.generate_forecast(
                client_id=str(client_id),
                user_id=user_id,
                item_ids=item_ids,
                prediction_length=30,
                primary_model="chronos-2",
                include_baseline=False
            )
            
            # Commit to ensure forecast_run is saved
            await db.commit()
            
        except Exception as e:
            # Exception was raised - check if forecast_run was created before error
            await db.rollback()
            # If exception occurred, forecast_run might still be in session
            # Try to get it from database or session
            await db.rollback()
            
            # Try to get the latest forecast_run from database
            from models.forecast import ForecastRun
            try:
                latest_run = await db.execute(
                    select(ForecastRun)
                    .where(ForecastRun.client_id == client_id)
                    .order_by(ForecastRun.created_at.desc())
                    .limit(1)
                )
                latest = latest_run.scalar_one_or_none()
                if latest and latest.created_at and (date.today() - latest.created_at.date()).days < 1:
                    # Use this run if it was created today (likely from this attempt)
                    forecast_run = latest
                    print(f"⚠️  Exception occurred, but found forecast_run in database:")
                    print(f"   Run ID: {forecast_run.forecast_run_id}")
                    print(f"   Status: {forecast_run.status}")
            except:
                pass
            
            if forecast_run is None:
                print(f"❌ Forecast generation error: {str(e)}")
                print(f"   Error type: {type(e).__name__}")
                import traceback
                print("\n   Full traceback:")
                traceback.print_exc()
                return
        
        if forecast_run is None:
            print("❌ Forecast generation returned None")
            print("   Checking database for forecast_run that might have been created...")
            
            # Check if a forecast_run was created in the database
            from models.forecast import ForecastRun
            from datetime import datetime, timezone
            try:
                latest_run = await db.execute(
                    select(ForecastRun)
                    .where(ForecastRun.client_id == client_id)
                    .order_by(ForecastRun.created_at.desc())
                    .limit(1)
                )
                latest = latest_run.scalar_one_or_none()
                if latest:
                    # Check if it was created recently (within last 2 minutes)
                    if latest.created_at:
                        time_diff = (datetime.now(timezone.utc) - latest.created_at).total_seconds()
                        if time_diff < 120:  # Created within last 2 minutes
                            forecast_run = latest
                            print(f"   ✅ Found forecast_run in database: {forecast_run.forecast_run_id}")
                            print(f"      Status: {forecast_run.status}")
                            if forecast_run.error_message:
                                print(f"      Error: {forecast_run.error_message}")
                        else:
                            print(f"   ⚠️  Found forecast_run but it's too old ({int(time_diff)}s ago)")
                    else:
                        # No created_at, but use it anyway
                        forecast_run = latest
                        print(f"   ✅ Found forecast_run in database: {forecast_run.forecast_run_id}")
                        print(f"      Status: {forecast_run.status}")
                else:
                    print("   ❌ No forecast_run found in database")
            except Exception as db_error:
                print(f"   ⚠️  Error checking database: {db_error}")
                import traceback
                traceback.print_exc()
            
            if forecast_run is None:
                print("\n   💡 Possible causes:")
                print("      - Exception occurred before forecast_run was created")
                print("      - Check application logs for detailed error messages")
                print("      - Try running forecast for a single item to isolate the issue")
                return
        
        if forecast_run.status != "completed":
            print(f"❌ Forecast generation failed: {forecast_run.status}")
            if hasattr(forecast_run, 'error_message') and forecast_run.error_message:
                print(f"   Error: {forecast_run.error_message}")
            else:
                print(f"   No error message available")
            print(f"   Forecast Run ID: {forecast_run.forecast_run_id}")
            print(f"   You can check the forecast_run record in database for details")
            return
        
        print(f"✅ Forecast generated: {forecast_run.forecast_run_id}")
        print(f"   Status: {forecast_run.status}")
        print(f"   Created: {forecast_run.created_at}")
        if forecast_run.recommended_method:
            print(f"   Recommended method: {forecast_run.recommended_method}")
        
        # Get metrics AFTER forecast
        print("\n📊 Getting metrics AFTER forecast (using forecast data)...")
        metrics_after = {}
        for item_id in item_ids:
            metrics_after[item_id] = await get_metrics_after_forecast(
                db, client_id, item_id, forecast_run.forecast_run_id
            )
            print(f"   {item_id}: DIR={metrics_after[item_id]['dir']}, Risk={metrics_after[item_id]['stockout_risk']}")
        
        # Compare results
        print("\n" + "="*80)
        print("📈 COMPARISON RESULTS")
        print("="*80)
        
        for item_id in item_ids:
            await print_comparison(metrics_before[item_id], metrics_after[item_id])
        
        # Summary
        print("\n" + "="*80)
        print("📋 SUMMARY")
        print("="*80)
        print(f"✅ Forecast generated successfully")
        print(f"   Forecast Run ID: {forecast_run.forecast_run_id}")
        print(f"   Items tested: {len(item_ids)}")
        print(f"\n💡 Next steps:")
        print(f"   1. Check if DIR/metrics changed with forecast")
        print(f"   2. Verify forecast results in database:")
        print(f"      SELECT * FROM forecast_results WHERE forecast_run_id = '{forecast_run.forecast_run_id}'")
        print(f"   3. Test integration in dashboard/products API")
        print(f"   4. Backfill actuals after sales data arrives")
        print("="*80)
        
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())

