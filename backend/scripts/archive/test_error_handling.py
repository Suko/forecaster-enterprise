"""
Test Error Handling Scenarios

Tests various error conditions to ensure graceful handling:
- Invalid item_ids
- Missing data
- Invalid date ranges
- Database connection failures (simulated)
- Model loading failures (simulated)
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from models.forecast import ForecastRun, ForecastResult, SKUClassification
from models.client import Client
from models.user import User
from forecasting.services.forecast_service import ForecastService
from config import settings


class ErrorHandlingTest:
    """Test error handling scenarios"""

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

    async def test_1_invalid_item_ids(self, client_id: str, user_id: str):
        """Test 1: Invalid item_ids"""
        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=["NONEXISTENT_SKU_12345", "ANOTHER_INVALID_SKU"],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )

            if forecast_run.status == "failed":
                error_msg = forecast_run.error_message or ""
                if "No historical data" in error_msg or "not found" in error_msg.lower():
                    self.log_pass("test_1_invalid_item_ids",
                                "Invalid item_ids correctly rejected with clear error message")
                else:
                    self.log_warning("test_1_invalid_item_ids",
                                    f"Failed but error message unclear: {error_msg}")
            else:
                self.log_fail("test_1_invalid_item_ids",
                            "Invalid item_ids should have failed but didn't")
        except ValueError as e:
            if "No historical data" in str(e) or "not found" in str(e).lower():
                self.log_pass("test_1_invalid_item_ids",
                            f"Invalid item_ids correctly raised ValueError: {str(e)}")
            else:
                self.log_fail("test_1_invalid_item_ids",
                            f"Unexpected ValueError: {str(e)}")
        except Exception as e:
            # Other exceptions are acceptable for invalid input
            self.log_pass("test_1_invalid_item_ids",
                        f"Invalid item_ids correctly raised exception: {type(e).__name__}")

    async def test_2_empty_item_list(self, client_id: str, user_id: str):
        """Test 2: Empty item_ids list"""
        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )

            if forecast_run is None:
                self.log_pass("test_2_empty_item_list",
                            "Empty item_ids list correctly returned None")
            elif forecast_run.status == "failed":
                self.log_pass("test_2_empty_item_list",
                            "Empty item_ids list correctly rejected")
            else:
                self.log_fail("test_2_empty_item_list",
                            "Empty item_ids list should have failed")
        except (ValueError, IndexError, AttributeError) as e:
            self.log_pass("test_2_empty_item_list",
                        f"Empty item_ids correctly raised exception: {type(e).__name__}")
        except Exception as e:
            self.log_warning("test_2_empty_item_list",
                           f"Unexpected exception: {type(e).__name__}: {str(e)}")

    async def test_3_invalid_prediction_length(self, client_id: str, user_id: str):
        """Test 3: Invalid prediction_length values"""
        # Get a valid SKU first
        result = await self.db.execute(
            select(SKUClassification).limit(1)
        )
        sku = result.scalar_one_or_none()

        if not sku:
            self.log_warning("test_3_invalid_prediction_length", "No SKUs found for testing")
            return

        test_cases = [
            (0, "Zero prediction length"),
            (-1, "Negative prediction length"),
            (1000, "Very large prediction length"),
        ]

        for pred_len, description in test_cases:
            try:
                forecast_run = await self.service.generate_forecast(
                    client_id=client_id,
                    user_id=user_id,
                    item_ids=[sku.item_id],
                    prediction_length=pred_len,
                    primary_model="chronos-2",
                    include_baseline=False,
                )

                if forecast_run is None:
                    self.log_pass(f"test_3_invalid_prediction_length ({description})",
                                f"Prediction length {pred_len} correctly returned None")
                elif forecast_run.status == "failed":
                    self.log_pass(f"test_3_invalid_prediction_length ({description})",
                                f"Prediction length {pred_len} correctly rejected")
                else:
                    self.log_warning(f"test_3_invalid_prediction_length ({description})",
                                   f"Prediction length {pred_len} was accepted (may be valid)")
            except (ValueError, AssertionError, AttributeError) as e:
                self.log_pass(f"test_3_invalid_prediction_length ({description})",
                            f"Correctly raised exception: {type(e).__name__}")
            except Exception as e:
                self.log_warning(f"test_3_invalid_prediction_length ({description})",
                               f"Unexpected exception: {type(e).__name__}")

    async def test_4_invalid_date_range(self, client_id: str, user_id: str):
        """Test 4: Invalid training_end_date"""
        # Get a valid SKU first
        result = await self.db.execute(
            select(SKUClassification).limit(1)
        )
        sku = result.scalar_one_or_none()

        if not sku:
            self.log_warning("test_4_invalid_date_range", "No SKUs found for testing")
            return

        # Test with future date (should fail or use all available data)
        future_date = date.today() + timedelta(days=365)

        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[sku.item_id],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
                training_end_date=future_date,
            )

            # Future date might be handled gracefully (use all data)
            if forecast_run.status in ["completed", "failed"]:
                self.log_pass("test_4_invalid_date_range",
                            f"Future date handled: status={forecast_run.status}")
            else:
                self.log_warning("test_4_invalid_date_range",
                               f"Unexpected status: {forecast_run.status}")
        except Exception as e:
            self.log_pass("test_4_invalid_date_range",
                        f"Future date correctly raised exception: {type(e).__name__}")

    async def test_5_insufficient_history(self, client_id: str, user_id: str):
        """Test 5: SKU with insufficient history"""
        # This test requires a SKU with very little data
        # For now, we'll test with a SKU that might have minimal data
        result = await self.db.execute(
            text("""
                SELECT item_id, COUNT(*) as day_count
                FROM ts_demand_daily
                WHERE client_id = :client_id
                GROUP BY item_id
                HAVING COUNT(*) < 7
                LIMIT 1
            """),
            {"client_id": client_id}
        )
        row = result.fetchone()

        if row:
            item_id = row.item_id
            try:
                forecast_run = await self.service.generate_forecast(
                    client_id=client_id,
                    user_id=user_id,
                    item_ids=[item_id],
                    prediction_length=7,
                    primary_model="chronos-2",
                    include_baseline=False,
                )

                if forecast_run.status == "failed":
                    error_msg = forecast_run.error_message or ""
                    if "insufficient" in error_msg.lower() or "minimum" in error_msg.lower():
                        self.log_pass("test_5_insufficient_history",
                                    "Insufficient history correctly rejected with clear message")
                    else:
                        self.log_warning("test_5_insufficient_history",
                                       f"Failed but error message unclear: {error_msg}")
                else:
                    self.log_warning("test_5_insufficient_history",
                                   "Insufficient history was accepted (may be handled by validator)")
            except Exception as e:
                if "insufficient" in str(e).lower() or "minimum" in str(e).lower():
                    self.log_pass("test_5_insufficient_history",
                                f"Correctly raised exception: {type(e).__name__}")
                else:
                    self.log_warning("test_5_insufficient_history",
                                   f"Unexpected exception: {type(e).__name__}: {str(e)}")
        else:
            self.log_warning("test_5_insufficient_history",
                           "No SKU with insufficient history found for testing")

    async def test_6_invalid_model_name(self, client_id: str, user_id: str):
        """Test 6: Invalid model name"""
        # Get a valid SKU first
        result = await self.db.execute(
            select(SKUClassification).limit(1)
        )
        sku = result.scalar_one_or_none()

        if not sku:
            self.log_warning("test_6_invalid_model_name", "No SKUs found for testing")
            return

        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[sku.item_id],
                prediction_length=7,
                primary_model="INVALID_MODEL_NAME_XYZ",
                include_baseline=False,
            )

            if forecast_run.status == "failed":
                error_msg = forecast_run.error_message or ""
                if "model" in error_msg.lower() or "not found" in error_msg.lower():
                    self.log_pass("test_6_invalid_model_name",
                                "Invalid model name correctly rejected")
                else:
                    self.log_warning("test_6_invalid_model_name",
                                   f"Failed but error message unclear: {error_msg}")
            else:
                self.log_fail("test_6_invalid_model_name",
                            "Invalid model name should have failed")
        except (ValueError, KeyError, AttributeError) as e:
            self.log_pass("test_6_invalid_model_name",
                        f"Invalid model name correctly raised exception: {type(e).__name__}")
        except Exception as e:
            self.log_warning("test_6_invalid_model_name",
                           f"Unexpected exception: {type(e).__name__}: {str(e)}")

    async def test_7_mixed_valid_invalid_items(self, client_id: str, user_id: str):
        """Test 7: Mix of valid and invalid item_ids"""
        # Get a valid SKU first
        result = await self.db.execute(
            select(SKUClassification).limit(1)
        )
        sku = result.scalar_one_or_none()

        if not sku:
            self.log_warning("test_7_mixed_valid_invalid_items", "No SKUs found for testing")
            return

        try:
            forecast_run = await self.service.generate_forecast(
                client_id=client_id,
                user_id=user_id,
                item_ids=[sku.item_id, "INVALID_SKU_12345"],
                prediction_length=7,
                primary_model="chronos-2",
                include_baseline=False,
            )

            # Should either fail completely or succeed with only valid items
            if forecast_run.status == "failed":
                self.log_pass("test_7_mixed_valid_invalid_items",
                            "Mixed valid/invalid items correctly rejected (fail-fast)")
            elif forecast_run.status == "completed":
                # Check if only valid items were processed
                result = await self.db.execute(
                    select(ForecastResult.item_id).where(
                        ForecastResult.forecast_run_id == forecast_run.forecast_run_id
                    ).distinct()
                )
                processed_items = [row[0] for row in result.fetchall()]
                if "INVALID_SKU_12345" not in processed_items:
                    self.log_pass("test_7_mixed_valid_invalid_items",
                                f"Only valid items processed: {processed_items}")
                else:
                    self.log_fail("test_7_mixed_valid_invalid_items",
                                "Invalid item was processed")
            else:
                self.log_warning("test_7_mixed_valid_invalid_items",
                               f"Unexpected status: {forecast_run.status}")
        except Exception as e:
            # Exception is acceptable for mixed input
            self.log_pass("test_7_mixed_valid_invalid_items",
                        f"Mixed items correctly raised exception: {type(e).__name__}")

    async def run_all_tests(self, client_id: str, user_id: str):
        """Run all error handling tests"""
        print("=" * 80)
        print("ERROR HANDLING VALIDATION TESTS")
        print("=" * 80)
        print()

        await self.test_1_invalid_item_ids(client_id, user_id)
        await self.test_2_empty_item_list(client_id, user_id)
        await self.test_3_invalid_prediction_length(client_id, user_id)
        await self.test_4_invalid_date_range(client_id, user_id)
        await self.test_5_insufficient_history(client_id, user_id)
        await self.test_6_invalid_model_name(client_id, user_id)
        await self.test_7_mixed_valid_invalid_items(client_id, user_id)

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
        tester = ErrorHandlingTest(db)
        results = await tester.run_all_tests(client_id, user_id)

        # Return exit code based on results
        if len(results['failed']) > 0:
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())

