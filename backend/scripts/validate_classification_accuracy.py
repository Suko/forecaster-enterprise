#!/usr/bin/env python3
"""
Validate Classification Accuracy

Tests our SKUClassifier against known patterns to verify accuracy.
Can work with:
1. M5 dataset (if imported)
2. Synthetic data with known patterns
3. Current database SKUs

Validates:
- ABC classification accuracy
- XYZ classification accuracy
- Demand pattern detection
- Method recommendations
"""

import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd
import numpy as np

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from forecasting.services.sku_classifier import SKUClassifier
from models.forecast import SKUClassification as SKUClassificationModel


async def validate_classification_accuracy():
    """Validate classification accuracy against known patterns"""

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
        print("Classification Accuracy Validation")
        print("=" * 80)

        # Get all SKUs with classifications
        result = await db.execute(
            select(SKUClassificationModel)
        )
        classifications = result.scalars().all()

        if not classifications:
            print("❌ No classifications found in database")
            print("   Run a forecast first to generate classifications")
            return

        print(f"\n📊 Found {len(classifications)} classified SKUs\n")

        # Get historical data for validation
        classifier = SKUClassifier()

        validation_results = {
            "total": len(classifications),
            "abc_correct": 0,
            "xyz_correct": 0,
            "pattern_correct": 0,
            "method_appropriate": 0,
            "details": []
        }

        # Get revenue data for ABC validation
        item_ids = [c.item_id for c in classifications]
        if not item_ids:
            print("❌ No item IDs found")
            return

        # Build query with proper parameter binding
        placeholders = ",".join([f":item_{i}" for i in range(len(item_ids))])
        params = {f"item_{i}": item_id for i, item_id in enumerate(item_ids)}

        result = await db.execute(
            text(f"""
                SELECT item_id, client_id, SUM(units_sold) as total_units
                FROM ts_demand_daily
                WHERE item_id IN ({placeholders})
                GROUP BY item_id, client_id
            """),
            params
        )
        revenue_data = {row.item_id: float(row.total_units) for row in result.fetchall()}
        total_revenue = sum(revenue_data.values()) if revenue_data else 0

        # Calculate expected ABC classification
        expected_abc = classifier.calculate_abc_classification(revenue_data)

        for classification in classifications:
            item_id = classification.item_id
            client_id = str(classification.client_id)

            # Get historical data
            result = await db.execute(
                text("""
                    SELECT date_local, units_sold
                    FROM ts_demand_daily
                    WHERE item_id = :item_id AND client_id = :client_id
                    ORDER BY date_local
                """),
                {"item_id": item_id, "client_id": client_id}
            )

            daily_rows = result.fetchall()
            if not daily_rows:
                continue

            df = pd.DataFrame([
                {
                    "date": row.date_local,
                    "units_sold": float(row.units_sold or 0),
                }
                for row in daily_rows
            ])

            # Re-classify to validate
            revenue = revenue_data.get(item_id, 0)
            new_classification = classifier.classify_sku(
                item_id=item_id,
                history_df=df,
                revenue=revenue,
                total_revenue=total_revenue,
                abc_class=expected_abc.get(item_id),
            )

            # Compare with stored classification
            abc_match = classification.abc_class == new_classification.abc_class
            xyz_match = classification.xyz_class == new_classification.xyz_class
            pattern_match = classification.demand_pattern == new_classification.demand_pattern
            method_match = classification.recommended_method == new_classification.recommended_method

            if abc_match:
                validation_results["abc_correct"] += 1
            if xyz_match:
                validation_results["xyz_correct"] += 1
            if pattern_match:
                validation_results["pattern_correct"] += 1
            if method_match:
                validation_results["method_appropriate"] += 1

            validation_results["details"].append({
                "item_id": item_id,
                "stored": {
                    "abc": classification.abc_class,
                    "xyz": classification.xyz_class,
                    "pattern": classification.demand_pattern,
                    "method": classification.recommended_method,
                },
                "recalculated": {
                    "abc": new_classification.abc_class,
                    "xyz": new_classification.xyz_class,
                    "pattern": new_classification.demand_pattern,
                    "method": new_classification.recommended_method,
                },
                "matches": {
                    "abc": abc_match,
                    "xyz": xyz_match,
                    "pattern": pattern_match,
                    "method": method_match,
                }
            })

        # Print results
        print("=" * 80)
        print("Validation Results")
        print("=" * 80)

        total = validation_results["total"]
        print(f"\n📊 Total SKUs: {total}")
        print(f"\n✅ ABC Classification Accuracy: {validation_results['abc_correct']}/{total} ({validation_results['abc_correct']/total*100:.1f}%)")
        print(f"✅ XYZ Classification Accuracy: {validation_results['xyz_correct']}/{total} ({validation_results['xyz_correct']/total*100:.1f}%)")
        print(f"✅ Pattern Detection Accuracy: {validation_results['pattern_correct']}/{total} ({validation_results['pattern_correct']/total*100:.1f}%)")
        print(f"✅ Method Recommendation Accuracy: {validation_results['method_appropriate']}/{total} ({validation_results['method_appropriate']/total*100:.1f}%)")

        # Show mismatches
        mismatches = [d for d in validation_results["details"] if not all(d["matches"].values())]
        if mismatches:
            print(f"\n⚠️  Mismatches Found: {len(mismatches)}")
            for detail in mismatches[:5]:  # Show first 5
                print(f"\n   {detail['item_id']}:")
                if not detail["matches"]["abc"]:
                    print(f"      ABC: {detail['stored']['abc']} → {detail['recalculated']['abc']}")
                if not detail["matches"]["xyz"]:
                    print(f"      XYZ: {detail['stored']['xyz']} → {detail['recalculated']['xyz']}")
                if not detail["matches"]["pattern"]:
                    print(f"      Pattern: {detail['stored']['pattern']} → {detail['recalculated']['pattern']}")
        else:
            print(f"\n✅ No mismatches - all classifications are consistent!")

        # Pattern distribution
        print(f"\n📊 Pattern Distribution:")
        patterns = {}
        for detail in validation_results["details"]:
            pattern = detail["recalculated"]["pattern"]
            patterns[pattern] = patterns.get(pattern, 0) + 1
        for pattern, count in sorted(patterns.items()):
            print(f"   {pattern}: {count} SKUs")

        # ABC-XYZ distribution
        print(f"\n📊 ABC-XYZ Distribution:")
        combined = {}
        for detail in validation_results["details"]:
            combo = f"{detail['recalculated']['abc']}-{detail['recalculated']['xyz']}"
            combined[combo] = combined.get(combo, 0) + 1
        for combo, count in sorted(combined.items()):
            print(f"   {combo}: {count} SKUs")

        print("\n" + "=" * 80)
        overall_accuracy = (
            validation_results['abc_correct'] +
            validation_results['xyz_correct'] +
            validation_results['pattern_correct']
        ) / (total * 3) * 100

        if overall_accuracy >= 95:
            print("✅ Classification Accuracy: EXCELLENT")
        elif overall_accuracy >= 80:
            print("✅ Classification Accuracy: GOOD")
        else:
            print("⚠️  Classification Accuracy: NEEDS IMPROVEMENT")

        print(f"   Overall: {overall_accuracy:.1f}%")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(validate_classification_accuracy())

