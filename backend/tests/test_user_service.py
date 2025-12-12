import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from services.user_service import (
    get_user_by_email,
    get_user_by_id,
    get_all_users,
    create_user,
    update_user,
    delete_user,
    authenticate_user,
)
from schemas.auth import UserCreate, UserUpdate
from models.user import User, UserRole


@pytest.mark.asyncio
async def test_get_user_by_email(test_session: AsyncSession, test_user: User):
    """Test getting user by email."""
    user = await get_user_by_email(test_session, test_user.email)
    assert user is not None
    assert user.email == test_user.email
    assert user.id == test_user.id


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(test_session: AsyncSession):
    """Test getting non-existent user by email."""
    user = await get_user_by_email(test_session, "nonexistent@example.com")
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_id(test_session: AsyncSession, test_user: User):
    """Test getting user by ID."""
    user = await get_user_by_id(test_session, test_user.id)
    assert user is not None
    assert user.id == test_user.id
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(test_session: AsyncSession):
    """Test getting non-existent user by ID."""
    user = await get_user_by_id(test_session, "nonexistent-id")
    assert user is None


@pytest.mark.asyncio
async def test_get_all_users(test_session: AsyncSession, test_user: User, test_admin_user: User):
    """Test getting all users."""
    users = await get_all_users(test_session)
    assert len(users) >= 2
    emails = [u.email for u in users]
    assert test_user.email in emails
    assert test_admin_user.email in emails


@pytest.mark.asyncio
async def test_create_user(test_session: AsyncSession):
    """Test creating a new user."""
    user_data = UserCreate(
        email="newuser@example.com",
        password="newpassword123",
        name="New User"
    )
    user = await create_user(test_session, user_data)

    assert user is not None
    assert user.email == "newuser@example.com"
    assert user.name == "New User"
    assert user.role == UserRole.USER.value
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_duplicate_email(test_session: AsyncSession, test_user: User):
    """Test creating user with duplicate email."""
    user_data = UserCreate(
        email=test_user.email,
        password="password123",
        name="Duplicate"
    )

    with pytest.raises(HTTPException) as exc_info:
        await create_user(test_session, user_data)

    assert exc_info.value.status_code == 400
    assert "already registered" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_user_short_password(test_session: AsyncSession):
    """Test creating user with short password."""
    from pydantic import ValidationError

    # Pydantic validation will catch short password before function is called
    with pytest.raises(ValidationError):
        UserCreate(
            email="shortpass@example.com",
            password="short",  # Too short - Pydantic validator will reject
            name="Short Pass"
        )


@pytest.mark.asyncio
async def test_update_user(test_session: AsyncSession, test_user: User):
    """Test updating user."""
    user_data = UserUpdate(
        name="Updated Name",
        role="admin",
        is_active=False
    )

    updated_user = await update_user(test_session, test_user.id, user_data)

    assert updated_user.name == "Updated Name"
    assert updated_user.role == "admin"
    assert updated_user.is_active is False


@pytest.mark.asyncio
async def test_update_user_partial(test_session: AsyncSession, test_user: User):
    """Test partial user update."""
    user_data = UserUpdate(name="Partial Update")

    updated_user = await update_user(test_session, test_user.id, user_data)

    assert updated_user.name == "Partial Update"
    # Other fields should remain unchanged
    assert updated_user.email == test_user.email


@pytest.mark.asyncio
async def test_update_user_not_found(test_session: AsyncSession):
    """Test updating non-existent user."""
    user_data = UserUpdate(name="Test")

    with pytest.raises(HTTPException) as exc_info:
        await update_user(test_session, "nonexistent-id", user_data)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_user_invalid_role(test_session: AsyncSession, test_user: User):
    """Test updating user with invalid role."""
    user_data = UserUpdate(role="invalid_role")

    with pytest.raises(HTTPException) as exc_info:
        await update_user(test_session, test_user.id, user_data)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_user(test_session: AsyncSession, test_user: User, test_admin_user: User):
    """Test deleting user."""
    await delete_user(test_session, test_user.id, test_admin_user.id)

    # Verify user is deleted
    deleted_user = await get_user_by_id(test_session, test_user.id)
    assert deleted_user is None


@pytest.mark.asyncio
async def test_delete_user_self(test_session: AsyncSession, test_user: User):
    """Test deleting own account (should fail)."""
    with pytest.raises(HTTPException) as exc_info:
        await delete_user(test_session, test_user.id, test_user.id)

    assert exc_info.value.status_code == 400
    assert "own account" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_delete_user_not_found(test_session: AsyncSession, test_admin_user: User):
    """Test deleting non-existent user."""
    with pytest.raises(HTTPException) as exc_info:
        await delete_user(test_session, "nonexistent-id", test_admin_user.id)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_authenticate_user(test_session: AsyncSession, test_user: User):
    """Test authenticating user with correct password."""
    user = await authenticate_user(test_session, test_user.email, "testpass123")
    assert user is not None
    assert user.email == test_user.email


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(test_session: AsyncSession, test_user: User):
    """Test authenticating user with wrong password."""
    user = await authenticate_user(test_session, test_user.email, "wrongpassword")
    assert user is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(test_session: AsyncSession):
    """Test authenticating non-existent user."""
    user = await authenticate_user(test_session, "nonexistent@example.com", "password")
    assert user is None

