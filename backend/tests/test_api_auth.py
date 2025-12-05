import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


@pytest.mark.asyncio
async def test_register_endpoint(test_client: AsyncClient):
    """Test user registration endpoint."""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": "register@example.com",
            "password": "registerpass123",
            "name": "Register User"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "register@example.com"
    assert data["name"] == "Register User"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_endpoint_duplicate(test_client: AsyncClient, test_user: User):
    """Test registration with duplicate email."""
    response = await test_client.post(
        "/auth/register",
        json={
            "email": test_user.email,
            "password": "password123",
            "name": "Duplicate"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_endpoint(test_client: AsyncClient, test_user: User):
    """Test login endpoint."""
    response = await test_client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "testpass123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_endpoint_invalid(test_client: AsyncClient, test_user: User):
    """Test login with invalid credentials."""
    response = await test_client.post(
        "/auth/login",
        data={
            "username": test_user.email,
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_endpoint(test_client: AsyncClient, test_user: User):
    """Test /auth/me endpoint."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_user.email})
    
    response = await test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


@pytest.mark.asyncio
async def test_get_me_endpoint_unauthorized(test_client: AsyncClient):
    """Test /auth/me without token."""
    response = await test_client.get("/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_users_endpoint(test_client: AsyncClient, test_admin_user: User):
    """Test /auth/users endpoint (admin only)."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_admin_user.email})
    
    response = await test_client.get(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@pytest.mark.asyncio
async def test_list_users_endpoint_non_admin(test_client: AsyncClient, test_user: User):
    """Test /auth/users endpoint with non-admin user."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_user.email})
    
    response = await test_client.get(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_user_endpoint(test_client: AsyncClient, test_admin_user: User):
    """Test POST /auth/users endpoint (admin only)."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_admin_user.email})
    
    response = await test_client.post(
        "/auth/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "email": "admincreated@example.com",
            "password": "adminpass123",
            "name": "Admin Created"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admincreated@example.com"


@pytest.mark.asyncio
async def test_update_user_endpoint(test_client: AsyncClient, test_user: User, test_admin_user: User):
    """Test PATCH /auth/users/{user_id} endpoint."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_admin_user.email})
    
    response = await test_client.patch(
        f"/auth/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Updated Name",
            "role": "admin"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_delete_user_endpoint(test_client: AsyncClient, test_user: User, test_admin_user: User):
    """Test DELETE /auth/users/{user_id} endpoint."""
    from auth import create_access_token
    
    token = create_access_token(data={"sub": test_admin_user.email})
    
    response = await test_client.delete(
        f"/auth/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 204
    
    # Verify user is deleted
    response = await test_client.get(
        f"/auth/users/{test_user.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    # Should return 404 or 403 depending on implementation
    assert response.status_code in [404, 403]

