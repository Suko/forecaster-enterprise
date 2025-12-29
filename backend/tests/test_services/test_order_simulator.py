from datetime import date

from services.simulation.order_simulator import OrderSimulator


def test_place_order_sets_arrival_date():
    simulator = OrderSimulator()
    order_date = date(2024, 1, 1)

    order = simulator.place_order(
        item_id="SKU1",
        quantity=10,
        order_date=order_date,
        lead_time_days=5,
    )

    assert order is not None
    assert order.order_date == order_date
    assert order.lead_time_days == 5
    assert order.arrival_date == date(2024, 1, 6)


def test_place_order_applies_min_order_quantity():
    simulator = OrderSimulator()

    order = simulator.place_order(
        item_id="SKU1",
        quantity=0,
        order_date=date(2024, 1, 1),
        lead_time_days=1,
        min_order_quantity=3,
    )

    assert order is not None
    assert order.quantity == 3


def test_get_orders_arriving_excludes_received_orders():
    simulator = OrderSimulator()
    order_date = date(2024, 1, 1)

    order = simulator.place_order(
        item_id="SKU1",
        quantity=10,
        order_date=order_date,
        lead_time_days=2,
    )
    assert order is not None

    assert simulator.get_orders_arriving(date(2024, 1, 2)) == []

    arriving = simulator.get_orders_arriving(date(2024, 1, 3))
    assert [o.order_id for o in arriving] == [order.order_id]

    simulator.mark_order_received(order)
    assert simulator.get_orders_arriving(date(2024, 1, 3)) == []


def test_reset_clears_state():
    simulator = OrderSimulator()
    simulator.place_order(
        item_id="SKU1",
        quantity=10,
        order_date=date(2024, 1, 1),
        lead_time_days=1,
    )
    assert simulator.get_total_orders_placed() == 1

    simulator.reset()
    assert simulator.get_total_orders_placed() == 0

