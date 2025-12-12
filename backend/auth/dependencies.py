from fastapi import Depends, HTTPException, status, Request
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models import get_db, User
from models.client import Client
from .jwt import decode_token


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from Authorization header.
    Only accepts Bearer tokens via Authorization header for security.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Get token from Authorization header only
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.split(" ")[1]
    if not token:
        raise credentials_exception

    try:
        # Decode and validate token (expects access token type)
        payload = decode_token(token, expected_type="access")
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def get_client_id_from_token(request: Request) -> str | None:
    """
    Extract client_id from JWT token.
    Used for unified multi-tenant architecture (SaaS and on-premise).

    Returns:
        client_id as string (UUID)

    Raises:
        HTTPException: If token is invalid or client_id is missing
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise credentials_exception

    token = authorization.split(" ")[1]
    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token, expected_type="access")
        client_id = payload.get("client_id")
        if client_id is None:
            # Fallback: get from user if client_id not in token
            # This allows gradual migration
            email = payload.get("sub")
            if email:
                # Will be resolved in get_current_user
                return None
        return str(client_id)
    except JWTError:
        raise credentials_exception


async def get_current_client(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Client:
    """
    Dependency to get the current client from JWT token or user.
    Returns the Client object for the authenticated user.
    """
    # Get client_id from user (user is already authenticated)
    if not current_user.client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have a client_id assigned"
        )

    client_id = current_user.client_id

    # Fetch client from database
    result = await db.execute(select(Client).filter(Client.client_id == client_id))
    client = result.scalar_one_or_none()

    if client is None or not client.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found or inactive"
        )

    return client


async def require_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency to require admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
