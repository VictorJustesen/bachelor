

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler

class helper:
    """Helper class to handle scaling within CV splits"""
    
    def __init__(self):
        self.scaler = StandardScaler()
    


    def scale_with_scaler(self, X_train, X_test):
        """
        Scale final train/test data
        
        Args:
            X_train: Final training data
            X_test: Final test data
            
        Returns:
            X_train_scaled, X_test_scaled, scaler (fitted scaler for later use)
        """
        final_scaler = StandardScaler()
        
        X_train_scaled = pd.DataFrame(
            final_scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        X_test_scaled = pd.DataFrame(
            final_scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )

        return X_train_scaled, X_test_scaled, final_scaler
    
    def scale(self, X_train, X_test):
        """
        Scale final train/test data
        
        Args:
            X_train: Final training data
            X_test: Final test data
            
        Returns:
            X_train_scaled, X_test_scaled, scaler (fitted scaler for later use)
        """
        final_scaler = StandardScaler()
        
        X_train_scaled = pd.DataFrame(
            final_scaler.fit_transform(X_train),
            columns=X_train.columns,
            index=X_train.index
        )
        
        X_test_scaled = pd.DataFrame(
            final_scaler.transform(X_test),
            columns=X_test.columns,
            index=X_test.index
        )
        
        return X_train_scaled, X_test_scaled