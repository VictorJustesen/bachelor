from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.base import BaseEstimator, RegressorMixin
from .base_model import BaseModelConfig

class LinearRegressionConfig(BaseModelConfig, BaseEstimator, RegressorMixin):
    """Linear Regression model with configuration - combines wrapper and config in one class"""
    
    def __init__(self, model_type='linear', alpha=1.0, l1_ratio=0.5, 
                 fit_intercept=True, random_state=42, loss_fn=None, **kwargs):
        self.model_type = model_type  # 'linear', 'ridge', 'lasso', 'elastic'
        self.alpha = alpha  # Regularization strength
        self.l1_ratio = l1_ratio  # ElasticNet mixing parameter
        self.fit_intercept = fit_intercept
        self.random_state = random_state
        self.loss_fn = loss_fn  # Store custom loss function
        self.kwargs = kwargs
        self.model = None
    
    def _get_linear_model(self, model_type, alpha, l1_ratio, fit_intercept, random_state):
        """Get the appropriate linear model based on type"""
        if model_type == 'linear':
            return LinearRegression(fit_intercept=fit_intercept)
        elif model_type == 'ridge':
            return Ridge(alpha=alpha, fit_intercept=fit_intercept, random_state=random_state)
        elif model_type == 'lasso':
            return Lasso(alpha=alpha, fit_intercept=fit_intercept, random_state=random_state, max_iter=2000)
        elif model_type == 'elastic':
            return ElasticNet(alpha=alpha, l1_ratio=l1_ratio, fit_intercept=fit_intercept, 
                            random_state=random_state, max_iter=2000)
        else:
            return LinearRegression(fit_intercept=fit_intercept)  # Fallback
    
    # BaseModelConfig methods (configuration interface)
    def get_model(self, loss_fn=None, **kwargs):
        """Create Linear Regression model with default parameters"""
        default_params = {
            'model_type': 'linear',
            'alpha': 1.0,
            'l1_ratio': 0.5,
            'fit_intercept': True,
            'random_state': 42,
            'loss_fn': loss_fn  # Pass loss function
        }
        params = {**default_params, **kwargs}
        return LinearRegressionConfig(**params)
    
    def get_model_name(self):
        return 'linear_regression'
    
    def get_param_grid(self, grid_type):
        """Get parameter grid for hyperparameter tuning"""
        grids = {
            'small': {
                'model_type': ['linear', 'ridge'],
                'alpha': [0.1, 1.0, 10.0],
                'fit_intercept': [True]
            },
            'big': {
                'model_type': ['linear', 'ridge', 'lasso', 'elastic'],
                'alpha': [0.01, 0.1, 1.0, 10.0, 100.0],
                'l1_ratio': [0.1, 0.5, 0.7, 0.9],
                'fit_intercept': [True, False]
            },
            'custom': {
                'model_type': ['ridge', 'lasso'],
                'alpha': [0.1, 1.0, 10.0],
                'fit_intercept': [True]
            }
        }
        return grids.get(grid_type, grids['small'])
    
    # Sklearn interface methods (model functionality)
    def fit(self, X, y):
        """Fit the Linear Regression model"""
        self.model = self._get_linear_model(
            model_type=self.model_type,
            alpha=self.alpha,
            l1_ratio=self.l1_ratio,
            fit_intercept=self.fit_intercept,
            random_state=self.random_state
        )
        
        # Fit the model
        self.model.fit(X, y)
        return self
    
    def predict(self, X):
        """Make predictions"""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return self.model.predict(X)
    
    def get_params(self, deep=True):
        """Get parameters for this estimator"""
        return {
            'model_type': self.model_type,
            'alpha': self.alpha,
            'l1_ratio': self.l1_ratio,
            'fit_intercept': self.fit_intercept,
            'random_state': self.random_state,
            'loss_fn': self.loss_fn
        }
    
    def set_params(self, **params):
        """Set the parameters of this estimator"""
        for key, value in params.items():
            setattr(self, key, value)
        return self
    
    def score(self, X, y):
        """Return the coefficient of determination R^2 of the prediction"""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        return self.model.score(X, y)
    
    def get_feature_importance(self):
        """Get feature importance (coefficients for linear models)"""
        if self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        if hasattr(self.model, 'coef_'):
            return abs(self.model.coef_)  # Return absolute coefficients as importance
        else:
            return None
    
    def get_model_info(self):
        """Get information about the fitted model"""
        if self.model is None:
            return {"status": "not_fitted"}
        
        info = {
            "model_type": self.model_type,
            "alpha": self.alpha,
            "fit_intercept": self.fit_intercept,
            "status": "fitted"
        }
        
        if hasattr(self.model, 'coef_'):
            info["n_features"] = len(self.model.coef_)
            info["intercept"] = self.model.intercept_ if hasattr(self.model, 'intercept_') else None
        
        # Add regularization info
        if self.model_type in ['ridge', 'lasso', 'elastic']:
            info["regularization"] = self.model_type
            info["alpha"] = self.alpha
            if self.model_type == 'elastic':
                info["l1_ratio"] = self.l1_ratio
        
        return info
