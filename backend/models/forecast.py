from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
import uuid
from enum import Enum

from .database import Base


# ============================================================================
# Dialect-Aware Types
# ============================================================================

class GUID(TypeDecorator):
    """
    Platform-independent GUID type.
    Uses PostgreSQL's UUID when available, otherwise uses CHAR(36) for SQLite.
    """
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            # PostgreSQL expects UUID object or string
            if isinstance(value, uuid.UUID):
                return value
            # Try to convert string to UUID, but allow non-UUID strings for testing
            try:
                return uuid.UUID(value) if value else None
            except (ValueError, TypeError):
                # If not a valid UUID string, store as string (for testing with "test_client")
                return str(value)
        else:
            # SQLite stores as string
            if isinstance(value, uuid.UUID):
                return str(value)
            # For SQLite, always store as string (allows non-UUID strings for testing)
            return str(value)
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        # If already a UUID, return as-is
        if isinstance(value, uuid.UUID):
            return value
        # For SQLite, value is a string; for PostgreSQL, it might already be UUID
        if dialect.name == 'postgresql':
            # PostgreSQL returns UUID objects directly
            if isinstance(value, uuid.UUID):
                return value
            # If it's a string, convert it
            try:
                return uuid.UUID(value) if value else None
            except (ValueError, TypeError):
                return value
        else:
            # SQLite returns strings
            try:
                return uuid.UUID(value) if value else None
            except (ValueError, TypeError):
                # If conversion fails, return as string (shouldn't happen, but be safe)
                return value


class JSONBType(TypeDecorator):
    """
    Platform-independent JSON type.
    Uses PostgreSQL's JSONB when available, otherwise uses JSON for SQLite.
    """
    impl = String
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            # SQLite uses JSON (which is stored as TEXT)
            from sqlalchemy import JSON
            return dialect.type_descriptor(JSON())

# ============================================================================
# ENUMS
# ============================================================================

class ForecastStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

# ============================================================================
# FORECAST MODELS
# ============================================================================

class ForecastRun(Base):
    """Tracks forecast execution metadata and configuration"""
    __tablename__ = "forecast_runs"
    
    forecast_run_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)  # Keep String for FK compatibility
    
    # Configuration
    primary_model = Column(String(50), nullable=False, default="chronos-2")
    prediction_length = Column(Integer, nullable=False)
    item_ids = Column(JSONBType())  # JSONB in PostgreSQL, JSON in SQLite
    
    # Results
    recommended_method = Column(String(50))  # Best method used
    status = Column(String(20), nullable=False, default=ForecastStatus.PENDING.value)
    error_message = Column(Text)
    
    # Audit trail (data flow documentation)
    audit_metadata = Column(JSONBType(), nullable=True)  # Stores IN->OUT->COMPARISON audit trail
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ForecastResult(Base):
    """Stores daily forecast outputs from each method"""
    __tablename__ = "forecast_results"
    
    result_id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    forecast_run_id = Column(GUID(), ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    client_id = Column(GUID(), nullable=False, index=True)
    
    # What
    item_id = Column(String(255), nullable=False, index=True)
    method = Column(String(50), nullable=False)  # 'chronos-2' or 'statistical_ma7'
    
    # When
    date = Column(Date, nullable=False)
    horizon_day = Column(Integer, nullable=False)  # 1, 2, 3... days ahead
    
    # Predictions
    point_forecast = Column(Numeric(18, 2), nullable=False)  # Main prediction
    p10 = Column(Numeric(18, 2))  # 10th percentile (lower)
    p50 = Column(Numeric(18, 2))  # 50th percentile (median)
    p90 = Column(Numeric(18, 2))  # 90th percentile (upper)
    
    # Actuals (filled later)
    actual_value = Column(Numeric(18, 2))  # Real sales (backfilled)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SKUClassification(Base):
    """Stores ABC-XYZ classification for SKUs"""
    __tablename__ = "sku_classifications"
    
    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    client_id = Column(GUID(), nullable=False, index=True)
    item_id = Column(String(255), nullable=False, index=True)
    
    # ABC-XYZ Classification
    abc_class = Column(String(1), nullable=False)  # A, B, or C
    xyz_class = Column(String(1), nullable=False)  # X, Y, or Z
    
    # Demand Pattern
    demand_pattern = Column(String(50), nullable=False)  # regular, intermittent, lumpy, seasonal
    
    # Metrics
    coefficient_of_variation = Column(Numeric(10, 4), nullable=False)
    average_demand_interval = Column(Numeric(10, 4), nullable=False)
    revenue_contribution = Column(Numeric(10, 4))  # Percentage of total revenue
    
    # Forecasting
    forecastability_score = Column(Numeric(5, 4), nullable=False)  # 0.0 to 1.0
    recommended_method = Column(String(50), nullable=False)
    expected_mape_min = Column(Numeric(5, 2))
    expected_mape_max = Column(Numeric(5, 2))
    
    # Metadata
    classification_date = Column(DateTime(timezone=True), server_default=func.now())
    history_days_used = Column(Integer)
    classification_metadata = Column(JSONBType(), nullable=True)  # Additional metadata (warnings, etc.)

