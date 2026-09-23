"""Mulberry Processing Engine & Canonical Document Model.

This package defines the canonical document model for Mulberry, enabling
local-first processing of handwritten/scanned images and PDFs into digital notes.
"""

from processing.models.common import BoundingBox, Point, Color, CoordinateUnit, SourceMedia
from processing.models.text import TextElement, TextKind, TextStyle
from processing.models.diagram import (
    DiagramElement,
    DiagramCategory,
    DiagramPrimitive,
    BoxPrimitive,
    CirclePrimitive,
    LinePrimitive,
    ArrowPrimitive,
    LabelPrimitive,
    ConnectionPrimitive,
    StructuredDiagramData,
    IllustratedDiagramData,
)
from processing.models.element import DocumentElement, BaseElement
from processing.models.document import Document, Page, DocumentMetadata

__all__ = [
    "BoundingBox",
    "Point",
    "Color",
    "CoordinateUnit",
    "SourceMedia",
    "TextElement",
    "TextKind",
    "TextStyle",
    "DiagramElement",
    "DiagramCategory",
    "DiagramPrimitive",
    "BoxPrimitive",
    "CirclePrimitive",
    "LinePrimitive",
    "ArrowPrimitive",
    "LabelPrimitive",
    "ConnectionPrimitive",
    "StructuredDiagramData",
    "IllustratedDiagramData",
    "DocumentElement",
    "BaseElement",
    "Document",
    "Page",
    "DocumentMetadata",
]

__version__ = "0.1.0"


def main():
    print("Mulberry processing module initialized.")
