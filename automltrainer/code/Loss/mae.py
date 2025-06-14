import numpy as np
from sklearn.metrics import mean_absolute_error
from .Loss import Loss

class mae(Loss):
    """Calculates the Mean Absolute Error."""

    @property
    def name(self) -> str:
        return "mae"

    @property
    def higher_is_better(self) -> bool:
        return False # Lower MAE is better

    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return mean_absolute_error(y_true, y_pred)