from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from typing import Any, Tuple

class FeatureSelectionInterface(ABC, BaseEstimator, TransformerMixin):
    """Abstract interface for feature selection methods."""
    
    def __init__(self, estimator, loss_fn, cv=None, verbose=0):
        """
        Initialize feature selector.
        
        Args:
            estimator: The model to use for evaluation
            loss_fn: Loss function to optimize
            cv: Cross-validation splitter
            verbose: Verbosity level
        """
        self.estimator = estimator
        self.loss_fn = loss_fn
        self.cv = cv
        self.verbose = verbose
        self.selected_features_ = None
        self.best_score_ = None
    
    @abstractmethod
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'FeatureSelectionInterface':
        """
        Fit the feature selector on training data.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            self: Fitted selector
        """
        pass
    
    @abstractmethod
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data using selected features.
        
        Args:
            X: Feature matrix to transform
            
        Returns:
            Transformed feature matrix with selected features only
        """
        pass
    
    def fit_transform(self, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        """
        Fit selector and transform data in one step.
        
        Args:
            X: Feature matrix
            y: Target vector
            
        Returns:
            Transformed feature matrix with selected features only
        """
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
