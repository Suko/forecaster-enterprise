"""
Test Data Loader

Loads and transforms synthetic test data for forecasting tests.
"""
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict
from datetime import date, datetime


class TestDataLoader:  # noqa: PytestCollectionWarning
    """Load and transform test data from CSV"""
    
    def __init__(self, csv_path: Optional[str] = None):
        """
        Initialize test data loader.
        
        Args:
            csv_path: Path to CSV file. If None, uses default test data path.
        """
        if csv_path is None:
            # Default path relative to backend directory
            base_path = Path(__file__).parent.parent.parent
            csv_path = base_path.parent / "data" / "sintetic_data" / "synthetic_ecom_chronos2_demo.csv"
        
        self.csv_path = Path(csv_path)
        self._df: Optional[pd.DataFrame] = None
    
    def load_csv(self) -> pd.DataFrame:
        """Load CSV file into DataFrame"""
        if self._df is None:
            self._df = pd.read_csv(self.csv_path)
            # Convert date column
            self._df['date'] = pd.to_datetime(self._df['date'])
        return self._df
    
    def get_item_data(
        self,
        item_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        store_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Get historical data for a specific item, formatted for Chronos-2.
        
        Args:
            item_id: SKU identifier (e.g., "SKU001")
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            store_id: Store filter (optional, defaults to first store)
        
        Returns:
            DataFrame with columns: id, timestamp, target, [covariates]
        """
        df = self.load_csv()
        
        # Filter by item
        item_df = df[df['sku'] == item_id].copy()
        
        if item_df.empty:
            return pd.DataFrame()
        
        # Filter by store (use first store if not specified)
        if store_id:
            item_df = item_df[item_df['store_id'] == store_id]
        else:
            # Use first available store
            store_id = item_df['store_id'].iloc[0]
            item_df = item_df[item_df['store_id'] == store_id]
        
        # Filter by date range
        if start_date:
            item_df = item_df[item_df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            item_df = item_df[item_df['date'] <= pd.to_datetime(end_date)]
        
        # Sort by date
        item_df = item_df.sort_values('date')
        
        # Transform to Chronos-2 format
        result_df = pd.DataFrame()
        result_df['id'] = item_id
        result_df['timestamp'] = item_df['date']
        result_df['target'] = item_df['sales_qty']
        
        # Add covariates (if available)
        if 'promo_flag' in item_df.columns:
            result_df['promo_flag'] = item_df['promo_flag'].astype(int)
        if 'holiday_flag' in item_df.columns:
            result_df['holiday_flag'] = item_df['holiday_flag'].astype(int)
        if 'is_weekend' in item_df.columns:
            result_df['is_weekend'] = item_df['is_weekend'].astype(int)
        if 'marketing_index' in item_df.columns:
            result_df['marketing_index'] = item_df['marketing_index']
        
        return result_df
    
    def get_multiple_items(
        self,
        item_ids: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple items.
        
        Returns:
            Dictionary mapping item_id to DataFrame
        """
        return {
            item_id: self.get_item_data(item_id, start_date, end_date)
            for item_id in item_ids
        }
    
    def get_available_items(self) -> List[str]:
        """Get list of available item IDs in test data"""
        df = self.load_csv()
        return sorted(df['sku'].unique().tolist())
    
    def get_date_range(self) -> tuple[date, date]:
        """Get min and max dates in test data"""
        df = self.load_csv()
        min_date = df['date'].min().date()
        max_date = df['date'].max().date()
        return (min_date, max_date)
    
    def get_item_summary(self, item_id: str) -> Dict:
        """Get summary statistics for an item"""
        df = self.get_item_data(item_id)
        
        if df.empty:
            return {}
        
        return {
            "item_id": item_id,
            "date_range": (df['timestamp'].min().date(), df['timestamp'].max().date()),
            "total_days": len(df),
            "avg_daily_sales": float(df['target'].mean()),
            "total_sales": float(df['target'].sum()),
            "min_sales": float(df['target'].min()),
            "max_sales": float(df['target'].max()),
        }

