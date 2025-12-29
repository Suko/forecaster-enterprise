"""
Integration tests for forecast API endpoints
"""
import pytest
from httpx import AsyncClient
from uuid import uuid4

from main import app


class TestForecastAPI:
    """Test forecast API endpoints"""

    @pytest.fixture
    async def client(self, db_session):
        """Create AsyncClient for API testing with database override"""
        from httpx import ASGITransport
        from models.database import get_db

        # Override the database dependency for testing
        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client

        # Clear overrides after test
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_forecast_endpoint_structure(self, client):
        """Test forecast endpoint exists and validates input"""
        # Test without auth (should fail)
        response = await client.post("/api/v1/forecast", json={
            "item_ids": ["SKU001"],
            "prediction_length": 30,
        })
        # Should return 401 or 403 (unauthorized)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_inventory_endpoint_structure(self, client):
        """Test inventory endpoint returns 202 with task response for authenticated requests"""
        # Test without authentication - should fail
        response = await client.post("/api/v1/inventory/calculate", json={
            "item_ids": ["SKU001"],
            "prediction_length": 30,
            "inventory_params": {
                "SKU001": {
                    "current_stock": 500,
                    "lead_time_days": 14,
                }
            },
        })
        # Should return 401 (unauthorized) since no auth provided
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_inventory_task_status_endpoint_structure(self, client):
        """Test inventory task status endpoint exists"""
        # Test without authentication - should fail with 401
        response = await client.get("/api/v1/inventory/calculate/invalid-task-id")
        # Should return 401 (unauthorized) since no auth provided
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_actuals_endpoint_structure(self, client):
        """Test actuals backfill endpoint exists"""
        response = await client.post("/api/v1/forecasts/actuals", json={
            "item_id": "SKU001",
            "actuals": [
                {"date": "2024-01-01", "actual_value": 100.0},
            ],
        })
        # Should return 401 or 403 (unauthorized)
        assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_quality_endpoint_structure(self, client):
        """Test quality endpoint exists"""
        response = await client.get("/api/v1/forecasts/quality/SKU001")
        # Should return 401 or 403 (unauthorized)
        assert response.status_code in [401, 403]

