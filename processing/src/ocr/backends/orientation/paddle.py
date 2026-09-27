"""Paddle-based text orientation classifier."""

import logging
from typing import Tuple
import cv2 as cv
import numpy as np

from processing.ocr.backends.orientation.base import BaseOrientationClassifier
from processing.ocr.config import DeviceType, OCRConfig

logger = logging.getLogger(__name__)


class PaddleOrientationClassifier(BaseOrientationClassifier):
    """Paddle-based text orientation classifier and rotation corrector."""

    def __init__(self, config: OCRConfig, device: DeviceType):
        self.config = config
        self.device = device
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
            logger.info(f"Initializing PaddleOrientationClassifier (device={device_str})...")
            self._engine = PaddleOCR(
                lang=self.config.language,
                device=device_str,
                use_textline_orientation=True,
                enable_mkldnn=False,
            )
        except Exception as e:
            logger.warning(f"Could not initialize PaddleOrientationClassifier: {e}")
            self._engine = None

    def classify_and_rotate(self, crop_bgr: np.ndarray) -> Tuple[np.ndarray, float]:
        if crop_bgr is None or crop_bgr.size == 0 or crop_bgr.shape[0] < 2 or crop_bgr.shape[1] < 2:
            return crop_bgr, 1.0

        if self._engine is None:
            return crop_bgr, 1.0

        try:
            results = list(self._engine.predict(crop_bgr))
            if not results:
                return crop_bgr, 1.0

            for page in results:
                if isinstance(page, dict):
                    angle = page.get("angle", 0)
                    if angle == 180:
                        rotated = cv.rotate(crop_bgr, cv.ROTATE_180)
                        return rotated, 0.95
                    elif angle == 90:
                        rotated = cv.rotate(crop_bgr, cv.ROTATE_90_CLOCKWISE)
                        return rotated, 0.95
                    elif angle == 270:
                        rotated = cv.rotate(crop_bgr, cv.ROTATE_90_COUNTERCLOCKWISE)
                        return rotated, 0.95

            return crop_bgr, 1.0
        except Exception as e:
            logger.warning(f"Orientation classification failed: {e}")
            return crop_bgr, 1.0
