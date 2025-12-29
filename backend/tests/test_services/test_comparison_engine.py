from datetime import date
from decimal import Decimal

from services.simulation.comparison_engine import ComparisonEngine


def test_item_level_metrics_and_rates():
    engine = ComparisonEngine()
    unit_cost = Decimal("2.00")

    engine.record_daily_comparison(
        current_date=date(2024, 1, 1),
        item_id="SKU1",
        simulated_stock=0.0,   # stockout
        real_stock=5.0,
        unit_cost=unit_cost,
    )
    engine.record_daily_comparison(
        current_date=date(2024, 1, 2),
        item_id="SKU1",
        simulated_stock=1.0,
        real_stock=0.0,        # stockout
        unit_cost=unit_cost,
    )

    stockout_rate = engine.calculate_stockout_rate("SKU1")
    assert stockout_rate["simulated"] == 0.5
    assert stockout_rate["real"] == 0.5

    service_level = engine.calculate_service_level("SKU1")
    assert service_level["simulated"] == 0.5
    assert service_level["real"] == 0.5

    inventory_value = engine.calculate_inventory_value("SKU1")
    # simulated: (0*2 + 1*2) / 2 = 1
    # real: (5*2 + 0*2) / 2 = 5
    assert inventory_value["simulated"] == Decimal("1")
    assert inventory_value["real"] == Decimal("5")


def test_global_aggregation_across_items():
    engine = ComparisonEngine()
    unit_cost = Decimal("1.00")

    # 2 items, 1 day each => total_days=2 in global aggregation
    engine.record_daily_comparison(
        current_date=date(2024, 1, 1),
        item_id="SKU1",
        simulated_stock=0.0,  # stockout
        real_stock=1.0,
        unit_cost=unit_cost,
    )
    engine.record_daily_comparison(
        current_date=date(2024, 1, 1),
        item_id="SKU2",
        simulated_stock=2.0,
        real_stock=0.0,       # stockout
        unit_cost=unit_cost,
    )

    stockout_rate = engine.calculate_stockout_rate()
    assert stockout_rate["simulated"] == 0.5
    assert stockout_rate["real"] == 0.5

    service_level = engine.calculate_service_level()
    assert service_level["simulated"] == 0.5
    assert service_level["real"] == 0.5

    inventory_value = engine.calculate_inventory_value()
    # simulated avg value: (0 + 2) / 2 = 1
    # real avg value: (1 + 0) / 2 = 0.5
    assert inventory_value["simulated"] == Decimal("1")
    assert inventory_value["real"] == Decimal("0.5")

