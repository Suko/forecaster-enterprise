from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock

import pytest

from schemas.simulation import SimulationConfig, SimulationRequest
from services.simulation_service import SimulationService


@dataclass(frozen=True)
class _FakeProduct:
    unit_cost: float = 1.0
    safety_buffer_days: int = 7


@pytest.mark.asyncio
async def test_places_single_order_and_applies_arrival_before_sales(monkeypatch: pytest.MonkeyPatch):
    db = MagicMock()
    service = SimulationService(db)

    start = date(2024, 1, 1)
    end = date(2024, 1, 3)
    item_id = "SKU1"

    async def _stock_snapshot(*_args: Any, **_kwargs: Any):
        return {item_id: 5.0}

    async def _products(*_args: Any, **_kwargs: Any):
        return {item_id: _FakeProduct(unit_cost=1.0, safety_buffer_days=7)}

    async def _sales(*_args: Any, **_kwargs: Any):
        return 0.0

    async def _real_stock(*_args: Any, **_kwargs: Any):
        return 5.0

    forecast_calls: list[tuple[date, int]] = []

    async def _forecast(_client_id: Any, _item_id: str, training_end_date: date, prediction_length: int = 30):
        forecast_calls.append((training_end_date, prediction_length))
        return 30.0

    async def _lead_time(*_args: Any, **_kwargs: Any):
        return 2

    async def _moq(*_args: Any, **_kwargs: Any):
        return None

    monkeypatch.setattr(service, "_get_stock_snapshot", _stock_snapshot)
    monkeypatch.setattr(service, "_get_products", _products)
    monkeypatch.setattr(service, "_get_actual_sales", _sales)
    monkeypatch.setattr(service, "_get_real_stock_for_date", _real_stock)
    monkeypatch.setattr(service, "_get_forecasted_demand", _forecast)
    monkeypatch.setattr(service, "_get_lead_time", _lead_time)
    monkeypatch.setattr(service, "_get_moq", _moq)

    # Make reorder logic deterministic (we're testing orchestration, not math).
    monkeypatch.setattr(service.inventory_calc, "calculate_safety_stock", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(service.inventory_calc, "calculate_reorder_point", lambda *_a, **_k: 10.0)
    monkeypatch.setattr(service.inventory_calc, "calculate_recommended_order_quantity", lambda *_a, **_k: 20.0)

    request = SimulationRequest(
        client_id="00000000-0000-0000-0000-000000000000",
        start_date=start,
        end_date=end,
        item_ids=[item_id],
        simulation_config=SimulationConfig(
            auto_place_orders=True,
            lead_time_buffer_days=0,
            min_order_quantity=1,
            service_level=0.95,
        ),
    )

    result = await service.run_simulation(request)
    assert result.status == "completed"

    assert service.order_simulator.get_total_orders_placed(item_id) == 1
    order = service.order_simulator.orders[0]
    assert order.item_id == item_id
    assert order.quantity == 20.0
    assert order.order_date == start
    assert order.arrival_date == date(2024, 1, 3)
    assert order.received is True

    # Forecast should be called only on day 0 for < 7-day simulations.
    assert forecast_calls == [(start, 30)]

    daily = [d for d in (result.daily_comparison or []) if d.item_id == item_id]
    assert [d.date for d in daily] == [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    assert [d.simulated_stock for d in daily] == [5.0, 5.0, 25.0]

    orders_placed = [d for d in daily if d.order_placed]
    assert len(orders_placed) == 1
    assert orders_placed[0].date == start
    assert orders_placed[0].order_quantity == 20.0


@pytest.mark.asyncio
async def test_stock_is_clamped_to_non_negative(monkeypatch: pytest.MonkeyPatch):
    db = MagicMock()
    service = SimulationService(db)

    start = date(2024, 1, 1)
    end = date(2024, 1, 1)
    item_id = "SKU1"

    async def _stock_snapshot(*_args: Any, **_kwargs: Any):
        return {item_id: 5.0}

    async def _products(*_args: Any, **_kwargs: Any):
        return {item_id: _FakeProduct(unit_cost=1.0, safety_buffer_days=7)}

    async def _sales(*_args: Any, **_kwargs: Any):
        return 10.0

    async def _real_stock(*_args: Any, **_kwargs: Any):
        return 5.0

    async def _forecast(*_args: Any, **_kwargs: Any):
        return 30.0

    async def _lead_time(*_args: Any, **_kwargs: Any):
        return 1

    async def _moq(*_args: Any, **_kwargs: Any):
        return None

    monkeypatch.setattr(service, "_get_stock_snapshot", _stock_snapshot)
    monkeypatch.setattr(service, "_get_products", _products)
    monkeypatch.setattr(service, "_get_actual_sales", _sales)
    monkeypatch.setattr(service, "_get_real_stock_for_date", _real_stock)
    monkeypatch.setattr(service, "_get_forecasted_demand", _forecast)
    monkeypatch.setattr(service, "_get_lead_time", _lead_time)
    monkeypatch.setattr(service, "_get_moq", _moq)

    monkeypatch.setattr(service.inventory_calc, "calculate_safety_stock", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(service.inventory_calc, "calculate_reorder_point", lambda *_a, **_k: 10.0)
    monkeypatch.setattr(service.inventory_calc, "calculate_recommended_order_quantity", lambda *_a, **_k: 1.0)

    request = SimulationRequest(
        client_id="00000000-0000-0000-0000-000000000000",
        start_date=start,
        end_date=end,
        item_ids=[item_id],
        simulation_config=SimulationConfig(
            auto_place_orders=True,
            lead_time_buffer_days=0,
            min_order_quantity=1,
            service_level=0.95,
        ),
    )

    result = await service.run_simulation(request)
    assert result.status == "completed"

    daily = [d for d in (result.daily_comparison or []) if d.item_id == item_id]
    assert len(daily) == 1
    assert daily[0].simulated_stock == 0.0

