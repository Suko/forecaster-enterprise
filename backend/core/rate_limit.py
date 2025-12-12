from fastapi import Request
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

from config import settings

# Simple in-memory rate limiting storage
_rate_limit_storage: Dict[str, List[datetime]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    """Check if request exceeds rate limits"""
    if not settings.rate_limit_enabled:
        return

    client_id = get_remote_address(request)
    now = datetime.utcnow()

    # Clean old entries (older than 1 hour)
    _rate_limit_storage[client_id] = [
        ts for ts in _rate_limit_storage[client_id]
        if now - ts < timedelta(hours=1)
    ]

    # Check per-minute limit
    minute_ago = now - timedelta(minutes=1)
    recent_minute = [ts for ts in _rate_limit_storage[client_id] if ts > minute_ago]
    if len(recent_minute) >= settings.rate_limit_per_minute:
        raise RateLimitExceeded(
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests per minute"
        )

    # Check per-hour limit
    hour_ago = now - timedelta(hours=1)
    recent_hour = [ts for ts in _rate_limit_storage[client_id] if ts > hour_ago]
    if len(recent_hour) >= settings.rate_limit_per_hour:
        raise RateLimitExceeded(
            detail=f"Rate limit exceeded: {settings.rate_limit_per_hour} requests per hour"
        )

    # Record this request
    _rate_limit_storage[client_id].append(now)

