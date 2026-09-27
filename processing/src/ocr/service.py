"""Unified OCR Service orchestrating preprocessing, detection, orientation, recognition, and layout analysis."""

import logging
import time
from pathlib import Path
from typing import List, Optional, Tuple, Union
import cv2 as cv
import numpy as np
from PIL import Image

from processing.ocr.backends.detectors.base import BaseTextDetector
from processing.ocr.backends.detectors.paddle import PaddleTextDetector
from processing.ocr.backends.orientation.base import BaseOrientationClassifier
from processing.ocr.backends.orientation.paddle import PaddleOrientationClassifier
from processing.ocr.backends.recognizers.base import BaseTextRecognizer
from processing.ocr.backends.recognizers.paddle import PaddleTextRecognizer
from processing.ocr.backends.recognizers.trocr import TrOCRTextRecognizer
from processing.ocr.config import (
    DeviceType,
    DetectorBackend,
    OCRConfig,
    RecognizerBackend,
)
from processing.ocr.exceptions import InvalidImageError, OCRInitializationError
from processing.ocr.layout import assign_reading_order
from processing.ocr.models import BoundingBox, DetectedRegion, TextRegion
from processing.ocr.preprocessing import normalize_image, preprocess_image
from processing.ocr.runtime import ResolvedRuntimeConfig, RuntimeSelector
from processing.ocr.tiling import generate_tiles, suppress_duplicate_detections

logger = logging.getLogger(__name__)


def crop_bbox_region(image_bgr: np.ndarray, bbox: BoundingBox) -> np.ndarray:
    """Crop sub-region from BGR image based on bounding box."""
    h, w = image_bgr.shape[:2]
    x_start = max(0, int(round(bbox.x)))
    y_start = max(0, int(round(bbox.y)))
    x_end = min(w, int(round(bbox.x + bbox.width)))
    y_end = min(h, int(round(bbox.y + bbox.height)))

    if x_end <= x_start or y_end <= y_start:
        return np.array([])
    return image_bgr[y_start:y_end, x_start:x_end]


