from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Request

from models import User
from auth import create_access_token
from services.user_service import authenticate_user, create_user as create_user_service
from auth.security_logger import (
    log_login_success,
    log_login_failure,
    log_rate_limit,
)


async def login_user(
    request: Request,
    db: AsyncSession,
    email: str,
    password: str
) -> dict:
    """Authenticate user and return access token"""
    user = await authenticate_user(db, email, password)
    
    if not user:
        log_login_failure(request, email=email, reason="Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        log_login_failure(request, email=email, reason="Account inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token with client_id for multi-tenant architecture
    token_data = {"sub": user.email}
    if user.client_id:
        token_data["client_id"] = str(user.client_id)
    
    access_token = create_access_token(data=token_data)
    
    # Log successful login
    log_login_success(request, email=user.email)
    
    return {"access_token": access_token, "token_type": "bearer"}


async def register_user(
    request: Request,
    db: AsyncSession,
    user_data
):
    """Register a new user"""
    try:
        user = await create_user_service(db, user_data)
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
