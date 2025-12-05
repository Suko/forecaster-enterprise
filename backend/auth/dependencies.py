from fastapi import Depends, HTTPException, status, Cookie, Request
from jose import JWTError
from sqlalchemy.orm import Session
from typing import Optional

from models import get_db, User, UserRole
from .jwt import decode_token

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    access_token: Optional[str] = Cookie(None)
) -> User:
    """
    Dependency to get the current authenticated user from cookie or Authorization header
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try to get token from Authorization header first
    token = None
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token:
        # Fallback to cookie
        token = access_token

    # No token found in either header or cookies
    if not token:
        raise credentials_exception

    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except (JWTError, Exception):
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user

async def require_admin(current_user: User = Depends(get_current_user)):
    """
    Dependency to require admin role
    """
    if current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

