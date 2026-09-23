"""Mulberry Processing Engine package.

Modular architecture containing two core sub-modules:
- `processing.canonical`: Canonical JSON document model & exports
- `processing.ocr`: PaddleOCR engine, hardware detection & OCR service
"""

from processing import canonical
from processing import ocr

# Re-exports for convenient top-level access
from processing.canonical import (
    Document,
    Page,
    DocumentMetadata,
    TextElement,
    TextKind,
    DiagramElement,
    DiagramCategory,
    DocumentElement,
)
from processing.canonical.common import BoundingBox, CoordinateUnit
from processing.ocr import OCRService, OCRConfig, TextRegion, DeviceType, OCRRuntime

__all__ = [
    "canonical",
    "ocr",
    "Document",
    "Page",
    "DocumentMetadata",
    "BoundingBox",
    "CoordinateUnit",
    "TextElement",
    "TextKind",
    "DiagramElement",
    "DiagramCategory",
    "DocumentElement",
    "OCRService",
    "OCRConfig",
    "TextRegion",
    "DeviceType",
    "OCRRuntime",
]

__version__ = "0.1.0"
