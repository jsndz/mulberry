"""Inference backends for PaddleOCR, ONNX Runtime, and OpenVINO."""

import logging
from abc import ABC, abstractmethod
from typing import List, Any
import numpy as np

from processing.ocr.config import DeviceType, OCRConfig, OCRRuntime
from processing.ocr.exceptions import OCRInitializationError
from processing.ocr.models import BoundingBox, TextRegion

logger = logging.getLogger(__name__)


class BaseOCRBackend(ABC):
    """Abstract base class for OCR inference backends."""

    @abstractmethod
    def run_ocr(self, image_bgr: np.ndarray) -> List[TextRegion]:
        """Execute OCR on a BGR image numpy array.

        Returns:
            List[TextRegion] with bounding box coordinates relative to input image_bgr.
        """
        pass


def _polygon_to_bbox(poly_pts: Any) -> BoundingBox:
    """Convert 4-point polygon or box coordinates to BoundingBox(x, y, width, height)."""
    pts = np.array(poly_pts, dtype=np.float32)
    if pts.ndim == 1 and len(pts) == 4:
        # [x_min, y_min, x_max, y_max] or [x, y, w, h]
        x_min, y_min, x_max, y_max = pts[0], pts[1], pts[2], pts[3]
        if x_max >= x_min and y_max >= y_min:
            w = max(0.0, float(x_max - x_min))
            h = max(0.0, float(y_max - y_min))
            return BoundingBox(x=float(x_min), y=float(y_min), width=w, height=h)
        else:
            return BoundingBox(x=float(x_min), y=float(y_min), width=float(x_max), height=float(y_max))

    pts_2d = pts.reshape(-1, 2)
    x_min = float(np.min(pts_2d[:, 0]))
    y_min = float(np.min(pts_2d[:, 1]))
    x_max = float(np.max(pts_2d[:, 0]))
    y_max = float(np.max(pts_2d[:, 1]))
    width = max(0.0, x_max - x_min)
    height = max(0.0, y_max - y_min)
    return BoundingBox(x=x_min, y=y_min, width=width, height=height)


class PaddleOCRBackend(BaseOCRBackend):
    """PaddleOCR Backend wrapper supporting Paddle and ONNX engines."""

    def __init__(self, config: OCRConfig, device: DeviceType, runtime: OCRRuntime):
        self.config = config
        self.device = device
        self.runtime = runtime
        self._engine = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from paddleocr import PaddleOCR

            device_str = "gpu" if self.device == DeviceType.GPU else "cpu"
            engine_str = "onnxruntime" if self.runtime == OCRRuntime.ONNX else None

            kwargs = {
                "lang": self.config.language,
                "device": device_str,
                "cpu_threads": self.config.cpu_threads,
                "use_textline_orientation": self.config.use_angle_cls,
                "text_rec_score_thresh": self.config.drop_score,
            }

            if engine_str:
                kwargs["engine"] = engine_str

            if self.config.extra_params:
                kwargs.update(self.config.extra_params)

            logger.info(
                f"Initializing PaddleOCR engine (lang={self.config.language}, device={device_str}, engine={engine_str or 'paddle'})..."
            )
            self._engine = PaddleOCR(**kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR backend: {e}")
            raise OCRInitializationError(f"Failed to initialize PaddleOCR backend: {e}") from e

    def run_ocr(self, image_bgr: np.ndarray) -> List[TextRegion]:
        if self._engine is None:
            raise OCRInitializationError("PaddleOCR engine is not initialized.")

        regions: List[TextRegion] = []
        try:
            # Call predict or ocr
            res = self._engine.predict(image_bgr)
            if not res:
                return []

            for page in res:
                if isinstance(page, dict):
                    texts = page.get("rec_texts") or page.get("rec_text") or []
                    scores = page.get("rec_scores") or page.get("rec_score") or []
                    polys = page.get("dt_polys") or page.get("dt_boxes") or page.get("rec_polys") or []

                    for text, score, poly in zip(texts, scores, polys):
                        score_val = float(score)
                        if score_val < self.config.drop_score or not str(text).strip():
                            continue
                        bbox = _polygon_to_bbox(poly)
                        regions.append(
                            TextRegion(
                                text=str(text).strip(),
                                bbox=bbox,
                                confidence=min(1.0, max(0.0, score_val)),
                            )
                        )
                elif isinstance(page, list):
                    for item in page:
                        if isinstance(item, list) and len(item) >= 2:
                            poly = item[0]
                            text_score = item[1]
                            if isinstance(text_score, (list, tuple)) and len(text_score) >= 2:
                                text, score = text_score[0], float(text_score[1])
                                if score >= self.config.drop_score and str(text).strip():
                                    bbox = _polygon_to_bbox(poly)
                                    regions.append(
                                        TextRegion(
                                            text=str(text).strip(),
                                            bbox=bbox,
                                            confidence=min(1.0, max(0.0, score)),
                                        )
                                    )
        except Exception as e:
            logger.warning(f"Error during PaddleOCR inference execution: {e}")
            raise

        return regions


class RapidONNXBackend(BaseOCRBackend):
    """RapidOCR ONNX Runtime Backend fallback."""

    def __init__(self, config: OCRConfig):
        self.config = config
        self._engine = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from rapidocr_onnxruntime import RapidOCR

            logger.info("Initializing RapidOCR ONNXRuntime backend...")
            self._engine = RapidOCR()
        except Exception as e:
            raise OCRInitializationError(f"Failed to initialize RapidOCR ONNX backend: {e}") from e

    def run_ocr(self, image_bgr: np.ndarray) -> List[TextRegion]:
        if self._engine is None:
            raise OCRInitializationError("RapidOCR engine not initialized.")

        res, _ = self._engine(image_bgr)
        if not res:
            return []

        regions: List[TextRegion] = []
        for item in res:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                poly, text, score = item[0], item[1], float(item[2])
                if score >= self.config.drop_score and str(text).strip():
                    bbox = _polygon_to_bbox(poly)
                    regions.append(
                        TextRegion(
                            text=str(text).strip(),
                            bbox=bbox,
                            confidence=min(1.0, max(0.0, score)),
                        )
                    )
        return regions


def create_backend(
    config: OCRConfig, device: DeviceType, runtime: OCRRuntime
) -> BaseOCRBackend:
    """Factory function to instantiate appropriate OCR backend."""
    if runtime == OCRRuntime.ONNX:
        try:
            return PaddleOCRBackend(config, device, runtime)
        except Exception as e:
            logger.info(f"Falling back to RapidONNXBackend due to: {e}")
            return RapidONNXBackend(config)
    else:
        return PaddleOCRBackend(config, device, runtime)
