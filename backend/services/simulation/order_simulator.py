"""
Order Simulator

Tracks orders placed during simulation, manages lead times, and processes arrivals.
"""
from typing import Dict, List, Optional
from datetime import date, timedelta
from dataclasses import dataclass
from uuid import UUID
import uuid


@dataclass
class SimulatedOrder:
    """Represents an order placed during simulation"""
    
    order_id: str
    item_id: str
    quantity: float
    order_date: date
    lead_time_days: int
    arrival_date: Optional[date] = None
    received: bool = False
    
    def __post_init__(self):
        """Calculate arrival date from order date and lead time"""
        if self.arrival_date is None:
            self.arrival_date = self.order_date + timedelta(days=self.lead_time_days)


class OrderSimulator:
    """Manages order placement and arrival tracking during simulation"""
    
    def __init__(self):
        """Initialize order simulator"""
        self.orders: List[SimulatedOrder] = []
    
    def place_order(
        self,
        item_id: str,
        quantity: float,
        order_date: date,
        lead_time_days: int,
        min_order_quantity: int = 1
    ) -> Optional[SimulatedOrder]:
        """
        Place an order during simulation.
        
        Args:
            item_id: Item to order
            quantity: Order quantity
            order_date: Date order is placed
            lead_time_days: Lead time in days
            min_order_quantity: Minimum order quantity (default: 1)
        
        Returns:
            SimulatedOrder if order placed, None if quantity too small
        """
        # Apply minimum order quantity
        if quantity < min_order_quantity:
            quantity = min_order_quantity
        
        if quantity <= 0:
            return None
        
        order = SimulatedOrder(
            order_id=str(uuid.uuid4()),
            item_id=item_id,
            quantity=quantity,
            order_date=order_date,
            lead_time_days=lead_time_days
        )
        
        self.orders.append(order)
        return order
    
    def get_orders_arriving(self, current_date: date) -> List[SimulatedOrder]:
        """
        Get orders that arrive on the current date.
        
        Args:
            current_date: Current simulation date
        
        Returns:
            List of orders arriving today
        """
        arriving = [
            order for order in self.orders
            if order.arrival_date == current_date and not order.received
        ]
        return arriving
    
    def mark_order_received(self, order: SimulatedOrder):
        """Mark an order as received"""
        order.received = True
    
    def get_total_orders_placed(self, item_id: Optional[str] = None) -> int:
        """
        Get total number of orders placed.
        
        Args:
            item_id: Optional filter by item_id
        
        Returns:
            Total orders placed
        """
        if item_id:
            return len([o for o in self.orders if o.item_id == item_id])
        return len(self.orders)
    
    def get_orders_by_item(self, item_id: str) -> List[SimulatedOrder]:
        """Get all orders for a specific item"""
        return [o for o in self.orders if o.item_id == item_id]
    
    def reset(self):
        """Reset all orders (for new simulation)"""
        self.orders = []

