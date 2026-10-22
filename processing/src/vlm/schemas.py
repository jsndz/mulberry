"""Structured schemas and canonical converters for Mulberry VLM module."""

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4
from pydantic import BaseModel, Field, field_validator, model_validator

from processing.canonical.common import BoundingBox, CoordinateUnit, SourceMedia
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.canonical.element import DocumentElement
from processing.canonical.text import TextElement, TextKind


class VLMBlockType(str, Enum):
    """Semantic block classification recognized by the VLM."""

    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    UNCLEAR = "unclear"


class VLMListItem(BaseModel):
    """Single item entry within a list block."""

    text: str = Field(..., description="Item text content")
    level: int = Field(default=1, ge=1, description="List indentation/nesting level (1-indexed)")
    index: Optional[int] = Field(default=None, ge=1, description="Item number index for numbered lists")

    @model_validator(mode="before")
    @classmethod
    def parse_raw_item(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"text": data, "level": 1, "index": None}
        return data


class VLMBlock(BaseModel):
    """Extracted text block produced by the VLM."""

    type: VLMBlockType = Field(..., description="Block type: heading, paragraph, list, unclear")
    text: Optional[str] = Field(default=None, description="Plain text for heading, paragraph, or unclear blocks")
    level: Optional[int] = Field(default=None, ge=1, le=6, description="Heading level (1-6) if type is heading")
    list_type: Optional[Literal["bullet", "numbered"]] = Field(
        default=None, description="List type discriminator ('bullet' or 'numbered') if type is list"
    )
    items: Optional[List[VLMListItem]] = Field(
        default=None, description="List of items if type is list"
    )
    confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence score (0.0 to 1.0)"
    )
    bounding_box: Optional[List[float]] = Field(
        default=None, description="Optional bounding box [x, y, width, height]"
    )

    @field_validator("items", mode="before")
    @classmethod
    def normalize_items(cls, v: Any) -> Any:
        if v is None:
            return None
        if isinstance(v, list):
            normalized = []
            for idx, item in enumerate(v, start=1):
                if isinstance(item, str):
                    normalized.append({"text": item, "level": 1, "index": idx})
                elif isinstance(item, dict):
                    normalized.append(item)
                else:
                    normalized.append(item)
            return normalized
        return v

    @model_validator(mode="after")
    def validate_block_fields(self) -> "VLMBlock":
        if self.type == VLMBlockType.HEADING:
            if not self.text:
                raise ValueError("Heading block must have non-empty 'text'")
            if self.level is None:
                self.level = 1
        elif self.type == VLMBlockType.PARAGRAPH:
            if not self.text:
                raise ValueError("Paragraph block must have non-empty 'text'")
        elif self.type == VLMBlockType.LIST:
            if not self.items or len(self.items) == 0:
                raise ValueError("List block must contain at least one item in 'items'")
            if self.list_type is None:
                self.list_type = "bullet"
        elif self.type == VLMBlockType.UNCLEAR:
            if not self.text:
                self.text = "[unclear]"
        return self


