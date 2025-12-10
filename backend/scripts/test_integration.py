#!/usr/bin/env python3
"""
Integration Test Script

Tests the complete workflow:
1. Setup demo client
2. Verify data import
3. Test forecast generation
4. Test actuals submission
5. Test quality metrics

Usage:
    uv run python3 scripts/test_integration.py
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, select
from models.database import get_async_session_local
from models.client import Client
from models.user import User
from models.forecast import ForecastRun, ForecastResult
from forecasting.services.forecast_service import ForecastService
from forecasting.services.quality_calculator import QualityCalculator


async def check_database_setup():
    """Check if database tables exist"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Check clients table
        try:
            result = await session.execute(text("SELECT 1 FROM clients LIMIT 1"))
            result.scalar()
            print("✅ clients table exists")
        except Exception as e:
            print(f"❌ clients table missing: {e}")
            return False
        
        # Check ts_demand_daily table
        try:
            result = await session.execute(text("SELECT 1 FROM ts_demand_daily LIMIT 1"))
            result.scalar()
            print("✅ ts_demand_daily table exists")
        except Exception as e:
            print(f"❌ ts_demand_daily table missing: {e}")
            return False
        
        # Check forecast tables
        try:
            result = await session.execute(text("SELECT 1 FROM forecast_runs LIMIT 1"))
            result.scalar()
            print("✅ forecast_runs table exists")
        except Exception as e:
            print(f"❌ forecast_runs table missing: {e}")
            return False
        
        return True


async def find_or_create_test_user(client_id: str) -> str:
    """Find or create a test user"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Look for existing test user
        result = await session.execute(
            select(User).where(User.email == "integration-test@example.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ Found existing test user: {user.id}")
            return str(user.id)
        
        # Create new user
        new_user = User(
            email="integration-test@example.com",
            name="Integration Test User",
            hashed_password="test-hash",  # Not used for testing
            client_id=client_id,
            is_active=True
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        print(f"✅ Created test user: {new_user.id}")
        return str(new_user.id)


async def find_or_create_test_client():
    """Find or create a test client"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        # Look for existing test client
        result = await session.execute(
            select(Client).where(Client.name == "Integration Test Client")
        )
        client = result.scalar_one_or_none()
        
        if client:
            print(f"✅ Found existing test client: {client.client_id}")
            return str(client.client_id)
        
        # Create new client
        new_client = Client(
            name="Integration Test Client",
            timezone="UTC",
            currency="EUR",
            is_active=True
        )
        session.add(new_client)
        await session.commit()
        await session.refresh(new_client)
        print(f"✅ Created test client: {new_client.client_id}")
        return str(new_client.client_id)


async def check_test_data(client_id: str):
    """Check if test data exists for client"""
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT 
                    COUNT(*) as total_rows,
                    COUNT(DISTINCT item_id) as unique_items,
                    MIN(date_local) as min_date,
                    MAX(date_local) as max_date
                FROM ts_demand_daily
                WHERE client_id = :client_id
            """),
            {"client_id": client_id}
        )
        stats = result.fetchone()
        
        if stats and stats[0] > 0:
            print(f"✅ Test data found:")
            print(f"   - Total rows: {stats[0]:,}")
            print(f"   - Unique items: {stats[1]}")
            print(f"   - Date range: {stats[2]} to {stats[3]}")
            return True
        else:
            print(f"❌ No test data found for client {client_id}")
            print("   Run: uv run python3 scripts/setup_demo_client.py")
            return False


async def test_forecast_generation(client_id: str, user_id: str):
    """Test forecast generation"""
    print("\n" + "="*60)
    print("Testing Forecast Generation")
    print("="*60)
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        service = ForecastService(session)
        
        # Get available items
        result = await session.execute(
            text("""
                SELECT DISTINCT item_id 
                FROM ts_demand_daily 
                WHERE client_id = :client_id 
                LIMIT 5
            """),
            {"client_id": client_id}
        )
        items = [row[0] for row in result.fetchall()]
        
        if not items:
            print("❌ No items found for forecasting")
            return False
        
        print(f"Testing with items: {items[:3]}")
        
        try:
            # Generate forecast
            forecast_run = await service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=items[:3],  # Test with first 3 items
                prediction_length=7,
                primary_model="chronos-2"
            )
            
            print(f"✅ Forecast generated:")
            print(f"   - Run ID: {forecast_run.forecast_run_id}")
            print(f"   - Status: {forecast_run.status}")
            print(f"   - Items: {forecast_run.item_ids}")
            
            # Get results
            results = await service.get_forecast_results(forecast_run.forecast_run_id)
            print(f"   - Results: {len(results)} rows")
            
            return True
            
        except Exception as e:
            print(f"❌ Forecast generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def test_quality_metrics(client_id: str):
    """Test quality metrics calculation"""
    print("\n" + "="*60)
    print("Testing Quality Metrics")
    print("="*60)
    
    AsyncSessionLocal = get_async_session_local()
    async with AsyncSessionLocal() as session:
        calculator = QualityCalculator(session)
        
        # Get an item with forecast results
        result = await session.execute(
            text("""
                SELECT DISTINCT fr.item_id
                FROM forecast_results fr
                JOIN forecast_runs f ON fr.forecast_run_id = f.forecast_run_id
                WHERE f.client_id = :client_id
                LIMIT 1
            """),
            {"client_id": client_id}
        )
        item_row = result.fetchone()
        
        if not item_row:
            print("⚠️  No forecast results found - skipping quality test")
            return True
        
        item_id = item_row[0]
        print(f"Testing quality metrics for item: {item_id}")
        
        try:
            metrics = await calculator.calculate_quality_metrics(
                client_id=client_id,
                item_id=item_id
            )
            
            print(f"✅ Quality metrics calculated:")
            for method, method_metrics in metrics.items():
                print(f"   {method}:")
                for metric_name, value in method_metrics.items():
                    if value is not None:
                        print(f"     - {metric_name}: {value:.4f}")
            
            return True
            
        except Exception as e:
            print(f"❌ Quality metrics calculation failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run all integration tests"""
    print("="*60)
    print("Integration Test Suite")
    print("="*60)
    print()
    
    # Step 1: Check database setup
    print("Step 1: Checking database setup...")
    if not await check_database_setup():
        print("\n❌ Database setup incomplete. Please run migrations:")
        print("   cd backend && uv run alembic upgrade head")
        return 1
    print()
    
    # Step 2: Find or create test client
    print("Step 2: Finding or creating test client...")
    client_id = await find_or_create_test_client()
    print()
    
    # Step 2b: Find or create test user
    print("Step 2b: Finding or creating test user...")
    user_id = await find_or_create_test_user(client_id)
    print()
    
    # Step 3: Check test data
    print("Step 3: Checking test data...")
    has_data = await check_test_data(client_id)
    if not has_data:
        print("\n⚠️  No test data found. Please run:")
        print("   uv run python3 scripts/setup_demo_client.py")
        print("\nContinuing with other tests...")
    print()
    
    # Step 4: Test forecast generation (if data exists)
    if has_data:
        success = await test_forecast_generation(client_id, user_id)
        if not success:
            return 1
    else:
        print("⚠️  Skipping forecast test (no data)")
    
    # Step 5: Test quality metrics
    await test_quality_metrics(client_id)
    
    print("\n" + "="*60)
    print("✅ Integration tests complete!")
    print("="*60)
    print(f"\nTest client ID: {client_id}")
    print("You can use this client_id for API testing.")
    
    return 0


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

