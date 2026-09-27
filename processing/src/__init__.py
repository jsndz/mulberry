"""Mulberry Processing Engine package.

Modular architecture containing core sub-modules:
- `processing.canonical`: Canonical JSON document model & exports
- `processing.ocr`: Decoupled OCR engine, hardware detection & OCR service
- `processing.diagram`: Dynamic GPU/CPU diagram detection system
- `processing.converter`: Image format converter (DNG to PNG, etc.)
"""

from processing import canonical
from processing import ocr
from processing import diagram
from processing import converter

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
from processing.converter import (
    ImageConverter,
    convert_dng_to_png,
    dng_bytes_to_png_bytes,
    dng_to_numpy,
    convert_image,
)

__all__ = [
    "canonical",
    "ocr",
    "diagram",
    "converter",
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
    "ImageConverter",
    "convert_dng_to_png",
    "dng_bytes_to_png_bytes",
    "dng_to_numpy",
    "convert_image",
]


__version__ = "0.1.0"
