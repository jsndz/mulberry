"""Unit tests for HCD-HTR extract schemas, polygon geometry, and canonical conversion."""

import pytest
from processing.extract.schemas import (
    CanvasDimensions,
    ExtractionDocument,
    ExtractionMetadata,
    LineItem,
    NonTextElement,
    Polygon,
    TextBlock,
)
from processing.extract.config import ExtractionConfig, HardwareTier


def test_polygon_creation_and_bounds():
    pts = [(10.0, 20.0), (100.0, 25.0), (95.0, 80.0), (12.0, 75.0)]
    poly = Polygon(points=pts)
    assert len(poly.points) == 4
    bbox = poly.to_bbox()
    assert bbox == [10.0, 20.0, 100.0, 80.0]
    assert poly.center_of_mass == ((10.0 + 100.0 + 95.0 + 12.0) / 4.0, (20.0 + 25.0 + 80.0 + 75.0) / 4.0)

    # from_bbox
    rect_poly = Polygon.from_bbox(5.0, 15.0, 50.0, 60.0)
    assert rect_poly.to_bbox() == [5.0, 15.0, 50.0, 60.0]
    assert rect_poly.to_list() == [[5.0, 15.0], [50.0, 15.0], [50.0, 60.0], [5.0, 60.0]]


def test_polygon_validation_errors():
    with pytest.raises(ValueError):
        Polygon(points=[(0, 0), (1, 1)])  # not 4 points

    with pytest.raises(ValueError):
        Polygon(points=[(0, 0, 0), (1, 1, 1), (2, 2, 2), (3, 3, 3)])  # 3D points


def test_extraction_document_schema_serialization():
    doc_json = {
        "document_id": "doc_dist_sys_001",
        "metadata": {
            "detected_topic": "Distributed System Engineering",
            "canvas_dimensions": {
                "width": 3072,
                "height": 4096,
                "unit": "px",
            },
        },
        "non_text_elements": [
            {
                "id": "meta_box_01",
                "type": "preprinted_header",
                "polygon": [[2210, 80], [2850, 92], [2845, 230], [2205, 218]],
                "metadata": {"brand": "YOUVA", "fields": ["Date", "Page No", "Days"]},
            }
        ],
        "text_blocks": [
            {
                "id": "block_01",
                "type": "heading",
                "level": 1,
                "content": "Distributed System Engineering",
                "polygon": [[520, 140], [1820, 155], [1815, 240], [515, 225]],
            },
            {
                "id": "block_02",
                "type": "heading",
                "level": 2,
                "content": "1. CAP Theory:",
                "polygon": [[240, 280], [890, 288], [885, 360], [235, 352]],
            },
            {
                "id": "block_03",
                "type": "paragraph",
                "lines": [
                    {
                        "line_id": "line_03_01",
                        "content": "Every read receives most recent write or error.",
                        "polygon": [[320, 840], [2140, 855], [2135, 925], [315, 910]],
                    },
                    {
                        "line_id": "line_03_02",
                        "content": "Meaning any system when performed to ask to read",
                        "polygon": [[340, 930], [2160, 942], [2155, 1010], [335, 998]],
                    },
                ],
            },
        ],
    }

    doc = ExtractionDocument.model_validate(doc_json)
    assert doc.document_id == "doc_dist_sys_001"
    assert len(doc.non_text_elements) == 1
    assert len(doc.text_blocks) == 3
    assert doc.text_blocks[0].content == "Distributed System Engineering"
    assert len(doc.text_blocks[2].lines) == 2

    # Test conversion to Mulberry Canonical Document
    canonical = doc.to_canonical_document()
    assert canonical.id == "doc_dist_sys_001"
    assert len(canonical.pages) == 1
    page = canonical.pages[0]
    assert page.width == 3072.0
    assert page.height == 4096.0
    # 1 non-text diagram + 2 headings + 2 paragraph lines = 5 elements
    assert len(page.elements) == 5


def test_extraction_config_tiers():
    cfg = ExtractionConfig(tier=HardwareTier.TIER_2_BALANCED)
    assert cfg.tier == HardwareTier.TIER_2_BALANCED
    assert cfg.pad_y == 6
    assert cfg.pad_x == 12
    assert cfg.scout_ratio == 0.25
