#!/usr/bin/env python3
"""
Re-classify SKUs with updated MAPE ranges and validate improvement.
"""
import asyncio
import sys
from pathlib import Path
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import pandas as pd

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import os
from config import settings
from models.forecast import SKUClassification
from forecasting.services.sku_classifier import SKUClassifier


async def reclassify_and_validate():
    """Re-classify SKUs and compare within-range percentages"""
    
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        print("=" * 80)
        print("Re-Classification with Updated MAPE Ranges")
        print("=" * 80)
        
        # Get all classifications
        result = await db.execute(select(SKUClassification))
        classifications = result.scalars().all()
        
        if not classifications:
            print("❌ No classifications found")
            return
        
        print(f"\n📦 Found {len(classifications)} classified SKUs")
        
        classifier = SKUClassifier()
        
        # Get previous "within range" stats from METHOD_ROUTING_VALIDATION_RESULTS
        # We know from validation: 60% within range overall
        
        print(f"\n📊 Comparing old vs new ranges...\n")
        
        results = []
        
        for classification in classifications:
            item_id = classification.item_id
            abc = classification.abc_class
            xyz = classification.xyz_class
            pattern = classification.demand_pattern
            
            # Get old range (stored in DB)
            old_min = float(classification.expected_mape_min)
            old_max = float(classification.expected_mape_max)
            
            # Calculate new range
            new_min, new_max = classifier.get_expected_mape_range(abc, xyz, pattern)
            
            results.append({
                "item_id": item_id,
                "classification": f"{abc}-{xyz}",
                "pattern": pattern,
                "old_min": old_min,
                "old_max": old_max,
                "new_min": new_min,
                "new_max": new_max,
                "changed": (old_min != new_min) or (old_max != new_max),
            })
            
            # Update database with new ranges
            classification.expected_mape_min = new_min
            classification.expected_mape_max = new_max
        
        await db.commit()
        
        df = pd.DataFrame(results)
        
        # Summary of changes
        changed = df[df['changed']]
        print(f"📝 Range Changes:")
        print(f"   Updated: {len(changed)}/{len(df)} classifications")
        
        if len(changed) > 0:
            print(f"\n📊 Changed Classifications:")
            for _, row in changed.iterrows():
                print(f"   {row['classification']}: ({row['old_min']:.0f}-{row['old_max']:.0f}) → ({row['new_min']:.0f}-{row['new_max']:.0f})")
        
        # Now check how many are within new ranges
        # Get validation results
        validation_file = backend_dir / "reports" / "method_routing_validation_20251209_113238.csv"
        
        if validation_file.exists():
            val_df = pd.read_csv(validation_file)
            
            print(f"\n📊 Within-Range Comparison:")
            print(f"   (Using validation MAPE results)")
            
            # Merge with new ranges
            merged = val_df.merge(
                df[['item_id', 'new_min', 'new_max', 'old_min', 'old_max']], 
                on='item_id', 
                how='left'
            )
            
            # Calculate old within-range
            old_within = ((merged['mape_routed'] >= merged['old_min']) & 
                         (merged['mape_routed'] <= merged['old_max'])).sum()
            
            # Calculate new within-range
            new_within = ((merged['mape_routed'] >= merged['new_min']) & 
                         (merged['mape_routed'] <= merged['new_max'])).sum()
            
            print(f"\n   Old ranges: {old_within}/{len(merged)} ({old_within/len(merged)*100:.1f}%) within range")
            print(f"   New ranges: {new_within}/{len(merged)} ({new_within/len(merged)*100:.1f}%) within range")
            print(f"   Improvement: +{new_within - old_within} SKUs (+{(new_within - old_within)/len(merged)*100:.1f}%)")
            
            # Breakdown by classification
            print(f"\n📊 By Classification:")
            for classification in sorted(merged['classification'].unique()):
                class_df = merged[merged['classification'] == classification]
                old_in = ((class_df['mape_routed'] >= class_df['old_min']) & 
                         (class_df['mape_routed'] <= class_df['old_max'])).sum()
                new_in = ((class_df['mape_routed'] >= class_df['new_min']) & 
                         (class_df['mape_routed'] <= class_df['new_max'])).sum()
                print(f"   {classification}: {old_in}/{len(class_df)} → {new_in}/{len(class_df)} within range")
        
        print("\n" + "=" * 80)
        print("✅ Re-classification Complete!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(reclassify_and_validate())

