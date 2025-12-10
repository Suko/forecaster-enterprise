"""
ETL Connectors

Abstract base classes and implementations for external data sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from uuid import UUID


class ETLConnector(ABC):
    """Abstract base class for ETL connectors"""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to data source"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to data source"""
        pass
    
    @abstractmethod
    async def fetch_sales_history(
        self,
        client_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch sales history data
        
        Returns:
            List of dicts with keys: item_id, date_local, units_sold, etc.
        """
        pass
    
    @abstractmethod
    async def fetch_products(self, client_id: UUID) -> List[Dict[str, Any]]:
        """
        Fetch product master data
        
        Returns:
            List of dicts with keys: item_id, product_name, category, unit_cost, etc.
        """
        pass
    
    @abstractmethod
    async def fetch_stock_levels(self, client_id: UUID) -> List[Dict[str, Any]]:
        """
        Fetch current stock levels
        
        Returns:
            List of dicts with keys: item_id, location_id, current_stock
        """
        pass
    
    @abstractmethod
    async def fetch_locations(self, client_id: UUID) -> List[Dict[str, Any]]:
        """
        Fetch location master data
        
        Returns:
            List of dicts with keys: location_id, name, address, etc.
        """
        pass


class BigQueryConnector(ETLConnector):
    """BigQuery connector implementation"""
    
    def __init__(self, project_id: str, credentials_path: Optional[str] = None):
        self.project_id = project_id
        self.credentials_path = credentials_path
        self.client = None
    
    async def connect(self) -> None:
        """Establish BigQuery connection"""
        try:
            from google.cloud import bigquery
            from google.oauth2 import service_account
            
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = bigquery.Client(
                    project=self.project_id,
                    credentials=credentials
                )
            else:
                # Use default credentials
                self.client = bigquery.Client(project=self.project_id)
        except ImportError:
            raise ImportError(
                "google-cloud-bigquery is required for BigQuery connector. "
                "Install with: pip install google-cloud-bigquery"
            )
    
    async def disconnect(self) -> None:
        """Close BigQuery connection"""
        self.client = None
    
    async def fetch_sales_history(
        self,
        client_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Fetch sales history from BigQuery"""
        if not self.client:
            raise RuntimeError("Not connected to BigQuery")
        
        # TODO: Implement BigQuery query
        # This is a placeholder - actual implementation depends on BigQuery schema
        query = f"""
        SELECT 
            sku as item_id,
            date as date_local,
            quantity as units_sold,
            promotion_flag,
            holiday_flag,
            is_weekend,
            marketing_spend
        FROM `{self.project_id}.sales.sales_history`
        WHERE client_id = @client_id
        """
        
        if start_date:
            query += " AND date >= @start_date"
        if end_date:
            query += " AND date <= @end_date"
        
        # Execute query and return results
        # This is a placeholder - actual implementation needed
        return []
    
    async def fetch_products(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch products from BigQuery"""
        if not self.client:
            raise RuntimeError("Not connected to BigQuery")
        
        # TODO: Implement BigQuery query
        return []
    
    async def fetch_stock_levels(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch stock levels from BigQuery"""
        if not self.client:
            raise RuntimeError("Not connected to BigQuery")
        
        # TODO: Implement BigQuery query
        return []
    
    async def fetch_locations(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch locations from BigQuery"""
        if not self.client:
            raise RuntimeError("Not connected to BigQuery")
        
        # TODO: Implement BigQuery query
        return []


class SQLConnector(ETLConnector):
    """Generic SQL connector for PostgreSQL, MySQL, etc."""
    
    def __init__(self, connection_string: str, driver: str = "postgresql"):
        self.connection_string = connection_string
        self.driver = driver
        self.connection = None
    
    async def connect(self) -> None:
        """Establish SQL connection"""
        if self.driver == "postgresql":
            import asyncpg
            self.connection = await asyncpg.connect(self.connection_string)
        else:
            raise ValueError(f"Unsupported driver: {self.driver}")
    
    async def disconnect(self) -> None:
        """Close SQL connection"""
        if self.connection:
            await self.connection.close()
            self.connection = None
    
    async def fetch_sales_history(
        self,
        client_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Fetch sales history from SQL database"""
        if not self.connection:
            raise RuntimeError("Not connected to SQL database")
        
        # TODO: Implement SQL query
        # This is a placeholder - actual implementation depends on SQL schema
        query = """
        SELECT 
            sku as item_id,
            date as date_local,
            quantity as units_sold,
            promotion_flag,
            holiday_flag,
            is_weekend,
            marketing_spend
        FROM sales_history
        WHERE client_id = $1
        """
        
        params = [str(client_id)]
        if start_date:
            query += " AND date >= $2"
            params.append(start_date)
        if end_date:
            query += " AND date <= $3"
            params.append(end_date)
        
        # Execute query and return results
        # This is a placeholder - actual implementation needed
        return []
    
    async def fetch_products(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch products from SQL database"""
        if not self.connection:
            raise RuntimeError("Not connected to SQL database")
        
        # TODO: Implement SQL query
        return []
    
    async def fetch_stock_levels(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch stock levels from SQL database"""
        if not self.connection:
            raise RuntimeError("Not connected to SQL database")
        
        # TODO: Implement SQL query
        return []
    
    async def fetch_locations(self, client_id: UUID) -> List[Dict[str, Any]]:
        """Fetch locations from SQL database"""
        if not self.connection:
            raise RuntimeError("Not connected to SQL database")
        
        # TODO: Implement SQL query
        return []

