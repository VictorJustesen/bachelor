import numpy as np
from sklearn.metrics import r2_score
from .Loss import Loss

class r2(Loss):

    @property
    def name(self) -> str:
        return "r2"

    @property
    def higher_is_better(self) -> bool:
        return True 

    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return r2_score(y_true, y_pred)