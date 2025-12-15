#!/usr/bin/env python3
"""
Analyze SKU patterns for Phase 2A (ABC-XYZ Classification)

This script analyzes all SKUs in the database to determine:
- ABC classification (volume/revenue)
- XYZ classification (variability)
- Demand patterns (regular, intermittent, lumpy, seasonal)
- Coefficient of Variation (CV)
- Average Demand Interval (ADI)

Output: JSON report with classification recommendations
"""

import asyncio
import sys
from pathlib import Path
from datetime import date, timedelta
from collections import defaultdict
import pandas as pd
import numpy as np
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings


def calculate_abc_classification(revenue_dict: dict) -> dict:
    """
    Calculate ABC classification based on revenue.

    A: Top 80% of revenue (~20% of SKUs)
    B: Next 15% of revenue (~30% of SKUs)
    C: Bottom 5% of revenue (~50% of SKUs)
    """
    # Sort by revenue descending
    sorted_skus = sorted(revenue_dict.items(), key=lambda x: x[1], reverse=True)
    total_revenue = sum(revenue_dict.values())

    classification = {}
    cumulative_revenue = 0

    for sku, revenue in sorted_skus:
        cumulative_revenue += revenue
        pct = (cumulative_revenue / total_revenue) * 100

        if pct <= 80:
            classification[sku] = "A"
        elif pct <= 95:
            classification[sku] = "B"
        else:
            classification[sku] = "C"

    return classification


def calculate_xyz_classification(cv_dict: dict) -> dict:
    """
    Calculate XYZ classification based on Coefficient of Variation.

    X: CV < 0.5 (low variability)
    Y: 0.5 ≤ CV < 1.0 (medium variability)
    Z: CV ≥ 1.0 (high variability)
    """
    classification = {}

    for sku, cv in cv_dict.items():
        if cv < 0.5:
            classification[sku] = "X"
        elif cv < 1.0:
            classification[sku] = "Y"
        else:
            classification[sku] = "Z"

    return classification


def calculate_adi(units_sold: pd.Series) -> float:
    """
    Calculate Average Demand Interval (ADI).

    ADI = Total days / Number of non-zero days

    ADI > 1.32 indicates intermittent demand
    """
    total_days = len(units_sold)
    non_zero_days = (units_sold > 0).sum()

    if non_zero_days == 0:
        return float('inf')  # No demand at all

    return total_days / non_zero_days


def detect_demand_pattern(units_sold: pd.Series, adi: float, cv: float) -> str:
    """
    Detect demand pattern based on ADI and CV.

    Patterns:
    - Regular: ADI ≤ 1.32
    - Intermittent: ADI > 1.32
    - Lumpy: ADI > 1.32 AND CV² > 0.49
    - Seasonal: (to be detected via seasonal decomposition)
    """
    if adi > 1.32:
        cv_squared = cv ** 2
        if cv_squared > 0.49:
            return "lumpy"
        else:
            return "intermittent"
    else:
        return "regular"


