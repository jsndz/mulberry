"""Mulberry OCR Processing Engine Submodule."""

from processing.ocr.config import (
    DeviceType,
    DetectorBackend,
    RecognizerBackend,
    DetectionRuntime,
    RecognitionRuntime,
    OCRRuntime,
    ImagePreprocessingConfig,
    OCRConfig,
)
from processing.ocr.exceptions import (
    OCRError,
    MissingModelError,
    UnsupportedRuntimeError,
    GPUUnavailableError,
    InvalidImageError,
    OCRInitializationError,
)
from processing.ocr.models import BoundingBox, DetectedRegion, TextRegion
from processing.ocr.runtime import (
    RuntimeSelector,
    ResolvedRuntimeConfig,
    SystemCapabilities,
)
from processing.ocr.service import OCRService
from processing.ocr.preprocessing import normalize_image, preprocess_image
from processing.ocr.layout import assign_reading_order
from processing.ocr.tiling import generate_tiles, suppress_duplicate_detections
from processing.ocr.backends.detectors.base import BaseTextDetector
from processing.ocr.backends.detectors.paddle import PaddleTextDetector
from processing.ocr.backends.recognizers.base import BaseTextRecognizer, TextResult
from processing.ocr.backends.recognizers.paddle import PaddleTextRecognizer
from processing.ocr.backends.recognizers.trocr import TrOCRTextRecognizer
from processing.ocr.backends.orientation.base import BaseOrientationClassifier
from processing.ocr.backends.orientation.paddle import PaddleOrientationClassifier

__all__ = [
    "BoundingBox",
    "DetectedRegion",
    "TextRegion",
    "DeviceType",
    "DetectorBackend",
    "RecognizerBackend",
    "DetectionRuntime",
    "RecognitionRuntime",
    "OCRRuntime",
    "ImagePreprocessingConfig",
    "OCRConfig",
    "RuntimeSelector",
    "ResolvedRuntimeConfig",
    "SystemCapabilities",
    "OCRService",
    "normalize_image",
    "preprocess_image",
    "assign_reading_order",
    "generate_tiles",
    "suppress_duplicate_detections",
    "BaseTextDetector",
    "PaddleTextDetector",
    "BaseTextRecognizer",
    "TextResult",
    "PaddleTextRecognizer",
    "TrOCRTextRecognizer",
    "BaseOrientationClassifier",
    "PaddleOrientationClassifier",
    "OCRError",
    "MissingModelError",
    "UnsupportedRuntimeError",
    "GPUUnavailableError",
    "InvalidImageError",
    "OCRInitializationError",
]
