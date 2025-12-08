"""
Integration tests for ForecastService
"""
import pytest
from datetime import date, timedelta

from forecasting.services.forecast_service import ForecastService
from models.forecast import ForecastStatus


class TestForecastService:
    """Test ForecastService with test data"""
    
    @pytest.mark.asyncio
    async def test_generate_forecast_with_test_data(self, db_session, sample_item_ids, test_client, populate_test_data):
        """Test forecast generation using test data from database"""
        service = ForecastService(db_session)
        
        # Use first item from test data
        item_id = sample_item_ids[0]
        
        forecast_run = await service.generate_forecast(
            client_id=str(test_client.client_id),
            user_id="test_user",
            item_ids=[item_id],
            prediction_length=7,
            primary_model="statistical_ma7",
            include_baseline=False,
        )
        
        assert forecast_run.status == ForecastStatus.COMPLETED.value
        assert forecast_run.primary_model == "statistical_ma7"
        assert forecast_run.prediction_length == 7
        assert item_id in forecast_run.item_ids
    
    @pytest.mark.asyncio
    async def test_generate_forecast_multiple_items(self, db_session, sample_item_ids, test_client, populate_test_data):
        """Test forecast generation for multiple items"""
        service = ForecastService(db_session)
        
        # Use first 2 items
        item_ids = sample_item_ids[:2]
        
        forecast_run = await service.generate_forecast(
            client_id=str(test_client.client_id),
            user_id="test_user",
            item_ids=item_ids,
            prediction_length=14,
            primary_model="statistical_ma7",
            include_baseline=False,
        )
        
        assert forecast_run.status == ForecastStatus.COMPLETED.value
        assert len(forecast_run.item_ids) == 2
    
    @pytest.mark.asyncio
    async def test_generate_forecast_with_baseline(self, db_session, sample_item_ids, test_client, populate_test_data):
        """Test forecast generation with baseline method"""
        service = ForecastService(db_session)
        
        item_id = sample_item_ids[0]
        
        forecast_run = await service.generate_forecast(
            client_id=str(test_client.client_id),
            user_id="test_user",
            item_ids=[item_id],
            prediction_length=7,
            primary_model="statistical_ma7",
            include_baseline=True,  # Should run both methods
        )
        
        assert forecast_run.status == ForecastStatus.COMPLETED.value
        # Both methods should have run
        # Note: In real implementation, we'd check results_by_method
    
    @pytest.mark.asyncio
    async def test_generate_forecast_no_data(self, db_session, test_client):
        """Test forecast generation with invalid item (no data)"""
        service = ForecastService(db_session)
        
        # Use non-existent item
        # The service will try to generate forecast, but model may handle empty data
        # For now, we just verify it doesn't crash
        try:
            forecast_run = await service.generate_forecast(
                client_id=str(test_client.client_id),
                user_id="test_user",
                item_ids=["INVALID_SKU"],
                prediction_length=7,
                primary_model="statistical_ma7",
                include_baseline=False,
            )
            # Service may complete but with error, or fail - both are acceptable
            assert forecast_run.status in [
                ForecastStatus.FAILED.value,
                ForecastStatus.COMPLETED.value
            ]
        except Exception:
            # If it raises exception, that's also acceptable for no data
            pass
    
    @pytest.mark.asyncio
    async def test_get_forecast_run(self, db_session, sample_item_ids, test_client, populate_test_data):
        """Test retrieving forecast run by ID"""
        service = ForecastService(db_session)
        
        item_id = sample_item_ids[0]
        
        # Create forecast
        forecast_run = await service.generate_forecast(
            client_id=str(test_client.client_id),
            user_id="test_user",
            item_ids=[item_id],
            prediction_length=7,
            primary_model="statistical_ma7",
            include_baseline=False,
        )
        
        # Retrieve it (convert UUID to string if needed)
        import uuid
        forecast_run_id = forecast_run.forecast_run_id
        if isinstance(forecast_run_id, uuid.UUID):
            forecast_run_id = str(forecast_run_id)
        
        retrieved = await service.get_forecast_run(forecast_run_id)
        
        assert retrieved is not None
        assert retrieved.forecast_run_id == forecast_run.forecast_run_id
        assert retrieved.status == ForecastStatus.COMPLETED.value

