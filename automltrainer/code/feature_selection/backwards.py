import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from .feature_selection_interface import FeatureSelectionInterface

class BackwardFeatureSelector(FeatureSelectionInterface):
    def __init__(self, estimator, loss_fn, cv=None, verbose=0):
        super().__init__(estimator, loss_fn, cv, verbose)
        self.scoring = 'neg_mean_squared_error'  # Keep for compatibility

    def fit(self, X, y):
        from helper.helper import helper  # Import helper
        
        available_features = list(X.columns)
        selected_features = list(X.columns)  # Start with all features
        
        # Calculate initial score with all features
        initial_scores = []
        for train_idx, val_idx in self.cv.split(X):
            X_train_cv = X.iloc[train_idx]
            X_val_cv = X.iloc[val_idx]
            y_train_cv = y.iloc[train_idx]
            y_val_cv = y.iloc[val_idx]
            
            data_scaler = helper()
            X_train_scaled, X_val_scaled = data_scaler.scale(X_train_cv, X_val_cv)
            
            temp_estimator = self.estimator.__class__(**self.estimator.get_params())
            temp_estimator.fit(X_train_scaled, y_train_cv)
            predictions = temp_estimator.predict(X_val_scaled)
            score = self.loss_fn(y_val_cv, predictions)
            initial_scores.append(score)
        
        self.best_score_ = np.mean(initial_scores)
        
        if self.verbose > 0:
            print(f"Starting backward feature selection with {len(selected_features)} features")
            print(f"Initial CV Score: {self.best_score_:.4f}")

        while len(selected_features) > 1:
            scores = {}
            
            for feature_to_drop in selected_features:
                temp_features = [f for f in selected_features if f != feature_to_drop]
                temp_X = X[temp_features]

                # Use cross-validation with proper scaling per split
                cv_scores = []
                
                for train_idx, val_idx in self.cv.split(temp_X):
                    X_train_cv = temp_X.iloc[train_idx]
                    X_val_cv = temp_X.iloc[val_idx]
                    y_train_cv = y.iloc[train_idx]
                    y_val_cv = y.iloc[val_idx]

                    # Scale this specific split using helper
                    data_scaler = helper()
                    X_train_scaled, X_val_scaled = data_scaler.scale(X_train_cv, X_val_cv)

                    # Clone estimator to avoid fitting issues
                    temp_estimator = self.estimator.__class__(**self.estimator.get_params())
                    temp_estimator.fit(X_train_scaled, y_train_cv)
                    predictions = temp_estimator.predict(X_val_scaled)

                    score = self.loss_fn(y_val_cv, predictions)
                    cv_scores.append(score)

                # Average CV score
                scores[feature_to_drop] = np.mean(cv_scores)

            # Find the feature whose removal gives the BEST score (lowest MAE)
            best_feature_to_drop = min(scores, key=scores.get)  # Min because lower MAE is better
            best_score_after_drop = scores[best_feature_to_drop]

            # Only drop if it improves or maintains performance
            if best_score_after_drop <= self.best_score_:  # <= because lower MAE is better
                self.best_score_ = best_score_after_drop
                selected_features.remove(best_feature_to_drop)
                if self.verbose > 0:
                    print(f"Dropped feature: {best_feature_to_drop}, CV Score: {self.best_score_:.4f}, Remaining: {len(selected_features)}")
            else:
                if self.verbose > 0:
                    print(f"No improvement found")
                break  # Stop if no improvement

        self.selected_features_ = selected_features  # Store the final selected features
        
        
        return self

    def transform(self, X):
        if self.selected_features_ is None:
            raise ValueError("BackwardFeatureSelector not fitted. Call fit() first.")
        return X[self.selected_features_]

    def fit_transform(self, X, y):
        return self.fit(X, y).transform(X)