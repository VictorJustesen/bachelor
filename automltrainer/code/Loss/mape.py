import numpy as np
from .Loss import Loss
from sklearn.metrics import mean_absolute_percentage_error

class mape(Loss):
    """Calculates the Mean Absolute Percentage Error."""

    @property
    def name(self) -> str:
        return "mape"

    @property
    def higher_is_better(self) -> bool:
        return False 

    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return mean_absolute_percentage_error(y_true, y_pred)