from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator
from typing import Dict, Any

class HypertuningInterface(ABC, BaseEstimator):
    """Abstract interface for hyperparameter tuning methods."""
    
    def __init__(self, estimator, loss_fn, param_grid: Dict[str, Any], cv=None, n_jobs=-1, verbose=0):
 
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
        
        pass
    
    @property
    def optimized_estimator(self) -> BaseEstimator:
     
        if self.best_params_ is None:
            raise ValueError("Tuner has not been fitted yet")
        
        # Create new estimator with best parameters
        return self.estimator.__class__(**{**self.estimator.get_params(), **self.best_params_})
    
    def get_best_params(self) -> Dict[str, Any]:
        if self.best_params_ is None:
            raise ValueError("Tuner has not been fitted yet")
        return self.best_params_.copy()
    
    def get_best_score(self) -> float:
        if self.best_score_ is None:
            raise ValueError("Tuner has not been fitted yet")
        return self.best_score_
