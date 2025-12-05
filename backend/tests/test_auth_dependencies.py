import pytest
from fastapi import HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import Mock, patch

from auth.dependencies import get_current_user, require_admin
from models.user import User, UserRole


@pytest.mark.asyncio
async def test_get_current_user_success(test_session: AsyncSession, test_user: User):
    """Test getting current user with valid token."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_user.email})
    mock_request = Mock()
    mock_request.headers = {"Authorization": f"Bearer {token}"}
    
    user = await get_current_user(mock_request, test_session)
    
    assert user is not None
    assert user.email == test_user.email
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_current_user_no_header(test_session: AsyncSession):
    """Test getting current user without Authorization header."""
    mock_request = Mock()
    mock_request.headers = {}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_request, test_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(test_session: AsyncSession):
    """Test getting current user with invalid token."""
    mock_request = Mock()
    mock_request.headers = {"Authorization": "Bearer invalid_token"}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_request, test_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive(test_session: AsyncSession, test_user: User):
    """Test getting current user with inactive account."""
    from auth import create_access_token
    
    test_user.is_active = False
    await test_session.commit()
    
    token = create_access_token(data={"sub": test_user.email})
    mock_request = Mock()
    mock_request.headers = {"Authorization": f"Bearer {token}"}
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(mock_request, test_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_admin_success(test_admin_user: User):
    """Test require_admin with admin user."""
    admin = await require_admin(test_admin_user)
    assert admin.role == UserRole.ADMIN.value


@pytest.mark.asyncio
async def test_require_admin_failure(test_user: User):
    """Test require_admin with non-admin user."""
    with pytest.raises(HTTPException) as exc_info:
        await require_admin(test_user)
    
    assert exc_info.value.status_code == 403
    assert "admin" in exc_info.value.detail.lower()

