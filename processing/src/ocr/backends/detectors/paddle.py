"""PaddleOCR text detector implementation."""

import logging
from typing import Tuple, List, Any
import numpy as np

from processing.ocr.backends.detectors.base import BaseTextDetector
from processing.ocr.config import DeviceType, OCRConfig, DetectionRuntime
from processing.ocr.exceptions import OCRInitializationError
from processing.ocr.models import BoundingBox, DetectedRegion

logger = logging.getLogger(__name__)


def polygon_to_bbox(poly_pts: Any) -> Tuple[BoundingBox, List[List[float]]]:
    """Convert 4-point polygon coordinates into BoundingBox and 2D float polygon list."""
    pts = np.array(poly_pts, dtype=np.float32)
    if pts.ndim == 1 and len(pts) == 4:
        x_min, y_min, x_max, y_max = float(pts[0]), float(pts[1]), float(pts[2]), float(pts[3])
        w = max(0.0, x_max - x_min)
        h = max(0.0, y_max - y_min)
        poly = [
            [x_min, y_min],
            [x_max, y_min],
            [x_max, y_max],
            [x_min, y_max],
        ]
        return BoundingBox(x=x_min, y=y_min, width=w, height=h), poly

    pts_2d = pts.reshape(-1, 2)
    poly = [[float(p[0]), float(p[1])] for p in pts_2d]

    x_min = float(np.min(pts_2d[:, 0]))
    y_min = float(np.min(pts_2d[:, 1]))
    x_max = float(np.max(pts_2d[:, 0]))
    y_max = float(np.max(pts_2d[:, 1]))
    width = max(0.0, x_max - x_min)
    height = max(0.0, y_max - y_min)

    return BoundingBox(x=x_min, y=y_min, width=width, height=height), poly


class PaddleTextDetector(BaseTextDetector):
    """PaddleOCR Text Detector Backend."""

    def __init__(self, config: OCRConfig, device: DeviceType, runtime: DetectionRuntime):
        self.config = config
        self.device = device
        self.runtime = runtime
        self._engine = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from paddleocr import PaddleOCR
            import paddle

            has_paddle_gpu = (
                hasattr(paddle, "is_compiled_with_cuda")
                and paddle.is_compiled_with_cuda()
                and (not hasattr(paddle.device, "cuda") or paddle.device.cuda.device_count() > 0)
            )
            device_str = "gpu" if (self.device == DeviceType.GPU and has_paddle_gpu) else "cpu"
            engine_str = "onnxruntime" if self.runtime == DetectionRuntime.ONNX else None

            kwargs = {
                "lang": self.config.language,
                "device": device_str,
                "cpu_threads": self.config.cpu_threads,
                "use_textline_orientation": False,  # Orientation handled separately
                "enable_mkldnn": False,  # Disable MKLDNN to avoid PIR OneDNN instruction errors
            }

            if engine_str:
                kwargs["engine"] = engine_str

            if self.config.extra_params:
                kwargs.update(self.config.extra_params)

            logger.info(f"Initializing PaddleTextDetector (device={device_str})...")
            self._engine = PaddleOCR(**kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize PaddleTextDetector: {e}")
            raise OCRInitializationError(f"Failed to initialize PaddleTextDetector: {e}") from e

    def detect(self, image_bgr: np.ndarray) -> List[DetectedRegion]:
        if self._engine is None:
            raise OCRInitializationError("PaddleTextDetector engine is not initialized.")

        regions: List[DetectedRegion] = []
        try:
            results = list(self._engine.predict(image_bgr))
            if not results:
                return []

            for page in results:
                if isinstance(page, dict):
                    polys = page.get("dt_polys") or page.get("dt_boxes") or page.get("rec_polys") or []
                    scores = page.get("dt_scores") or page.get("rec_scores") or []

                    if not scores:
                        scores = [1.0] * len(polys)

                    for poly_raw, score in zip(polys, scores):
                        score_val = float(score)
                        bbox, poly_coords = polygon_to_bbox(poly_raw)
                        regions.append(
                            DetectedRegion(
                                polygon=poly_coords,
                                bbox=bbox,
                                confidence=min(1.0, max(0.0, score_val)),
                            )
                        )
                elif isinstance(page, list):
                    for item in page:
                        if isinstance(item, list) and len(item) >= 1:
                            poly_raw = item[0]
                            score = 1.0
                            if len(item) >= 2 and isinstance(item[1], (list, tuple)) and len(item[1]) >= 2:
                                score = float(item[1][1])
                            bbox, poly_coords = polygon_to_bbox(poly_raw)
                            regions.append(
                                DetectedRegion(
                                    polygon=poly_coords,
                                    bbox=bbox,
                                    confidence=min(1.0, max(0.0, score)),
                                )
                            )
        except Exception as e:
            logger.warning(f"Error during PaddleTextDetector execution: {e}")
            raise

        return regions
