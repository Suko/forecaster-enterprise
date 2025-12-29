# Logging Strategy & Implementation Guide

**Version:** 1.0
**Last Updated:** 2025-12-29
**Status:** Implementation Guide

---

## Executive Summary

This document defines the **enterprise logging strategy** for Forecaster Enterprise, covering implementation patterns, configuration standards, and production requirements. The strategy ensures observability, debugging capabilities, and operational monitoring across all environments.

**Key Principles:**
- **Structured logging** for machine readability
- **Business context** in all log entries
- **Multi-level logging** (security, performance, application)
- **Production-ready** configuration and monitoring

---

## 1. Current Implementation Analysis

### 1.1 Existing Logging Infrastructure

#### Backend Logging Layers

**🔐 Security Logger** (`security_logger`)
```python
# Dedicated security event logging
security_logger = logging.getLogger("security")
# JSON structured format for SIEM integration
# Captures: authentication, authorization, admin actions
```

**📈 Performance Logger** (`performance_logger`)
```python
# Performance metrics and forecasting accuracy
performance_logger = logging.getLogger("performance")
# JSON structured with timestamps and business context
# Tracks: forecast generation, accuracy metrics, method performance
```

**🏗️ Application Logger** (Module-based)
```python
# Standard Python logging across all modules
logger = logging.getLogger(__name__)
# Levels: DEBUG, INFO, WARNING, ERROR
# Context: Business operations, errors, warnings
```

#### Frontend Logging
```typescript
// Sentry integration (partial setup)
// Machine ID tagging
// Error boundaries and performance monitoring
```

### 1.2 Current Strengths

✅ **Security logging** - Comprehensive, structured, SIEM-ready
✅ **Performance tracking** - Detailed metrics with business context
✅ **Consistent patterns** - All modules use `logging.getLogger(__name__)`
✅ **Multi-tenant awareness** - Client context in logs where applicable
✅ **Error correlation** - Request IDs and business context

### 1.3 Current Gaps

❌ **No central configuration** - Relies on Python logging defaults
❌ **Inconsistent formats** - Mix of JSON and plain text
❌ **No production setup** - No log rotation, aggregation, or external monitoring
❌ **Limited observability** - No request tracing or distributed logging
❌ **No alerting strategy** - No defined thresholds or escalation paths

---

## 2. Logging Configuration Standards

### 2.1 Environment Variables

```bash
# Core Logging Configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT=json                   # json or text
LOG_FILE=/var/log/forecaster.log  # Optional file output

# Sentry Integration (when implemented)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.1

# Security Logging
SECURITY_LOG_FILE=/var/log/security.log
SECURITY_LOG_FORMAT=json

# Performance Logging
PERFORMANCE_LOG_FILE=/var/log/performance.log
PERFORMANCE_LOG_FORMAT=json

# Application Logging
APP_LOG_FILE=/var/log/application.log
APP_LOG_FORMAT=json
```

### 2.2 Configuration Implementation

#### Backend Configuration (`config.py`)

```python
class Settings(BaseSettings):
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    log_file: Optional[str] = os.getenv("LOG_FILE")

    # Security logging
    security_log_file: Optional[str] = os.getenv("SECURITY_LOG_FILE")
    security_log_format: str = os.getenv("SECURITY_LOG_FORMAT", "json")

    # Performance logging
    performance_log_file: Optional[str] = os.getenv("PERFORMANCE_LOG_FILE")
    performance_log_format: str = os.getenv("PERFORMANCE_LOG_FORMAT", "json")

    # Application logging
    app_log_file: Optional[str] = os.getenv("APP_LOG_FILE")
    app_log_format: str = os.getenv("APP_LOG_FORMAT", "json")

    def model_post_init(self, __context) -> None:
        # Validate log levels
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of: {valid_levels}")

        # Validate formats
        if self.log_format not in ["json", "text"]:
            raise ValueError("LOG_FORMAT must be 'json' or 'text'")
```

#### Logging Setup (`main.py`)

