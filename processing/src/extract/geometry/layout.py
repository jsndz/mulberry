"""Diagram, non-text, and layout segmentation for Stage 2 geometric path."""

from typing import Any, Dict, List, Optional, Union
import cv2
import numpy as np
from PIL import Image

from processing.diagram import get_detector
from processing.extract.geometry.base import BaseLayoutSegmenter
from processing.extract.schemas import NonTextElement, Polygon


class DiagramLayoutSegmenter(BaseLayoutSegmenter):
    """
    Detects non-text regions such as diagrams, tables, flowcharts, and pre-printed branding.

    Reuses Mulberry's unified diagram detector (Microsoft DiT for GPU, YOLO for CPU).
    """

    def __init__(
        self,
        force_device: Optional[str] = None,
        conf_threshold: float = 0.25,
    ) -> None:
        self.detector = get_detector(force_device=force_device, default_conf_threshold=conf_threshold)
        self.conf_threshold = conf_threshold

    def segment(self, image: Union[np.ndarray, Image.Image]) -> List[NonTextElement]:
        """Detect and return non-text elements."""
        detections = self.detector.predict(image, conf_threshold=self.conf_threshold)

        non_text_elements: List[NonTextElement] = []
        for idx, det in enumerate(detections):
            box = det.get("box", [0, 0, 0, 0])
            poly = Polygon.from_bbox(box[0], box[1], box[2], box[3])
            conf = det.get("confidence", 1.0)
            label = det.get("label", "diagram")

            non_text_elements.append(
                NonTextElement(
                    id=f"non_text_{idx + 1:02d}",
                    type=label,
                    polygon=poly.to_list(),
                    metadata={"confidence": conf, "box": box},
                )
            )

        return non_text_elements

    @staticmethod
    def create_non_text_mask(
        shape: tuple[int, int],
        non_text_elements: List[NonTextElement],
    ) -> np.ndarray:
        """
        Creates a binary mask (uint8) where non-text regions are 255 and text regions are 0.
        """
        mask = np.zeros((shape[0], shape[1]), dtype=np.uint8)
        for elem in non_text_elements:
            pts = np.array(elem.polygon, dtype=np.int32)
            cv2.fillPoly(mask, [pts], 255)
        return mask
