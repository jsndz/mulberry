"""Pydantic data models for Mulberry OCR requests, detected regions, and canonical results."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class BoundingBox(BaseModel):
    """Bounding box in pixel coordinates.

    Origin (0, 0) is anchored at the top-left corner of the original input image.
    x: X coordinate (left offset in pixels)
    y: Y coordinate (top offset in pixels)
    width: Bounding box width in pixels
    height: Bounding box height in pixels
    """

    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of bounding box")
    height: float = Field(..., description="Height of bounding box")

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Bounding box width and height must be non-negative")
        return v


class DetectedRegion(BaseModel):
    """Intermediate text region produced by TextDetector before recognition."""

    polygon: List[List[float]] = Field(
        ..., description="4-point polygon coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]"
    )
    bbox: BoundingBox = Field(..., description="Axis-aligned bounding box")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Detection confidence score between 0.0 and 1.0"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v


class TextRegion(BaseModel):
    """Canonical narrow OCR result for a single detected and recognized text region."""

    id: str = Field(default="ocr_text_1", description="Unique element identifier")
    text: str = Field(..., description="Recognized text string")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction/recognition confidence score between 0.0 and 1.0"
    )
    polygon: List[List[float]] = Field(
        default_factory=list,
        description="4-point polygon coordinates [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]",
    )
    bbox: BoundingBox = Field(
        ..., description="Exact bounding box relative to original input image"
    )
    recognizer: str = Field(
        default="paddle", description="Recognizer backend used, e.g. 'trocr' or 'paddle'"
    )
    reading_order: int = Field(
        default=0, description="Spatial reading order index (0-indexed)"
    )

    # Extensible metadata fields for document understanding
    element_type: str = Field(
        default="text", description="Element type e.g. 'text', 'heading', 'code'"
    )
    handwriting: bool = Field(
        default=True, description="Whether the text region is classified as handwriting"
    )
    paragraph_id: Optional[str] = Field(
        default=None, description="Optional paragraph grouping ID"
    )
    heading_level: Optional[int] = Field(
        default=None, description="Optional heading level (1-6)"
    )
    code_snippet: bool = Field(
        default=False, description="Whether element belongs to a code snippet block"
    )
    diagram_reference: Optional[str] = Field(
        default=None, description="Optional referenced diagram element ID"
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary additional key-value metadata"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