```python
import logging
import json
from pythonjsonlogger import jsonlogger  # pip install python-json-logger

def setup_logging(settings: Settings):
    """Configure all logging for the application"""

    # Base configuration
    log_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {},
        'handlers': {},
        'loggers': {},
        'root': {
            'level': settings.log_level,
            'handlers': ['console']
        }
    }

    # JSON Formatter
    if settings.log_format == "json":
        log_config['formatters']['json'] = {
            'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        }
    else:
        log_config['formatters']['text'] = {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }

    # Console Handler
    log_config['handlers']['console'] = {
        'class': 'logging.StreamHandler',
        'formatter': settings.log_format,
        'level': settings.log_level
    }

    # File Handler (optional)
    if settings.log_file:
        log_config['handlers']['file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': settings.log_file,
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': settings.log_format,
            'level': settings.log_level
        }
        log_config['root']['handlers'].append('file')

    # Security Logger Configuration
    log_config['loggers']['security'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False
    }
    if settings.security_log_file:
        log_config['handlers']['security_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': settings.security_log_file,
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'json' if settings.security_log_format == "json" else 'text',
            'level': 'INFO'
        }
        log_config['loggers']['security']['handlers'].append('security_file')

    # Performance Logger Configuration
    log_config['loggers']['performance'] = {
        'level': 'INFO',
        'handlers': ['console'],
        'propagate': False
    }
    if settings.performance_log_file:
        log_config['handlers']['performance_file'] = {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': settings.performance_log_file,
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'json' if settings.performance_log_format == "json" else 'text',
            'level': 'INFO'
        }
        log_config['loggers']['performance']['handlers'].append('performance_file')

    # Apply configuration
    logging.config.dictConfig(log_config)

# Initialize logging before app creation
setup_logging(settings)

# Create FastAPI app after logging setup
app = FastAPI(...)
```

### 2.3 Environment-Specific Configurations

#### Development
```bash
LOG_LEVEL=DEBUG
LOG_FORMAT=text
LOG_FILE=/dev/null  # Console only
# Sentry automatically disabled in development
# SENTRY_DSN will be ignored even if set
```
**Note:** Sentry is automatically disabled in development environments (`development`, `dev`, `local`) to avoid noise from development errors and prevent mixing development issues with production monitoring.

#### Staging
```bash
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/forecaster/staging.log
SENTRY_ENVIRONMENT=staging
SENTRY_TRACES_SAMPLE_RATE=0.1
```

#### Production
```bash
LOG_LEVEL=WARNING  # Only warnings and errors to console
LOG_FORMAT=json
LOG_FILE=/var/log/forecaster/production.log
SECURITY_LOG_FILE=/var/log/forecaster/security.log
PERFORMANCE_LOG_FILE=/var/log/forecaster/performance.log
SENTRY_ENVIRONMENT=production
SENTRY_TRACES_SAMPLE_RATE=0.2
```

---

## 3. Logging Implementation Patterns

### 3.1 Log Levels Usage Guide

#### DEBUG
```python
# Development troubleshooting only
logger.debug("Processing item %s with %d data points", item_id, len(data))
logger.debug("SQL Query: %s", query)
logger.debug("API response headers: %s", dict(response.headers))
```

#### INFO
```python
# Business operations and milestones
logger.info("Forecast generation started for client %s, %d items",
           client_id, len(item_ids))
logger.info("User %s logged in successfully", user_email)
logger.info("Data validation completed: %d passed, %d failed", passed, failed)
```

#### WARNING
```python
# Non-critical issues that should be monitored
logger.warning("Slow query detected: %s took %.2fs", query, duration)
logger.warning("Rate limit approaching: %d/%d requests", current, limit)
logger.warning("Forecast accuracy below threshold: MAPE=%.1f%%", mape)
```

#### ERROR
```python
# Application errors requiring attention
logger.error("Forecast generation failed for client %s: %s", client_id, str(e))
logger.error("Database connection lost, attempting reconnection")
logger.exception("Unexpected error in inventory calculation")  # Includes traceback
```

#### CRITICAL
```python
# System-threatening issues
logger.critical("Database completely unavailable")
logger.critical("License validation failed - system shutdown imminent")
```

### 3.2 Structured Logging Format

#### JSON Format Standard
```json
{
  "timestamp": "2025-12-29T10:30:45.123Z",
  "level": "INFO",
  "logger": "forecasting.services.forecast_service",
  "message": "Forecast generation completed",
  "client_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user123",
  "operation": "forecast_generation",
  "item_count": 25,
  "duration_seconds": 12.5,
  "method": "chronos-2",
  "success": true
}
```

