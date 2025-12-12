from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from slowapi.errors import RateLimitExceeded

from models import get_db, User
from auth import get_current_user, require_admin
from auth.security_logger import log_rate_limit
from schemas.auth import Token, UserResponse, UserCreate, UserUpdate, UserPreferencesResponse, UserPreferencesUpdate
from services.auth_service import login_user, register_user
from services.user_service import (
    get_all_users,
    create_user,
    update_user,
    delete_user,
)
from core.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login endpoint - returns JWT access token
    Rate limited to prevent brute force attacks
    """
    # Check rate limits
    try:
        check_rate_limit(request)
    except RateLimitExceeded:
        # Log rate limit violation
        log_rate_limit(request, email=form_data.username)
        raise

    # OAuth2PasswordRequestForm uses 'username' field for email
    return await login_user(request, db, form_data.username, form_data.password)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    Rate limited to prevent abuse
    Password validation: 8-128 characters
    """
    # Check rate limits
    check_rate_limit(request)

    return await register_user(request, db, user_data)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    return current_user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (admin only)
    """
    return await get_all_users(db)


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new user (admin only)
    """
    check_rate_limit(request)
    return await create_user(db, user_data)


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user (admin only)
    """
    return await update_user(db, user_id, user_data)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    await delete_user(db, user_id, current_user.id)


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's preferences
    """
    return UserPreferencesResponse(preferences=current_user.preferences or {})


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_user_preferences(
    data: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's preferences
    """
    from sqlalchemy import select
    
    # Get fresh user from database
    result = await db.execute(
        select(User).where(User.id == current_user.id)
    )
    user = result.scalar_one()
    
    # Update preferences
    user.preferences = data.preferences or {}
    await db.commit()
    await db.refresh(user)
    
    return UserPreferencesResponse(preferences=user.preferences or {})
    return None
