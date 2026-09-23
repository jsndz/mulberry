"""Mulberry OCR Processing Engine Submodule."""

from processing.ocr.models import BoundingBox, TextRegion
from processing.ocr.config import OCRConfig, DeviceType, OCRRuntime
from processing.ocr.runtime import RuntimeSelector, SystemCapabilities
from processing.ocr.service import OCRService
from processing.ocr.exceptions import (
    OCRError,
    MissingModelError,
    UnsupportedRuntimeError,
    GPUUnavailableError,
    InvalidImageError,
    OCRInitializationError,
)

__all__ = [
    "BoundingBox",
    "TextRegion",
    "OCRConfig",
    "DeviceType",
    "OCRRuntime",
    "RuntimeSelector",
    "SystemCapabilities",
    "OCRService",
    "OCRError",
    "MissingModelError",
    "UnsupportedRuntimeError",
    "GPUUnavailableError",
    "InvalidImageError",
    "OCRInitializationError",
]
