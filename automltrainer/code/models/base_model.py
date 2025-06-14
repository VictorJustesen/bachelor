from abc import ABC, abstractmethod
from typing import Dict, List, Any
import numpy as np
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

class BaseModelConfig(ABC):
    """Abstract base class for all model configurations"""
    
    @abstractmethod
    def get_model(self, **kwargs):
        """Create model instance with parameters"""
        pass
    
    @abstractmethod
    def get_param_grid(self, grid_type):
        """Get parameter grid for hyperparameter tuning"""
        pass
    
    @abstractmethod
    def get_model_name(self):
        """Get model name"""
        pass
    
    def get_default_configs(self):
        """Get default model configurations for multiple model training"""
        return {
            f'{self.get_model_name()}_quick': self.get_param_grid('quick'),
            f'{self.get_model_name()}_full': self.get_param_grid('full'),
            f'{self.get_model_name()}_conservative': self.get_param_grid('conservative')
        }
    
    def train_and_predict(self, X_train, y_train, X_test, loss_fn=None, **model_params):
        """
        Simple train and predict - no hyperparameter tuning, no metrics calculation
        
        Args:
            X_train, y_train: Training data
            X_test: Test data for prediction
            loss_fn: Custom loss function to pass to model
            **model_params: Specific model parameters to use
            
        Returns:
            Tuple of (trained_model, predictions)
        """
        # Create and train model with specific parameters and loss function
        model = self.get_model(loss_fn=loss_fn, **model_params)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        return model, y_pred
    
    def save_model(self, filepath):
        """
        Optional method to save model weights/state in model-specific format.
        
        Args:
            filepath (str): Base filepath (without extension)
            
        Returns:
            str or None: Path to saved weights file, or None if not implemented
        """
        return None  # Default implementation - no special saving needed