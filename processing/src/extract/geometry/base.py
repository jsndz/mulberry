"""Abstract interfaces and protocols for layout segmentation and line detection."""

from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np
from PIL import Image

from processing.extract.schemas import NonTextElement, Polygon


class BaseLayoutSegmenter(ABC):
    """Abstract interface for segmenting non-text regions (diagrams, tables, headers)."""

    @abstractmethod
    def segment(self, image: Union[np.ndarray, Image.Image]) -> List[NonTextElement]:
        """
        Detect and isolate non-text visual elements on the page.

        Returns:
            List of NonTextElement instances.
        """
        pass


class BaseLineDetector(ABC):
    """Abstract interface for detecting oriented text line polygons."""

    @abstractmethod
    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Union[np.ndarray, None] = None,
    ) -> List[Polygon]:
        """
        Detect text line polygons, optionally ignoring masked non-text regions.

        Returns:
            List of 4-point Polygon instances in detection order.
        """
        pass
