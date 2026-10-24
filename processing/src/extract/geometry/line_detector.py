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

        # Scale-normalization to handle 4K / smartphone 12MP photos consistently
        scale = 1200.0 / max(h, w) if max(h, w) > 1200 else 1.0
        if scale < 1.0:
            small_w, small_h = int(w * scale), int(h * scale)
            small_gray = cv2.resize(gray, (small_w, small_h), interpolation=cv2.INTER_AREA)
        else:
            small_w, small_h = w, h
            small_gray = gray

        # Equalize contrast across uneven shadows and paper textures
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        norm = clahe.apply(small_gray)

        # Adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            norm, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 31, 12
        )

        # Mask out non-text regions (diagrams, etc.)
        if non_text_mask is not None:
            if non_text_mask.shape[:2] != (small_h, small_w):
                scaled_mask = cv2.resize(
                    non_text_mask, (small_w, small_h), interpolation=cv2.INTER_NEAREST
                )
            else:
                scaled_mask = non_text_mask
            thresh[scaled_mask > 0] = 0

        # Dilate horizontally to connect words within lines while keeping vertical lines separate
        kw = max(18, int(small_w * 0.035))
        kh = max(2, int(small_h * 0.003))
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, kh))
        dilated = cv2.dilate(thresh, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        polygons: List[Polygon] = []

        for cnt in contours:
            rect = cv2.minAreaRect(cnt)
            (cx, cy), (rw, rh), angle = rect

            box_w = max(rw, rh)
            box_h = min(rw, rh)

            # Discard outer paper boundary / background page borders
            if box_w >= small_w * 0.85 and box_h >= small_h * 0.85:
                continue

            # Filter out tiny noise artifacts and excessively tall blocks
            min_w = min(self.min_line_width * scale, max(15.0, small_w * 0.02))
            min_h = min(self.min_line_height * scale, 3.0)
            if box_w < min_w or box_h < min_h or box_h > small_h * 0.25:
                continue

            # Extract 4-point polygon and scale back to original image coordinates
            box_pts = cv2.boxPoints(rect)
            scaled_pts = []
            for pt in box_pts:
                orig_x = max(0.0, min(float(w), float(pt[0] / scale)))
                orig_y = max(0.0, min(float(h), float(pt[1] / scale)))
                scaled_pts.append((orig_x, orig_y))

            poly = Polygon(points=scaled_pts)
            polygons.append(poly)

        return polygons


class SuryaLineDetector(BaseLineDetector):
    """
    Stage 2 Tier 1 detector using Surya Text Detection (SegFormer backbone).
    """

    def __init__(self) -> None:
        self.fallback_used: bool = False
        self.fallback_reason: Optional[str] = None
        try:
            from surya.model.detection.segformer import load_model, load_processor
            self.processor = load_processor()
            self.model = load_model()
            self._available = True
        except Exception as e:
            logger.warning(f"Surya detection is not available: {e}")
            self._available = False
            self.fallback_used = True
            self.fallback_reason = str(e)

    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[Polygon]:
        if not getattr(self, "_available", False):
            self.fallback_used = True
            if not self.fallback_reason:
                self.fallback_reason = "Surya detector dependencies or weights not available"
            fallback = MorphologyLineDetector()
            return fallback.detect_lines(image, non_text_mask=non_text_mask)

        from surya.detection import batch_text_detection

        if isinstance(image, np.ndarray):
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_img = image.convert("RGB")

        try:
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
        except Exception as e:
            logger.warning(f"Surya text detection failed: {e}. Falling back to morphology.")
            self.fallback_used = True
            self.fallback_reason = str(e)
            fallback = MorphologyLineDetector()
            return fallback.detect_lines(image, non_text_mask=non_text_mask)


class PaddleDBNetLineDetector(BaseLineDetector):
    """
    Stage 2 Tier 2 Line Detector using Mulberry's PaddleOCR DBNet backend.
    """

    def __init__(self) -> None:
        self.fallback_used: bool = False
        self.fallback_reason: Optional[str] = None
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
            self.fallback_used = True
            self.fallback_reason = str(e)

    def detect_lines(
        self,
        image: Union[np.ndarray, Image.Image],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[Polygon]:
        if not getattr(self, "_available", False):
            self.fallback_used = True
            if not self.fallback_reason:
                self.fallback_reason = "PaddleTextDetector dependencies or weights not available"
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
            self.fallback_used = True
            self.fallback_reason = str(e)
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
