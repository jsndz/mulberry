"""Backend-independent abstract base class for text recognizer interface."""

from abc import ABC, abstractmethod
from typing import List
import numpy as np
from pydantic import BaseModel, Field


class TextResult(BaseModel):
    """Result of text recognition on an image crop."""

    text: str = Field(..., description="Recognized text string")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Recognition confidence score between 0.0 and 1.0"
    )
    recognizer_name: str = Field(
        ..., description="Name of recognizer engine used, e.g. 'trocr' or 'paddle'"
    )


class BaseTextRecognizer(ABC):
    """Abstract base class for text recognition backends.

    Narrow Responsibility:
    Recognize text string and confidence score from a cropped BGR image region.
    """

    @abstractmethod
    def recognize_crop(self, crop_bgr: np.ndarray) -> TextResult:
        """Recognize text in a single cropped BGR image numpy array.

        Returns:
            TextResult containing recognized text string, confidence, and recognizer_name.
        """
        pass

    def recognize_batch(self, crops: List[np.ndarray]) -> List[TextResult]:
        """Recognize text in a batch of cropped BGR image numpy arrays."""
        return [self.recognize_crop(c) for c in crops]
