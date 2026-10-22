"""Line polygon detection backends (Surya, PaddleOCR DBNet, and CV Morphology fallback)."""

import logging
from typing import List, Optional, Union
import cv2
import numpy as np
from PIL import Image

from processing.extract.geometry.base import BaseLineDetector
from processing.extract.schemas import Polygon

logger = logging.getLogger("mulberry.extract.geometry.line_detector")


class MorphologyLineDetector(BaseLineDetector):
    """
    Morphology-based line polygon detector.
    Does not require multi-gigabyte neural network weights, making it ideal for edge execution,
    unit testing, and lightweight CPU fallback.
    """

    def __init__(self, min_line_height: int = 8, min_line_width: int = 20) -> None:
        self.min_line_height = min_line_height
        self.min_line_width = min_line_width

    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[Polygon]:
        if isinstance(image, Image.Image):
            rgb = np.array(image.convert("RGB"))
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        else:
            bgr = image.copy()

        h, w = bgr.shape[:2]
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

        # Apply adaptive thresholding to detect strokes
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 8
        )

        # Mask out non-text regions (diagrams, etc.)
        if non_text_mask is not None and non_text_mask.shape[:2] == (h, w):
            thresh[non_text_mask > 0] = 0

        # Dilate horizontally to connect words within lines while keeping vertical lines separate
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        polygons: List[Polygon] = []

        for cnt in contours:
            # Oriented bounding rectangle
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (rw, rh), angle = rect

            box_w = max(rw, rh)
            box_h = min(rw, rh)

            if box_w < self.min_line_width or box_h < self.min_line_height:
                continue

            # Extract 4-point polygon
            box_pts = cv2.boxPoints(rect)
            # Ensure within canvas
            clamped_pts = []
            for pt in box_pts:
                x = max(0.0, min(float(w), float(pt[0])))
                y = max(0.0, min(float(h), float(pt[1])))
                clamped_pts.append((x, y))

            # Order points
            poly = Polygon(points=clamped_pts)
            polygons.append(poly)

        return polygons


class SuryaLineDetector(BaseLineDetector):
    """
    Stage 2 Tier 1 detector using Surya Text Detection (SegFormer backbone).
    """

    def __init__(self) -> None:
        try:
            from surya.model.detection.segformer import load_model, load_processor
            self.processor = load_processor()
            self.model = load_model()
            self._available = True
        except Exception as e:
            logger.warning(f"Surya detection is not available: {e}")
            self._available = False

    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[Polygon]:
        if not getattr(self, "_available", False):
            fallback = MorphologyLineDetector()
            return fallback.detect_lines(image, non_text_mask=non_text_mask)

        from surya.detection import batch_text_detection

        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_img = image.convert("RGB")

        preds = batch_text_detection([pil_img], self.model, self.processor)
        boxes = preds[0].bboxes

        polygons: List[Polygon] = []
        for box in boxes:
            xmin, ymin, xmax, ymax = float(box[0]), float(box[1]), float(box[2]), float(box[3])
            # Check if center intersects non_text_mask
            if non_text_mask is not None:
                cx, cy = int((xmin + xmax) / 2), int((ymin + ymax) / 2)
                h, w = non_text_mask.shape[:2]
                if 0 <= cy < h and 0 <= cx < w and non_text_mask[cy, cx] > 0:
                    continue
            polygons.append(Polygon.from_bbox(xmin, ymin, xmax, ymax))

        return polygons


class PaddleDBNetLineDetector(BaseLineDetector):
    """
    Stage 2 Tier 2 Line Detector using Mulberry's PaddleOCR DBNet backend.
    """

    def __init__(self) -> None:
        try:
            from processing.ocr.backends.detectors.paddle import PaddleTextDetector
            from processing.ocr.config import DetectionRuntime, DeviceType, OCRConfig

            config = OCRConfig()
            self.detector = PaddleTextDetector(
                config=config,
                device=DeviceType.AUTO,
                runtime=DetectionRuntime.AUTO,
            )
            self._available = True
        except Exception as e:
            logger.warning(f"PaddleTextDetector is not available: {e}")
            self._available = False

    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[Polygon]:
        if not getattr(self, "_available", False):
            fallback = MorphologyLineDetector()
            return fallback.detect_lines(image, non_text_mask=non_text_mask)

        if isinstance(image, Image.Image):
            rgb = np.array(image.convert("RGB"))
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        else:
            bgr = image.copy()

        try:
            detected_regions = self.detector.detect(bgr)
            polygons: List[Polygon] = []
            for region in detected_regions:
                poly = Polygon(points=region.polygon)  # type: ignore
                if non_text_mask is not None:
                    cx, cy = int(poly.x_bar), int(poly.y_bar)
                    h, w = non_text_mask.shape[:2]
                    if 0 <= cy < h and 0 <= cx < w and non_text_mask[cy, cx] > 0:
                        continue
                polygons.append(poly)
            return polygons
        except Exception as e:
            logger.warning(f"PaddleTextDetector line detection failed: {e}. Falling back to morphology.")
            fallback = MorphologyLineDetector()
            return fallback.detect_lines(image, non_text_mask=non_text_mask)


def get_line_detector(
    tier: str = "tier_1_max_accuracy",
    force_fallback: bool = False,
) -> BaseLineDetector:
    """Factory function returning the appropriate BaseLineDetector for the given tier."""
    if force_fallback or tier == "tier_3_edge_cpu":
        return MorphologyLineDetector()

    if tier == "tier_2_balanced":
        try:
            paddle_detector = PaddleDBNetLineDetector()
            if paddle_detector._available:
                return paddle_detector
        except Exception:
            pass

    try:
        surya_detector = SuryaLineDetector()
        if surya_detector._available:
            return surya_detector
    except Exception:
        pass

    try:
        paddle_detector = PaddleDBNetLineDetector()
        if paddle_detector._available:
            return paddle_detector
    except Exception:
        pass

    return MorphologyLineDetector()
