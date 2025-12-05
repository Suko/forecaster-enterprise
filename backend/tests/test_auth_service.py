import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock

from services.auth_service import login_user, register_user
from schemas.auth import UserCreate
from models.user import User


@pytest.mark.asyncio
async def test_login_user_success(test_session: AsyncSession, test_user: User, mock_request: Request):
    """Test successful user login."""
    result = await login_user(mock_request, test_session, test_user.email, "testpassword123")
    
    assert "access_token" in result
    assert "token_type" in result
    assert result["token_type"] == "bearer"
    assert len(result["access_token"]) > 0


@pytest.mark.asyncio
async def test_login_user_invalid_credentials(test_session: AsyncSession, test_user: User, mock_request: Request):
    """Test login with invalid password."""
    with pytest.raises(HTTPException) as exc_info:
        await login_user(mock_request, test_session, test_user.email, "wrongpassword")
    
    assert exc_info.value.status_code == 401
    assert "password" in exc_info.value.detail.lower() or "incorrect" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_login_user_inactive_account(test_session: AsyncSession, test_user: User, mock_request: Request):
    """Test login with inactive account."""
    test_user.is_active = False
    await test_session.commit()
    
    with pytest.raises(HTTPException) as exc_info:
        await login_user(mock_request, test_session, test_user.email, "testpassword123")
    
    assert exc_info.value.status_code == 403
    assert "inactive" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_login_user_not_found(test_session: AsyncSession, mock_request: Request):
    """Test login with non-existent user."""
    with pytest.raises(HTTPException) as exc_info:
        await login_user(mock_request, test_session, "nonexistent@example.com", "password")
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_register_user_success(test_session: AsyncSession, mock_request: Request):
    """Test successful user registration."""
    user_data = UserCreate(
        email="newuser@example.com",
        password="newpassword123",
        name="New User"
    )
    
    user = await register_user(mock_request, test_session, user_data)
    
    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.name == "New User"


@pytest.mark.asyncio
async def test_register_user_duplicate_email(test_session: AsyncSession, test_user: User, mock_request: Request):
    """Test registration with duplicate email."""
    user_data = UserCreate(
        email=test_user.email,
        password="password123",
        name="Duplicate"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await register_user(mock_request, test_session, user_data)
    
    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_register_user_short_password(test_session: AsyncSession, mock_request: Request):
    """Test registration with short password."""
    user_data = UserCreate(
        email="shortpass@example.com",
        password="short",
        name="Short Pass"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await register_user(mock_request, test_session, user_data)
    
    assert exc_info.value.status_code == 400

