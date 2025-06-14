# AutoML Framework Interfaces Documentation

This document explains the interface-based architecture for feature selection and hyperparameter tuning in the AutoML framework.

## Overview

The framework now provides abstract interfaces that allow for easy extension and customization of:
1. **Feature Selection Methods** via `FeatureSelectionInterface`
2. **Hyperparameter Tuning Methods** via `HypertuningInterface`

## Feature Selection Interface

### `FeatureSelectionInterface`

Abstract base class for all feature selection methods.

#### Key Methods:
- `fit(X, y)`: Fit the selector on training data
- `transform(X)`: Transform data using selected features
- `fit_transform(X, y)`: Fit and transform in one step

#### Properties:
- `n_features_selected`: Number of features selected
- `feature_names`: Names of selected features
- `selected_features_`: List of selected feature names
- `best_score_`: Best cross-validation score achieved

### Implemented Feature Selectors:

#### `BackwardFeatureSelector`
- Starts with all features and removes them one by one
- Keeps features that maintain or improve performance
- Uses cross-validation with proper scaling for evaluation

#### Usage Example:
```python
from feature_selection import BackwardFeatureSelector
from Loss import mae

# Create selector
selector = BackwardFeatureSelector(
    estimator=model,
    loss_fn=mae(),
    cv=TimeSeriesSplit(n_splits=5),
    verbose=1
)

# Fit and transform
X_selected = selector.fit_transform(X_train, y_train)
X_test_selected = selector.transform(X_test)

print(f"Selected {selector.n_features_selected} features")
print(f"Feature names: {selector.feature_names}")
```

## Hyperparameter Tuning Interface

### `HypertuningInterface`

Abstract base class for all hyperparameter tuning methods.

#### Key Methods:
- `fit(X, y)`: Fit the tuner and find best parameters
- `get_best_params()`: Get the best parameters found
- `get_best_score()`: Get the best score achieved
- `optimized_estimator`: Get estimator with best parameters

#### Properties:
- `best_params_`: Dictionary of best parameters
- `best_score_`: Best cross-validation score achieved

### Implemented Hyperparameter Tuners:

#### `GridSearchTuner`
- Exhaustive search over parameter grid
- Tests all parameter combinations
- Guaranteed to find global optimum within the grid

#### `LineSearchTuner`
- Optimizes one parameter at a time
- Multiple passes through parameters
- More efficient than grid search for high-dimensional spaces

#### Usage Example:
```python
from hyper_tuning import GridSearchTuner
from Loss import mae

# Define parameter grid
param_grid = {
    'n_estimators': [100, 200, 500],
    'learning_rate': [0.01, 0.1, 0.2],
    'max_depth': [3, 6, 9]
}

# Create tuner
tuner = GridSearchTuner(
    estimator=model,
    loss_fn=mae(),
    param_grid=param_grid,
    cv=TimeSeriesSplit(n_splits=5),
    verbose=1
)

# Fit tuner
tuner.fit(X_train, y_train)

# Get results
best_params = tuner.get_best_params()
best_model = tuner.optimized_estimator
```

## Integration with AutoML

The interfaces integrate seamlessly with the `SimpleAutoML` class:

```python
from automl.automl import SimpleAutoML
from feature_selection import BackwardFeatureSelector
from hyper_tuning import GridSearchTuner
from Loss import mae

# Initialize AutoML
automl = SimpleAutoML(target_col='target')

# Run with feature selection and hypertuning
results = automl.run_automl(
    df=data,
    feature_selection_fn=BackwardFeatureSelector,
    hypertuning_fn=GridSearchTuner,
    loss_fn=mae(),
    n_splits=5,
    test_split=0.2,
    verbose=1
)
```

## Creating Custom Implementations

### Custom Feature Selector

```python
from feature_selection.feature_selection_interface import FeatureSelectionInterface

class MyCustomFeatureSelector(FeatureSelectionInterface):
    def __init__(self, estimator, loss_fn, cv=None, verbose=0):
        super().__init__(estimator, loss_fn, cv, verbose)
        # Add custom parameters
    
    def fit(self, X, y):
        # Implement your feature selection logic
        # Set self.selected_features_ and self.best_score_
        return self
    
    def transform(self, X):
        # Transform using selected features
        return X[self.selected_features_]
```

### Custom Hyperparameter Tuner

```python
from hyper_tuning.hypertuning_interface import HypertuningInterface

class MyCustomTuner(HypertuningInterface):
    def __init__(self, estimator, loss_fn, param_grid, cv=None, n_jobs=-1, verbose=0):
        super().__init__(estimator, loss_fn, param_grid, cv, n_jobs, verbose)
        # Add custom parameters
    
    def fit(self, X, y):
        # Implement your hyperparameter optimization logic
        # Set self.best_params_ and self.best_score_
        return self
```

## Loss Functions

The framework includes multiple loss functions that work with the interfaces:

- `mae()`: Mean Absolute Error
- `mape()`: Mean Absolute Percentage Error  
- `rmse()`: Root Mean Squared Error

All loss functions implement the `Loss` interface with:
- `__call__(y_true, y_pred)`: Calculate loss
- `name`: Loss function name
- `higher_is_better`: Whether higher scores are better

## Benefits of Interface-Based Architecture

1. **Extensibility**: Easy to add new feature selection and hypertuning methods
2. **Consistency**: All implementations follow the same interface
3. **Interchangeability**: Can swap methods without changing other code
4. **Testability**: Each component can be tested independently
5. **Maintainability**: Clear separation of concerns

## File Structure

```
code/
├── feature_selection/
│   ├── __init__.py
│   ├── feature_selection_interface.py  # Abstract interface
│   └── backwards.py                    # Implementation
├── hyper_tuning/
│   ├── __init__.py
│   ├── hypertuning_interface.py        # Abstract interface
│   ├── grid_search.py                  # Implementation
│   └── line_search.py                  # Implementation
└── Loss/
    ├── __init__.py
    ├── Loss.py                         # Abstract loss interface
    ├── mae.py                          # MAE implementation
    ├── mape.py                         # MAPE implementation
    └── rmse.py                         # RMSE implementation
```
