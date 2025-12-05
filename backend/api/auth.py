from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List

from models import get_db, User, UserRole
from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    require_admin,
)
from auth.security_logger import (
    log_login_success,
    log_login_failure,
    log_rate_limit,
)
from config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

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
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_minute} requests per minute"
        )
    
    # Check per-hour limit
    hour_ago = now - timedelta(hours=1)
    recent_hour = [ts for ts in _rate_limit_storage[client_id] if ts > hour_ago]
    if len(recent_hour) >= settings.rate_limit_per_hour:
        raise RateLimitExceeded(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {settings.rate_limit_per_hour} requests per hour"
        )
    
    # Record this request
    _rate_limit_storage[client_id].append(now)

# Password validation constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 72  # bcrypt limit


def validate_password(password: str) -> None:
    """
    Validate password meets security requirements.
    Raises ValueError with descriptive message if validation fails.
    """
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long")
    if len(password) > MAX_PASSWORD_LENGTH:
        raise ValueError(f"Password must be no more than {MAX_PASSWORD_LENGTH} characters long")


# Request/Response models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password on model creation"""
        validate_password(v)
        return v


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
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
    
    # Find user by email (OAuth2PasswordRequestForm uses 'username' field for email)
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        # Log failed login attempt
        log_login_failure(request, email=form_data.username, reason="Invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        # Log failed login attempt (inactive account)
        log_login_failure(request, email=form_data.username, reason="Account inactive")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    # Log successful login
    log_login_success(request, email=user.email)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    Rate limited to prevent abuse
    Password validation: 8-72 characters (bcrypt limit)
    """
    # Check rate limits
    check_rate_limit(request)
    # Password validation is handled by Pydantic model validator
    # Additional explicit check for clarity
    try:
        validate_password(user_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    """
    return current_user


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class UserUpdateRole(BaseModel):
    role: str


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only)
    """
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user (admin only)
    """
    check_rate_limit(request)
    
    try:
        validate_password(user_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        name=user_data.name,
        hashed_password=hashed_password,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update user (admin only)
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.role is not None:
        if user_data.role not in [UserRole.ADMIN.value, UserRole.USER.value]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role"
            )
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete user (admin only)
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db.delete(user)
    db.commit()
    
    return None