async def analyze_sku_patterns():
    """Analyze all SKUs in the database"""

    # Get database URL from environment or config
    database_url = os.getenv("DATABASE_URL", settings.database_url)

    # Convert postgres:// to postgresql+asyncpg:// for async operations
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Get all SKUs with data
        result = await db.execute(
            text("""
                SELECT
                    item_id,
                    client_id,
                    COUNT(*) as total_days,
                    MIN(date_local) as min_date,
                    MAX(date_local) as max_date,
                    SUM(units_sold) as total_units,
                    SUM(units_sold) as total_revenue,  -- Using units as proxy for revenue (ABC classification)
                    AVG(units_sold) as avg_units,
                    STDDEV(units_sold) as std_units
                FROM ts_demand_daily
                GROUP BY item_id, client_id
                HAVING COUNT(*) >= 30
                ORDER BY total_revenue DESC
            """)
        )

        rows = result.fetchall()

        if not rows:
            print("❌ No SKUs found in database")
            return

        print(f"✅ Found {len(rows)} SKUs to analyze\n")

        # Get client_id (assuming all same client)
        client_id = str(rows[0].client_id)

        # Collect data for each SKU
        sku_data = {}
        revenue_dict = {}

        for row in rows:
            item_id = row.item_id

            # Get daily data for this SKU
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

            # Calculate revenue as units_sold (proxy for ABC classification)
            df["revenue"] = df["units_sold"]

            units_sold = df["units_sold"]

            # Calculate metrics
            mean_units = units_sold.mean()
            std_units = units_sold.std()
            cv = (std_units / mean_units) if mean_units > 0 else float('inf')
            adi = calculate_adi(units_sold)
            total_revenue = df["revenue"].sum()

            # Detect pattern
            pattern = detect_demand_pattern(units_sold, adi, cv)

            # Store data
            sku_data[item_id] = {
                "total_days": len(df),
                "total_units": units_sold.sum(),
                "total_revenue": total_revenue,
                "mean_units": mean_units,
                "std_units": std_units,
                "cv": cv,
                "adi": adi,
                "pattern": pattern,
                "zero_days": (units_sold == 0).sum(),
                "zero_pct": (units_sold == 0).sum() / len(units_sold) * 100,
                "min_units": units_sold.min(),
                "max_units": units_sold.max(),
            }

            revenue_dict[item_id] = total_revenue

        # Calculate ABC classification
        abc_classification = calculate_abc_classification(revenue_dict)

        # Calculate XYZ classification
        cv_dict = {sku: data["cv"] for sku, data in sku_data.items()}
        xyz_classification = calculate_xyz_classification(cv_dict)

        # Build final report
        report = {
            "summary": {
                "total_skus": len(sku_data),
                "analysis_date": str(date.today()),
            },
            "classifications": {
                "abc": {
                    "A": sum(1 for c in abc_classification.values() if c == "A"),
                    "B": sum(1 for c in abc_classification.values() if c == "B"),
                    "C": sum(1 for c in abc_classification.values() if c == "C"),
                },
                "xyz": {
                    "X": sum(1 for c in xyz_classification.values() if c == "X"),
                    "Y": sum(1 for c in xyz_classification.values() if c == "Y"),
                    "Z": sum(1 for c in xyz_classification.values() if c == "Z"),
                },
                "patterns": defaultdict(int),
            },
            "skus": {}
        }

        # Add SKU details
        for item_id, data in sku_data.items():
            abc = abc_classification.get(item_id, "?")
            xyz = xyz_classification.get(item_id, "?")

            report["classifications"]["patterns"][data["pattern"]] += 1

            report["skus"][item_id] = {
                **data,
                "abc_class": abc,
                "xyz_class": xyz,
                "combined_class": f"{abc}-{xyz}",
            }

        # Convert defaultdict to dict for JSON
        report["classifications"]["patterns"] = dict(report["classifications"]["patterns"])

        # Print summary
        print("=" * 80)
        print("SKU Pattern Analysis Summary")
        print("=" * 80)
        print(f"\n📊 Total SKUs: {len(sku_data)}")

        print(f"\n📈 ABC Classification (by revenue):")
        print(f"   A (Top 80%): {report['classifications']['abc']['A']} SKUs")
        print(f"   B (Next 15%): {report['classifications']['abc']['B']} SKUs")
        print(f"   C (Bottom 5%): {report['classifications']['abc']['C']} SKUs")

        print(f"\n📊 XYZ Classification (by variability):")
        print(f"   X (Low CV < 0.5): {report['classifications']['xyz']['X']} SKUs")
        print(f"   Y (Medium 0.5-1.0): {report['classifications']['xyz']['Y']} SKUs")
        print(f"   Z (High CV ≥ 1.0): {report['classifications']['xyz']['Z']} SKUs")

        print(f"\n🔄 Demand Patterns:")
        for pattern, count in report["classifications"]["patterns"].items():
            print(f"   {pattern}: {count} SKUs")

        print(f"\n📋 Combined Classification (ABC-XYZ):")
        combined = defaultdict(int)
        for sku_data_item in report["skus"].values():
            combined[sku_data_item["combined_class"]] += 1
        for combo, count in sorted(combined.items()):
            print(f"   {combo}: {count} SKUs")

        # Save report
        import json
        from datetime import datetime

        report_file = backend_dir / "reports" / f"sku_pattern_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_file.parent.mkdir(exist_ok=True)

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n✅ Report saved to: {report_file}")

        # Recommendations
        print(f"\n💡 Recommendations:")
        print(f"   - Review report to see which patterns we have")
        print(f"   - Identify missing patterns (e.g., intermittent, lumpy)")
        print(f"   - Consider downloading M5 dataset for more diverse patterns")
        print(f"   - Generate synthetic data for missing edge cases")


if __name__ == "__main__":
    asyncio.run(analyze_sku_patterns())

