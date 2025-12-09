#!/usr/bin/env python3
"""Quick script to check demand patterns in database"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from models.forecast import SKUClassification
from config import settings
import os

async def check():
    database_url = os.getenv('DATABASE_URL', settings.database_url)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+asyncpg://', 1)
    elif database_url.startswith('postgresql://') and '+asyncpg' not in database_url:
        database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        result = await db.execute(select(SKUClassification))
        all_skus = result.scalars().all()
        
        patterns = {}
        for sku in all_skus:
            pattern = sku.demand_pattern
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        print("Demand Pattern Distribution:")
        for pattern, count in sorted(patterns.items()):
            print(f"  {pattern}: {count} SKUs")
        
        # Check for intermittent
        result = await db.execute(
            select(SKUClassification).where(
                SKUClassification.demand_pattern == 'intermittent'
            )
        )
        intermittent = result.scalars().all()
        print(f"\nIntermittent demand SKUs: {len(intermittent)}")
        if intermittent:
            print("  Examples:")
            for sku in intermittent[:5]:
                print(f"    - {sku.item_id} ({sku.abc_class}-{sku.xyz_class})")

asyncio.run(check())

