from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing import Any, Tuple

class FeatureSelectionInterface(ABC, BaseEstimator, TransformerMixin):
    
    def __init__(self, estimator, loss_fn, cv=None, verbose=0):
    
        self.estimator = estimator
        self.loss_fn = loss_fn
        self.cv = cv
        self.verbose = verbose
        self.selected_features_ = None
        self.best_score_ = None
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'FeatureSelectionInterface':
      
        pass
    
    @abstractmethod
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
       
        pass
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
      
        return self.fit(X, y).transform(X)
    
    @property
    def n_features_selected(self) -> int:
        """Number of features selected."""
        if self.selected_features_ is None:
            return 0
        return len(self.selected_features_)
    
    @property
    def feature_names(self) -> list:
        """Names of selected features."""
        return self.selected_features_ if self.selected_features_ is not None else []
