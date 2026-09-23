"""Text element definitions for Mulberry canonical document model."""

from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
from processing.models.common import BoundingBox, Color


class TextKind(str, Enum):
    """Supported text element categories."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    BULLET = "bullet"
    NUMBERED_LIST = "numbered_list"


class TextStyle(BaseModel):
    """Formatting style metadata for text blocks."""

    font_family: Optional[str] = Field(default=None, description="Font family name")
    font_size: Optional[float] = Field(default=None, ge=0.0, description="Font size in points or pixels")
    font_weight: Optional[str] = Field(default=None, description="Font weight e.g. 'bold', 'normal', '700'")
    italic: bool = Field(default=False, description="Whether text is italicized")
    color: Optional[Color] = Field(default=None, description="Text color")


class TextElement(BaseModel):
    """Canonical representation of a text block in a document.

    Supports headings, paragraphs, bullet points, and numbered list items with exact
    positioning and OCR confidence metrics.
    """

    id: str = Field(..., description="Unique identifier for the text element")
    type: Literal["text"] = Field(default="text", description="Element type discriminator")
    kind: TextKind = Field(..., description="Semantic text kind: heading, paragraph, bullet, numbered_list")
    content: str = Field(..., description="Extracted plain text or markdown content")
    position: BoundingBox = Field(..., description="Exact bounding box and coordinates")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="OCR/AI extraction confidence score (0.0 - 1.0)"
    )

    # Contextual hierarchy metadata
    heading_level: Optional[int] = Field(
        default=None, ge=1, le=6, description="Heading depth level (1-6) when kind is 'heading'"
    )
    list_level: Optional[int] = Field(
        default=None, ge=1, description="Nesting indent level (1-based) for bullet or numbered list items"
    )
    list_index: Optional[int] = Field(
        default=None, ge=1, description="Item index number (1-based) when kind is 'numbered_list'"
    )

    style: Optional[TextStyle] = Field(default=None, description="Styling attributes")

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
