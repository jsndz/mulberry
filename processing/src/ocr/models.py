"""Pydantic data models for Mulberry OCR results and bounding boxes."""

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


class TextRegion(BaseModel):
    """Canonical narrow OCR result for a single detected text region."""

    text: str = Field(..., description="Recognized text string")
    bbox: BoundingBox = Field(
        ..., description="Exact bounding box relative to original input image"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Extraction confidence score between 0.0 and 1.0"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
