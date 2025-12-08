"""
Service Authentication

Supports system/automated forecasts without JWT tokens.
Uses API key authentication for scheduled/background jobs.
"""
from fastapi import Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from models import get_db
from config import settings


async def get_service_token(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
) -> Optional[str]:
    """
    Extract service API key from header.
    
    Returns:
        API key if present, None otherwise
    """
    return x_api_key


async def verify_service_token(
    x_api_key: Optional[str] = Depends(get_service_token)
) -> bool:
    """
    Verify service API key.
    
    Returns:
        True if valid service token, False otherwise
    
    Raises:
        HTTPException: If token is invalid
    """
    if not x_api_key:
        return False
    
    # Get service API key from environment or config
    from config import settings
    valid_api_key = settings.service_api_key or os.getenv("SERVICE_API_KEY")
    
    if not valid_api_key:
        # Service auth not configured - reject
        return False
    
    # Constant-time comparison to prevent timing attacks
    if len(x_api_key) != len(valid_api_key):
        return False
    
    result = 0
    for a, b in zip(x_api_key, valid_api_key):
        result |= ord(a) ^ ord(b)
    
    return result == 0


async def get_client_id_from_request_or_token(
    request: Request,
    client_id: Optional[str] = None,  # From request body/query
    x_api_key: Optional[str] = Depends(get_service_token),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    Get client_id from multiple sources (unified multi-tenant).
    
    Priority:
    1. Request body/query parameter (for system calls)
    2. JWT token (for user calls)
    3. Service token (for automated calls - requires client_id in request)
    
    Args:
        request: FastAPI request
        client_id: Optional client_id from request
        x_api_key: Optional service API key
        db: Database session
    
    Returns:
        client_id as string
    
    Raises:
        HTTPException: If client_id cannot be determined
    """
    # Priority 1: Explicit client_id in request (for system/automated calls)
    if client_id:
        return client_id
    
    # Priority 2: Try JWT token (for user calls)
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        if token:
            try:
                from auth.jwt import decode_token
                from jose import JWTError
                payload = decode_token(token, expected_type="access")
                # Try to get client_id from token
                if "client_id" in payload:
                    return str(payload["client_id"])
                # Fallback: get from user
                email = payload.get("sub")
                if email:
                    from sqlalchemy import select
                    from models import User
                    result = await db.execute(select(User).filter(User.email == email))
                    user = result.scalar_one_or_none()
                    if user and user.client_id:
                        return str(user.client_id)
            except JWTError:
                pass  # Not a valid JWT, continue to service token
            except Exception:
                pass  # JWT auth failed, continue to service token
    
    # Priority 3: Service token (requires client_id in request)
    if x_api_key:
        is_valid = await verify_service_token(x_api_key)
        if is_valid:
            # Service token valid, but still need client_id
            if not client_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="client_id is required when using service API key"
                )
            return client_id
    
    # No valid authentication found
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide JWT token or valid service API key with client_id",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_optional_client_id(
    request: Request,
    client_id: Optional[str] = None,
    x_api_key: Optional[str] = Depends(get_service_token),
    db: AsyncSession = Depends(get_db),
) -> Optional[str]:
    """
    Get client_id if available, but don't require it.
    
    For client-agnostic endpoints (health checks, system status, etc.).
    
    Returns:
        client_id if available, None otherwise
    """
    try:
        return await get_client_id_from_request_or_token(request, client_id, x_api_key, db)
    except HTTPException:
        # No auth provided - that's OK for client-agnostic endpoints
        return None

