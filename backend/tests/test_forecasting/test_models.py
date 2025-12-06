"""
Unit tests for forecasting models
"""
import pytest
import pandas as pd
from datetime import date, timedelta

from forecasting.core.models.base import BaseForecastModel
from forecasting.modes.statistical.moving_average import MovingAverageModel
from tests.fixtures.test_data_loader import TestDataLoader


class TestMovingAverageModel:
    """Test MovingAverageModel"""
    
    @pytest.fixture
    def model(self):
        return MovingAverageModel(window=7)
    
    @pytest.fixture
    def sample_data(self, test_data_loader):
        """Get sample historical data"""
        return test_data_loader.get_item_data("SKU001")
    
    @pytest.mark.asyncio
    async def test_initialize(self, model):
        """Test model initialization"""
        await model.initialize()
        assert model.is_initialized()
        assert model.model_name == "statistical_ma7"
    
    @pytest.mark.asyncio
    async def test_predict_basic(self, model, sample_data):
        """Test basic prediction"""
        await model.initialize()
        
        # Use subset of data
        context_df = sample_data.head(30)
        
        predictions = await model.predict(
            context_df=context_df,
            prediction_length=7,
        )
        
        assert len(predictions) == 7
        assert "point_forecast" in predictions.columns
        assert "timestamp" in predictions.columns
        assert all(predictions["point_forecast"] >= 0)
    
    @pytest.mark.asyncio
    async def test_validate_input(self, model, sample_data):
        """Test input validation"""
        await model.initialize()
        
        # Test empty DataFrame
        with pytest.raises(ValueError, match="empty"):
            await model.predict(
                context_df=pd.DataFrame(),
                prediction_length=7,
            )
        
        # Test insufficient history
        short_data = sample_data.head(5)
        with pytest.raises(ValueError, match="Insufficient history"):
            await model.predict(
                context_df=short_data,
                prediction_length=7,
            )
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, model):
        """Test model info"""
        await model.initialize()
        info = model.get_model_info()
        
        assert info["model_name"] == "statistical_ma7"
        assert info["window"] == 7
        assert info["initialized"] is True


class TestModelFactory:
    """Test ModelFactory"""
    
    def test_create_statistical_model(self):
        """Test creating statistical model"""
        from forecasting.modes.factory import ModelFactory
        
        model = ModelFactory.create_model("statistical_ma7")
        assert isinstance(model, MovingAverageModel)
        assert model.model_name == "statistical_ma7"
    
    def test_create_invalid_model(self):
        """Test creating invalid model"""
        from forecasting.modes.factory import ModelFactory
        
        with pytest.raises(ValueError, match="Unknown model_id"):
            ModelFactory.create_model("invalid_model")
    
    def test_list_models(self):
        """Test listing available models"""
        from forecasting.modes.factory import ModelFactory
        
        models = ModelFactory.list_models()
        assert "statistical_ma7" in models
        assert "chronos-2" in models

