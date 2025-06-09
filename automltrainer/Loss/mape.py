import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
import numpy as np
from Loss import Loss
from sklearn.metrics import mean_absolute_percentage_error

class mape(Loss):
    """Calculates the Mean Absolute Percentage Error."""

    @property
    def name(self) -> str:
        return "mape"

    @property
    def higher_is_better(self) -> bool:
        return False  # Lower MAPE is better

    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        # Add a small epsilon to avoid division by zero
        return mean_absolute_percentage_error(y_true, y_pred)