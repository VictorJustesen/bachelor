import numpy as np
from sklearn.metrics import mean_squared_error
from .Loss import Loss

class rmse(Loss):
    """Calculates the Root Mean Squared Error."""

    @property
    def name(self) -> str:
        return "rmse"

    @property
    def higher_is_better(self) -> bool:
        return False # Lower RMSE is better

    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return np.sqrt(mean_squared_error(y_true, y_pred))