#### Business Context Fields
```python
# Always include when available
context = {
    "client_id": client_id,           # Multi-tenant isolation
    "user_id": user_id,              # User actions
    "operation": "forecast_generate", # Business operation
    "item_id": item_id,              # Specific resource
    "request_id": request_id,        # Request correlation
    "session_id": session_id,        # User session
    "ip_address": ip_address,        # Client IP
    "user_agent": user_agent,        # Browser/client info
}
```

### 3.3 Security Event Logging

#### Authentication Events
```python
from auth.security_logger import log_login_success, log_login_failure

# Successful login
log_login_success(request, email)

# Failed login
log_login_failure(request, email, "Invalid password")

# Rate limiting
log_rate_limit(request, email)
```

#### Authorization Events
```python
logger.info("Access granted: user %s accessed %s for client %s",
           user_id, resource, client_id)

logger.warning("Access denied: user %s attempted to access %s for client %s",
              user_id, resource, client_id)
```

#### Data Access Events
```python
logger.info("Data export initiated: user %s exported %d records for client %s",
           user_id, record_count, client_id)

logger.warning("Large data query: user %s queried %d records in %.2fs",
              user_id, record_count, duration)
```

### 3.4 Performance Logging

#### Forecast Operations
```python
from core.monitoring import track_forecast_generation

@track_forecast_generation("chronos-2")
async def generate_forecast(...):
    # Function automatically logs performance metrics
    pass
```

#### Custom Performance Events
```python
from core.monitoring import get_monitor

monitor = get_monitor()
monitor.log_forecast_generation(
    method="chronos-2",
    duration=12.5,
    success=True,
    item_count=25,
    client_id=client_id,
    error=None
)
```

#### Database Performance
```python
start_time = time.time()
result = await db.execute(query)
duration = time.time() - start_time

if duration > 1.0:  # Log slow queries
    logger.warning("Slow database query: %.2fs - %s", duration, query)
```

### 3.5 Error Context and Correlation

#### Request Correlation
```python
import uuid

@app.middleware("http")
async def add_request_context(request: Request, call_next):
    request_id = str(uuid.uuid4())
    # Add to request state for use in handlers
    request.state.request_id = request_id

    # Add to logging context
    logging_context = {
        "request_id": request_id,
        "method": request.method,
        "url": str(request.url),
        "client_ip": get_client_ip(request),
    }

    # Structured logging with context
    logger.info("Request started", extra=logging_context)

    try:
        response = await call_next(request)
        logger.info("Request completed", extra={
            **logging_context,
            "status_code": response.status_code,
            "duration": time.time() - start_time
        })
        return response
    except Exception as e:
        logger.error("Request failed", extra={
            **logging_context,
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise
```

#### Exception Handling
```python
try:
    result = await forecast_service.generate_forecast(...)
except Exception as e:
    logger.error("Forecast generation failed: %s", str(e), extra={
        "client_id": client_id,
        "user_id": user_id,
        "item_count": len(item_ids),
        "operation": "forecast_generation",
        "error_type": type(e).__name__,
        "error_details": {
            "traceback": traceback.format_exc(),
            "context": "User initiated forecast generation"
        }
    }, exc_info=True)
    raise
```

---

## 4. Production Requirements

### 4.1 Log Rotation and Retention

#### File Rotation Configuration
```python
# In logging setup
'handlers': {
    'application_file': {
        'class': 'logging.handlers.TimedRotatingFileHandler',
        'filename': '/var/log/forecaster/application.log',
        'when': 'midnight',  # Rotate daily
        'backupCount': 30,   # Keep 30 days
        'formatter': 'json',
    }
}
```

#### Retention Policies
- **Application logs**: 30 days
- **Security logs**: 90 days (compliance requirement)
- **Performance logs**: 90 days
- **Error logs**: 90 days
- **Audit logs**: 7 years (as per contracts)

### 4.2 Log Aggregation and Monitoring

#### ELK Stack Setup
```yaml
# docker-compose.yml for ELK
version: '3.8'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

#### Logstash Configuration
```conf
input {
  file {
    path => "/var/log/forecaster/*.log"
    codec => "json"
    type => "forecaster"
  }
}

