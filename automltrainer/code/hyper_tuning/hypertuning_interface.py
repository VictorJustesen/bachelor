from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator
from typing import Dict, Any

class HypertuningInterface(ABC, BaseEstimator):
    """Abstract interface for hyperparameter tuning methods."""
    
    def __init__(self, estimator, loss_fn, param_grid: Dict[str, Any], cv=None, n_jobs=-1, verbose=0):
        """
        Initialize hyperparameter tuner.
        
        Args:
            estimator: The model to tune
            loss_fn: Loss function to optimize
            param_grid: Dictionary of parameters to search
            cv: Cross-validation splitter
            n_jobs: Number of parallel jobs
            verbose: Verbosity level
        """
        self.estimator = estimator
        self.loss_fn = loss_fn
        self.param_grid = param_grid
        self.cv = cv
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.best_params_ = None
        self.best_score_ = None
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'HypertuningInterface':
        """
        Fit the hyperparameter tuner on training data.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            self: Fitted tuner with best_params_ and best_score_ set
        """
        pass
    
    @property
    def optimized_estimator(self) -> BaseEstimator:
        """
        Get an estimator with the best parameters found.
        
        Returns:
            Estimator instance with best parameters
        """
        if self.best_params_ is None:
            raise ValueError("Tuner has not been fitted yet")
        
        # Create new estimator with best parameters
        return self.estimator.__class__(**{**self.estimator.get_params(), **self.best_params_})
    
    def get_best_params(self) -> Dict[str, Any]:
        """Get the best parameters found."""
        if self.best_params_ is None:
            raise ValueError("Tuner has not been fitted yet")
        return self.best_params_.copy()
    
    def get_best_score(self) -> float:
        """Get the best score achieved."""
        if self.best_score_ is None:
            raise ValueError("Tuner has not been fitted yet")
        return self.best_score_
