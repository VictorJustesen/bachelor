import xgboost as xgb
from sklearn.base import BaseEstimator, RegressorMixin
from .base_model import BaseModelConfig

class XGBoostConfig(BaseModelConfig, BaseEstimator, RegressorMixin):
    """XGBoost model with configuration - combines wrapper and config in one class"""
    
    def __init__(self, n_estimators=100, learning_rate=0.1, max_depth=6, 
                 subsample=1.0, colsample_bytree=1.0, random_state=42, **kwargs):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.kwargs = kwargs
        self.model = None
    
    # BaseModelConfig methods (configuration interface)
    def get_model(self, **kwargs):
        """Create XGBoost model with default parameters"""
        default_params = {
            'random_state': 42,
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6
        }
        params = {**default_params, **kwargs}
        return XGBoostConfig(**params)
    
    def get_model_name(self):
        return 'xgboost'
    
    def get_param_grid(self, grid_type):
        """Get parameter grid for hyperparameter tuning"""
        grids = {
            'small': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1],   
                'max_depth': [3, 6, 9]
            },
            'big': {
                'n_estimators': [100, 200, 300, 750],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'max_depth': [3, 6, 9],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            },
            'custom': {
                'n_estimators': [100, 300, 600],
                'learning_rate': [0.01, 0.05],
                'max_depth': [3, 6, 9]
            }
        }
        return grids.get(grid_type)
    
    # Sklearn interface methods (model functionality)
    def fit(self, X, y):
        """Fit the XGBoost model"""
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            **self.kwargs
        )
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not fitted yet. Call fit() first.")
        return self.model.predict(X)
    
    def get_params(self, deep=True):
        """Get parameters for this estimator"""
        return {
            'n_estimators': self.n_estimators,
            'learning_rate': self.learning_rate,
            'max_depth': self.max_depth,
            'subsample': self.subsample,
            'colsample_bytree': self.colsample_bytree,
            'random_state': self.random_state,
            **self.kwargs
        }
    
    def set_params(self, **params):
        """Set the parameters of this estimator"""
        for param, value in params.items():
            if param in ['n_estimators', 'learning_rate', 'max_depth', 
                        'subsample', 'colsample_bytree', 'random_state']:
                setattr(self, param, value)
            else:
                self.kwargs[param] = value
        return self