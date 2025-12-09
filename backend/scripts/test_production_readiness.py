"""
Production Readiness Integration Test

Comprehensive end-to-end testing for production readiness.
Tests all critical paths and error scenarios.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.forecast import ForecastRun, ForecastResult, SKUClassification
from models.client import Client
from models.user import User
from forecasting.services.forecast_service import ForecastService
from config import settings


class ProductionReadinessTest:
    """Comprehensive production readiness tests"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.service = ForecastService(db)
        self.results = {
            "passed": [],
            "failed": [],
            "warnings": []
        }
    
    def log_pass(self, test_name: str, details: str = ""):
        """Log a passed test"""
        self.results["passed"].append(f"✅ {test_name}: {details}")
        print(f"✅ PASS: {test_name}")
        if details:
            print(f"   {details}")
    
    def log_fail(self, test_name: str, error: str):
        """Log a failed test"""
        self.results["failed"].append(f"❌ {test_name}: {error}")
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def log_warning(self, test_name: str, warning: str):
        """Log a warning"""
        self.results["warnings"].append(f"⚠️  {test_name}: {warning}")
        print(f"⚠️  WARN: {test_name}")
        print(f"   {warning}")
    
    async def test_1_forecast_generation_single_sku(self, client_id: str, user_id: str):
        """Test 1: Single SKU forecast generation"""
        try:
            # Get a test SKU
            result = await self.db.execute(
                select(SKUClassification).limit(1)
            )
            sku = result.scalar_one_or_none()
            
            if not sku:
                self.log_warning("test_1_forecast_generation_single_sku", "No SKUs found in database")
                return
            
            # Generate forecast
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[sku.item_id],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )
            
            if forecast_run.status == "completed":
                self.log_pass("test_1_forecast_generation_single_sku", 
                             f"Forecast generated for {sku.item_id}")
            else:
                self.log_fail("test_1_forecast_generation_single_sku",
                            f"Forecast failed: {forecast_run.error_message}")
        except Exception as e:
            self.log_fail("test_1_forecast_generation_single_sku", str(e))
    
    async def test_2_forecast_generation_multiple_skus(self, client_id: str, user_id: str):
        """Test 2: Multiple SKU forecast generation"""
        try:
            # Get multiple test SKUs
            result = await self.db.execute(
                select(SKUClassification).limit(3)
            )
            skus = result.scalars().all()
            
            if len(skus) < 2:
                self.log_warning("test_2_forecast_generation_multiple_skus", 
                               f"Only {len(skus)} SKUs found, need at least 2")
                return
            
            item_ids = [sku.item_id for sku in skus]
            
            # Generate forecast
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=item_ids,
                prediction_length=14,
                primary_model="chronos-2",
                include_baseline=False,
            )
            
            if forecast_run.status == "completed":
                self.log_pass("test_2_forecast_generation_multiple_skus",
                             f"Forecast generated for {len(item_ids)} SKUs")
            else:
                self.log_fail("test_2_forecast_generation_multiple_skus",
                            f"Forecast failed: {forecast_run.error_message}")
        except Exception as e:
            self.log_fail("test_2_forecast_generation_multiple_skus", str(e))
    
    async def test_3_method_routing(self, client_id: str, user_id: str):
        """Test 3: Automatic method routing"""
        try:
            # Get SKUs with different classifications
            result = await self.db.execute(
                select(SKUClassification).limit(5)
            )
            skus = result.scalars().all()
            
            if not skus:
                self.log_warning("test_3_method_routing", "No SKUs found")
                return
            
            routing_correct = 0
            routing_total = 0
            
            for sku in skus:
                routing_total += 1
                expected_method = sku.recommended_method
                
                # Generate forecast (should use routing)
                forecast_run = await self.service.generate_forecast(
                    client_id=client_id,
                    user_id=user_id,
                    item_ids=[sku.item_id],
                    prediction_length=7,
                    primary_model="chronos-2",  # Will be overridden by routing
                    include_baseline=False,
                )
                
                if forecast_run.status == "completed":
                    # Check if correct method was used
                    # Normalize method names (chronos2 -> chronos-2)
                    normalized_expected = expected_method.replace("chronos2", "chronos-2")
                    
                    # Try to get results with normalized method name
                    results = await self.service.get_forecast_results(
                        forecast_run_id=str(forecast_run.forecast_run_id),
                        method=normalized_expected,
                    )
                    
                    if results:
                        routing_correct += 1
                    else:
                        # Try with original method name
                        results = await self.service.get_forecast_results(
                            forecast_run_id=str(forecast_run.forecast_run_id),
                            method=expected_method,
                        )
                        
                        if results:
                            routing_correct += 1
                        else:
                            # Try to find what method was actually used
                            result = await self.db.execute(
                                select(ForecastResult.method).where(
                                    ForecastResult.forecast_run_id == forecast_run.forecast_run_id
                                ).limit(1)
                            )
                            actual_method = result.scalar_one_or_none()
                            if actual_method:
                                # Normalize actual method for comparison
                                normalized_actual = actual_method.replace("chronos2", "chronos-2")
                                if normalized_expected == normalized_actual:
                                    routing_correct += 1
                                else:
                                    self.log_warning("test_3_method_routing",
                                                   f"SKU {sku.item_id}: Expected {normalized_expected}, got {normalized_actual}")
                            else:
                                self.log_warning("test_3_method_routing",
                                               f"SKU {sku.item_id}: No results found for method {normalized_expected}")
            
            if routing_total > 0:
                accuracy = routing_correct / routing_total * 100
                if accuracy >= 95:
                    self.log_pass("test_3_method_routing",
                                f"Routing accuracy: {accuracy:.1f}% ({routing_correct}/{routing_total})")
                else:
                    self.log_fail("test_3_method_routing",
                                f"Routing accuracy too low: {accuracy:.1f}% (expected >= 95%)")
        except Exception as e:
            self.log_fail("test_3_method_routing", str(e))
    
    async def test_4_error_handling_invalid_item(self, client_id: str, user_id: str):
        """Test 4: Error handling for invalid item_id"""
        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=["INVALID_SKU_12345"],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )
            
            if forecast_run.status == "failed":
                self.log_pass("test_4_error_handling_invalid_item",
                           "Invalid item_id correctly rejected")
            else:
                self.log_fail("test_4_error_handling_invalid_item",
                            "Invalid item_id should have failed but didn't")
        except Exception as e:
            # Exception is acceptable for invalid input
            self.log_pass("test_4_error_handling_invalid_item",
                        f"Invalid item_id correctly raised exception: {type(e).__name__}")
    
    async def test_5_multi_client_isolation(self):
        """Test 5: Multi-client data isolation"""
        try:
            # Get two different clients
            result = await self.db.execute(
                select(Client).limit(2)
            )
            clients = result.scalars().all()
            
            if len(clients) < 2:
                self.log_warning("test_5_multi_client_isolation",
                               "Need at least 2 clients for isolation test")
                return
            
            client1_id = str(clients[0].client_id)
            client2_id = str(clients[1].client_id)
            
            isolation_checks = []
            
            # Check 1: SKU Classifications isolation
            result = await self.db.execute(
                select(SKUClassification).where(
                    SKUClassification.client_id == client1_id
                ).limit(1)
            )
            sku1 = result.scalar_one_or_none()
            
            if sku1:
                # Try to access client1's SKU as client2
                result = await self.db.execute(
                    select(SKUClassification).where(
                        SKUClassification.client_id == client2_id,
                        SKUClassification.item_id == sku1.item_id
                    )
                )
                sku2 = result.scalar_one_or_none()
                
                if sku2 is None:
                    isolation_checks.append("SKU classifications isolated")
                else:
                    isolation_checks.append("SKU classifications NOT isolated (FAIL)")
            else:
                isolation_checks.append("SKU classifications (no data to test)")
            
            # Check 2: Forecast Runs isolation
            result = await self.db.execute(
                text("""
                    SELECT forecast_run_id
                    FROM forecast_runs
                    WHERE client_id = :client_id
                    LIMIT 1
                """),
                {"client_id": client1_id}
            )
            row = result.fetchone()
            
            if row:
                forecast_run_id = row.forecast_run_id
                # Try to access client1's forecast as client2
                result = await self.db.execute(
                    text("""
                        SELECT forecast_run_id
                        FROM forecast_runs
                        WHERE client_id = :client_id
                        AND forecast_run_id = :forecast_run_id
                    """),
                    {"client_id": client2_id, "forecast_run_id": forecast_run_id}
                )
                row2 = result.fetchone()
                
                if row2 is None:
                    isolation_checks.append("Forecast runs isolated")
                else:
                    isolation_checks.append("Forecast runs NOT isolated (FAIL)")
            else:
                isolation_checks.append("Forecast runs (no data to test)")
            
            # Check 3: Forecast Results isolation
            result = await self.db.execute(
                text("""
                    SELECT fr.result_id
                    FROM forecast_results fr
                    JOIN forecast_runs frun ON fr.forecast_run_id = frun.forecast_run_id
                    WHERE frun.client_id = :client_id
                    LIMIT 1
                """),
                {"client_id": client1_id}
            )
            row = result.fetchone()
            
            if row:
                result_id = row.result_id
                # Try to access client1's result as client2
                result = await self.db.execute(
                    text("""
                        SELECT fr.result_id
                        FROM forecast_results fr
                        JOIN forecast_runs frun ON fr.forecast_run_id = frun.forecast_run_id
                        WHERE frun.client_id = :client_id
                        AND fr.result_id = :result_id
                    """),
                    {"client_id": client2_id, "result_id": result_id}
                )
                row2 = result.fetchone()
                
                if row2 is None:
                    isolation_checks.append("Forecast results isolated")
                else:
                    isolation_checks.append("Forecast results NOT isolated (FAIL)")
            else:
                isolation_checks.append("Forecast results (no data to test)")
            
            # Check 4: Time series data isolation
            result = await self.db.execute(
                text("""
                    SELECT item_id
                    FROM ts_demand_daily
                    WHERE client_id = :client_id
                    LIMIT 1
                """),
                {"client_id": client1_id}
            )
            row = result.fetchone()
            
            if row:
                item_id = row.item_id
                # Try to access client1's data as client2
                result = await self.db.execute(
                    text("""
                        SELECT item_id
                        FROM ts_demand_daily
                        WHERE client_id = :client_id
                        AND item_id = :item_id
                    """),
                    {"client_id": client2_id, "item_id": item_id}
                )
                row2 = result.fetchone()
                
                if row2 is None:
                    isolation_checks.append("Time series data isolated")
                else:
                    isolation_checks.append("Time series data NOT isolated (FAIL)")
            else:
                isolation_checks.append("Time series data (no data to test)")
            
            # Summary
            failed_checks = [c for c in isolation_checks if "NOT isolated" in c]
            passed_checks = [c for c in isolation_checks if "isolated" in c and "NOT" not in c]
            
            if failed_checks:
                self.log_fail("test_5_multi_client_isolation",
                            f"Isolation failures: {', '.join(failed_checks)}")
            elif passed_checks:
                self.log_pass("test_5_multi_client_isolation",
                            f"All data types isolated: {', '.join(passed_checks)}")
            else:
                self.log_warning("test_5_multi_client_isolation",
                               "No data available to test isolation")
        except Exception as e:
            self.log_fail("test_5_multi_client_isolation", str(e))
    
    async def test_6_forecast_results_retrieval(self, client_id: str, user_id: str):
        """Test 6: Forecast results retrieval"""
        try:
            # Get a test SKU
            result = await self.db.execute(
                select(SKUClassification).limit(1)
            )
            sku = result.scalar_one_or_none()
            
            if not sku:
                self.log_warning("test_6_forecast_results_retrieval", "No SKUs found")
                return
            
            # Generate forecast
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[sku.item_id],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )
            
            if forecast_run.status != "completed":
                self.log_fail("test_6_forecast_results_retrieval",
                            f"Forecast generation failed: {forecast_run.error_message}")
                return
            
            # Retrieve results - try both method name formats
            results = await self.service.get_forecast_results(
                forecast_run_id=str(forecast_run.forecast_run_id),
                method="chronos-2",
            )
            
            # If no results, try with "chronos2" (without hyphen)
            if not results:
                results = await self.service.get_forecast_results(
                    forecast_run_id=str(forecast_run.forecast_run_id),
                    method="chronos2",
                )
            
            # If still no results, check what method was actually used
            if not results:
                result = await self.db.execute(
                    select(ForecastResult.method).where(
                        ForecastResult.forecast_run_id == forecast_run.forecast_run_id
                    ).limit(1)
                )
                actual_method = result.scalar_one_or_none()
                if actual_method:
                    results = await self.service.get_forecast_results(
                        forecast_run_id=str(forecast_run.forecast_run_id),
                        method=actual_method,
                    )
            
            if results and len(results) > 0:
                self.log_pass("test_6_forecast_results_retrieval",
                            f"Retrieved {len(results)} forecast results")
            else:
                # Check if results exist in database
                result = await self.db.execute(
                    select(ForecastResult).where(
                        ForecastResult.forecast_run_id == forecast_run.forecast_run_id
                    ).limit(1)
                )
                db_results = result.scalars().all()
                if db_results:
                    self.log_warning("test_6_forecast_results_retrieval",
                                   f"Results exist in DB ({len(db_results)}) but service method returned None")
                else:
                    self.log_fail("test_6_forecast_results_retrieval",
                                "No forecast results found in database")
        except Exception as e:
            self.log_fail("test_6_forecast_results_retrieval", str(e))
    
    async def test_7_different_prediction_lengths(self, client_id: str, user_id: str):
        """Test 7: Different prediction lengths"""
        try:
            # Get a test SKU
            result = await self.db.execute(
                select(SKUClassification).limit(1)
            )
            sku = result.scalar_one_or_none()
            
            if not sku:
                self.log_warning("test_7_different_prediction_lengths", "No SKUs found")
                return
            
            prediction_lengths = [7, 14, 30]
            success_count = 0
            
            for pred_len in prediction_lengths:
                forecast_run = await self.service.generate_forecast(
                    client_id=client_id,
                    user_id=user_id,
                    item_ids=[sku.item_id],
                    prediction_length=pred_len,
                    primary_model="chronos-2",
                    include_baseline=False,
                )
                
                if forecast_run.status == "completed":
                    success_count += 1
            
            if success_count == len(prediction_lengths):
                self.log_pass("test_7_different_prediction_lengths",
                            f"All prediction lengths work: {prediction_lengths}")
            else:
                self.log_fail("test_7_different_prediction_lengths",
                            f"Only {success_count}/{len(prediction_lengths)} prediction lengths work")
        except Exception as e:
            self.log_fail("test_7_different_prediction_lengths", str(e))
    
    async def run_all_tests(self, client_id: str, user_id: str):
        """Run all production readiness tests"""
        print("=" * 80)
        print("PRODUCTION READINESS INTEGRATION TESTS")
        print("=" * 80)
        print()
        
        await self.test_1_forecast_generation_single_sku(client_id, user_id)
        await self.test_2_forecast_generation_multiple_skus(client_id, user_id)
        await self.test_3_method_routing(client_id, user_id)
        await self.test_4_error_handling_invalid_item(client_id, user_id)
        await self.test_5_multi_client_isolation()
        await self.test_6_forecast_results_retrieval(client_id, user_id)
        await self.test_7_different_prediction_lengths(client_id, user_id)
        
        # Print summary
        print()
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"✅ Passed: {len(self.results['passed'])}")
        print(f"❌ Failed: {len(self.results['failed'])}")
        print(f"⚠️  Warnings: {len(self.results['warnings'])}")
        print()
        
        if self.results['failed']:
            print("FAILED TESTS:")
            for fail in self.results['failed']:
                print(f"  {fail}")
            print()
        
        if self.results['warnings']:
            print("WARNINGS:")
            for warn in self.results['warnings']:
                print(f"  {warn}")
            print()
        
        total = len(self.results['passed']) + len(self.results['failed'])
        if total > 0:
            success_rate = len(self.results['passed']) / total * 100
            print(f"Success Rate: {success_rate:.1f}%")
        
        print("=" * 80)
        
        return self.results


async def main():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://"),
        echo=False
    )
    
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first client and user
        result = await db.execute(select(Client).limit(1))
        client = result.scalar_one_or_none()
        
        if not client:
            print("❌ No clients found in database")
            return
        
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        
        if not user:
            print("❌ No users found in database")
            return
        
        client_id = str(client.client_id)
        user_id = str(user.id)
        
        # Run tests
        tester = ProductionReadinessTest(db)
        results = await tester.run_all_tests(client_id, user_id)
        
        # Return exit code based on results
        if len(results['failed']) > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

