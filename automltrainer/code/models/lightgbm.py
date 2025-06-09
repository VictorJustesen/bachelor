import lightgbm as lgb
from sklearn.base import BaseEstimator, RegressorMixin
from .base_model import BaseModelConfig

class LightgbmConfig(BaseModelConfig, BaseEstimator, RegressorMixin):
    """LightGBM model with configuration"""

    def __init__(self, n_estimators=100, learning_rate=0.1, max_depth=-1,
                 num_leaves=31, subsample=1.0, colsample_bytree=1.0,
                 random_state=42, loss_fn=None, **kwargs):
        self.n_estimators = n_estimators
        self.learning_rate = learning_rate
        self.max_depth = max_depth
        self.num_leaves = num_leaves
        self.subsample = subsample
        self.colsample_bytree = colsample_bytree
        self.random_state = random_state
        self.loss_fn = loss_fn
        self.kwargs = kwargs
        self.model = None

    def _get_lgb_objective(self, loss_fn):
        """Map custom loss function to LightGBM objective"""
        if loss_fn is None:
            return 'regression_l2'  # Default to RMSE

        loss_name = loss_fn.name.lower()
        if loss_name == 'mae':
            return 'regression_l1'
        elif loss_name == 'rmse':
            return 'regression_l2'
        elif loss_name == 'mape':
            return 'mape'
        else:
            return 'regression_l2'  # Fallback

    def get_model(self, loss_fn=None, **kwargs):
        """Create LightGBM model with default parameters"""
        default_params = {
            'random_state': 42,
            'n_estimators': 100,
            'learning_rate': 0.1,
            'max_depth': -1,
            'loss_fn': loss_fn
        }
        params = {**default_params, **kwargs}
        return LightgbmConfig(**params)

    def get_model_name(self):
        return 'lightgbm'

    def get_param_grid(self, grid_type):
        """Get parameter grid for hyperparameter tuning"""
        grids = {
            'small': {
                'n_estimators': [100, 200],
                'learning_rate': [0.05, 0.1],
                'num_leaves': [20, 31, 40]
            },
            'big': {
                'n_estimators': [100, 200, 500, 1000],
                'learning_rate': [0.01, 0.05, 0.1],
                'max_depth': [-1, 10, 20],
                'num_leaves': [31, 50, 100],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0]
            },
            'custom': {
                'n_estimators': [100, 300, 600],
                'learning_rate': [0.01, 0.05, 0.1],
                'num_leaves': [31, 40, 50]
            }
        }
        return grids.get(grid_type, grids['small'])

    def fit(self, X, y):
        """Fit the LightGBM model"""
        objective = self._get_lgb_objective(self.loss_fn)

        self.model = lgb.LGBMRegressor(
            n_estimators=self.n_estimators,
            learning_rate=self.learning_rate,
            max_depth=self.max_depth,
            num_leaves=self.num_leaves,
            subsample=self.subsample,
            colsample_bytree=self.colsample_bytree,
            random_state=self.random_state,
            objective=objective,
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
            'num_leaves': self.num_leaves,
            'subsample': self.subsample,
            'colsample_bytree': self.colsample_bytree,
            'random_state': self.random_state,
            'loss_fn': self.loss_fn,
            **self.kwargs
        }

    def set_params(self, **params):
        """Set the parameters of this estimator"""
        for param, value in params.items():
            if hasattr(self, param):
                setattr(self, param, value)
            else:
                self.kwargs[param] = value
        return self