class VLMStructuredOutput(BaseModel):
    """Complete structured response extracted from a single handwritten document image."""

    blocks: List[VLMBlock] = Field(default_factory=list, description="Ordered sequence of document text blocks")

    @model_validator(mode="before")
    @classmethod
    def normalize_input_data(cls, data: Any) -> Any:
        if isinstance(data, list):
            return {"blocks": data}

        if isinstance(data, dict):
            if "blocks" in data:
                return data

            # Normalize alternate key layouts e.g. {"heading": "...", "paragraphs": [...], "lists": [...]}
            normalized_blocks: List[Dict[str, Any]] = []

            # 1. Heading
            if "heading" in data and data["heading"]:
                h_val = data["heading"]
                if isinstance(h_val, str):
                    normalized_blocks.append({"type": "heading", "level": 1, "text": h_val})
                elif isinstance(h_val, dict):
                    normalized_blocks.append({"type": "heading", **h_val})
                elif isinstance(h_val, list):
                    for item in h_val:
                        if isinstance(item, str):
                            normalized_blocks.append({"type": "heading", "level": 1, "text": item})
                        elif isinstance(item, dict):
                            normalized_blocks.append({"type": "heading", **item})

            # 2. Paragraphs / body
            for p_key in ["paragraphs", "paragraph", "body", "sections"]:
                if p_key in data and data[p_key]:
                    p_val = data[p_key]
                    if isinstance(p_val, str):
                        normalized_blocks.append({"type": "paragraph", "text": p_val})
                    elif isinstance(p_val, list):
                        for item in p_val:
                            if isinstance(item, str):
                                normalized_blocks.append({"type": "paragraph", "text": item})
                            elif isinstance(item, dict):
                                text = item.get("text") or item.get("content") or ""
                                if text:
                                    normalized_blocks.append({"type": "paragraph", "text": text})

            # 3. Lists
            for l_key in ["lists", "list", "items"]:
                if l_key in data and data[l_key]:
                    l_val = data[l_key]
                    if isinstance(l_val, list):
                        for item in l_val:
                            if isinstance(item, dict) and item.get("type") == "list":
                                normalized_blocks.append(item)
                            elif isinstance(item, list):
                                normalized_blocks.append({"type": "list", "items": item})
                            elif isinstance(item, str):
                                normalized_blocks.append({"type": "list", "items": [item]})

            if normalized_blocks:
                return {"blocks": normalized_blocks}

        return data

    def to_canonical_elements(self) -> List[DocumentElement]:
        """Convert VLM blocks to a list of canonical DocumentElement instances."""
        elements: List[DocumentElement] = []
        elem_counter = 1

        for block in self.blocks:
            bbox = self._create_bounding_box(block.bounding_box)

            if block.type == VLMBlockType.HEADING:
                elements.append(
                    TextElement(
                        id=f"vlm_text_{elem_counter}",
                        kind=TextKind.HEADING,
                        heading_level=block.level or 1,
                        content=block.text or "",
                        position=bbox,
                        confidence=block.confidence,
                    )
                )
                elem_counter += 1

            elif block.type == VLMBlockType.PARAGRAPH:
                elements.append(
                    TextElement(
                        id=f"vlm_text_{elem_counter}",
                        kind=TextKind.PARAGRAPH,
                        content=block.text or "",
                        position=bbox,
                        confidence=block.confidence,
                    )
                )
                elem_counter += 1

            elif block.type == VLMBlockType.LIST:
                is_numbered = block.list_type == "numbered"
                for item_idx, item in enumerate(block.items or [], start=1):
                    kind = TextKind.NUMBERED_LIST if is_numbered else TextKind.BULLET
                    list_index = item.index if (is_numbered and item.index is not None) else (item_idx if is_numbered else None)

                    elements.append(
                        TextElement(
                            id=f"vlm_text_{elem_counter}",
                            kind=kind,
                            list_level=item.level,
                            list_index=list_index,
                            content=item.text,
                            position=bbox,
                            confidence=block.confidence,
                        )
                    )
                    elem_counter += 1

            elif block.type == VLMBlockType.UNCLEAR:
                content = block.text if block.text else "[unclear]"
                elements.append(
                    TextElement(
                        id=f"vlm_text_{elem_counter}",
                        kind=TextKind.PARAGRAPH,
                        content=content,
                        position=bbox,
                        confidence=0.0,
                    )
                )
                elem_counter += 1

        return elements

    def to_canonical_document(
        self,
        width: float = 1000.0,
        height: float = 1000.0,
        doc_id: Optional[str] = None,
        source_file: Optional[str] = None,
        media_type: str = "image/png",
    ) -> Document:
        """Convert structured output into a full canonical Mulberry Document."""
        elements = self.to_canonical_elements()
        resolved_doc_id = doc_id or f"doc_{uuid4().hex[:12]}"

        page = Page(
            page_number=1,
            width=float(width),
            height=float(height),
            unit=CoordinateUnit.PX,
            source_media=SourceMedia(
                file_path=source_file,
                media_type=media_type,
                original_page_number=1,
            )
            if source_file
            else None,
            elements=elements,
        )

        return Document(
            id=resolved_doc_id,
            version="1.0",
            metadata=DocumentMetadata(
                source_file=source_file,
                generator_version="0.1.0",
                extra_metadata={"vlm_model": "Qwen/Qwen3-VL-4B-Instruct"},
            ),
            pages=[page],
        )

    @staticmethod
    def _create_bounding_box(box_coords: Optional[List[float]]) -> BoundingBox:
        if box_coords and len(box_coords) == 4:
            return BoundingBox(
                x=float(box_coords[0]),
                y=float(box_coords[1]),
                width=max(0.0, float(box_coords[2])),
                height=max(0.0, float(box_coords[3])),
                unit=CoordinateUnit.PX,
            )
        # Spatial info not provided; canonical schema allows non-negative dimensions (0.0)
        return BoundingBox(x=0.0, y=0.0, width=0.0, height=0.0, unit=CoordinateUnit.PX)
