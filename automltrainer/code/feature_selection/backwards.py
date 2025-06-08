import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import TimeSeriesSplit

class BackwardFeatureSelector(BaseEstimator, TransformerMixin):
    def __init__(self, estimator, cv=None, scoring='neg_mean_squared_error', verbose=0):
        self.estimator = estimator  # The model to use for evaluation
        self.cv = cv  # CV splitter (e.g., TimeSeriesSplit)
        self.scoring = scoring
        self.verbose = verbose
        self.selected_features_ = None  # To store the final selected features
        self.best_score_ = None

    def fit(self, X, y):
        """Fit using provided CV splitter with proper scaling per split"""
        from helper.helper import helper  # Import helper
        
        available_features = list(X.columns)
        selected_features = list(X.columns)  # Start with all features
        self.best_score_ = float('-inf')  # Initialize with a very low score

        if self.verbose > 0:
            print(f"Starting backward feature selection with {len(selected_features)} features")

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

                    if self.scoring == 'neg_mean_squared_error':
                        score = -mean_squared_error(y_val_cv, predictions)  # Negative for maximization
                    else:
                        raise ValueError(f"Unsupported scoring metric: {self.scoring}")
                    
                    cv_scores.append(score)

                # Average CV score
                scores[feature_to_drop] = np.mean(cv_scores)

            best_feature_to_drop = max(scores, key=scores.get)

            if scores[best_feature_to_drop] > self.best_score_:  # Improvement
                self.best_score_ = scores[best_feature_to_drop]
                selected_features.remove(best_feature_to_drop)
                if self.verbose > 0:
                    print(f"Dropped feature: {best_feature_to_drop}, CV Score: {self.best_score_:.4f}, Remaining: {len(selected_features)}")
            else:
                if self.verbose > 0:
                    print("No improvement found, stopping feature selection")
                break  # Stop if no improvement

        self.selected_features_ = selected_features  # Store the final selected features
        
        if self.verbose > 0:
            print(f"Feature selection complete. Selected {len(self.selected_features_)} features")
        
        return self

    def transform(self, X):
        """Transform any dataset using selected features"""
        if self.selected_features_ is None:
            raise ValueError("BackwardFeatureSelector not fitted. Call fit() first.")
        return X[self.selected_features_]

    def fit_transform(self, X, y):
        """Fit and transform in one step"""
        return self.fit(X, y).transform(X)