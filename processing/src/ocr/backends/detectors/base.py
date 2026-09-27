"""Backend-independent abstract base class for text detector interface."""

from abc import ABC, abstractmethod
from typing import List
import numpy as np

from processing.ocr.models import DetectedRegion


class BaseTextDetector(ABC):
    """Abstract base class for text region detection.

    Narrow Responsibility:
    Detect text region polygons and bounding boxes in an image.
    Does NOT perform text recognition.
    """

    @abstractmethod
    def detect(self, image_bgr: np.ndarray) -> List[DetectedRegion]:
        """Detect text regions in a BGR OpenCV numpy image array.

        Returns:
            List[DetectedRegion] containing polygon, bbox, and detection confidence score.
        """
        pass
