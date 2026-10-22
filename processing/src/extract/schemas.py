"""Data models, geometry schemas, and production output representation for HCD-HTR."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple, Union
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator

from processing.canonical.common import BoundingBox, CoordinateUnit
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.canonical.element import DocumentElement
from processing.canonical.text import TextElement, TextKind
from processing.canonical.diagram import DiagramCategory, DiagramElement


class Polygon(BaseModel):
    """4-point oriented polygon representing tight bounding coordinates: [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]."""

    points: List[Tuple[float, float]] = Field(
        ...,
        description="4 points (x, y) forming an oriented quadrilateral in clockwise order.",
    )

    @field_validator("points", mode="before")
    @classmethod
    def validate_points(cls, v: Any) -> List[Tuple[float, float]]:
        if not isinstance(v, (list, tuple)):
            raise ValueError(f"Polygon points must be a list or tuple of coordinates, got {type(v)}")
        if len(v) != 4:
            raise ValueError(f"Polygon must have exactly 4 points, got {len(v)}")
        converted = []
        for pt in v:
            if not isinstance(pt, (list, tuple)) or len(pt) != 2:
                raise ValueError(f"Each point must be a 2-element tuple/list (x, y), got {pt}")
            converted.append((float(pt[0]), float(pt[1])))
        return converted

    @property
    def center_of_mass(self) -> Tuple[float, float]:
        """Calculates vertical center of mass (y_bar) and horizontal center (x_bar)."""
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return sum(xs) / 4.0, sum(ys) / 4.0

    @property
    def x_bar(self) -> float:
        return self.center_of_mass[0]

    @property
    def y_bar(self) -> float:
        return self.center_of_mass[1]

    def to_bbox(self) -> List[float]:
        """Convert polygon into axis-aligned bounding box [xmin, ymin, xmax, ymax]."""
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return [min(xs), min(ys), max(xs), max(ys)]

    @classmethod
    def from_bbox(cls, xmin: float, ymin: float, xmax: float, ymax: float) -> "Polygon":
        """Construct a 4-point rectangular polygon from axis-aligned bounding coordinates."""
        return cls(points=[(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax)])

    def to_list(self) -> List[List[float]]:
        """Serialize points to a list of lists [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]."""
        return [[round(p[0], 2), round(p[1], 2)] for p in self.points]


class CanvasDimensions(BaseModel):
    """Page canvas dimensions."""

    width: int = Field(..., gt=0, description="Canvas width in pixels")
    height: int = Field(..., gt=0, description="Canvas height in pixels")
    unit: str = Field(default="px", description="Measurement unit (default 'px')")


class NonTextElement(BaseModel):
    """Isolated non-text component (diagram, table, flowchart, or pre-printed branding)."""

    id: str = Field(..., description="Unique non-text component identifier")
    type: str = Field(..., description="Element category: 'diagram', 'flowchart', 'table', 'preprinted_header'")
    polygon: List[List[float]] = Field(..., description="Polygonal coordinates [[x1,y1]...[x4,y4]]")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as brand, fields, confidence")


class LineItem(BaseModel):
    """Recognized single line of text bound to spatial coordinates."""

    line_id: str = Field(..., description="Unique line identifier")
    content: str = Field(..., description="Verbatim transcribed line text")
    polygon: Optional[List[List[float]]] = Field(default=None, description="4-point bounding polygon")
    bbox: Optional[List[float]] = Field(default=None, description="Axis-aligned [xmin, ymin, xmax, ymax]")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class TextBlock(BaseModel):
    """Logical document text block (heading or paragraph)."""

    id: str = Field(..., description="Unique block identifier")
    type: Literal["heading", "paragraph"] = Field(..., description="Block type: 'heading' or 'paragraph'")
    level: Optional[int] = Field(default=None, ge=1, le=6, description="Heading level if type is 'heading'")
    content: Optional[str] = Field(default=None, description="Direct text content for heading blocks")
    polygon: Optional[List[List[float]]] = Field(default=None, description="Bounding polygon for heading blocks")
    lines: Optional[List[LineItem]] = Field(default=None, description="Line entries if type is 'paragraph'")

    @model_validator(mode="after")
    def validate_type_fields(self) -> "TextBlock":
        if self.type == "heading":
            if not self.content:
                raise ValueError("Heading block must have non-empty 'content'")
            if self.level is None:
                self.level = 1
        elif self.type == "paragraph":
            if not self.lines:
                raise ValueError("Paragraph block must contain at least one line in 'lines'")
        return self


class ExtractionMetadata(BaseModel):
    """Metadata describing document extraction result."""

    detected_topic: Optional[str] = Field(default=None, description="Topic inferred by macro scout sweep")
    canvas_dimensions: CanvasDimensions = Field(..., description="Page width and height")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary engine execution metadata")


class ExtractionDocument(BaseModel):
    """Strict JSON schema output for HCD-HTR specified in docs/extract_design.md."""

    document_id: str = Field(..., description="Unique document extraction ID")
    metadata: ExtractionMetadata = Field(..., description="Document metadata")
    non_text_elements: List[NonTextElement] = Field(
        default_factory=list, description="Extracted diagrams, preprinted headers, tables"
    )
    text_blocks: List[TextBlock] = Field(
        default_factory=list, description="Ordered hierarchy of headings and paragraphs"
    )

    def to_canonical_document(self) -> Document:
        """Convert the ExtractionDocument into Mulberry's canonical Document model."""
        width = float(self.metadata.canvas_dimensions.width)
        height = float(self.metadata.canvas_dimensions.height)

        elements: List[DocumentElement] = []

        # 1. Convert non-text elements
        for non_text in self.non_text_elements:
            poly = Polygon(points=non_text.polygon)  # type: ignore
            bbox = poly.to_bbox()
            elements.append(
                DiagramElement(
                    id=non_text.id,
                    position=BoundingBox(
                        x=bbox[0],
                        y=bbox[1],
                        width=max(1.0, bbox[2] - bbox[0]),
                        height=max(1.0, bbox[3] - bbox[1]),
                        unit=CoordinateUnit.PX,
                    ),
                    category=DiagramCategory.STRUCTURED,
                    confidence=non_text.metadata.get("confidence", 1.0),
                    metadata={"original_type": non_text.type, **non_text.metadata},
                )
            )

        # 2. Convert text blocks
        for block in self.text_blocks:
            if block.type == "heading":
                poly = Polygon(points=block.polygon) if block.polygon else Polygon.from_bbox(0, 0, width, 50)
                bbox = poly.to_bbox()
                elements.append(
                    TextElement(
                        id=block.id,
                        position=BoundingBox(
                            x=bbox[0],
                            y=bbox[1],
                            width=max(1.0, bbox[2] - bbox[0]),
                            height=max(1.0, bbox[3] - bbox[1]),
                            unit=CoordinateUnit.PX,
                        ),
                        content=block.content or "",
                        kind=TextKind.HEADING,
                        heading_level=block.level or 1,
                        metadata={"level": block.level or 1},
                    )
                )
            elif block.type == "paragraph" and block.lines:
                # Group lines into paragraph text element or separate elements
                for line in block.lines:
                    if line.polygon:
                        poly = Polygon(points=line.polygon)  # type: ignore
                        bbox = poly.to_bbox()
                    elif line.bbox:
                        bbox = line.bbox
                    else:
                        bbox = [0.0, 0.0, width, 30.0]

                    elements.append(
                        TextElement(
                            id=line.line_id,
                            position=BoundingBox(
                                x=bbox[0],
                                y=bbox[1],
                                width=max(1.0, bbox[2] - bbox[0]),
                                height=max(1.0, bbox[3] - bbox[1]),
                                unit=CoordinateUnit.PX,
                            ),
                            content=line.content,
                            kind=TextKind.PARAGRAPH,
                            confidence=line.confidence,
                            metadata={"parent_block_id": block.id},
                        )
                    )

        page = Page(
            page_number=1,
            width=width,
            height=height,
            unit=CoordinateUnit.PX,
            elements=elements,
        )

        return Document(
            id=self.document_id,
            metadata=DocumentMetadata(
                title=self.metadata.detected_topic,
                generator_version="HCD-HTR-1.0",
                extra_metadata=self.metadata.extra,
            ),
            pages=[page],
        )
