#!/usr/bin/env python3
"""
Download and Import M5 Dataset

Downloads M5 Forecasting Competition dataset from Kaggle and imports
diverse SKUs to test classification accuracy.

M5 Dataset:
- 42,840 time series (products × stores)
- 3,049 products across 10 stores
- Daily sales (2011-2016)
- Hierarchical structure
- Multiple demand patterns

Usage:
1. Install kaggle: pip install kaggle
2. Set up Kaggle API credentials: ~/.kaggle/kaggle.json
3. Run: python download_m5_data.py
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set up Kaggle API token from environment BEFORE importing kaggle
# Kaggle library authenticates on import, so we need env vars set first
if os.getenv("KAGGLE_API_TOKEN") and not os.getenv("KAGGLE_KEY"):
    os.environ["KAGGLE_KEY"] = os.getenv("KAGGLE_API_TOKEN")
    # Try to get username from kaggle.json if it exists
    kaggle_json_path = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json_path.exists():
        import json
        try:
            with open(kaggle_json_path) as f:
                kaggle_config = json.load(f)
                if "username" in kaggle_config and kaggle_config["username"] != "kaggle":
                    os.environ["KAGGLE_USERNAME"] = kaggle_config["username"]
        except:
            pass

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings


def download_m5_dataset() -> Path:
    """
    Download M5 dataset from Kaggle (or use existing files).
    
    Returns:
        Path to downloaded data directory
    """
    # Check both possible locations: backend/data/m5 and project_root/data/m5
    data_dir_backend = backend_dir / "data" / "m5"
    data_dir_root = backend_dir.parent / "data" / "m5"
    
    # Use whichever exists, or create in backend
    if data_dir_root.exists() and (data_dir_root / "sales_train_evaluation.csv").exists():
        data_dir = data_dir_root
    elif data_dir_backend.exists() and (data_dir_backend / "sales_train_evaluation.csv").exists():
        data_dir = data_dir_backend
    else:
        data_dir = data_dir_backend
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if already downloaded (check for either evaluation or validation file)
    sales_eval = data_dir / "sales_train_evaluation.csv"
    sales_val = data_dir / "sales_train_validation.csv"
    
    if sales_eval.exists() or sales_val.exists():
        print(f"✅ M5 dataset already exists at: {data_dir}")
        print("   Skipping download...")
        return data_dir
    
    # Only import kaggle if we need to download
    print("📥 M5 dataset not found. Attempting to download from Kaggle...")
    print("   (If download fails, download manually from: https://zenodo.org/records/12636070)")
    try:
        import kaggle
    except ImportError:
        print("❌ Kaggle package not installed")
        print("   Install with: pip install kaggle")
        print("   Or download manually from: https://zenodo.org/records/12636070")
        print(f"   Extract to: {data_dir}")
        sys.exit(1)
    
    print("📥 Downloading M5 dataset from Kaggle...")
    print("   This may take a few minutes (dataset is ~500MB)...")
    
    try:
        # Authentication should already be set up via environment variables
        # (set before importing kaggle module)
        # Just verify authentication
        kaggle.api.authenticate()
        
        # Download competition data
        print("   Downloading files...")
        kaggle.api.competition_download_files(
            'm5-forecasting-accuracy',
            path=str(data_dir)
        )
        
        # Unzip downloaded files
        import zipfile
        import glob
        zip_files = glob.glob(str(data_dir / "*.zip"))
        for zip_file in zip_files:
            print(f"   Extracting {Path(zip_file).name}...")
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(data_dir)
            # Remove zip file after extraction
            os.remove(zip_file)
        
        print(f"✅ Dataset downloaded to: {data_dir}")
        return data_dir
    
    except Exception as e:
        print(f"❌ Download failed: {e}")
        print("\n💡 Alternatives:")
        print("   1. Download from Kaggle manually:")
        print("      https://www.kaggle.com/c/m5-forecasting-accuracy/data")
        print("   2. Download from Zenodo (no account needed):")
        print("      https://zenodo.org/records/12636070")
        print("\n   Extract to: backend/data/m5/")
        print("   Required files:")
        print("   - sales_train_evaluation.csv (or sales_train_validation.csv)")
        print("   - calendar.csv")
        return data_dir


def analyze_m5_patterns(data_dir: Path) -> pd.DataFrame:
    """
    Analyze M5 dataset to find diverse SKU patterns.
    
    Returns:
        DataFrame with SKU analysis (volume, variability, pattern)
    """
    print("\n📊 Analyzing M5 dataset patterns...")
    
    # Load sales data
    sales_file = data_dir / "sales_train_evaluation.csv"
    if not sales_file.exists():
        print(f"❌ Sales file not found: {sales_file}")
        print("   Please download M5 dataset first")
        return pd.DataFrame()
    
    # Read sales data (first few columns are metadata)
    sales_df = pd.read_csv(sales_file, nrows=1000)  # Sample for analysis
    
    print(f"   Loaded {len(sales_df)} products")
    
    # Analyze each product
    results = []
    
    for idx, row in sales_df.iterrows():
        # Get sales columns (d_1 to d_1913)
        sales_cols = [col for col in row.index if col.startswith('d_')]
        sales_values = row[sales_cols].values.astype(float)
        
        # Calculate metrics
        total_sales = sales_values.sum()
        mean_sales = sales_values.mean()
        std_sales = sales_values.std()
        cv = std_sales / mean_sales if mean_sales > 0 else float('inf')
        
        # Calculate ADI (Average Demand Interval)
        non_zero_days = (sales_values > 0).sum()
        adi = len(sales_values) / non_zero_days if non_zero_days > 0 else float('inf')
        
        # Detect pattern
        if adi > 1.32:
            if cv ** 2 > 0.49:
                pattern = "lumpy"
            else:
                pattern = "intermittent"
        else:
            pattern = "regular"
        
        # Classify XYZ
        if cv < 0.5:
            xyz = "X"
        elif cv < 1.0:
            xyz = "Y"
        else:
            xyz = "Z"
        
        results.append({
            "id": row.get('id', f"PROD_{idx}"),
            "item_id": row.get('item_id', f"ITEM_{idx}"),
            "dept_id": row.get('dept_id', ''),
            "cat_id": row.get('cat_id', ''),
            "store_id": row.get('store_id', ''),
            "state_id": row.get('state_id', ''),
            "total_sales": total_sales,
            "mean_sales": mean_sales,
            "cv": cv,
            "adi": adi,
            "pattern": pattern,
            "xyz": xyz,
        })
    
    analysis_df = pd.DataFrame(results)
    
    # Calculate ABC classification
    analysis_df = analysis_df.sort_values('total_sales', ascending=False)
    total_revenue = analysis_df['total_sales'].sum()
    cumulative = 0
    
    abc_classes = []
    for _, row in analysis_df.iterrows():
        cumulative += row['total_sales']
        pct = (cumulative / total_revenue) * 100
        if pct <= 80:
            abc_classes.append("A")
        elif pct <= 95:
            abc_classes.append("B")
        else:
            abc_classes.append("C")
    
    analysis_df['abc'] = abc_classes
    
    print(f"\n📊 Pattern Distribution:")
    print(f"   Regular: {(analysis_df['pattern'] == 'regular').sum()}")
    print(f"   Intermittent: {(analysis_df['pattern'] == 'intermittent').sum()}")
    print(f"   Lumpy: {(analysis_df['pattern'] == 'lumpy').sum()}")
    
    print(f"\n📊 ABC Distribution:")
    print(f"   A: {(analysis_df['abc'] == 'A').sum()}")
    print(f"   B: {(analysis_df['abc'] == 'B').sum()}")
    print(f"   C: {(analysis_df['abc'] == 'C').sum()}")
    
    print(f"\n📊 XYZ Distribution:")
    print(f"   X: {(analysis_df['xyz'] == 'X').sum()}")
    print(f"   Y: {(analysis_df['xyz'] == 'Y').sum()}")
    print(f"   Z: {(analysis_df['xyz'] == 'Z').sum()}")
    
    return analysis_df


def select_diverse_skus(analysis_df: pd.DataFrame, n_skus: int = 20) -> List[Dict]:
    """
    Select diverse SKUs covering all patterns.
    
    Returns:
        List of SKU info dicts
    """
    print(f"\n🎯 Selecting {n_skus} diverse SKUs...")
    
    selected = []
    
    # Target distribution
    targets = {
        ("A", "X"): 3,
        ("A", "Y"): 2,
        ("A", "Z"): 2,
        ("B", "X"): 2,
        ("B", "Y"): 2,
        ("B", "Z"): 1,
        ("C", "X"): 2,
        ("C", "Y"): 2,
        ("C", "Z"): 1,
        ("*", "intermittent"): 2,
        ("*", "lumpy"): 1,
    }
    
    for (abc_target, xyz_or_pattern), count in targets.items():
        if abc_target == "*":
            # Pattern-based selection
            candidates = analysis_df[analysis_df['pattern'] == xyz_or_pattern]
        else:
            # ABC-XYZ selection
            candidates = analysis_df[
                (analysis_df['abc'] == abc_target) &
                (analysis_df['xyz'] == xyz_or_pattern)
            ]
        
        if len(candidates) > 0:
            selected.extend(candidates.head(count).to_dict('records'))
    
    # Fill remaining slots with any diverse patterns
    remaining = n_skus - len(selected)
    if remaining > 0:
        all_skus = analysis_df.to_dict('records')
        for sku in all_skus:
            if sku not in selected and len(selected) < n_skus:
                selected.append(sku)
    
    print(f"✅ Selected {len(selected)} diverse SKUs")
    
    return selected[:n_skus]


async def import_m5_skus_to_database(
    data_dir: Path,
    selected_skus: List[Dict],
    client_id: str
) -> None:
    """
    Import selected M5 SKUs to ts_demand_daily table.
    
    Args:
        data_dir: Path to M5 data directory
        selected_skus: List of SKU info dicts
        client_id: Client ID to import under
    """
    print(f"\n📥 Importing {len(selected_skus)} SKUs to database...")
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Load sales data
        sales_file = data_dir / "sales_train_evaluation.csv"
        sales_df = pd.read_csv(sales_file)
        
        # Create a mapping of id to row
        sales_dict = {row['id']: row for _, row in sales_df.iterrows()}
        
        # Get calendar for dates
        calendar_file = data_dir / "calendar.csv"
        if calendar_file.exists():
            calendar_df = pd.read_csv(calendar_file)
            # M5 starts from 2011-01-29
            dates = pd.to_datetime(calendar_df['date']).tolist()
        else:
            # Generate dates manually
            start_date = datetime(2011, 1, 29)
            dates = [start_date + pd.Timedelta(days=i) for i in range(1913)]
        
        imported_count = 0
        
        for sku_info in selected_skus:
            sku_id = sku_info['id']
            
            if sku_id not in sales_dict:
                print(f"⚠️  SKU {sku_id} not found in sales data")
                continue
            
            row = sales_dict[sku_id]
            sales_cols = [col for col in row.index if col.startswith('d_')]
            sales_values = row[sales_cols].values.astype(float)
            
            # Insert daily records
            for day_idx, sales_qty in enumerate(sales_values):
                if day_idx >= len(dates):
                    break
                
                sale_date = dates[day_idx].date()
                
                # Insert into ts_demand_daily (no location_id in current schema)
                await db.execute(
                    text("""
                        INSERT INTO ts_demand_daily (
                            client_id, item_id, date_local,
                            units_sold
                        ) VALUES (
                            :client_id, :item_id, :date_local,
                            :units_sold
                        )
                        ON CONFLICT (client_id, item_id, date_local)
                        DO UPDATE SET units_sold = EXCLUDED.units_sold
                    """),
                    {
                        "client_id": client_id,
                        "item_id": f"M5_{sku_id}",
                        "date_local": sale_date,
                        "units_sold": int(sales_qty) if not np.isnan(sales_qty) else 0,
                    }
                )
            
            imported_count += 1
            if imported_count % 5 == 0:
                print(f"   Imported {imported_count}/{len(selected_skus)} SKUs...")
                await db.commit()
        
        await db.commit()
        print(f"\n✅ Imported {imported_count} SKUs to database")
        print(f"   Item IDs: M5_<original_id>")


async def main():
    """Main function"""
    print("=" * 80)
    print("M5 Dataset Download and Import")
    print("=" * 80)
    
    # Step 1: Download dataset
    data_dir = download_m5_dataset()
    
    if not (data_dir / "sales_train_evaluation.csv").exists():
        print("\n⚠️  Dataset files not found")
        print("   Please download manually from:")
        print("   https://www.kaggle.com/c/m5-forecasting-accuracy/data")
        print(f"   Extract to: {data_dir}")
        return
    
    # Step 2: Analyze patterns
    analysis_df = analyze_m5_patterns(data_dir)
    
    if analysis_df.empty:
        return
    
    # Step 3: Select diverse SKUs
    selected_skus = select_diverse_skus(analysis_df, n_skus=20)
    
    # Step 4: Get client_id
    database_url = os.getenv("DATABASE_URL", settings.database_url)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    engine = create_async_engine(database_url, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Get first client_id
        result = await db.execute(text("SELECT client_id FROM clients LIMIT 1"))
        row = result.fetchone()
        
        if not row:
            print("❌ No clients found in database")
            print("   Please create a client first")
            return
        
        client_id = str(row[0])
        print(f"\n📦 Using client_id: {client_id}")
    
    # Step 5: Import to database
    await import_m5_skus_to_database(data_dir, selected_skus, client_id)
    
    print("\n" + "=" * 80)
    print("✅ M5 Dataset Import Complete!")
    print("=" * 80)
    print("\n💡 Next steps:")
    print("   1. Run classification test: python scripts/test_sku_classifier.py")
    print("   2. Verify diverse patterns are classified correctly")
    print("   3. Test forecast accuracy with different SKU types")


if __name__ == "__main__":
    asyncio.run(main())

