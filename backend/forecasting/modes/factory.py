"""
Model Factory

Creates forecasting model instances based on model identifier.
"""
from typing import Dict
from ..core.models.base import BaseForecastModel
from .ml.chronos2 import Chronos2Model
from .statistical.moving_average import MovingAverageModel


class ModelFactory:
    """Factory for creating forecasting model instances"""
    
    _models: Dict[str, type] = {
        "chronos-2": Chronos2Model,
        "statistical_ma7": MovingAverageModel,
    }
    
    @classmethod
    def create_model(cls, model_id: str, **kwargs) -> BaseForecastModel:
        """
        Create model instance based on model_id.
        
        Args:
            model_id: Model identifier ("chronos-2", "statistical_ma7", etc.)
            **kwargs: Additional arguments passed to model constructor
        
        Returns:
            BaseForecastModel instance
        
        Raises:
            ValueError: If model_id is not supported
        """
        if model_id not in cls._models:
            available = ", ".join(cls._models.keys())
            raise ValueError(
                f"Unknown model_id: {model_id}. "
                f"Available models: {available}"
            )
        
        model_class = cls._models[model_id]
        return model_class(**kwargs)
    
    @classmethod
    def list_models(cls) -> list[str]:
        """List all available model identifiers"""
        return list(cls._models.keys())
    
    @classmethod
    def register_model(cls, model_id: str, model_class: type) -> None:
        """
        Register a new model class.
        
        Args:
            model_id: Model identifier
            model_class: Model class (must inherit from BaseForecastModel)
        """
        if not issubclass(model_class, BaseForecastModel):
            raise TypeError("model_class must inherit from BaseForecastModel")
        cls._models[model_id] = model_class