filter {
  if [type] == "forecaster" {
    # Parse timestamp
    date {
      match => ["timestamp", "ISO8601"]
      target => "@timestamp"
    }

    # Add geoip for client IPs
    if [client_ip] {
      geoip {
        source => "client_ip"
        target => "geoip"
      }
    }

    # Extract error patterns
    if [level] == "ERROR" or [level] == "CRITICAL" {
      grok {
        match => { "message" => "%{DATA:error_type}: %{GREEDYDATA:error_message}" }
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "forecaster-%{+YYYY.MM.dd}"
  }
}
```

### 4.3 Alerting and Monitoring

#### Alert Thresholds
```yaml
# Prometheus Alert Rules
groups:
  - name: forecaster_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | printf "%.2f" }}%"

      - alert: SlowForecastGeneration
        expr: histogram_quantile(0.95, rate(forecast_generation_duration_bucket[5m])) > 60
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow forecast generation"
          description: "95th percentile forecast time is {{ $value | printf "%.1f" }}s"

      - alert: FailedLoginSpike
        expr: increase(login_failures_total[5m]) > 5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Multiple failed login attempts"
          description: "{{ $value }} failed logins in 5 minutes"
```

#### Dashboard Setup
- **Error Rate Dashboard**: Track errors by endpoint, client, time
- **Performance Dashboard**: Response times, forecast accuracy, resource usage
- **Security Dashboard**: Failed logins, suspicious activities, access patterns
- **Business Metrics**: Forecast usage, client activity, system health

---

## 5. Testing and Validation

### 5.1 Log Output Testing

#### Unit Tests for Logging
```python
import pytest
from unittest.mock import patch, MagicMock

def test_forecast_logging():
    """Test that forecast operations are properly logged"""
    with patch('forecasting.services.forecast_service.logger') as mock_logger:
        # Execute forecast operation
        result = await forecast_service.generate_forecast(...)

        # Verify logging calls
        mock_logger.info.assert_called_with(
            "Forecast generation completed",
            extra={
                "client_id": "test_client",
                "item_count": 10,
                "duration": pytest.approx(5.0, abs=1.0)
            }
        )
```

#### Log Format Validation
```python
def test_json_log_format():
    """Test that logs are properly formatted as JSON"""
    import json

    # Capture log output
    with capture_logs() as logs:
        logger.info("Test message", extra={"client_id": "123"})

    # Parse and validate JSON
    log_entry = json.loads(logs[0])
    assert "timestamp" in log_entry
    assert log_entry["level"] == "INFO"
    assert log_entry["client_id"] == "123"
```

### 5.2 Integration Testing

#### End-to-End Log Flow
```python
def test_complete_log_flow():
    """Test logs flow from application to monitoring system"""
    # 1. Generate application activity
    # 2. Verify logs written to files
    # 3. Verify logs ingested by log aggregation
    # 4. Verify alerts trigger appropriately
    # 5. Verify dashboard displays correct data
```

#### Performance Impact Testing
```python
def test_logging_performance():
    """Ensure logging doesn't significantly impact performance"""
    import time

    # Measure time with logging enabled
    start = time.time()
    for _ in range(1000):
        logger.info("Performance test message")
    with_logging = time.time() - start

    # Measure time with logging disabled
    # (Should be minimal difference)
    assert with_logging < without_logging * 1.1  # Max 10% overhead
```

---

## 6. Future Roadmap

### Phase 1: Enhanced Observability (Q1 2026)
- [ ] Implement distributed request tracing
- [ ] Add OpenTelemetry integration
- [ ] Create log correlation across services
- [ ] Implement log sampling for high-volume operations

### Phase 2: Advanced Monitoring (Q2 2026)
- [ ] Real-time alerting with PagerDuty integration
- [ ] Anomaly detection for performance metrics
- [ ] Predictive alerting for forecast accuracy degradation
- [ ] Automated incident response workflows

### Phase 3: Enterprise Features (Q3 2026)
- [ ] Compliance logging (SOX, GDPR, HIPAA)
- [ ] Advanced audit trails with data lineage
- [ ] Multi-region log aggregation
- [ ] AI-powered log analysis and insights

---

## Compliance

This logging strategy ensures compliance with:

1. ✅ **Data retention policies** (security logs: 90 days, audit logs: 7 years)
2. ✅ **Security event logging** (all authentication and authorization events)
3. ✅ **Performance monitoring** (response times and error rates)
4. ✅ **Business continuity** (comprehensive error tracking and alerting)
5. ✅ **Debugging capabilities** (structured logs with full context)

---

*This document serves as the central reference for all logging implementation and configuration across Forecaster Enterprise.*