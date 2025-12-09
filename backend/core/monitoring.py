"""
Performance Monitoring and Metrics

Tracks:
- Forecast generation metrics (count, duration, success/failure)
- Accuracy metrics (MAPE by classification)
- Method usage statistics
- Error rates
- Performance metrics (response times, resource usage)
"""

import logging
import time
import json
from datetime import datetime
from typing import Dict, Optional, Any
from contextlib import contextmanager
from functools import wraps

# Configure performance logger
performance_logger = logging.getLogger("performance")
performance_logger.setLevel(logging.INFO)

# Create handler if not exists
if not performance_logger.handlers:
    handler = logging.StreamHandler()
    # Use JSON formatter for structured logging
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    performance_logger.addHandler(handler)


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {
            "forecast_generation": {
                "total": 0,
                "success": 0,
                "failed": 0,
                "by_method": {},
                "durations": []
            },
            "accuracy": {
                "by_classification": {},
                "by_method": {}
            },
            "errors": {
                "by_type": {},
                "total": 0
            }
        }
    
    def log_forecast_generation(
        self,
        method: str,
        duration: float,
        success: bool,
        item_count: int = 1,
        client_id: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Log forecast generation event"""
        self.metrics["forecast_generation"]["total"] += 1
        
        if success:
            self.metrics["forecast_generation"]["success"] += 1
        else:
            self.metrics["forecast_generation"]["failed"] += 1
            if error:
                error_type = type(error).__name__ if isinstance(error, Exception) else str(error)
                self.metrics["errors"]["by_type"][error_type] = \
                    self.metrics["errors"]["by_type"].get(error_type, 0) + 1
                self.metrics["errors"]["total"] += 1
        
        # Track by method
        if method not in self.metrics["forecast_generation"]["by_method"]:
            self.metrics["forecast_generation"]["by_method"][method] = {
                "total": 0,
                "success": 0,
                "failed": 0,
                "avg_duration": 0.0,
                "durations": []
            }
        
        method_metrics = self.metrics["forecast_generation"]["by_method"][method]
        method_metrics["total"] += 1
        if success:
            method_metrics["success"] += 1
        else:
            method_metrics["failed"] += 1
        
        method_metrics["durations"].append(duration)
        # Keep only last 100 durations for rolling average
        if len(method_metrics["durations"]) > 100:
            method_metrics["durations"] = method_metrics["durations"][-100:]
        
        method_metrics["avg_duration"] = sum(method_metrics["durations"]) / len(method_metrics["durations"])
        self.metrics["forecast_generation"]["durations"].append(duration)
        
        # Log structured event
        event = {
            "event_type": "forecast_generation",
            "timestamp": datetime.utcnow().isoformat(),
            "method": method,
            "duration_seconds": round(duration, 3),
            "success": success,
            "item_count": item_count,
            "client_id": client_id,
        }
        
        if error:
            event["error"] = str(error)
            event["error_type"] = type(error).__name__ if isinstance(error, Exception) else "Unknown"
        
        performance_logger.info(json.dumps(event))
    
    def log_accuracy(
        self,
        classification: str,
        method: str,
        mape: float,
        mae: Optional[float] = None,
        rmse: Optional[float] = None,
        item_id: Optional[str] = None
    ):
        """Log forecast accuracy metrics"""
        # Track by classification
        if classification not in self.metrics["accuracy"]["by_classification"]:
            self.metrics["accuracy"]["by_classification"][classification] = {
                "mape_values": [],
                "mae_values": [],
                "rmse_values": [],
                "count": 0
            }
        
        class_metrics = self.metrics["accuracy"]["by_classification"][classification]
        class_metrics["mape_values"].append(mape)
        if mae is not None:
            class_metrics["mae_values"].append(mae)
        if rmse is not None:
            class_metrics["rmse_values"].append(rmse)
        class_metrics["count"] += 1
        
        # Keep only last 100 values
        if len(class_metrics["mape_values"]) > 100:
            class_metrics["mape_values"] = class_metrics["mape_values"][-100:]
            class_metrics["mae_values"] = class_metrics["mae_values"][-100:] if class_metrics["mae_values"] else []
            class_metrics["rmse_values"] = class_metrics["rmse_values"][-100:] if class_metrics["rmse_values"] else []
        
        # Track by method
        if method not in self.metrics["accuracy"]["by_method"]:
            self.metrics["accuracy"]["by_method"][method] = {
                "mape_values": [],
                "count": 0
            }
        
        method_metrics = self.metrics["accuracy"]["by_method"][method]
        method_metrics["mape_values"].append(mape)
        method_metrics["count"] += 1
        
        if len(method_metrics["mape_values"]) > 100:
            method_metrics["mape_values"] = method_metrics["mape_values"][-100:]
        
        # Log structured event
        event = {
            "event_type": "forecast_accuracy",
            "timestamp": datetime.utcnow().isoformat(),
            "classification": classification,
            "method": method,
            "mape": round(mape, 2),
            "item_id": item_id,
        }
        
        if mae is not None:
            event["mae"] = round(mae, 2)
        if rmse is not None:
            event["rmse"] = round(rmse, 2)
        
        performance_logger.info(json.dumps(event))
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary"""
        summary = {
            "forecast_generation": {
                "total": self.metrics["forecast_generation"]["total"],
                "success": self.metrics["forecast_generation"]["success"],
                "failed": self.metrics["forecast_generation"]["failed"],
                "success_rate": (
                    self.metrics["forecast_generation"]["success"] / 
                    self.metrics["forecast_generation"]["total"] * 100
                    if self.metrics["forecast_generation"]["total"] > 0 else 0
                ),
                "avg_duration": (
                    sum(self.metrics["forecast_generation"]["durations"]) / 
                    len(self.metrics["forecast_generation"]["durations"])
                    if self.metrics["forecast_generation"]["durations"] else 0
                ),
                "by_method": {}
            },
            "accuracy": {
                "by_classification": {},
                "by_method": {}
            },
            "errors": {
                "total": self.metrics["errors"]["total"],
                "by_type": self.metrics["errors"]["by_type"]
            }
        }
        
        # Calculate method summaries
        for method, method_metrics in self.metrics["forecast_generation"]["by_method"].items():
            summary["forecast_generation"]["by_method"][method] = {
                "total": method_metrics["total"],
                "success": method_metrics["success"],
                "failed": method_metrics["failed"],
                "success_rate": (
                    method_metrics["success"] / method_metrics["total"] * 100
                    if method_metrics["total"] > 0 else 0
                ),
                "avg_duration": round(method_metrics["avg_duration"], 3)
            }
        
        # Calculate accuracy summaries
        for classification, class_metrics in self.metrics["accuracy"]["by_classification"].items():
            if class_metrics["mape_values"]:
                summary["accuracy"]["by_classification"][classification] = {
                    "count": class_metrics["count"],
                    "avg_mape": round(sum(class_metrics["mape_values"]) / len(class_metrics["mape_values"]), 2),
                    "min_mape": round(min(class_metrics["mape_values"]), 2),
                    "max_mape": round(max(class_metrics["mape_values"]), 2)
                }
        
        for method, method_metrics in self.metrics["accuracy"]["by_method"].items():
            if method_metrics["mape_values"]:
                summary["accuracy"]["by_method"][method] = {
                    "count": method_metrics["count"],
                    "avg_mape": round(sum(method_metrics["mape_values"]) / len(method_metrics["mape_values"]), 2)
                }
        
        return summary


# Global instance
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    return _monitor


@contextmanager
def track_forecast_generation(method: str, item_count: int = 1, client_id: Optional[str] = None):
    """Context manager to track forecast generation performance"""
    start_time = time.time()
    error = None
    success = False
    
    try:
        yield
        success = True
    except Exception as e:
        error = e
        raise
    finally:
        duration = time.time() - start_time
        _monitor.log_forecast_generation(
            method=method,
            duration=duration,
            success=success,
            item_count=item_count,
            client_id=client_id,
            error=error
        )


def monitor_forecast_generation(method: str):
    """Decorator to monitor forecast generation"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            success = False
            item_count = kwargs.get("item_ids", [])
            if isinstance(item_count, list):
                item_count = len(item_count)
            else:
                item_count = 1
            
            client_id = kwargs.get("client_id")
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                _monitor.log_forecast_generation(
                    method=method,
                    duration=duration,
                    success=success,
                    item_count=item_count,
                    client_id=str(client_id) if client_id else None,
                    error=error
                )
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            success = False
            item_count = kwargs.get("item_ids", [])
            if isinstance(item_count, list):
                item_count = len(item_count)
            else:
                item_count = 1
            
            client_id = kwargs.get("client_id")
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                _monitor.log_forecast_generation(
                    method=method,
                    duration=duration,
                    success=success,
                    item_count=item_count,
                    client_id=str(client_id) if client_id else None,
                    error=error
                )
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

