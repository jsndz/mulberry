"""Mulberry Canonical JSON & Document Representation Module."""

from processing.canonical.common import BoundingBox, Point, Color, CoordinateUnit, SourceMedia
from processing.canonical.text import TextElement, TextKind, TextStyle
from processing.canonical.diagram import (
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
from processing.canonical.element import (
    DocumentElement,
    BaseElement,
    ImageElement,
    TableElement,
    EquationElement,
)
from processing.canonical.document import Document, Page, DocumentMetadata
from processing.canonical.exporter import generate_json_schema, create_realistic_example

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
    "ImageElement",
    "TableElement",
    "EquationElement",
    "Document",
    "Page",
    "DocumentMetadata",
    "generate_json_schema",
    "create_realistic_example",
]
