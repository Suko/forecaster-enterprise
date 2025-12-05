from fastapi import Depends, HTTPException, status, Request
from jose import JWTError
from sqlalchemy.orm import Session

from models import get_db, User, UserRole
from .jwt import decode_token

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
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

