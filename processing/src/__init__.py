"""Mulberry Processing Engine package.

Modular architecture containing core sub-modules:
- `processing.canonical`: Canonical JSON document model & exports
- `processing.ocr`: PaddleOCR engine, hardware detection & OCR service
- `processing.diagram`: Dynamic GPU/CPU diagram detection system
"""

from processing import canonical
from processing import ocr
from processing import diagram

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
from processing.diagram import (
    get_detector,
    draw_diagram_boxes,
    check_gpu_availability,
    BaseDiagramDetector,
    DiTDiagramDetector,
    YOLODiagramDetector,
    DiagramDetectionRegion,
)

__all__ = [
    "canonical",
    "ocr",
    "diagram",
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
    "get_detector",
    "draw_diagram_boxes",
    "check_gpu_availability",
    "BaseDiagramDetector",
    "DiTDiagramDetector",
    "YOLODiagramDetector",
    "DiagramDetectionRegion",
]


__version__ = "0.1.0"

