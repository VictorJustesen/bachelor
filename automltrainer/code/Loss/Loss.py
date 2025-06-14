from abc import ABC, abstractmethod
import numpy as np

class Loss(ABC):
    """Abstract base class for all loss functions."""
    
    @abstractmethod
    def __call__(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calculates the loss. This makes instances of the loss class callable.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """
        The official name of the loss function.
        """
        pass

    @property
    @abstractmethod
    def higher_is_better(self) -> bool:
        """
        Indicates if a higher score from this metric is better.
        (e.g., True for R-squared, False for RMSE).
        """
        pass
        
    def get_scoring_direction(self) -> int:
        """Returns 1 for 'higher is better', -1 for 'lower is better'."""
        return 1 if self.higher_is_better else -1