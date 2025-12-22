"""
Comparison Engine

Compares simulated outcomes vs real historical outcomes and calculates metrics.
"""
from typing import Dict, List, Optional
from datetime import date
from decimal import Decimal
from collections import defaultdict


class ComparisonEngine:
    """Compares simulated vs real outcomes and calculates metrics"""
    
    def __init__(self):
        """Initialize comparison engine"""
        self.daily_comparisons: List[Dict] = []
        self.item_metrics: Dict[str, Dict] = defaultdict(lambda: {
            "simulated_stockouts": 0,
            "real_stockouts": 0,
            "simulated_inventory_value": Decimal("0"),
            "real_inventory_value": Decimal("0"),
            "simulated_days_in_stock": 0,
            "real_days_in_stock": 0,
            "total_days": 0
        })
    
    def record_daily_comparison(
        self,
        current_date: date,
        item_id: str,
        simulated_stock: float,
        real_stock: float,
        unit_cost: Decimal,
        order_placed: Optional[bool] = None,
        order_quantity: Optional[float] = None
    ):
        """
        Record daily comparison for an item.
        
        Args:
            current_date: Current simulation date
            item_id: Item ID
            simulated_stock: Simulated stock level
            real_stock: Real stock level
            unit_cost: Unit cost for inventory value calculation
            order_placed: Whether order was placed today
            order_quantity: Order quantity if placed
        """
        simulated_stockout = simulated_stock <= 0
        real_stockout = real_stock <= 0
        
        # Record daily comparison
        self.daily_comparisons.append({
            "date": current_date,
            "item_id": item_id,
            "simulated_stock": simulated_stock,
            "real_stock": real_stock,
            "simulated_stockout": simulated_stockout,
            "real_stockout": real_stockout,
            "order_placed": order_placed,
            "order_quantity": order_quantity
        })
        
        # Update item metrics
        metrics = self.item_metrics[item_id]
        metrics["total_days"] += 1
        
        if simulated_stockout:
            metrics["simulated_stockouts"] += 1
        else:
            metrics["simulated_days_in_stock"] += 1
        
        if real_stockout:
            metrics["real_stockouts"] += 1
        else:
            metrics["real_days_in_stock"] += 1
        
        # Accumulate inventory value
        metrics["simulated_inventory_value"] += Decimal(str(simulated_stock)) * unit_cost
        metrics["real_inventory_value"] += Decimal(str(real_stock)) * unit_cost
    
    def calculate_stockout_rate(self, item_id: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate stockout rate (simulated vs real).
        
        Args:
            item_id: Optional filter by item_id
        
        Returns:
            Dict with 'simulated' and 'real' stockout rates
        """
        if item_id:
            metrics = self.item_metrics[item_id]
            total_days = metrics["total_days"]
            if total_days == 0:
                return {"simulated": 0.0, "real": 0.0}
            
            simulated_rate = metrics["simulated_stockouts"] / total_days
            real_rate = metrics["real_stockouts"] / total_days
            return {"simulated": simulated_rate, "real": real_rate}
        
        # Aggregate across all items
        total_days = sum(m["total_days"] for m in self.item_metrics.values())
        total_simulated_stockouts = sum(m["simulated_stockouts"] for m in self.item_metrics.values())
        total_real_stockouts = sum(m["real_stockouts"] for m in self.item_metrics.values())
        
        if total_days == 0:
            return {"simulated": 0.0, "real": 0.0}
        
        return {
            "simulated": total_simulated_stockouts / total_days,
            "real": total_real_stockouts / total_days
        }
    
    def calculate_inventory_value(self, item_id: Optional[str] = None) -> Dict[str, Decimal]:
        """
        Calculate average inventory value (simulated vs real).
        
        Args:
            item_id: Optional filter by item_id
        
        Returns:
            Dict with 'simulated' and 'real' average inventory values
        """
        if item_id:
            metrics = self.item_metrics[item_id]
            total_days = metrics["total_days"]
            if total_days == 0:
                return {"simulated": Decimal("0"), "real": Decimal("0")}
            
            simulated_avg = metrics["simulated_inventory_value"] / total_days
            real_avg = metrics["real_inventory_value"] / total_days
            return {"simulated": simulated_avg, "real": real_avg}
        
        # Aggregate across all items
        total_days = sum(m["total_days"] for m in self.item_metrics.values())
        total_simulated_value = sum(m["simulated_inventory_value"] for m in self.item_metrics.values())
        total_real_value = sum(m["real_inventory_value"] for m in self.item_metrics.values())
        
        if total_days == 0:
            return {"simulated": Decimal("0"), "real": Decimal("0")}
        
        return {
            "simulated": total_simulated_value / total_days,
            "real": total_real_value / total_days
        }
    
    def calculate_service_level(self, item_id: Optional[str] = None) -> Dict[str, float]:
        """
        Calculate service level (simulated vs real).
        
        Args:
            item_id: Optional filter by item_id
        
        Returns:
            Dict with 'simulated' and 'real' service levels
        """
        if item_id:
            metrics = self.item_metrics[item_id]
            total_days = metrics["total_days"]
            if total_days == 0:
                return {"simulated": 0.0, "real": 0.0}
            
            simulated_sl = metrics["simulated_days_in_stock"] / total_days
            real_sl = metrics["real_days_in_stock"] / total_days
            return {"simulated": simulated_sl, "real": real_sl}
        
        # Aggregate across all items
        total_days = sum(m["total_days"] for m in self.item_metrics.values())
        total_simulated_days_in_stock = sum(m["simulated_days_in_stock"] for m in self.item_metrics.values())
        total_real_days_in_stock = sum(m["real_days_in_stock"] for m in self.item_metrics.values())
        
        if total_days == 0:
            return {"simulated": 0.0, "real": 0.0}
        
        return {
            "simulated": total_simulated_days_in_stock / total_days,
            "real": total_real_days_in_stock / total_days
        }
    
    def get_daily_comparisons(self, item_id: Optional[str] = None) -> List[Dict]:
        """
        Get all daily comparisons.
        
        Args:
            item_id: Optional filter by item_id
        
        Returns:
            List of daily comparison records
        """
        if item_id:
            return [c for c in self.daily_comparisons if c["item_id"] == item_id]
        return self.daily_comparisons
    
    def get_item_metrics(self, item_id: str) -> Dict:
        """Get metrics for a specific item"""
        return self.item_metrics.get(item_id, {
            "simulated_stockouts": 0,
            "real_stockouts": 0,
            "simulated_inventory_value": Decimal("0"),
            "real_inventory_value": Decimal("0"),
            "simulated_days_in_stock": 0,
            "real_days_in_stock": 0,
            "total_days": 0
        })
    
    def reset(self):
        """Reset all comparisons (for new simulation)"""
        self.daily_comparisons = []
        self.item_metrics = defaultdict(lambda: {
            "simulated_stockouts": 0,
            "real_stockouts": 0,
            "simulated_inventory_value": Decimal("0"),
            "real_inventory_value": Decimal("0"),
            "simulated_days_in_stock": 0,
            "real_days_in_stock": 0,
            "total_days": 0
        })

