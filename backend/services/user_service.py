from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status

from models import User, UserRole
from auth import get_password_hash, verify_password
from schemas.auth import UserCreate, UserUpdate, validate_password


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Get user by email"""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Get user by ID"""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[User]:
    """Get all users"""
    result = await db.execute(select(User))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """Create a new user"""
    # Validate password
    try:
        validate_password(user_data.password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
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
    await db.commit()
    await db.refresh(new_user)

    return new_user


async def update_user(db: AsyncSession, user_id: str, user_data: UserUpdate) -> User:
    """Update user"""
    user = await get_user_by_id(db, user_id)
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

    await db.commit()
    await db.refresh(user)

    return user


async def delete_user(db: AsyncSession, user_id: str, current_user_id: str) -> None:
    """Delete user"""
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    await db.delete(user)
    await db.commit()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate user with email and password"""
    user = await get_user_by_email(db, email)
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
