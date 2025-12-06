from sqlalchemy import Column, String, Integer, Date, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import JSONB
import uuid
from enum import Enum

from .database import Base

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
    
    forecast_run_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Configuration
    primary_model = Column(String(50), nullable=False, default="chronos-2")
    prediction_length = Column(Integer, nullable=False)
    item_ids = Column(JSONB)  # List of item IDs forecasted
    
    # Results
    recommended_method = Column(String(50))  # Best method used
    status = Column(String(20), nullable=False, default=ForecastStatus.PENDING.value)
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ForecastResult(Base):
    """Stores daily forecast outputs from each method"""
    __tablename__ = "forecast_results"
    
    result_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    forecast_run_id = Column(String, ForeignKey("forecast_runs.forecast_run_id"), nullable=False)
    client_id = Column(String, nullable=False, index=True)
    
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

