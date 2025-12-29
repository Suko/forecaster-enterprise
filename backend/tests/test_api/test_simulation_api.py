from datetime import date
from uuid import uuid4

import pytest
from httpx import AsyncClient

from schemas.simulation import SimulationRequest, SimulationResponse


@pytest.mark.asyncio
async def test_simulation_rejects_client_id_mismatch(
    test_client: AsyncClient,
    test_client_obj,
    test_jwt_token: str,
):
    payload = SimulationRequest(
        client_id=uuid4(),  # mismatch vs authenticated client
        start_date=date(2024, 1, 1),
        end_date=date(2024, 2, 1),
        item_ids=["SKU1"],
    ).model_dump(mode="json")

    response = await test_client.post(
        "/api/v1/simulation/run",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=payload,
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_simulation_rejects_invalid_date_range(
    test_client: AsyncClient,
    test_client_obj,
    test_jwt_token: str,
):
    payload = SimulationRequest(
        client_id=test_client_obj.client_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 1),
        item_ids=["SKU1"],
    ).model_dump(mode="json")

    response = await test_client.post(
        "/api/v1/simulation/run",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_simulation_rejects_too_short_period(
    test_client: AsyncClient,
    test_client_obj,
    test_jwt_token: str,
):
    payload = SimulationRequest(
        client_id=test_client_obj.client_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 1, 15),  # 15 days (< 30)
        item_ids=["SKU1"],
    ).model_dump(mode="json")

    response = await test_client.post(
        "/api/v1/simulation/run",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_simulation_rejects_too_long_period(
    test_client: AsyncClient,
    test_client_obj,
    test_jwt_token: str,
):
    payload = SimulationRequest(
        client_id=test_client_obj.client_id,
        start_date=date(2020, 1, 1),
        end_date=date(2022, 1, 1),  # > 730 days
        item_ids=["SKU1"],
    ).model_dump(mode="json")

    response = await test_client.post(
        "/api/v1/simulation/run",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=payload,
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_simulation_happy_path_is_plumbed(
    test_client: AsyncClient,
    test_client_obj,
    test_jwt_token: str,
    monkeypatch: pytest.MonkeyPatch,
):
    async def _fake_run_simulation(self, request):  # noqa: ANN001
        return SimulationResponse(
            simulation_id=uuid4(),
            status="completed",
            start_date=request.start_date,
            end_date=request.end_date,
            total_days=(request.end_date - request.start_date).days + 1,
            results=None,
            improvements=None,
            daily_comparison=None,
            item_level_results=None,
            error_message=None,
        )

    monkeypatch.setattr(
        "services.simulation_service.SimulationService.run_simulation",
        _fake_run_simulation,
    )

    payload = SimulationRequest(
        client_id=test_client_obj.client_id,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 2, 1),
        item_ids=["SKU1"],
    ).model_dump(mode="json")

    response = await test_client.post(
        "/api/v1/simulation/run",
        headers={"Authorization": f"Bearer {test_jwt_token}"},
        json=payload,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "completed"
    assert data["total_days"] == 32

