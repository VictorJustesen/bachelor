import xgboost as xgb
from sklearn.base import BaseEstimator, RegressorMixin
from .base_model import BaseModelConfig

class XGBoostConfig(BaseModelConfig, BaseEstimator, RegressorMixin):
    """XGBoost model with configuration - combines wrapper and config in one class"""
    
    def __init__(self, n_estimators=100, learning_rate=0.1, max_depth=6, 
                 subsample=1.0, colsample_bytree=1.0, random_state=42, 
                 loss_fn=None, **kwargs):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.loss_fn = loss_fn  # Store custom loss function
        self.kwargs = kwargs
        self.model = None
    
    def _get_xgb_objective(self, loss_fn):
        """Map custom loss function to XGBoost objective"""
        if loss_fn is None:
            return 'reg:squarederror'  # Default
            
        loss_name = loss_fn.name.lower()
        if loss_name == 'mae':
            return 'reg:absoluteerror'
        elif loss_name == 'rmse':
            return 'reg:squarederror'
        else:
            return 'reg:squarederror'  # Fallback
    
    # BaseModelConfig methods (configuration interface)
    def get_model(self, loss_fn=None, **kwargs):
        """Create XGBoost model with default parameters"""
        default_params = {
            'random_state': 42,
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': 6,
            'loss_fn': loss_fn  # Pass loss function
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
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [3, 6, 9]
            }
        }
        return grids.get(grid_type, grids['small'])
    
    # Sklearn interface methods (model functionality)
    def fit(self, X, y):
        """Fit the XGBoost model"""
        # Map custom loss to XGBoost objective
        objective = self._get_xgb_objective(self.loss_fn)
        
        self.model = xgb.XGBRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            objective=objective,  # Use mapped objective
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
            'loss_fn': self.loss_fn,
            **self.kwargs
        }
    
    def set_params(self, **params):
        """Set the parameters of this estimator"""
        for param, value in params.items():
            if param in ['n_estimators', 'learning_rate', 'max_depth', 
                        'subsample', 'colsample_bytree', 'random_state', 'loss_fn']:
                setattr(self, param, value)
            else:
                self.kwargs[param] = value
        return self
    
    def save_model(self, filepath):
        """Save XGBoost model weights to JSON format"""
        if hasattr(self, 'model') and self.model is not None:
            weights_path = f"{filepath}_xgboost.json"
            self.model.save_model(weights_path)
            return weights_path
        return None