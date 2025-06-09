import numpy as np
from sklearn.base import BaseEstimator
from helper.helper import helper

class LineSearchTuner(BaseEstimator):
    def __init__(self, estimator, loss_fn, param_grid, cv=None, max_passes=2, n_jobs=-1, verbose=0):
        self.estimator = estimator
        self.param_grid = param_grid
        self.cv = cv
        self.loss_fn = loss_fn
        self.max_passes = max_passes
        self.n_jobs = n_jobs
        self.verbose = verbose
        self.best_params_ = None
        self.best_score_ = None

    def fit(self, X, y):
        """Fit using line search, optimizing one parameter at a time."""
        # Start with default or initial model parameters
        best_params = {k: v[0] for k, v in self.param_grid.items()}
        self.best_score_ = float('-inf') if self.loss_fn.higher_is_better else float('inf')

        if self.verbose > 0:
            print(f"Starting Line Search with initial params: {best_params}")

        for pass_num in range(self.max_passes):
            pass_improved = False
            if self.verbose > 0:
                print(f"\n--- Pass {pass_num + 1}/{self.max_passes} ---")

            for param_name, param_values in self.param_grid.items():
                param_scores = {}

                for value in param_values:
                    current_params = best_params.copy()
                    current_params[param_name] = value

                    # Cross-validation with proper scaling
                    cv_scores = []
                    for train_idx, val_idx in self.cv.split(X):
                        X_train_cv, X_val_cv = X.iloc[train_idx], X.iloc[val_idx]
                        y_train_cv, y_val_cv = y.iloc[train_idx], y.iloc[val_idx]

                        data_scaler = helper()
                        X_train_scaled, X_val_scaled = data_scaler.scale(X_train_cv, X_val_cv)

                        model = self.estimator.__class__(**{**self.estimator.get_params(), **current_params})
                        model.fit(X_train_scaled, y_train_cv)
                        predictions = model.predict(X_val_scaled)
                        score = self.loss_fn(y_val_cv, predictions)
                        cv_scores.append(score)

                    param_scores[value] = np.mean(cv_scores)

                # Find best value for the current parameter
                best_value_for_param = min(param_scores, key=param_scores.get) if not self.loss_fn.higher_is_better else max(param_scores, key=param_scores.get)
                current_best_score = param_scores[best_value_for_param]

                # Check for improvement
                improvement = (current_best_score < self.best_score_) if not self.loss_fn.higher_is_better else (current_best_score > self.best_score_)

                if improvement:
                    self.best_score_ = current_best_score
                    best_params[param_name] = best_value_for_param
                    pass_improved = True
                    if self.verbose > 0:
                        print(f"  New best for '{param_name}': {best_value_for_param} -> Score: {self.best_score_:.4f}")

            if not pass_improved and pass_num > 0:
                if self.verbose > 0:
                    print("Stopping early, no improvement in a full pass.")
                break

        self.best_params_ = best_params
        if self.verbose > 0:
            print(f"\nBest parameters found: {self.best_params_}")
            print(f"Best CV score: {self.best_score_:.4f}")

        return self