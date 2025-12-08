"""
Data Access Layer

Fetches historical sales data from database (ts_demand_daily table).
All data is stored per client_id in the database.
"""
import pandas as pd
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, text


class DataAccess:
    """Access historical sales data from database"""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize data access.
        
        Args:
            db: Database session
        """
        self.db = db
    
    async def fetch_historical_data(
        self,
        client_id: str,
        item_ids: List[str],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        location_id: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical sales data for specified items from database.
        
        All data is stored in ts_demand_daily table, filtered by client_id.
        Test users have test data in the table, real users have real data.
        
        Returns DataFrame with columns: id, timestamp, target, [covariates]
        
        Args:
            client_id: Client identifier (filters data per client)
            item_ids: List of item IDs
            start_date: Start date filter (optional)
            end_date: End date filter (optional)
            location_id: Location filter (optional)
        
        Returns:
            DataFrame with columns: id, timestamp, target, promo_flag, holiday_flag, etc.
            Empty DataFrame if table doesn't exist or no data found.
        """
        return await self._fetch_from_database(
            client_id, item_ids, start_date, end_date, location_id
        )
    
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
        
        All data is stored per client_id. Test users have test data,
        real users have real data - all in the same table.
        
        Returns empty DataFrame if table doesn't exist or no data found.
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

