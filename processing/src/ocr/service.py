"""Unified OCR Service for Mulberry local processing engine."""

import io
import logging
import time
from pathlib import Path
from typing import List, Optional, Union, Tuple
import cv2 as cv
import numpy as np
from PIL import Image

from processing.ocr.backends import BaseOCRBackend, create_backend
from processing.ocr.config import OCRConfig, DeviceType, OCRRuntime
from processing.ocr.exceptions import InvalidImageError, OCRInitializationError
from processing.ocr.models import BoundingBox, TextRegion
from processing.ocr.runtime import RuntimeSelector

logger = logging.getLogger(__name__)


class OCRService:
    """Mulberry OCR Engine Service.

    Narrow Responsibility:
    Converts page images (or image bounding box regions) into detected text strings,
    bounding box coordinates, and extraction confidence scores.

    - Loads OCR backend once and reuses model instances across calls.
    - Resolves hardware acceleration (GPU / CPU) and runtime selection.
    - Translates bounding box coordinates back to original image space.
    """

    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self._device: Optional[DeviceType] = None
        self._runtime: Optional[OCRRuntime] = None
        self._gpu_name: Optional[str] = None
        self._backend: Optional[BaseOCRBackend] = None

        self._initialize_service()

    def _initialize_service(self) -> None:
        """Resolve device/runtime and initialize inference backend."""
        try:
            device, runtime, gpu_name = RuntimeSelector.resolve_configuration(self.config)
            self._device = device
            self._runtime = runtime
            self._gpu_name = gpu_name

            logger.info(
                f"Initializing OCRService [Device: {self._device.value}, Runtime: {self._runtime.value}, GPU: {self._gpu_name or 'N/A'}]"
            )

            self._backend = create_backend(self.config, self._device, self._runtime)
        except Exception as e:
            logger.error(f"OCRService initialization failed: {e}")
            raise OCRInitializationError(f"OCRService initialization failed: {e}") from e

    @property
    def device(self) -> DeviceType:
        """Resolved execution device (CPU / GPU)."""
        return self._device or DeviceType.CPU

    @property
    def runtime(self) -> OCRRuntime:
        """Resolved inference runtime (paddle / onnx / openvino)."""
        return self._runtime or OCRRuntime.ONNX

    @property
    def gpu_name(self) -> Optional[str]:
        """Name of GPU hardware if detected and enabled."""
        return self._gpu_name

    def _convert_to_bgr(
        self, image: Union[Image.Image, np.ndarray, str, Path, bytes]
    ) -> Tuple[np.ndarray, int, int]:
        """Convert input image format into OpenCV BGR numpy array and (width, height)."""
        img_bgr: np.ndarray

        if isinstance(image, Image.Image):
            rgb_arr = np.array(image.convert("RGB"))
            img_bgr = cv.cvtColor(rgb_arr, cv.COLOR_RGB2BGR)
        elif isinstance(image, np.ndarray):
            if image.size == 0 or image.ndim < 2:
                raise InvalidImageError("Input numpy image array is empty or invalid.")
            if image.ndim == 2:
                img_bgr = cv.cvtColor(image, cv.COLOR_GRAY2BGR)
            elif image.ndim == 3 and image.shape[2] == 4:
                img_bgr = cv.cvtColor(image, cv.COLOR_BGRA2BGR)
            elif image.ndim == 3 and image.shape[2] == 3:
                img_bgr = image
            else:
                raise InvalidImageError(f"Unsupported image array shape: {image.shape}")
        elif isinstance(image, (bytes, memoryview)):
            nparr = np.frombuffer(image, np.uint8)
            img_decoded = cv.imdecode(nparr, cv.IMREAD_COLOR)
            if img_decoded is None:
                # Fallback to PIL decode
                try:
                    pil_img = Image.open(io.BytesIO(image)).convert("RGB")
                    img_bgr = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
                except Exception as e:
                    raise InvalidImageError(f"Could not decode image bytes: {e}") from e
            else:
                img_bgr = img_decoded
        elif isinstance(image, (str, Path)):
            path = Path(image)
            if not path.exists() or not path.is_file():
                raise InvalidImageError(f"Image file not found: '{path}'")
            img_read = cv.imread(str(path), cv.IMREAD_COLOR)
            if img_read is None:
                # Fallback to PIL decode
                try:
                    pil_img = Image.open(path).convert("RGB")
                    img_bgr = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
                except Exception as e:
                    raise InvalidImageError(f"Could not read image file '{path}': {e}") from e
            else:
                img_bgr = img_read
        else:
            raise InvalidImageError(f"Unsupported image input type: {type(image)}")

        h, w = img_bgr.shape[:2]
        if w <= 0 or h <= 0:
            raise InvalidImageError(f"Invalid image dimensions: width={w}, height={h}")

        return img_bgr, w, h

    def process(
        self,
        image: Union[Image.Image, np.ndarray, str, Path, bytes],
        bbox: Optional[BoundingBox] = None,
    ) -> List[TextRegion]:
        """Perform text detection and OCR recognition on an image or cropped bounding box region.

        Coordinate System Convention:
        - Origin (0, 0) is top-left corner of original input image.
        - x: horizontal offset from left (pixels)
        - y: vertical offset from top (pixels)
        - width & height: box dimensions (pixels)

        If `bbox` is supplied:
        - OCR is executed on cropped sub-region.
        - Output bounding boxes are translated back relative to the original image origin.

        Args:
            image: PIL Image, OpenCV BGR ndarray, image file path, or image bytes.
            bbox: Optional bounding box constraint for region OCR.

        Returns:
            List[TextRegion] containing text, bounding box (in original image coords), and confidence.

        Raises:
            InvalidImageError: If image is missing, corrupted, or invalid.
            OCRError: On inference execution failure.
        """
        start_time = time.perf_counter()

        img_bgr, orig_w, orig_h = self._convert_to_bgr(image)

        # Handle BoundingBox cropping and coordinate offsets
        offset_x: float = 0.0
        offset_y: float = 0.0
        target_img: np.ndarray = img_bgr

        if bbox is not None:
            offset_x = bbox.x
            offset_y = bbox.y

            x_start = max(0, int(round(bbox.x)))
            y_start = max(0, int(round(bbox.y)))
            x_end = min(orig_w, int(round(bbox.x + bbox.width)))
            y_end = min(orig_h, int(round(bbox.y + bbox.height)))

            crop_w = x_end - x_start
            crop_h = y_end - y_start

            if crop_w <= 0 or crop_h <= 0:
                logger.warning(
                    f"Bounding box {bbox} resulting crop area is empty (width={crop_w}, height={crop_h}). Returning empty results."
                )
                return []

            target_img = img_bgr[y_start:y_end, x_start:x_end]

        if self._backend is None:
            raise OCRInitializationError("OCR backend is not initialized.")

        raw_regions = self._backend.run_ocr(target_img)

        # Translate bounding box coordinates back to original image space
        final_regions: List[TextRegion] = []
        for reg in raw_regions:
            translated_bbox = BoundingBox(
                x=reg.bbox.x + offset_x,
                y=reg.bbox.y + offset_y,
                width=reg.bbox.width,
                height=reg.bbox.height,
            )
            final_regions.append(
                TextRegion(
                    text=reg.text,
                    bbox=translated_bbox,
                    confidence=reg.confidence,
                )
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"OCR processing completed in {duration_ms:.2f}ms | Device: {self.device.value} | "
            f"Runtime: {self.runtime.value} | Regions Detected: {len(final_regions)}"
        )

        return final_regions
