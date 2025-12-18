"""
Tests for API authentication (JWT and Service API Key)
"""
import pytest
from unittest.mock import patch
import os
import uuid
from datetime import date

from models.forecast import ForecastRun, ForecastStatus


@pytest.mark.asyncio
async def test_forecast_with_jwt_token_ignores_body_client_id(
    test_client, test_jwt_token, test_client_obj
):
    item_id = "SKU001"
    body_client_id = str(uuid.uuid4())

    async def fake_generate_forecast(self, **kwargs):
        assert kwargs["client_id"] == str(test_client_obj.client_id)
        return ForecastRun(
            forecast_run_id=uuid.uuid4(),
            client_id=kwargs["client_id"],
            user_id=kwargs["user_id"],
            primary_model=kwargs["primary_model"],
            prediction_length=kwargs["prediction_length"],
            item_ids=kwargs["item_ids"],
            recommended_method=kwargs["primary_model"],
            status=ForecastStatus.COMPLETED.value,
        )

    async def fake_get_forecast_results(self, **_kwargs):
        return {item_id: [{"date": date.today(), "point_forecast": 1.0}]}

    with patch(
        "forecasting.services.forecast_service.ForecastService.generate_forecast",
        new=fake_generate_forecast,
    ), patch(
        "forecasting.services.forecast_service.ForecastService.get_forecast_results",
        new=fake_get_forecast_results,
    ):
        response = await test_client.post(
            "/api/v1/forecast",
            headers={"Authorization": f"Bearer {test_jwt_token}"},
            json={
                "item_ids": [item_id],
                "prediction_length": 7,
                "model": "statistical_ma7",
                "include_baseline": False,
                "client_id": body_client_id,  # Must be ignored for JWT calls
            },
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_forecast_with_service_api_key_requires_body_client_id(test_client, test_client_obj):
    item_id = "SKU001"
    api_key = "test-service-api-key-12345"

    async def fake_generate_forecast(self, **kwargs):
        assert kwargs["client_id"] == str(test_client_obj.client_id)
        return ForecastRun(
            forecast_run_id=uuid.uuid4(),
            client_id=kwargs["client_id"],
            user_id=kwargs["user_id"],
            primary_model=kwargs["primary_model"],
            prediction_length=kwargs["prediction_length"],
            item_ids=kwargs["item_ids"],
            recommended_method=kwargs["primary_model"],
            status=ForecastStatus.COMPLETED.value,
        )

    async def fake_get_forecast_results(self, **_kwargs):
        return {item_id: [{"date": date.today(), "point_forecast": 1.0}]}

    with patch.dict(os.environ, {"SERVICE_API_KEY": api_key}), patch(
        "forecasting.services.forecast_service.ForecastService.generate_forecast",
        new=fake_generate_forecast,
    ), patch(
        "forecasting.services.forecast_service.ForecastService.get_forecast_results",
        new=fake_get_forecast_results,
    ):
        response = await test_client.post(
            "/api/v1/forecast",
            headers={"X-API-Key": api_key},
            json={
                "item_ids": [item_id],
                "prediction_length": 7,
                "model": "statistical_ma7",
                "include_baseline": False,
                "client_id": str(test_client_obj.client_id),
            },
        )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_forecast_without_auth_fails(test_client):
    response = await test_client.post(
        "/api/v1/forecast",
        json={
            "item_ids": ["SKU001"],
            "prediction_length": 7,
        },
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forecast_service_api_key_missing_client_id_fails(test_client):
    api_key = "test-service-api-key-12345"
    with patch.dict(os.environ, {"SERVICE_API_KEY": api_key}):
        response = await test_client.post(
            "/api/v1/forecast",
            headers={"X-API-Key": api_key},
            json={
                "item_ids": ["SKU001"],
                "prediction_length": 7,
            },
        )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_forecast_invalid_service_api_key_fails(test_client, test_client_obj):
    api_key = "test-service-api-key-12345"
    with patch.dict(os.environ, {"SERVICE_API_KEY": api_key}):
        response = await test_client.post(
            "/api/v1/forecast",
            headers={"X-API-Key": "invalid-key"},
            json={
                "item_ids": ["SKU001"],
                "prediction_length": 7,
                "client_id": str(test_client_obj.client_id),
            },
        )
    assert response.status_code == 401
