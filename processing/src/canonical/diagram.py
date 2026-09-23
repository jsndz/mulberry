"""Canonical diagram element definitions for Mulberry document model."""

from enum import Enum
from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator
from processing.canonical.common import BoundingBox, Color, Point


class DiagramCategory(str, Enum):
    """Category of diagram."""

    STRUCTURED = "structured"
    ILLUSTRATED = "illustrated"


class BasePrimitive(BaseModel):
    """Base class for all structured diagram primitives."""

    id: str = Field(..., description="Unique primitive identifier within the diagram")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Detection confidence score for this primitive"
    )


class BoxPrimitive(BasePrimitive):
    """Structured rectangle/box shape primitive."""

    primitive_type: Literal["box"] = Field(default="box", description="Primitive type discriminator")
    position: BoundingBox = Field(..., description="Bounding box of rectangle")
    label: Optional[str] = Field(default=None, description="Text label inside or associated with box")
    fill_color: Optional[Color] = Field(default=None, description="Fill color")
    stroke_color: Optional[Color] = Field(default=None, description="Border color")
    stroke_width: Optional[float] = Field(default=None, ge=0.0, description="Border line thickness")
    corner_radius: Optional[float] = Field(default=None, ge=0.0, description="Rounded corner radius")


class CirclePrimitive(BasePrimitive):
    """Structured circle/ellipse shape primitive."""

    primitive_type: Literal["circle"] = Field(default="circle", description="Primitive type discriminator")
    position: BoundingBox = Field(..., description="Bounding box enclosing circle/ellipse")
    label: Optional[str] = Field(default=None, description="Text label inside circle")
    fill_color: Optional[Color] = Field(default=None, description="Fill color")
    stroke_color: Optional[Color] = Field(default=None, description="Border color")
    stroke_width: Optional[float] = Field(default=None, ge=0.0, description="Border line thickness")


class LinePrimitive(BasePrimitive):
    """Structured straight or segmented line primitive."""

    primitive_type: Literal["line"] = Field(default="line", description="Primitive type discriminator")
    points: List[Point] = Field(..., min_length=2, description="Ordered sequence of points defining line/polyline")
    stroke_color: Optional[Color] = Field(default=None, description="Line stroke color")
    stroke_width: Optional[float] = Field(default=None, ge=0.0, description="Line thickness")
    style: Optional[str] = Field(default=None, description="Line style e.g. 'solid', 'dashed', 'dotted'")


class ArrowPrimitive(BasePrimitive):
    """Structured arrow primitive linking geometry or indicating direction."""

    primitive_type: Literal["arrow"] = Field(default="arrow", description="Primitive type discriminator")
    start_point: Point = Field(..., description="Starting point of arrow line")
    end_point: Point = Field(..., description="Ending point of arrow line")
    has_head_at_start: bool = Field(default=False, description="Whether arrowhead exists at start point")
    has_head_at_end: bool = Field(default=True, description="Whether arrowhead exists at end point")
    label: Optional[str] = Field(default=None, description="Text label associated with arrow")
    stroke_color: Optional[Color] = Field(default=None, description="Arrow line color")
    stroke_width: Optional[float] = Field(default=None, ge=0.0, description="Arrow line thickness")


class LabelPrimitive(BasePrimitive):
    """Standalone structured text label primitive inside a diagram."""

    primitive_type: Literal["label"] = Field(default="label", description="Primitive type discriminator")
    text: str = Field(..., description="Text content of label")
    position: BoundingBox = Field(..., description="Position of label")
    font_size: Optional[float] = Field(default=None, ge=0.0, description="Font size")
    color: Optional[Color] = Field(default=None, description="Text color")


class ConnectionPrimitive(BasePrimitive):
    """Explicit node connection / graph edge primitive connecting two shapes."""

    primitive_type: Literal["connection"] = Field(
        default="connection", description="Primitive type discriminator"
    )
    source_node_id: str = Field(..., description="Primitive ID of source shape/node")
    target_node_id: str = Field(..., description="Primitive ID of target shape/node")
    connection_type: Optional[str] = Field(
        default="arrow", description="Connection type e.g. 'arrow', 'line', 'dashed_arrow'"
    )
    label: Optional[str] = Field(default=None, description="Label attached to relationship edge")
    directional: bool = Field(default=True, description="Whether connection is directed")


DiagramPrimitive = Annotated[
    Union[
        BoxPrimitive,
        CirclePrimitive,
        LinePrimitive,
        ArrowPrimitive,
        LabelPrimitive,
        ConnectionPrimitive,
    ],
    Field(discriminator="primitive_type"),
]


class StructuredDiagramData(BaseModel):
    """Payload for structured diagrams reconstructible via shapes and connections."""

    primitives: List[DiagramPrimitive] = Field(
        default_factory=list, description="Ordered list of visual geometric primitives"
    )


class IllustratedDiagramData(BaseModel):
    """Payload for complex illustrated diagrams preserved via cropped image reference."""

    image_ref: str = Field(..., description="Path, URI, asset ID, or Base64 data of cropped illustration")
    mime_type: Optional[str] = Field(default="image/png", description="Image MIME type e.g. 'image/png'")
    width: Optional[float] = Field(default=None, ge=0.0, description="Original image width in pixels")
    height: Optional[float] = Field(default=None, ge=0.0, description="Original image height in pixels")
    caption: Optional[str] = Field(default=None, description="Text caption near or inside illustration")
    alt_text: Optional[str] = Field(default=None, description="Semantic description of drawing")


class DiagramElement(BaseModel):
    """Canonical representation of a diagram element."""

    id: str = Field(..., description="Unique identifier for diagram element")
    type: Literal["diagram"] = Field(default="diagram", description="Element type discriminator")
    category: DiagramCategory = Field(
        ..., description="Diagram category: 'structured' or 'illustrated'"
    )
    position: BoundingBox = Field(..., description="Exact outer bounding box of diagram on page")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Overall diagram detection confidence score (0.0 - 1.0)"
    )

    structured_data: Optional[StructuredDiagramData] = Field(
        default=None, description="Primitive geometry data if category is 'structured'"
    )
    illustrated_data: Optional[IllustratedDiagramData] = Field(
        default=None, description="Cropped image reference if category is 'illustrated'"
    )

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        return v
