"""Canonical document and page models for Mulberry."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from processing.canonical.common import CoordinateUnit, SourceMedia
from processing.canonical.element import DocumentElement


class DocumentMetadata(BaseModel):
    """Global document metadata."""

    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author or owner")
    created_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Creation timestamp (UTC)"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=datetime.utcnow, description="Last updated timestamp (UTC)"
    )
    source_file: Optional[str] = Field(default=None, description="Original input filename or path")
    generator_version: str = Field(
        default="0.1.0", description="Version of processing engine or schema that created document"
    )
    extra_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary custom key-value metadata"
    )


class Page(BaseModel):
    """Single page container holding an ordered sequence of document elements."""

    page_number: int = Field(..., ge=1, description="1-indexed page number within document")
    width: float = Field(..., gt=0.0, description="Page canvas width")
    height: float = Field(..., gt=0.0, description="Page canvas height")
    unit: CoordinateUnit = Field(
        default=CoordinateUnit.PX, description="Coordinate measurement unit for page dimensions and children"
    )
    source_media: Optional[SourceMedia] = Field(
        default=None, description="Metadata describing source image or PDF page"
    )
    elements: List[DocumentElement] = Field(
        default_factory=list, description="Ordered array of page elements (reading/layout order)"
    )

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Page width and height must be strictly positive (> 0)")
        return v


class Document(BaseModel):
    """Root canonical Mulberry document model."""

    version: str = Field(
        default="1.0", description="Canonical document schema specification version"
    )
    id: str = Field(..., description="Unique document ID (e.g. UUID)")
    metadata: DocumentMetadata = Field(
        default_factory=DocumentMetadata, description="Document level metadata"
    )
    pages: List[Page] = Field(
        default_factory=list, description="Ordered list of pages comprising document"
    )
