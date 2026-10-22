"""Unit tests for Stage 5 Assembly and Canonical Document Export."""

from pathlib import Path
import pytest
from processing.extract.assembly import StructuralAligner, export_to_canonical, export_to_json
from processing.extract.schemas import NonTextElement, Polygon


def test_structural_aligner_headings_and_paragraphs(tmp_path: Path):
    aligner = StructuralAligner()

    polygons = [
        Polygon.from_bbox(50, 20, 400, 60),    # Title: y~20, h=40
        Polygon.from_bbox(30, 80, 200, 110),   # Section header: "1. CAP Theory:"
        Polygon.from_bbox(40, 130, 500, 155),  # Body line 1
        Polygon.from_bbox(40, 165, 500, 190),  # Body line 2
    ]

    transcriptions = [
        "Distributed System Engineering",
        "1. CAP Theory:",
        "Every read receives most recent write or error.",
        "Meaning any system when performed to ask to read",
    ]

    non_text = [
        NonTextElement(
            id="diag_01",
            type="preprinted_header",
            polygon=Polygon.from_bbox(600, 20, 750, 70).to_list(),
            metadata={"brand": "YOUVA"},
        )
    ]

    doc = aligner.assemble(
        polygons=polygons,
        transcriptions=transcriptions,
        canvas_width=1000,
        canvas_height=1200,
        non_text_elements=non_text,
        detected_topic="Distributed System Engineering",
        document_id="test_doc_001",
    )

    assert doc.document_id == "test_doc_001"
    assert doc.metadata.detected_topic == "Distributed System Engineering"
    assert len(doc.non_text_elements) == 1
    assert len(doc.text_blocks) == 3

    # Check block types
    assert doc.text_blocks[0].type == "heading"
    assert doc.text_blocks[0].content == "Distributed System Engineering"
    assert doc.text_blocks[1].type == "heading"
    assert doc.text_blocks[1].content == "1. CAP Theory:"
    assert doc.text_blocks[2].type == "paragraph"
    assert len(doc.text_blocks[2].lines) == 2

    # Check JSON export
    json_path = tmp_path / "out.json"
    export_to_json(doc, json_path)
    assert json_path.exists()

    # Check Canonical Document export
    canonical_doc = export_to_canonical(doc)
    assert canonical_doc.id == "test_doc_001"
    assert len(canonical_doc.pages[0].elements) == 5
