import numpy as np
import pandas as pd
from .hypertuning_interface import HypertuningInterface
import random

class RandomSearchTuner(HypertuningInterface):
    """Random search hyperparameter tuning - randomly samples from parameter space."""
    
    def __init__(self, estimator, loss_fn, param_grid, cv=None, n_iter=10, n_jobs=-1, verbose=0, random_state=None):
        super().__init__(estimator, loss_fn, param_grid, cv, n_jobs, verbose)
        self.n_iter = n_iter
        self.random_state = random_state
        
        if random_state is not None:
            random.seed(random_state)
            np.random.seed(random_state)
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'RandomSearchTuner':
        """Fit using random search."""
        from helper.helper import helper
        
        best_score = float('-inf') if self.loss_fn.higher_is_better else float('inf')
        best_params = None
        
        if self.verbose > 0:
            print(f"Testing {self.n_iter} random parameter combinations")
        
        for i in range(self.n_iter):
            # Generate random parameters
            params = {}
            for param_name, param_values in self.param_grid.items():
                if isinstance(param_values, list):
                    params[param_name] = random.choice(param_values)
                elif hasattr(param_values, 'rvs'):  # scipy distributions
                    params[param_name] = param_values.rvs()
                else:
                    # Assume it's a range or uniform distribution
                    if isinstance(param_values, tuple) and len(param_values) == 2:
                        low, high = param_values
                        if isinstance(low, int) and isinstance(high, int):
                            params[param_name] = random.randint(low, high)
                        else:
                            params[param_name] = random.uniform(low, high)
                    else:
                        params[param_name] = random.choice(param_values)
            
            if self.verbose > 1:
                print(f"  Testing params {i+1}/{self.n_iter}: {params}")
            
            # Cross-validation with proper scaling
            cv_scores = []
            
            for train_idx, val_idx in self.cv.split(X):
                X_train_cv = X.iloc[train_idx]
                X_val_cv = X.iloc[val_idx]
                y_train_cv = y.iloc[train_idx]
                y_val_cv = y.iloc[val_idx]
                
                # Scale this specific split
                data_scaler = helper()
                X_train_scaled, X_val_scaled = data_scaler.scale(X_train_cv, X_val_cv)
                
                # Create model with these parameters
                model = self.estimator.__class__(**{**self.estimator.get_params(), **params})
                model.fit(X_train_scaled, y_train_cv)
                predictions = model.predict(X_val_scaled)
                
                score = self.loss_fn(y_val_cv, predictions)
                cv_scores.append(score)
            
            # Average CV score for these parameters
            avg_score = np.mean(cv_scores)
            
            # Check if this is the best score
            is_better = (avg_score > best_score) if self.loss_fn.higher_is_better else (avg_score < best_score)
            
            if is_better:
                best_score = avg_score
                best_params = params
                if self.verbose > 1:
                    print(f"    New best score: {best_score:.4f}")
        
        self.best_score_ = best_score
        self.best_params_ = best_params
        
        if self.verbose > 0:
            print(f"Best parameters: {self.best_params_}")
            print(f"Best CV score: {self.best_score_:.4f}")
        
        return self
