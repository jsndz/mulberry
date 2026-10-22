"""Structural alignment and document hierarchy assembly for Stage 5."""

import re
from typing import Any, Dict, List, Optional
from uuid import uuid4

from processing.extract.schemas import (
    CanvasDimensions,
    ExtractionDocument,
    ExtractionMetadata,
    LineItem,
    NonTextElement,
    Polygon,
    TextBlock,
)


class StructuralAligner:
    """
    Binds transcribed text strings directly to Stage 2 physical ink polygons,
    detects headings versus body paragraphs, and produces the complete ExtractionDocument.
    """

    HEADING_REGEX = re.compile(
        r"^(#+|\d+\.|\([a-zA-Z0-9]+\)|[A-Z0-9\s:_-]{4,35}:?$)", re.IGNORECASE
    )

    def __init__(self) -> None:
        pass

    def is_likely_heading(self, content: str, line_height: float, avg_line_height: float) -> bool:
        """Heuristic check whether a line represents a heading block."""
        stripped = content.strip()
        if not stripped:
            return False

        # Short text ending with colon or starting with section numbering
        if stripped.endswith(":") or re.match(r"^\d+[\.\)]\s+", stripped):
            return True

        # Heading regex pattern and short length
        if len(stripped) < 40 and self.HEADING_REGEX.match(stripped):
            return True

        # Significantly taller font height than document average
        if avg_line_height > 0 and line_height > (avg_line_height * 1.35) and len(stripped) < 50:
            return True

        return False

    def assemble(
        self,
        polygons: List[Polygon],
        transcriptions: List[str],
        canvas_width: int,
        canvas_height: int,
        non_text_elements: Optional[List[NonTextElement]] = None,
        detected_topic: Optional[str] = None,
        document_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> ExtractionDocument:
        """
        Assembles lines, polygons, and non-text elements into a validated ExtractionDocument.
        """
        doc_id = document_id or f"doc_{uuid4().hex[:8]}"
        non_text = non_text_elements or []

        # 1. Pair polygons and text into LineItems
        line_items: List[LineItem] = []
        line_heights: List[float] = []

        for idx, (poly, text) in enumerate(zip(polygons, transcriptions)):
            line_id = f"line_{idx + 1:03d}"
            bbox = poly.to_bbox()
            h = bbox[3] - bbox[1]
            line_heights.append(h)

            line_items.append(
                LineItem(
                    line_id=line_id,
                    content=text.strip(),
                    polygon=poly.to_list(),
                    bbox=bbox,
                    confidence=1.0,
                )
            )

        avg_line_height = sum(line_heights) / float(len(line_heights)) if line_heights else 20.0

        # 2. Group into TextBlocks (Headings vs Paragraphs)
        text_blocks: List[TextBlock] = []
        current_paragraph_lines: List[LineItem] = []
        block_idx = 1

        for idx, item in enumerate(line_items):
            poly = polygons[idx]
            h = line_heights[idx]

            if self.is_likely_heading(item.content, h, avg_line_height):
                # Flush pending paragraph lines
                if current_paragraph_lines:
                    text_blocks.append(
                        TextBlock(
                            id=f"block_{block_idx:02d}",
                            type="paragraph",
                            lines=list(current_paragraph_lines),
                        )
                    )
                    block_idx += 1
                    current_paragraph_lines.clear()

                # Add heading block
                level = 1 if (idx == 0 or h > avg_line_height * 1.3) else 2
                text_blocks.append(
                    TextBlock(
                        id=f"block_{block_idx:02d}",
                        type="heading",
                        level=level,
                        content=item.content,
                        polygon=poly.to_list(),
                    )
                )
                block_idx += 1
            else:
                current_paragraph_lines.append(item)

        # Flush remaining paragraph lines
        if current_paragraph_lines:
            text_blocks.append(
                TextBlock(
                    id=f"block_{block_idx:02d}",
                    type="paragraph",
                    lines=list(current_paragraph_lines),
                )
            )

        metadata = ExtractionMetadata(
            detected_topic=detected_topic,
            canvas_dimensions=CanvasDimensions(
                width=canvas_width,
                height=canvas_height,
                unit="px",
            ),
            extra=extra_metadata or {},
        )

        return ExtractionDocument(
            document_id=doc_id,
            metadata=metadata,
            non_text_elements=non_text,
            text_blocks=text_blocks,
        )
