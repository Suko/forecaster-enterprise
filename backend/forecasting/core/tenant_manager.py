"""
Tenant Database Manager (Optional - For Future Extensibility)

Note: This class is optional. The system works without it because:
- Both SaaS and on-premise use same database connection (get_db())
- Both use same queries (filter by client_id)
- Both use same schema (include client_id column)
- No mode detection needed - system is agnostic

This class can be kept for future extensibility (e.g., if we need
client-specific database routing in the future), but is not required
for basic unified operation.

Design Principle: Maximum unification
- Same schema (both include client_id column)
- Same queries (both filter by client_id)
- Same authentication (JWT token with client_id)
- No mode configuration needed
"""
from enum import Enum
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
import os
import json
from pathlib import Path


class TenantMode(str, Enum):
    """Tenant deployment mode"""
    SAAS = "saas"           # Shared database, filter by client_id
    ON_PREMISE = "on_premise"  # Separate database per client


class TenantDatabaseManager:
    """
    Optional tenant database manager (for future extensibility).
    
    Note: Not required for basic operation. The system works with standard get_db()
    because both SaaS and on-premise use the same approach:
    - Same database connection
    - Same queries (filter by client_id)
    - Same schema (include client_id)
    
    This class can be used if we need client-specific database routing in the future,
    but for now, standard get_db() is sufficient.
    """
    
    def __init__(
        self,
        default_db: AsyncSession,
        mode: TenantMode = None,
        client_databases: Dict[str, str] = None,
    ):
        """
        Initialize tenant database manager.
        
        Args:
            default_db: Default database session (used for SaaS mode)
            mode: Tenant mode (auto-detected from env if None)
            client_databases: Dict mapping client_id -> database_url (for on-premise)
        """
        self.default_db = default_db
        self.mode = mode or self._detect_mode()
        self._client_databases: Dict[str, AsyncSession] = {}
        self._client_engines: Dict[str, any] = {}
        self._client_sessions: Dict[str, async_sessionmaker] = {}
        
        # Load client database URLs
        if self.mode == TenantMode.ON_PREMISE:
            self.client_db_urls = client_databases or self._load_client_databases()
        else:
            self.client_db_urls = {}
    
    def _detect_mode(self) -> TenantMode:
        """
        Detect tenant mode (optional - not required for basic operation).
        
        Note: This is kept for future extensibility, but the system works
        without mode detection because both deployments use the same code.
        """
        # For now, always return SAAS (but code doesn't actually use this)
        # Both modes work the same way
        return TenantMode.SAAS
    
    def _load_client_databases(self) -> Dict[str, str]:
        """
        Load client database URLs for on-premise mode.
        
        Note: On-premise = one client per deployment.
        Uses DATABASE_URL from environment (same as default_db).
        This method is kept for future extensibility but not currently used.
        """
        # In unified design, on-premise uses default_db directly
        # (which is the client's database from DATABASE_URL)
        # This method is kept for future extensibility
        return {}
    
    async def get_database(self, client_id: str) -> AsyncSession:
        """
        Get database session (optional - standard get_db() works too).
        
        Note: This method just returns default_db. The system works the same
        way whether you use this class or standard get_db() dependency.
        
        Args:
            client_id: Client identifier (from JWT token)
            
        Returns:
            AsyncSession (same for both SaaS and on-premise)
        """
        # Both SaaS and on-premise use same database connection
        # Queries filter by client_id regardless of deployment model
        return self.default_db
    
    async def _create_client_session(self, client_id: str):
        """
        Create database session for a client (on-premise mode).
        
        Note: Not used in current implementation since on-premise
        uses default_db directly (one client per deployment).
        """
        # This method is kept for future extensibility
        # Currently, on-premise mode uses default_db directly
        pass
    
    async def close_client_sessions(self):
        """Close all client database sessions (cleanup)"""
        for client_id, session in self._client_databases.items():
            await session.close()
        
        for client_id, engine in self._client_engines.items():
            await engine.dispose()
        
        self._client_databases.clear()
        self._client_engines.clear()
        self._client_sessions.clear()
    
    def get_mode(self) -> TenantMode:
        """Get current tenant mode"""
        return self.mode
    
    def is_saas_mode(self) -> bool:
        """Check if running in SaaS mode"""
        return self.mode == TenantMode.SAAS
    
    def is_on_premise_mode(self) -> bool:
        """Check if running in on-premise mode"""
        return self.mode == TenantMode.ON_PREMISE

