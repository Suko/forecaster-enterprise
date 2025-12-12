"""API routes"""

from . import auth, forecast, inventory, orders, purchase_orders, settings, etl, suppliers

__all__ = ["auth", "forecast", "inventory", "orders", "purchase_orders", "settings", "etl", "suppliers"]