class OCRService:
    """Mulberry Orchestrated OCR Engine Service.

    Orchestrates high-level modular stages:
    Image Normalization ➔ Preprocessing/Tiling ➔ Detection ➔ ROI Crop ➔ Orientation ➔ Recognition ➔ Coordinate Mapping ➔ Reading Order layout.

    Decoupled from specific backend implementations (PaddleOCR, TrOCR).
    """

    def __init__(self, config: Optional[OCRConfig] = None):
        self.config = config or OCRConfig()
        self._resolved_runtime: Optional[ResolvedRuntimeConfig] = None
        self._detector: Optional[BaseTextDetector] = None
        self._recognizer: Optional[BaseTextRecognizer] = None
        self._orientation_classifier: Optional[BaseOrientationClassifier] = None

        self._initialize_service()

    def _initialize_service(self) -> None:
        """Resolve device/runtimes and instantiate backend modules."""
        try:
            self._resolved_runtime = RuntimeSelector.resolve_configuration(self.config)

            logger.info(
                f"Initializing OCRService [Device: {self._resolved_runtime.device.value}, "
                f"Detector: {self.config.detector_backend.value}, Recognizer: {self.config.recognizer_backend.value}]"
            )

            # 1. Instantiate Text Detector
            if self.config.detector_backend == DetectorBackend.PADDLE:
                self._detector = PaddleTextDetector(
                    config=self.config,
                    device=self._resolved_runtime.device,
                    runtime=self._resolved_runtime.detection_runtime,
                )
            else:
                self._detector = PaddleTextDetector(
                    config=self.config,
                    device=self._resolved_runtime.device,
                    runtime=self._resolved_runtime.detection_runtime,
                )

            # 2. Instantiate Text Recognizer
            if self.config.recognizer_backend == RecognizerBackend.TROCR:
                self._recognizer = TrOCRTextRecognizer(
                    config=self.config,
                    device=self._resolved_runtime.device,
                )
            else:
                self._recognizer = PaddleTextRecognizer(
                    config=self.config,
                    device=self._resolved_runtime.device,
                    runtime=self._resolved_runtime.recognition_runtime,
                )

            # 3. Instantiate Orientation Classifier (optional)
            if self.config.use_orientation or self.config.use_angle_cls:
                self._orientation_classifier = PaddleOrientationClassifier(
                    config=self.config,
                    device=self._resolved_runtime.device,
                )

        except Exception as e:
            logger.error(f"OCRService initialization failed: {e}")
            raise OCRInitializationError(f"OCRService initialization failed: {e}") from e

    @property
    def device(self) -> DeviceType:
        """Resolved execution device (CPU / GPU)."""
        if self._resolved_runtime:
            return self._resolved_runtime.device
        return DeviceType.CPU

    @property
    def runtime(self):
        """Resolved detection runtime."""
        if self._resolved_runtime:
            return self._resolved_runtime.detection_runtime
        return "auto"

    @property
    def gpu_name(self) -> Optional[str]:
        """Name of GPU hardware if detected and enabled."""
        if self._resolved_runtime:
            return self._resolved_runtime.gpu_name
        return None

    def process(
        self,
        image: Union[Image.Image, np.ndarray, str, Path, bytes],
        bbox: Optional[BoundingBox] = None,
    ) -> List[TextRegion]:
        """Perform text detection, optional orientation, recognition, and layout reading order.

        Args:
            image: Input image (PIL, ndarray, path, or bytes).
            bbox: Optional ROI bounding box constraint.

        Returns:
            List[TextRegion] ordered by spatial reading order with original coordinate system.
        """
        start_time = time.perf_counter()

        # 1. Normalize image format to standard OpenCV BGR array
        img_bgr, orig_w, orig_h = normalize_image(image)

        # 2. Apply handwriting preprocessing if configured
        processed_img = preprocess_image(img_bgr, self.config.preprocessing)

        # 3. Handle ROI Cropping
        offset_x: float = 0.0
        offset_y: float = 0.0
        target_img: np.ndarray = processed_img

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
                    f"ROI bounding box resulting crop is empty (width={crop_w}, height={crop_h}). Returning empty results."
                )
                return []

            target_img = processed_img[y_start:y_end, x_start:x_end]

        if self._detector is None or self._recognizer is None:
            raise OCRInitializationError("OCR detector or recognizer is not initialized.")

        # 4. Text Detection Stage (Standard vs Tile-Based Detections)
        detected_regions: List[DetectedRegion] = []
        prep_cfg = self.config.preprocessing

        if prep_cfg.enable_tiling:
            tiles = generate_tiles(
                target_img, tile_size=prep_cfg.tile_size, overlap=prep_cfg.tile_overlap
            )
            raw_tile_detections: List[DetectedRegion] = []

            for tile_bgr, t_off_x, t_off_y in tiles:
                tile_dets = self._detector.detect(tile_bgr)
                for d in tile_dets:
                    shifted_poly = [[p[0] + t_off_x, p[1] + t_off_y] for p in d.polygon]
                    shifted_bbox = BoundingBox(
                        x=d.bbox.x + t_off_x,
                        y=d.bbox.y + t_off_y,
                        width=d.bbox.width,
                        height=d.bbox.height,
                    )
                    raw_tile_detections.append(
                        DetectedRegion(
                            polygon=shifted_poly,
                            bbox=shifted_bbox,
                            confidence=d.confidence,
                        )
                    )

            # Deduplicate overlapping bounding boxes across tile seams using NMS
            detected_regions = suppress_duplicate_detections(
                raw_tile_detections, iou_threshold=prep_cfg.nms_iou_threshold
            )
        else:
            detected_regions = self._detector.detect(target_img)

        if not detected_regions:
            return []

        raw_text_regions: List[TextRegion] = []
        elem_counter = 1

        for det in detected_regions:
            # Crop detected region from unscaled target image for 100% full-res recognition
            crop_bgr = crop_bbox_region(target_img, det.bbox)
            if crop_bgr.size == 0:
                continue

            # 5. Orientation Classification Stage (Optional)
            if self._orientation_classifier and (self.config.use_orientation or self.config.use_angle_cls):
                crop_bgr, _ = self._orientation_classifier.classify_and_rotate(crop_bgr)

            # 6. Text Recognition Stage
            rec_result = self._recognizer.recognize_crop(crop_bgr)

            # Filter out empty text or results below drop_score confidence
            if rec_result.confidence < self.config.drop_score or not rec_result.text.strip():
                continue

            # 7. Coordinate Mapping Stage: Translate coordinates back to full image space
            translated_polygon = [
                [pt[0] + offset_x, pt[1] + offset_y] for pt in det.polygon
            ]
            translated_bbox = BoundingBox(
                x=det.bbox.x + offset_x,
                y=det.bbox.y + offset_y,
                width=det.bbox.width,
                height=det.bbox.height,
            )

            region = TextRegion(
                id=f"ocr_text_{elem_counter}",
                text=rec_result.text.strip(),
                confidence=round(rec_result.confidence, 4),
                polygon=translated_polygon,
                bbox=translated_bbox,
                recognizer=rec_result.recognizer_name,
                reading_order=0,
                element_type="text",
                handwriting=(rec_result.recognizer_name == "trocr"),
            )
            raw_text_regions.append(region)
            elem_counter += 1

        # 8. Spatial Reading Order Layout Stage
        final_regions = assign_reading_order(raw_text_regions)

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            f"OCR pipeline completed in {duration_ms:.2f}ms | Device: {self.device.value} | "
            f"Regions Detected & Recognized: {len(final_regions)}"
        )

        return final_regions
