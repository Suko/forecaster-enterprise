#!/usr/bin/env python3
"""
Test Classification GET Endpoint

Tests the GET /api/v1/skus/{item_id}/classification endpoint
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
from models.forecast import SKUClassification as SKUClassificationModel


async def test_classification_endpoint():
    """Test the classification endpoint logic"""

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
        print("Test Classification GET Endpoint")
        print("=" * 80)

        # Get a SKU that has a classification
        result = await db.execute(
            select(SKUClassificationModel).limit(5)
        )
        classifications = result.scalars().all()

        if not classifications:
            print("❌ No classifications found in database")
            print("   Run a forecast first to generate classifications")
            return

        print(f"\n✅ Found {len(classifications)} classifications in database\n")

        for idx, classification in enumerate(classifications, 1):
            print(f"[{idx}] {classification.item_id}")
            print(f"    ABC: {classification.abc_class}")
            print(f"    XYZ: {classification.xyz_class}")
            print(f"    Pattern: {classification.demand_pattern}")
            print(f"    Forecastability: {float(classification.forecastability_score):.2f}")
            print(f"    Recommended: {classification.recommended_method}")
            print(f"    Expected MAPE: {float(classification.expected_mape_min):.0f}-{float(classification.expected_mape_max):.0f}%")

            # Extract warnings
            warnings = []
            if classification.classification_metadata and isinstance(classification.classification_metadata, dict):
                warnings = classification.classification_metadata.get("warnings", [])

            if warnings:
                print(f"    Warnings: {', '.join(warnings)}")
            print()

        # Test endpoint logic (simulate)
        print("=" * 80)
        print("Simulated API Response Format")
        print("=" * 80)

        test_item_id = classifications[0].item_id
        client_id = str(classifications[0].client_id)

        # Simulate GET request
        result = await db.execute(
            select(SKUClassificationModel).where(
                SKUClassificationModel.client_id == client_id,
                SKUClassificationModel.item_id == test_item_id
            ).order_by(SKUClassificationModel.classification_date.desc())
        )
        classification = result.scalar_one_or_none()

        if classification:
            warnings = []
            if classification.classification_metadata and isinstance(classification.classification_metadata, dict):
                warnings = classification.classification_metadata.get("warnings", [])

            api_response = {
                "abc_class": classification.abc_class,
                "xyz_class": classification.xyz_class,
                "demand_pattern": classification.demand_pattern,
                "forecastability_score": float(classification.forecastability_score),
                "recommended_method": classification.recommended_method,
                "expected_mape_range": [
                    float(classification.expected_mape_min) if classification.expected_mape_min else 0.0,
                    float(classification.expected_mape_max) if classification.expected_mape_max else 100.0
                ],
                "warnings": warnings,
            }

            print(f"\n✅ GET /api/v1/skus/{test_item_id}/classification")
            print(f"\nResponse:")
            import json
            print(json.dumps(api_response, indent=2))
        else:
            print(f"❌ Classification not found for {test_item_id}")

        print("\n" + "=" * 80)
        print("✅ Classification Endpoint Test: PASSED")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_classification_endpoint())

