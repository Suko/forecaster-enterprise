"""
Data Audit Logger - Tracks data flow for investigation

Documents: IN (raw data) -> Model -> OUT (predictions) -> Comparison (actuals)
Follows ML observability best practices.
"""
import json
import logging
from typing import Dict, Optional, Any, List
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

logger = logging.getLogger(__name__)


class DataAuditLogger:
    """Log data transformations for audit and debugging"""

    def __init__(self, db: AsyncSession, forecast_run_id: Optional[str] = None):
        self.db = db
        self.forecast_run_id = forecast_run_id
        self.audit_trail: List[Dict[str, Any]] = []

    def log_data_input(
        self,
        item_id: str,
        context_df: pd.DataFrame,
        method: str,
        validation_report: Dict[str, Any],
    ) -> None:
        """Log data sent to model (IN)"""
        audit_entry = {
            "stage": "INPUT",
            "item_id": item_id,
            "method": method,
            "timestamp": datetime.utcnow().isoformat(),
            "data_summary": {
                "row_count": len(context_df),
                "date_range": {
                    "start": str(context_df["timestamp"].min().date()) if len(context_df) > 0 else None,
                    "end": str(context_df["timestamp"].max().date()) if len(context_df) > 0 else None,
                },
                "target_stats": {
                    "mean": float(pd.to_numeric(context_df["target"], errors='coerce').mean()) if len(context_df) > 0 else None,
                    "std": float(pd.to_numeric(context_df["target"], errors='coerce').std()) if len(context_df) > 0 else None,
                    "min": float(pd.to_numeric(context_df["target"], errors='coerce').min()) if len(context_df) > 0 else None,
                    "max": float(pd.to_numeric(context_df["target"], errors='coerce').max()) if len(context_df) > 0 else None,
                },
                "columns": list(context_df.columns),
            },
            "validation": validation_report,
        }

        self.audit_trail.append(audit_entry)
        logger.info(f"Data INPUT logged for {item_id} ({method}): {len(context_df)} rows")

    def log_model_output(
        self,
        item_id: str,
        predictions_df: pd.DataFrame,
        method: str,
        validation_report: Dict[str, Any],
    ) -> None:
        """Log predictions from model (OUT)"""
        audit_entry = {
            "stage": "OUTPUT",
            "item_id": item_id,
            "method": method,
            "timestamp": datetime.utcnow().isoformat(),
            "predictions_summary": {
                "count": len(predictions_df),
                "date_range": {
                    "start": str(predictions_df["timestamp"].min().date()) if len(predictions_df) > 0 else None,
                    "end": str(predictions_df["timestamp"].max().date()) if len(predictions_df) > 0 else None,
                },
                "forecast_stats": {
                    "mean": float(predictions_df["point_forecast"].mean()) if len(predictions_df) > 0 else None,
                    "min": float(predictions_df["point_forecast"].min()) if len(predictions_df) > 0 else None,
                    "max": float(predictions_df["point_forecast"].max()) if len(predictions_df) > 0 else None,
                },
            },
            "validation": validation_report,
        }

        self.audit_trail.append(audit_entry)
        logger.info(f"Model OUTPUT logged for {item_id} ({method}): {len(predictions_df)} predictions")

    def log_comparison(
        self,
        item_id: str,
        actuals: List[float],
        forecasts: List[float],
        dates: List[date],
        metrics: Dict[str, float],
    ) -> None:
        """Log comparison of predictions vs actuals"""
        audit_entry = {
            "stage": "COMPARISON",
            "item_id": item_id,
            "timestamp": datetime.utcnow().isoformat(),
            "comparison_summary": {
                "sample_size": len(actuals),
                "date_range": {
                    "start": str(min(dates)) if dates else None,
                    "end": str(max(dates)) if dates else None,
                },
                "metrics": metrics,
            },
        }

        self.audit_trail.append(audit_entry)
        logger.info(f"COMPARISON logged for {item_id}: MAPE={metrics.get('mape', 'N/A')}%")

    def get_audit_trail(self) -> List[Dict[str, Any]]:
        """Get complete audit trail"""
        return self.audit_trail

    def save_audit_trail(self, filepath: Optional[str] = None) -> str:
        """Save audit trail to JSON file"""
        if filepath is None:
            filepath = f"audit_trail_{self.forecast_run_id or 'unknown'}.json"

        with open(filepath, 'w') as f:
            json.dump(self.audit_trail, f, indent=2, default=str)

        return filepath

