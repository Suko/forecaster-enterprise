"""
Unit tests for QualityCalculator
"""
import pytest
from forecasting.services.quality_calculator import QualityCalculator


class TestQualityCalculator:
    """Test quality metric calculations"""
    
    def test_calculate_mape(self):
        """Test MAPE calculation"""
        actuals = [100, 110, 120, 130, 140]
        forecasts = [95, 105, 115, 125, 135]
        
        mape = QualityCalculator.calculate_mape(actuals, forecasts)
        assert mape is not None
        assert mape > 0
        # Should be approximately 5% error
        assert 4 < mape < 6
    
    def test_calculate_mae(self):
        """Test MAE calculation"""
        actuals = [100, 110, 120]
        forecasts = [95, 105, 115]
        
        mae = QualityCalculator.calculate_mae(actuals, forecasts)
        assert mae == 5.0  # Average of |100-95|, |110-105|, |120-115|
    
    def test_calculate_rmse(self):
        """Test RMSE calculation"""
        actuals = [100, 110, 120]
        forecasts = [95, 105, 115]
        
        rmse = QualityCalculator.calculate_rmse(actuals, forecasts)
        assert rmse is not None
        # RMSE = sqrt((25+25+25)/3) = sqrt(25) = 5.0
        assert abs(rmse - 5.0) < 0.01
    
    def test_calculate_bias(self):
        """Test bias calculation"""
        actuals = [100, 110, 120]
        forecasts = [105, 115, 125]  # Over-forecasting by 5
        
        bias = QualityCalculator.calculate_bias(actuals, forecasts)
        assert bias == 5.0  # Positive = over-forecasting
        
        forecasts = [95, 105, 115]  # Under-forecasting by 5
        bias = QualityCalculator.calculate_bias(actuals, forecasts)
        assert bias == -5.0  # Negative = under-forecasting
    
    def test_calculate_mape_with_zero_actuals(self):
        """Test MAPE with zero actuals (should skip)"""
        actuals = [0, 100, 110]
        forecasts = [0, 95, 105]
        
        mape = QualityCalculator.calculate_mape(actuals, forecasts)
        # Should calculate from non-zero values only
        assert mape is not None
        assert mape > 0

