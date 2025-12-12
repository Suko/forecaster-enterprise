"""
Unit tests for QualityCalculator
"""
import pytest
from forecasting.services.quality_calculator import QualityCalculator
from models.forecast import ForecastResult, ForecastRun
from datetime import date, timedelta
import uuid


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

    @pytest.mark.asyncio
    async def test_calculate_quality_metrics_with_db(self, db_session, test_client):
        """Test async calculate_quality_metrics method with database"""
        from sqlalchemy import select

        # Create a forecast run
        forecast_run = ForecastRun(
            forecast_run_id=uuid.uuid4(),
            client_id=test_client.client_id,
            user_id="test_user",
            primary_model="statistical_ma7",
            prediction_length=7,
            item_ids=["SKU001"],
            status="completed",
        )
        db_session.add(forecast_run)
        await db_session.flush()

        # Create forecast results with actuals
        base_date = date.today()
        for i in range(7):
            result = ForecastResult(
                result_id=uuid.uuid4(),
                forecast_run_id=forecast_run.forecast_run_id,
                client_id=test_client.client_id,
                item_id="SKU001",
                method="statistical_ma7",
                date=base_date + timedelta(days=i),
                horizon_day=i + 1,
                point_forecast=100.0 + i,
                actual_value=105.0 + i,  # Actual is 5 units higher
            )
            db_session.add(result)

        await db_session.commit()

        # Calculate quality metrics
        calculator = QualityCalculator(db_session)
        metrics = await calculator.calculate_quality_metrics(
            client_id=str(test_client.client_id),
            item_id="SKU001",
            method="statistical_ma7",
        )

        assert metrics["sample_size"] == 7
        assert metrics["mae"] is not None
        assert metrics["mae"] > 0
        assert metrics["bias"] is not None
        # Should show negative bias (under-forecasting)
        assert metrics["bias"] < 0

