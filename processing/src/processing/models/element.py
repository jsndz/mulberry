"""Element hierarchy and discriminated polymorphic union for Mulberry canonical models."""

from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from processing.models.common import BoundingBox
from processing.models.text import TextElement
from processing.models.diagram import DiagramElement


class BaseElement(BaseModel):
    """Base model for all page document elements."""

    id: str = Field(..., description="Unique element identifier")
    position: BoundingBox = Field(..., description="Exact bounding box position on page")
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Extraction confidence score"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Extensible key-value metadata for non-canonical attributes"
    )


# --- Future Element Types (Extensibility Stubs) ---


class ImageElement(BaseElement):
    """Future element type for standalone embedded images."""

    type: Literal["image"] = Field(default="image", description="Element type discriminator")
    image_ref: str = Field(..., description="Image URI, file path, or asset identifier")
    caption: Optional[str] = Field(default=None, description="Image caption text")


class TableElement(BaseElement):
    """Future element type for extracted structured tables."""

    type: Literal["table"] = Field(default="table", description="Element type discriminator")
    headers: List[str] = Field(default_factory=list, description="Table column header titles")
    rows: List[List[str]] = Field(default_factory=list, description="2D grid matrix of table cells")
    caption: Optional[str] = Field(default=None, description="Table caption")


class EquationElement(BaseElement):
    """Future element type for mathematical formulas / equations."""

    type: Literal["equation"] = Field(default="equation", description="Element type discriminator")
    latex: str = Field(..., description="LaTeX expression of mathematical equation")
    display_mode: bool = Field(default=True, description="True for block display, False for inline")


# Polymorphic Union of Document Elements using Pydantic v2 Discriminator
DocumentElement = Annotated[
    Union[
        TextElement,
        DiagramElement,
        ImageElement,
        TableElement,
        EquationElement,
    ],
    Field(discriminator="type"),
]
