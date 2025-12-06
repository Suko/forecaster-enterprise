"""
Unit tests for InventoryCalculator
"""
import pytest
from forecasting.applications.inventory.calculator import InventoryCalculator


class TestInventoryCalculator:
    """Test inventory calculations"""
    
    @pytest.fixture
    def calculator(self):
        return InventoryCalculator
    
    def test_calculate_dir(self, calculator):
        """Test Days of Inventory Remaining calculation"""
        dir_value = calculator.calculate_days_of_inventory_remaining(
            current_stock=500,
            avg_daily_demand=100,
        )
        assert dir_value == 5.0
    
    def test_calculate_dir_zero_demand(self, calculator):
        """Test DIR with zero demand"""
        dir_value = calculator.calculate_days_of_inventory_remaining(
            current_stock=500,
            avg_daily_demand=0,
        )
        assert dir_value == float('inf')
    
    def test_calculate_safety_stock(self, calculator):
        """Test safety stock calculation"""
        safety_stock = calculator.calculate_safety_stock(
            avg_daily_demand=100,
            lead_time_days=14,
            safety_stock_days=7,
            service_level=0.95,
        )
        assert safety_stock > 0
        # Should be approximately 100 * 7 * (1 + 1.65 * 0.2) = 931
        assert 800 < safety_stock < 1000
    
    def test_calculate_reorder_point(self, calculator):
        """Test reorder point calculation"""
        safety_stock = 200
        rop = calculator.calculate_reorder_point(
            avg_daily_demand=100,
            lead_time_days=14,
            safety_stock=safety_stock,
        )
        # ROP = (100 * 14) + 200 = 1600
        assert rop == 1600.0
    
    def test_calculate_recommended_order_quantity(self, calculator):
        """Test recommended order quantity"""
        qty = calculator.calculate_recommended_order_quantity(
            forecasted_demand=3000,
            safety_stock=200,
            current_stock=500,
            moq=100,
        )
        # Qty = 3000 + 200 - 500 = 2700
        assert qty == 2700.0
    
    def test_calculate_recommended_order_quantity_with_moq(self, calculator):
        """Test MOQ constraint"""
        qty = calculator.calculate_recommended_order_quantity(
            forecasted_demand=50,
            safety_stock=20,
            current_stock=60,
            moq=100,
        )
        # Qty = 50 + 20 - 60 = 10, but MOQ = 100, so should return 100
        assert qty == 100.0
    
    def test_calculate_stockout_risk(self, calculator):
        """Test stockout risk calculation"""
        risk = calculator.calculate_stockout_risk(
            forecasted_demand=500,
            current_stock=400,
        )
        # Risk = (500/400) * 100 = 125% -> critical
        assert risk == "critical"
        
        risk = calculator.calculate_stockout_risk(
            forecasted_demand=300,
            current_stock=500,
        )
        # Risk = (300/500) * 100 = 60% -> medium
        assert risk == "medium"
    
    def test_get_recommended_action(self, calculator):
        """Test recommendation generation"""
        rec = calculator.get_recommended_action(
            days_of_inventory_remaining=2.0,
            stockout_risk="critical",
        )
        assert rec["action"] == "URGENT_REORDER"
        assert rec["priority"] == "critical"
        
        rec = calculator.get_recommended_action(
            days_of_inventory_remaining=20.0,
            stockout_risk="low",
        )
        assert rec["action"] == "OK"
        assert rec["priority"] == "low"

