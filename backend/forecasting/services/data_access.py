"""
Data Access Layer

Fetches historical sales data from database or test data source.
"""
import pandas as pd
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text

# For test data fallback
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))
from tests.fixtures.test_data_loader import TestDataLoader


class DataAccess:
    """Access historical sales data from database or test data"""
    
    def __init__(self, db: AsyncSession, use_test_data: bool = False):
        """
        Initialize data access.
        
        Args:
            db: Database session
            use_test_data: If True, use CSV test data instead of database
        """
        self.db = db
        self.use_test_data = use_test_data
        self.test_loader = TestDataLoader() if use_test_data else None
    
    async def fetch_historical_data(
        self,
        client_id: str,
        item_ids: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical sales data for specified items.
        
        Returns DataFrame with columns: id, timestamp, target, [covariates]
        
        Args:
            client_id: Client identifier
            item_ids: List of item IDs
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            location_id: Location filter (optional)
        
        Returns:
            DataFrame with columns: id, timestamp, target, promo_flag, holiday_flag, etc.
        """
        if self.use_test_data:
            return await self._fetch_from_test_data(item_ids, start_date, end_date)
        else:
            return await self._fetch_from_database(
                client_id, item_ids, start_date, end_date, location_id
            )
    
    async def _fetch_from_test_data(
        self,
        item_ids: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> pd.DataFrame:
        """Fetch data from CSV test data"""
        all_data = []
        
        for item_id in item_ids:
            item_data = self.test_loader.get_item_data(
                item_id=item_id,
                start_date=start_date,
                end_date=end_date,
            )
            if not item_data.empty:
                all_data.append(item_data)
        
        if not all_data:
            return pd.DataFrame()
        
        # Combine all items
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Ensure required columns
        if "id" not in combined_df.columns:
            combined_df["id"] = combined_df.get("item_id", "")
        if "timestamp" not in combined_df.columns:
            combined_df["timestamp"] = combined_df.get("date", pd.NaT)
        if "target" not in combined_df.columns:
            combined_df["target"] = combined_df.get("sales_qty", 0)
        
        return combined_df
    
    async def _fetch_from_database(
        self,
        client_id: str,
        item_ids: List[str],
        start_date: Optional[date],
        end_date: Optional[date],
        location_id: Optional[str],
    ) -> pd.DataFrame:
        """
        Fetch data from ts_demand_daily table.
        
        Note: This assumes the table exists. If not, will return empty DataFrame.
        """
        try:
            # Check if table exists
            check_query = text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'ts_demand_daily'
                );
            """)
            result = await self.db.execute(check_query)
            table_exists = result.scalar()
            
            if not table_exists:
                # Table doesn't exist yet - return empty DataFrame
                # In production, this would be populated by ETL
                return pd.DataFrame()
            
            # Build query
            query = text("""
                SELECT 
                    item_id::text as id,
                    date_local as timestamp,
                    units_sold as target,
                    COALESCE(promotion_flag, false)::int as promo_flag,
                    COALESCE(holiday_flag, false)::int as holiday_flag,
                    COALESCE(is_weekend, false)::int as is_weekend,
                    COALESCE(marketing_spend, 0) as marketing_spend
                FROM ts_demand_daily
                WHERE client_id = :client_id
                  AND item_id::text = ANY(:item_ids)
            """)
            
            params = {
                "client_id": client_id,
                "item_ids": item_ids,
            }
            
            if start_date:
                query = text(str(query) + " AND date_local >= :start_date")
                params["start_date"] = start_date
            
            if end_date:
                query = text(str(query) + " AND date_local <= :end_date")
                params["end_date"] = end_date
            
            if location_id:
                query = text(str(query) + " AND location_id = :location_id")
                params["location_id"] = location_id
            
            query = text(str(query) + " ORDER BY item_id, date_local")
            
            # Execute query
            result = await self.db.execute(query, params)
            rows = result.fetchall()
            
            if not rows:
                return pd.DataFrame()
            
            # Convert to DataFrame
            df = pd.DataFrame(rows, columns=result.keys())
            
            # Ensure timestamp is datetime
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            
            return df
            
        except Exception as e:
            # If query fails, return empty DataFrame
            # In production, log this error
            print(f"Error fetching from database: {e}")
            return pd.DataFrame()

