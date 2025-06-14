import pandas as pd
import numpy as np
from .feature_selection_interface import FeatureSelectionInterface

class ForwardFeatureSelector(FeatureSelectionInterface):
    """Forward feature selection - starts with no features and adds them one by one."""
    
    def __init__(self, estimator, loss_fn, cv=None, verbose=0, max_features=None):
        super().__init__(estimator, loss_fn, cv, verbose)
        self.max_features = max_features
    
    def fit(self, X: pd.DataFrame, y: pd.Series) -> 'ForwardFeatureSelector':
        """Fit using forward feature selection with proper CV scaling."""
        from helper.helper import helper
        
        available_features = list(X.columns)
        selected_features = []
        self.best_score_ = float('-inf') if self.loss_fn.higher_is_better else float('inf')
        
        if self.verbose > 0:
            print(f"Starting forward feature selection with {len(available_features)} available features")
        
        max_features = self.max_features or len(available_features)
        
        while len(selected_features) < max_features and len(selected_features) < len(available_features):
            scores = {}
            remaining_features = [f for f in available_features if f not in selected_features]
            
            for feature_to_add in remaining_features:
                temp_features = selected_features + [feature_to_add]
                temp_X = X[temp_features]
                
                # Cross-validation with proper scaling per split
                cv_scores = []
                
                for train_idx, val_idx in self.cv.split(temp_X):
                    X_train_cv = temp_X.iloc[train_idx]
                    X_val_cv = temp_X.iloc[val_idx]
                    y_train_cv = y.iloc[train_idx]
                    y_val_cv = y.iloc[val_idx]
                    
                    # Scale this specific split
                    data_scaler = helper()
                    X_train_scaled, X_val_scaled = data_scaler.scale(X_train_cv, X_val_cv)
                    
                    # Clone estimator to avoid fitting issues
                    temp_estimator = self.estimator.__class__(**self.estimator.get_params())
                    temp_estimator.fit(X_train_scaled, y_train_cv)
                    predictions = temp_estimator.predict(X_val_scaled)
                    
                    score = self.loss_fn(y_val_cv, predictions)
                    cv_scores.append(score)
                
                # Average CV score
                scores[feature_to_add] = np.mean(cv_scores)
            
            # Find best feature to add
            if self.loss_fn.higher_is_better:
                best_feature_to_add = max(scores, key=scores.get)
                improvement = scores[best_feature_to_add] > self.best_score_
            else:
                best_feature_to_add = min(scores, key=scores.get)
                improvement = scores[best_feature_to_add] < self.best_score_
            
            if improvement or len(selected_features) == 0:  # Always add first feature
                self.best_score_ = scores[best_feature_to_add]
                selected_features.append(best_feature_to_add)
                if self.verbose > 0:
                    print(f"Added feature: {best_feature_to_add}, CV Score: {self.best_score_:.4f}, Selected: {len(selected_features)}")
            else:
                if self.verbose > 0:
                    print("No improvement found, stopping feature selection")
                break
        
        self.selected_features_ = selected_features
        
        if self.verbose > 0:
            print(f"Forward feature selection complete. Selected {len(self.selected_features_)} features")
        
        return self
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform dataset using selected features."""
        if self.selected_features_ is None:
            raise ValueError("ForwardFeatureSelector not fitted. Call fit() first.")
        return X[self.selected_features_]
