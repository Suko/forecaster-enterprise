"""
Inventory Calculator

Calculates inventory metrics using industry-standard formulas (APICS).
"""
from typing import Dict, Optional
from datetime import date, timedelta
import math


class InventoryCalculator:
    """Calculate inventory metrics from forecasts"""
    
    @staticmethod
    def calculate_days_of_inventory_remaining(
        current_stock: float,
        avg_daily_demand: float,
    ) -> float:
        """
        Calculate Days of Inventory Remaining (DIR).
        
        Formula: DIR = Current Stock / Average Daily Demand
        
        Industry Standard: APICS
        """
        if avg_daily_demand <= 0:
            return float('inf') if current_stock > 0 else 0.0
        return current_stock / avg_daily_demand
    
    @staticmethod
    def calculate_safety_stock(
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock_days: Optional[int] = None,
        service_level: float = 0.95,
        demand_std: Optional[float] = None,
    ) -> float:
        """
        Calculate Safety Stock using industry-standard formula.
        
        Formula (Service Level Method):
        Safety Stock = Z × σ_d × √L
        
        Where:
        - Z = Z-score for service level (95% = 1.65)
        - σ_d = Standard deviation of demand
        - L = Lead time in days
        
        Simplified (if variance not available):
        Safety Stock = Average Daily Demand × Safety Stock Days
        
        Industry Standard: APICS SCOR Model
        """
        # Z-scores for common service levels
        z_scores = {
            0.90: 1.28,
            0.95: 1.65,
            0.99: 2.33,
        }
        z = z_scores.get(service_level, 1.65)
        
        # If we have demand variance, use full formula
        if demand_std is not None:
            return z * demand_std * math.sqrt(lead_time_days)
        
        # Simplified: use safety stock days
        if safety_stock_days:
            return avg_daily_demand * safety_stock_days * (1 + z * 0.2)
        
        # Default: 7 days
        return avg_daily_demand * 7 * (1 + z * 0.2)
    
    @staticmethod
    def calculate_reorder_point(
        avg_daily_demand: float,
        lead_time_days: int,
        safety_stock: float,
    ) -> float:
        """
        Calculate Reorder Point (ROP).
        
        Formula: ROP = (Average Daily Demand × Lead Time) + Safety Stock
        
        Industry Standard: APICS
        """
        return (avg_daily_demand * lead_time_days) + safety_stock
    
    @staticmethod
    def calculate_recommended_order_quantity(
        forecasted_demand: float,
        safety_stock: float,
        current_stock: float,
        moq: Optional[int] = None,
    ) -> float:
        """
        Calculate Recommended Order Quantity.
        
        Formula: Recommended Qty = Forecasted Demand + Safety Stock - Current Stock
        
        MOQ Constraint: If Recommended Qty < MOQ, use MOQ
        
        Industry Standard: APICS
        """
        recommended = forecasted_demand + safety_stock - current_stock
        
        if moq and recommended < moq:
            return float(moq)
        
        return max(recommended, 0.0)
    
    @staticmethod
    def calculate_stockout_risk(
        forecasted_demand: float,
        current_stock: float,
    ) -> str:
        """
        Calculate stockout risk level.
        
        Formula: Stockout Risk = (Forecasted Demand / Current Stock) × 100
        
        Risk Levels (Industry Standard):
        - Low: < 50%
        - Medium: 50-70%
        - High: 70-90%
        - Critical: > 90%
        """
        if current_stock <= 0:
            return "critical"
        
        risk_pct = (forecasted_demand / current_stock) * 100
        
        if risk_pct > 90:
            return "critical"
        elif risk_pct > 70:
            return "high"
        elif risk_pct > 50:
            return "medium"
        else:
            return "low"
    
    @staticmethod
    def calculate_stockout_date(
        current_stock: float,
        avg_daily_demand: float,
    ) -> Optional[date]:
        """
        Calculate predicted stockout date.
        
        Formula: Stockout Date = Today + (Current Stock / Average Daily Demand)
        """
        if avg_daily_demand <= 0:
            return None
        
        days_until_stockout = current_stock / avg_daily_demand
        stockout_date = date.today() + timedelta(days=int(days_until_stockout))
        return stockout_date
    
    @staticmethod
    def get_recommended_action(
        days_of_inventory_remaining: float,
        stockout_risk: str,
    ) -> Dict[str, str]:
        """
        Generate actionable recommendation.
        
        Returns:
            Dict with action, priority, and message
        """
        if days_of_inventory_remaining < 3 or stockout_risk == "critical":
            return {
                "action": "URGENT_REORDER",
                "priority": "critical",
                "message": f"Stockout expected in {days_of_inventory_remaining:.1f} days. Reorder immediately.",
            }
        elif days_of_inventory_remaining < 7 or stockout_risk == "high":
            return {
                "action": "REORDER",
                "priority": "high",
                "message": f"Low inventory: {days_of_inventory_remaining:.1f} days remaining. Reorder soon.",
            }
        elif days_of_inventory_remaining < 14 or stockout_risk == "medium":
            return {
                "action": "MONITOR",
                "priority": "medium",
                "message": f"Inventory level: {days_of_inventory_remaining:.1f} days. Monitor closely.",
            }
        else:
            return {
                "action": "OK",
                "priority": "low",
                "message": f"Sufficient inventory: {days_of_inventory_remaining:.1f} days remaining.",
            }

