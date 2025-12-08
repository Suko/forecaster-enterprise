"""
Simple ETL Script: Minibambini CSV → ts_demand_daily format

Transforms messy CSV data into clean time series format for forecasting.
"""
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Optional
import hashlib
import json


class MinibambiniETL:
    """ETL to transform minibambini data to ts_demand_daily format"""
    
    def __init__(self, csv_path: str, output_path: str = "ts_demand_daily_clean.csv"):
        self.csv_path = Path(csv_path)
        self.output_path = Path(output_path)
        self.df_raw = None
        self.df_clean = None
        self.sku_mapping = {}
    
    def generate_sku(self, vendor: str, title: str, variant: str) -> str:
        """Generate standardized SKU"""
        # Vendor code (first 5 chars, uppercase, no spaces)
        vendor_code = vendor.upper().replace(" ", "")[:5] if pd.notna(vendor) else "UNK"
        
        # Product hash (first 6 chars of MD5)
        product_hash = hashlib.md5(str(title).encode()).hexdigest()[:6].upper() if pd.notna(title) else "XXXXXX"
        
        # Variant hash (first 4 chars of MD5)
        variant_hash = hashlib.md5(str(variant).encode()).hexdigest()[:4].upper() if pd.notna(variant) else "DEF"
        
        return f"MB-{vendor_code}-{product_hash}-{variant_hash}"
    
    def load_and_clean(self) -> pd.DataFrame:
        """Load and clean raw data"""
        print(f"Loading {self.csv_path}...")
        self.df_raw = pd.read_csv(self.csv_path)
        print(f"Loaded {len(self.df_raw):,} rows")
        
        # Clean data
        print("\nCleaning data...")
        
        # 1. Remove completely empty rows
        self.df_raw = self.df_raw.dropna(subset=['Product vendor', 'Product title'], how='all')
        print(f"  Removed empty rows: {len(self.df_raw):,} rows remaining")
        
        # 2. Convert dates
        self.df_raw['date'] = pd.to_datetime(self.df_raw['Day'], errors='coerce')
        self.df_raw = self.df_raw[self.df_raw['date'].notna()]  # Remove invalid dates
        print(f"  Valid dates: {len(self.df_raw):,} rows")
        
        # 3. Convert sales to numeric
        self.df_raw['units_sold'] = pd.to_numeric(self.df_raw['Net items sold'], errors='coerce').fillna(0)
        self.df_raw['units_sold'] = self.df_raw['units_sold'].clip(lower=0)  # No negative sales
        
        # 4. Convert inventory to numeric
        self.df_raw['inventory'] = pd.to_numeric(self.df_raw['Ending inventory units'], errors='coerce').fillna(0)
        self.df_raw['inventory'] = self.df_raw['inventory'].clip(lower=0)  # No negative inventory
        
        # 5. Fill missing values
        self.df_raw['Product vendor'] = self.df_raw['Product vendor'].fillna('Unknown')
        self.df_raw['Product title'] = self.df_raw['Product title'].fillna('Unknown Product')
        self.df_raw['Product variant title'] = self.df_raw['Product variant title'].fillna('Default Title')
        
        # 6. Generate SKUs
        print("  Generating SKUs...")
        self.df_raw['item_id'] = self.df_raw.apply(
            lambda row: self.generate_sku(
                row['Product vendor'],
                row['Product title'],
                row['Product variant title']
            ),
            axis=1
        )
        
        print(f"  Generated {self.df_raw['item_id'].nunique()} unique SKUs")
        
        return self.df_raw
    
    def create_full_daily_series(self) -> pd.DataFrame:
        """Create full daily series (fill gaps with zeros)"""
        print("\nCreating full daily series...")
        
        # Get date range
        min_date = self.df_raw['date'].min().date()
        max_date = self.df_raw['date'].max().date()
        all_dates = pd.date_range(min_date, max_date, freq='D')
        
        # Get unique items
        unique_items = self.df_raw['item_id'].unique()
        
        print(f"  Date range: {min_date} to {max_date} ({len(all_dates)} days)")
        print(f"  Items: {len(unique_items)}")
        
        # Create full series
        full_series = []
        for item_id in unique_items:
            item_data = self.df_raw[self.df_raw['item_id'] == item_id].copy()
            
            # Create date index
            item_dates = pd.DataFrame({
                'date': all_dates,
                'item_id': item_id
            })
            
            # Merge with actual data
            item_dates = item_dates.merge(
                item_data[['date', 'units_sold', 'inventory']],
                on='date',
                how='left'
            )
            
            # Fill missing with zeros
            item_dates['units_sold'] = item_dates['units_sold'].fillna(0)
            item_dates['inventory'] = item_dates['inventory'].fillna(0)
            
            # Add metadata
            first_row = item_data.iloc[0]
            item_dates['vendor'] = first_row['Product vendor']
            item_dates['product_title'] = first_row['Product title']
            item_dates['variant_title'] = first_row['Product variant title']
            
            full_series.append(item_dates)
        
        self.df_clean = pd.concat(full_series, ignore_index=True)
        print(f"  Created {len(self.df_clean):,} rows (full daily series)")
        
        return self.df_clean
    
    def transform_to_ts_demand_daily(self) -> pd.DataFrame:
        """Transform to ts_demand_daily format"""
        print("\nTransforming to ts_demand_daily format...")
        
        # Map to ts_demand_daily columns
        ts_df = pd.DataFrame({
            'client_id': 'minibambini',  # Single client for now
            'item_id': self.df_clean['item_id'],
            'location_id': 'default',  # Single location for now
            'date_local': self.df_clean['date'].dt.date,
            'date_utc': self.df_clean['date'].dt.date,  # Same for now
            'observed_at_utc': datetime.now(),
            
            # Target variables
            'units_sold': self.df_clean['units_sold'].astype(int),
            'revenue': None,  # Not available
            'orders_count': None,  # Not available
            
            # Inventory state
            'stock_on_hand_end': self.df_clean['inventory'].astype(int),
            'stockout_flag': (self.df_clean['inventory'] == 0).astype(bool),
            'lost_sales_flag': ((self.df_clean['units_sold'] == 0) & (self.df_clean['inventory'] == 0)).astype(bool),
            
            # Pricing (not available)
            'regular_price': None,
            'actual_price': None,
            'discount_pct': None,
            'promotion_flag': False,
            'promotion_type': None,
            
            # Covariates (not available yet)
            'marketing_spend': None,
            'impressions': None,
            'clicks': None,
            'email_sends': None,
            'email_opens': None,
            'holiday_flag': False,
            'holiday_type': None,
            'planned_promo_flag': False,
            'planned_promo_type': None,
            'seasonal_indicator': None,
            
            # Calendar features
            'is_weekend': self.df_clean['date'].dt.dayofweek.isin([5, 6]).astype(int),
            'day_of_week': self.df_clean['date'].dt.dayofweek + 1,
            'week_of_year': self.df_clean['date'].dt.isocalendar().week,
            
            # Metadata
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        })
        
        # Add month one-hot encoding
        for month in range(1, 13):
            ts_df[f'month_{month}'] = (self.df_clean['date'].dt.month == month).astype(int)
        
        print(f"  Transformed to {len(ts_df):,} rows")
        print(f"  Columns: {len(ts_df.columns)}")
        
        return ts_df
    
    def save_output(self, df: pd.DataFrame, format: str = 'csv'):
        """Save transformed data"""
        if format == 'csv':
            df.to_csv(self.output_path, index=False)
            print(f"\n✅ Saved to {self.output_path}")
        elif format == 'parquet':
            df.to_parquet(self.output_path.with_suffix('.parquet'), index=False)
            print(f"\n✅ Saved to {self.output_path.with_suffix('.parquet')}")
    
    def generate_summary(self) -> Dict:
        """Generate ETL summary"""
        summary = {
            'input_file': str(self.csv_path),
            'output_file': str(self.output_path),
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'input_rows': len(self.df_raw) if self.df_raw is not None else 0,
                'output_rows': len(self.df_clean) if self.df_clean is not None else 0,
                'unique_items': self.df_clean['item_id'].nunique() if self.df_clean is not None else 0,
                'date_range': {
                    'min': str(self.df_clean['date'].min()) if self.df_clean is not None else None,
                    'max': str(self.df_clean['date'].max()) if self.df_clean is not None else None,
                },
                'total_sales': self.df_clean['units_sold'].sum() if self.df_clean is not None else 0,
                'zero_sales_days': (self.df_clean['units_sold'] == 0).sum() if self.df_clean is not None else 0,
            }
        }
        
        return summary
    
    def run_etl(self):
        """Run complete ETL process"""
        print("=" * 60)
        print("MINIBAMBINI ETL PROCESS")
        print("=" * 60)
        
        # Step 1: Load and clean
        self.load_and_clean()
        
        # Step 2: Create full daily series
        self.create_full_daily_series()
        
        # Step 3: Transform to ts_demand_daily format
        ts_df = self.transform_to_ts_demand_daily()
        
        # Step 4: Save
        self.save_output(ts_df)
        
        # Step 5: Generate summary
        summary = self.generate_summary()
        
        # Save summary
        with open("etl_summary.json", "w") as f:
            json.dump(summary, f, indent=2, default=str)
        
        print("\n" + "=" * 60)
        print("ETL COMPLETE")
        print("=" * 60)
        print(f"Input:  {summary['stats']['input_rows']:,} rows")
        print(f"Output: {summary['stats']['output_rows']:,} rows")
        print(f"Items:  {summary['stats']['unique_items']} SKUs")
        print(f"Date range: {summary['stats']['date_range']['min']} to {summary['stats']['date_range']['max']}")
        
        return ts_df


if __name__ == "__main__":
    etl = MinibambiniETL("minibambini.csv", "ts_demand_daily_clean.csv")
    ts_df = etl.run_etl()
    
    print("\n✅ ETL complete! Use ts_demand_daily_clean.csv for forecasting tests.")


