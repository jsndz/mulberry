"""Common primitives for geometry, positioning, styling, and metadata."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CoordinateUnit(str, Enum):
    """Unit of measurement for spatial coordinates."""

    PX = "px"
    PT = "pt"
    NORMALIZED = "normalized"
    MM = "mm"
    INCH = "in"


class Point(BaseModel):
    """2D Point representation (x, y)."""

    x: float = Field(..., description="X coordinate relative to page origin (top-left)")
    y: float = Field(..., description="Y coordinate relative to page origin (top-left)")


class BoundingBox(BaseModel):
    """Exact spatial bounding box and position.

    Position is anchored at the top-left corner of the bounding box.
    """

    x: float = Field(..., description="X coordinate of top-left corner")
    y: float = Field(..., description="Y coordinate of top-left corner")
    width: float = Field(..., description="Width of bounding box")
    height: float = Field(..., description="Height of bounding box")
    unit: CoordinateUnit = Field(
        default=CoordinateUnit.PX,
        description="Unit of measurement for coordinates",
    )

    @field_validator("width", "height")
    @classmethod
    def validate_non_negative_dimensions(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Bounding box width and height must be non-negative")
        return v


class Color(BaseModel):
    """Color representation supporting hex codes or RGBA values."""

    hex: str = Field(..., description="Hex color string, e.g., '#000000' or '#FF5733'")
    alpha: float = Field(default=1.0, ge=0.0, le=1.0, description="Opacity from 0.0 to 1.0")


class SourceMedia(BaseModel):
    """Origin information for the source document page."""

    file_path: Optional[str] = Field(default=None, description="Original filename or path")
    media_type: str = Field(..., description="Media type, e.g., 'image/png', 'image/jpeg', 'application/pdf'")
    original_page_number: Optional[int] = Field(
        default=None, ge=1, description="1-indexed page number if derived from multi-page document"
    )
    dpi: Optional[int] = Field(default=None, ge=1, description="DPI/Resolution of input media")
