"""Backend-independent abstract base class for orientation classification interface."""

from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np


class BaseOrientationClassifier(ABC):
    """Abstract base class for text line orientation classification and rotation correction."""

    @abstractmethod
    def classify_and_rotate(self, crop_bgr: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detect orientation of text crop, perform rotation correction if needed, and return (rotated_crop, confidence)."""
        pass
