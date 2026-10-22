"""Hierarchical Context-Driven Handwriting Extraction (HCD-HTR) module."""

from processing.extract.config import ExtractionConfig, HardwareTier
from processing.extract.exceptions import (
    ExtractionError,
    PreprocessingError,
    GeometryError,
    ContextError,
    RecognitionError,
    AssemblyError,
)
from processing.extract.schemas import (
    Polygon,
    CanvasDimensions,
    NonTextElement,
    LineItem,
    TextBlock,
    ExtractionMetadata,
    ExtractionDocument,
)
from processing.extract.pipeline import HandwritingExtractionPipeline

__all__ = [
    "HandwritingExtractionPipeline",
    "ExtractionConfig",
    "HardwareTier",
    "ExtractionError",
    "PreprocessingError",
    "GeometryError",
    "ContextError",
    "RecognitionError",
    "AssemblyError",
    "Polygon",
    "CanvasDimensions",
    "NonTextElement",
    "LineItem",
    "TextBlock",
    "ExtractionMetadata",
    "ExtractionDocument",
]
