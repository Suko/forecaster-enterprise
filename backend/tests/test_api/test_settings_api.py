"""
API tests for Settings endpoints

Tests client settings and recommendation rules APIs.
"""
import pytest
from uuid import UUID

from models.settings import ClientSettings
from tests.fixtures.test_inventory_data import create_test_client_settings


@pytest.mark.asyncio
async def test_get_settings(test_client, test_jwt_token, test_client_obj):
    """Test getting client settings"""
    # Get settings
    response = await test_client.get(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "safety_buffer_days" in data
    assert "understocked_threshold" in data
    assert "overstocked_threshold" in data
    assert "dead_stock_days" in data


@pytest.mark.asyncio
async def test_update_settings(test_client, test_jwt_token, test_client_obj):
    """Test updating client settings"""
    # Use JWT token
    
    # Update settings
    response = await test_client.put(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "safety_buffer_days": 10,
            "understocked_threshold": 20,
            "overstocked_threshold": 100,
            "dead_stock_days": 120
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["safety_buffer_days"] == 10
    assert data["understocked_threshold"] == 20
    assert data["overstocked_threshold"] == 100
    assert data["dead_stock_days"] == 120


@pytest.mark.asyncio
async def test_get_recommendation_rules(test_client, test_jwt_token, test_client_obj):
    """Test getting recommendation rules"""
    # Use JWT token
    
    # Get rules
    response = await test_client.get(
        "/api/v1/settings/recommendation-rules",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "enabled_types" in data
    assert "role_rules" in data


@pytest.mark.asyncio
async def test_update_recommendation_rules(test_client, test_jwt_token, test_client_obj):
    """Test updating recommendation rules"""
    # Use JWT token
    
    # Update rules
    new_rules = {
        "enabled_types": ["REORDER", "URGENT"],
        "role_rules": {
            "PROCUREMENT": ["REORDER", "URGENT"],
            "CEO": ["URGENT"]
        },
        "min_inventory_value": 100,
        "min_risk_score": 0.5
    }
    
    response = await test_client.put(
        "/api/v1/settings/recommendation-rules",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=new_rules
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["enabled_types"] == ["REORDER", "URGENT"]
    assert data["role_rules"]["PROCUREMENT"] == ["REORDER", "URGENT"]


@pytest.mark.asyncio
async def test_settings_affect_recommendations(test_client, test_jwt_token, test_client_obj, populate_test_data):
    """Test that settings changes affect recommendations"""
    # Use JWT token
    
    # Update settings to be more restrictive
    await test_client.put(
        "/api/v1/settings",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json={
            "safety_buffer_days": 30,  # Higher buffer
            "understocked_threshold": 60  # Higher threshold
        }
    )
    
    # Get recommendations
    response = await test_client.get(
        "/api/v1/order-planning/recommendations",
        headers={"Authorization": f"Bearer {test_jwt_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Recommendations should reflect the new settings

