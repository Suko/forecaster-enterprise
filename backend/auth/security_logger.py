"""
Security event logging utility for backend
Logs security-related events for audit purposes
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import Request

# Configure security logger
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Create handler if not exists
if not security_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxy headers"""
    # Check for forwarded IP (when behind proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP if multiple
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request"""
    return request.headers.get("User-Agent", "unknown")


def log_security_event(
    event_type: str,
    request: Request,
    email: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    success: bool = False
) -> None:
    """
    Log a security event
    
    Args:
        event_type: Type of event (login_success, login_failure, rate_limit, etc.)
        request: FastAPI Request object
        email: User email if available
        details: Additional event details
        success: Whether the event represents a success or failure
    """
    event_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "ip": get_client_ip(request),
        "user_agent": get_user_agent(request),
        "email": email,
        "success": success,
        "details": details or {},
    }
    
    # Log as structured JSON for easy parsing
    security_logger.info(f"SECURITY_EVENT: {event_data}")
    
    # In production, you might want to send to:
    # - CloudWatch Logs
    # - Elasticsearch
    # - Splunk
    # - Your SIEM system


def log_login_success(request: Request, email: str) -> None:
    """Log successful login"""
    log_security_event(
        event_type="login_success",
        request=request,
        email=email,
        success=True
    )


def log_login_failure(request: Request, email: Optional[str] = None, reason: Optional[str] = None) -> None:
    """Log failed login attempt"""
    log_security_event(
        event_type="login_failure",
        request=request,
        email=email,
        details={"reason": reason or "Invalid credentials"},
        success=False
    )


def log_rate_limit(request: Request, email: Optional[str] = None) -> None:
    """Log rate limit violation"""
    log_security_event(
        event_type="rate_limit",
        request=request,
        email=email,
        details={"limit_exceeded": True},
        success=False
    )


def log_auth_failure(request: Request, email: Optional[str] = None, reason: Optional[str] = None) -> None:
    """Log authentication failure (invalid token, etc.)"""
    log_security_event(
        event_type="auth_failure",
        request=request,
        email=email,
        details={"reason": reason or "Authentication failed"},
        success=False
    )


def log_unauthorized_access(request: Request, email: Optional[str] = None, endpoint: Optional[str] = None) -> None:
    """Log unauthorized access attempt"""
    log_security_event(
        event_type="unauthorized_access",
        request=request,
        email=email,
        details={"endpoint": endpoint or request.url.path},
        success=False
    )


