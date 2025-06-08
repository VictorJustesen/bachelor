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
    
    def train_and_predict(self, X_train, y_train, X_test, **model_params):
        """
        Simple train and predict - no hyperparameter tuning, no metrics calculation
        
        Args:
            X_train, y_train: Training data
            X_test: Test data for prediction
            **model_params: Specific model parameters to use
            
        Returns:
            Tuple of (trained_model, predictions)
        """
        # Create and train model with specific parameters
        model = self.get_model(**model_params)
        model.fit(X_train, y_train)
        
        # Make predictions
        y_pred = model.predict(X_test)
        
        return model, y_pred
    
    def get_error_score(self, X_train, y_train, X_test, y_test, metric='rmse', **model_params):
        """
        Train model and return single error score
        
        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
            metric: Which metric to return ('rmse', 'mae', 'mse', 'r2')
            **model_params: Model parameters
            
        Returns:
            Single error score
        """
        model, y_pred = self.train_and_predict(X_train, y_train, X_test, **model_params)
        
        if metric == 'rmse':
            return np.sqrt(mean_squared_error(y_test, y_pred))
        elif metric == 'mae':
            return mean_absolute_error(y_test, y_pred)
        elif metric == 'mse':
            return mean_squared_error(y_test, y_pred)
        elif metric == 'r2':
            return r2_score(y_test, y_pred)
        else:
            raise ValueError(f"Unknown metric: {metric}")