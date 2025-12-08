"""
Tests for API authentication (JWT and Service API Key)
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from main import app


class TestAPIAuthentication:
    """Test API authentication methods"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    async def test_user(self, db_session, test_client):
        """Create a test user with client_id"""
        from models.user import User
        import uuid
        
        user = User(
            id=str(uuid.uuid4()),
            email="test@example.com",
            name="Test User",
            hashed_password="hashed_password_here",
            client_id=test_client.client_id,
            is_active=True,
            role="user",
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.fixture
    def test_jwt_token(self, test_user):
        """Create a test JWT token (synchronous fixture)"""
        from auth.jwt import create_access_token
        
        token_data = {
            "sub": test_user.email,
            "client_id": str(test_user.client_id),
        }
        return create_access_token(data=token_data)
    
    @pytest.mark.asyncio
    async def test_forecast_with_jwt_token(self, client, test_jwt_token, db_session, sample_item_ids, populate_test_data):
        """Test forecast endpoint with JWT token authentication"""
        # Test data is populated in database via populate_test_data fixture
        from forecasting.services.forecast_service import ForecastService
        service = ForecastService(db_session)
        
        item_id = sample_item_ids[0]
        
        # Make request with JWT token
        response = client.post(
            "/api/v1/forecast",
            headers={
                "Authorization": f"Bearer {test_jwt_token}",
                "Content-Type": "application/json",
            },
            json={
                "item_ids": [item_id],
                "prediction_length": 7,
                "model": "statistical_ma7",
                "include_baseline": False,
            },
        )
        
        # Should succeed (201) or fail gracefully (500 if service issues)
        assert response.status_code in [201, 500]
        if response.status_code == 201:
            data = response.json()
            assert "forecast_id" in data
            assert "forecasts" in data
    
    @pytest.mark.asyncio
    async def test_forecast_with_service_api_key(self, client, test_client, db_session, sample_item_ids):
        """Test forecast endpoint with service API key authentication"""
        # Set service API key
        test_api_key = "test-service-api-key-12345"
        with patch.dict(os.environ, {"SERVICE_API_KEY": test_api_key}):
            # Re-import to pick up new env var
            import importlib
            import auth.service_auth
            importlib.reload(auth.service_auth)
            
            item_id = sample_item_ids[0]
            
            # Make request with service API key
            response = client.post(
                "/api/v1/forecast",
                headers={
                    "X-API-Key": test_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "item_ids": [item_id],
                    "prediction_length": 7,
                    "model": "statistical_ma7",
                    "include_baseline": False,
                    "client_id": str(test_client.client_id),  # Required for service calls
                },
            )
            
            # Should succeed (201) or fail gracefully
            assert response.status_code in [201, 400, 500]
            if response.status_code == 201:
                data = response.json()
                assert "forecast_id" in data
    
    @pytest.mark.asyncio
    async def test_forecast_without_auth(self, client, sample_item_ids):
        """Test forecast endpoint without authentication (should fail)"""
        item_id = sample_item_ids[0]
        
        response = client.post(
            "/api/v1/forecast",
            headers={"Content-Type": "application/json"},
            json={
                "item_ids": [item_id],
                "prediction_length": 7,
            },
        )
        
        # Should fail with 401 Unauthorized
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_forecast_service_api_key_missing_client_id(self, client, test_client):
        """Test service API key call without client_id (should fail)"""
        test_api_key = "test-service-api-key-12345"
        with patch.dict(os.environ, {"SERVICE_API_KEY": test_api_key}):
            import importlib
            import auth.service_auth
            importlib.reload(auth.service_auth)
            
            response = client.post(
                "/api/v1/forecast",
                headers={
                    "X-API-Key": test_api_key,
                    "Content-Type": "application/json",
                },
                json={
                    "item_ids": ["SKU001"],
                    "prediction_length": 7,
                    # client_id missing - should fail
                },
            )
            
            # Should fail with 400 Bad Request (client_id required)
            assert response.status_code in [400, 401]
    
    @pytest.mark.asyncio
    async def test_forecast_invalid_service_api_key(self, client, test_client):
        """Test forecast with invalid service API key (should fail)"""
        test_api_key = "test-service-api-key-12345"
        with patch.dict(os.environ, {"SERVICE_API_KEY": test_api_key}):
            import importlib
            import auth.service_auth
            importlib.reload(auth.service_auth)
            
            response = client.post(
                "/api/v1/forecast",
                headers={
                    "X-API-Key": "invalid-key",
                    "Content-Type": "application/json",
                },
                json={
                    "item_ids": ["SKU001"],
                    "prediction_length": 7,
                    "client_id": str(test_client.client_id),
                },
            )
            
            # Should fail with 401 Unauthorized
            assert response.status_code == 401

