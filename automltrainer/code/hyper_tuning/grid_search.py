import numpy as np
from sklearn.base import BaseEstimator
from sklearn.model_selection import ParameterGrid
from sklearn.metrics import mean_squared_error
from .hypertuning_interface import HypertuningInterface
from .hypertuning_interface import HypertuningInterface

class GridSearchTuner(HypertuningInterface):
    def __init__(self, estimator, loss_fn, param_grid, cv=None, n_jobs=-1, verbose=0):
        super().__init__(estimator, loss_fn, param_grid, cv, n_jobs, verbose)

    def fit(self, X, y):
        """Fit with proper scaling per CV split"""
        from helper.helper import helper  # Import helper
        
        param_combinations = list(ParameterGrid(self.param_grid))
        best_score = float('-inf')
        best_params = None

        if self.verbose > 0:
            print(f"Testing {len(param_combinations)} parameter combinations")

        for i, params in enumerate(param_combinations):
            if self.verbose > 1:
                print(f"  Testing params {i+1}/{len(param_combinations)}: {params}")

            # Cross-validation with proper scaling
            cv_scores = []
            
            for train_idx, val_idx in self.cv.split(X):
                X_train_cv = X.iloc[train_idx]
                X_val_cv = X.iloc[val_idx]
                y_train_cv = y.iloc[train_idx]
                y_val_cv = y.iloc[val_idx]

                # Scale this specific split using helper
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
            
            if avg_score > best_score:
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