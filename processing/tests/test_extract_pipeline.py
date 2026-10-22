"""Integration tests for end-to-end HandwritingExtractionPipeline."""

from unittest.mock import MagicMock
import cv2
import numpy as np
from PIL import Image
import pytest

from processing.extract.config import ExtractionConfig, HardwareTier
from processing.extract.geometry.base import BaseLayoutSegmenter, BaseLineDetector
from processing.extract.pipeline import HandwritingExtractionPipeline
from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.schemas import NonTextElement, Polygon


class MockLayoutSegmenter(BaseLayoutSegmenter):
    def segment(self, image):
        return [
            NonTextElement(
                id="preprinted_01",
                type="preprinted_header",
                polygon=Polygon.from_bbox(2200, 80, 2800, 200).to_list(),
                metadata={"brand": "YOUVA"},
            )
        ]


class MockLineDetector(BaseLineDetector):
    def detect_lines(self, image, non_text_mask=None):
        return [
            Polygon.from_bbox(100, 50, 600, 90),     # Heading
            Polygon.from_bbox(80, 150, 700, 185),    # Paragraph line 1
            Polygon.from_bbox(80, 195, 700, 230),    # Paragraph line 2
        ]


class MockLineRecognizer(BaseLineRecognizer):
    def __init__(self):
        self.call_count = 0

    def transcribe_line(self, crop_pil, domain_glossary=None):
        self.call_count += 1
        transcriptions = [
            "Distributed System Engineering",
            "Every read receives most recent write or error.",
            "Meaning any system when performed to ask to read",
        ]
        idx = (self.call_count - 1) % len(transcriptions)
        return transcriptions[idx]


def test_end_to_end_extraction_pipeline():
    # Create synthetic test canvas
    canvas = np.full((600, 800, 3), 255, dtype=np.uint8)
    cv2.line(canvas, (100, 70), (500, 70), (0, 0, 0), 2)

    config = ExtractionConfig(
        tier=HardwareTier.TIER_3_EDGE_CPU,
        enable_dewarp=False,
        enable_clahe=True,
    )

    mock_segmenter = MockLayoutSegmenter()
    mock_detector = MockLineDetector()
    mock_recognizer = MockLineRecognizer()

    pipeline = HandwritingExtractionPipeline(
        config=config,
        layout_segmenter=mock_segmenter,
        line_detector=mock_detector,
        line_recognizer=mock_recognizer,
    )

    doc = pipeline.process_document(
        image_input=canvas,
        manual_glossary=["CAP Theory", "Consistency"],
        document_id="doc_test_123",
    )

    # 1. Verify schema output
    assert doc.document_id == "doc_test_123"
    assert doc.metadata.canvas_dimensions.width == 800
    assert doc.metadata.canvas_dimensions.height == 600
    assert len(doc.non_text_elements) == 1
    assert doc.non_text_elements[0].id == "preprinted_01"
    assert len(doc.text_blocks) == 2

    # Heading block
    assert doc.text_blocks[0].type == "heading"
    assert doc.text_blocks[0].content == "Distributed System Engineering"

    # Paragraph block
    assert doc.text_blocks[1].type == "paragraph"
    assert len(doc.text_blocks[1].lines) == 2
    assert "Every read receives" in doc.text_blocks[1].lines[0].content

    # 2. Verify Canonical Document conversion
    canonical = doc.to_canonical_document()
    assert canonical.id == "doc_test_123"
    assert len(canonical.pages[0].elements) == 4  # 1 non-text + 1 heading + 2 lines
