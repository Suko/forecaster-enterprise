#!/usr/bin/env python3
"""
Test SKU Classifier

Tests the SKUClassifier service with real data from the database.
"""

import asyncio
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from forecasting.services.sku_classifier import SKUClassifier


async def test_sku_classifier():
    """Test SKUClassifier with real database data"""
    
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
        # Get all SKUs with revenue data
        result = await db.execute(
            text("""
                SELECT 
                    item_id,
                    client_id,
                    SUM(units_sold) as total_units,
                    SUM(units_sold) as total_revenue  -- Using units as proxy
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 30
                ORDER BY total_revenue DESC
                LIMIT 10
            """)
        )
        
        rows = result.fetchall()
        
        if not rows:
            print("❌ No SKUs found in database")
            return
        
        print(f"✅ Testing SKUClassifier with {len(rows)} SKUs\n")
        print("=" * 80)
        
        client_id = str(rows[0].client_id)
        
        # Calculate total revenue for ABC classification
        total_revenue = float(sum(float(row.total_revenue) for row in rows))
        
        # Get revenue dict for ABC classification
        revenue_dict = {row.item_id: float(row.total_revenue) for row in rows}
        
        # Calculate ABC classification
        classifier = SKUClassifier()
        abc_classification = classifier.calculate_abc_classification(revenue_dict)
        
        # Test each SKU
        for idx, row in enumerate(rows, 1):
            item_id = row.item_id
            
            # Get daily data
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
            df = pd.DataFrame([
                {
                    "date": row.date_local,
                    "units_sold": float(row.units_sold or 0),
                }
                for row in daily_rows
            ])
            
            # Classify SKU
            classification = classifier.classify_sku(
                item_id=item_id,
                history_df=df,
                revenue=float(row.total_revenue),
                total_revenue=float(total_revenue),
                abc_class=abc_classification.get(item_id),
            )
            
            # Print results
            print(f"\n[{idx}] {item_id}")
            print(f"    ABC Class: {classification.abc_class}")
            print(f"    XYZ Class: {classification.xyz_class}")
            print(f"    Pattern: {classification.demand_pattern}")
            print(f"    CV: {classification.coefficient_of_variation:.3f}")
            print(f"    ADI: {classification.average_demand_interval:.3f}")
            print(f"    Forecastability: {classification.forecastability_score:.2f}")
            print(f"    Recommended Method: {classification.recommended_method}")
            print(f"    Expected MAPE: {classification.expected_mape_range[0]:.0f}-{classification.expected_mape_range[1]:.0f}%")
            if classification.warnings:
                print(f"    ⚠️  Warnings: {', '.join(classification.warnings)}")
        
        print("\n" + "=" * 80)
        print("✅ SKUClassifier test complete!")
        print(f"\nSummary:")
        print(f"  - ABC Distribution: A={sum(1 for c in abc_classification.values() if c == 'A')}, "
              f"B={sum(1 for c in abc_classification.values() if c == 'B')}, "
              f"C={sum(1 for c in abc_classification.values() if c == 'C')}")


if __name__ == "__main__":
    asyncio.run(test_sku_classifier())

