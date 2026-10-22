"""Configuration options for document exporters."""

from typing import Optional
from pydantic import BaseModel, Field


class MarkdownExportOptions(BaseModel):
    """Options controlling Markdown generation from Canonical Document."""

    include_frontmatter: bool = Field(
        default=True,
        description="Whether to emit YAML frontmatter (title, author, date, source).",
    )
    page_break_marker: str = Field(
        default="\n\n---\n\n",
        description="Delimiter inserted between consecutive pages.",
    )
    include_page_numbers: bool = Field(
        default=False,
        description="Whether to prefix each page with a 'Page N' comment or sub-heading.",
    )
    skip_diagrams: bool = Field(
        default=True,
        description="Whether to silently skip diagram elements without rendering placeholders.",
    )
    annotate_skipped_diagrams: bool = Field(
        default=False,
        description="Whether to insert HTML comments for skipped diagrams (e.g. <!-- diagram: id -->).",
    )


class PdfExportOptions(BaseModel):
    """Options controlling PDF generation from Canonical Document."""

    page_size: str = Field(
        default="A4",
        description="Standard paper size ('A4', 'LETTER', etc.).",
    )
    margin_pt: float = Field(
        default=36.0,
        ge=0.0,
        description="Document margins in points (1 pt = 1/72 inch). 36pt = 0.5 inch.",
    )
    font_name: str = Field(
        default="Helvetica",
        description="Base body font family name.",
    )
    heading_font_name: str = Field(
        default="Helvetica-Bold",
        description="Base heading font family name.",
    )
    include_page_numbers: bool = Field(
        default=True,
        description="Whether to render running 'Page X of Y' footers.",
    )
    page_break_between_pages: bool = Field(
        default=True,
        description="Whether canonical Document Page boundaries force a new PDF page break.",
    )
    skip_diagrams: bool = Field(
        default=True,
        description="Whether to skip diagram elements.",
    )
