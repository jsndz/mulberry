"""Integration tests for Input & Page Splitter with HandwritingExtractionPipeline."""

import io
from pathlib import Path
import numpy as np
from PIL import Image
import pypdfium2 as pdfium
import pytest

from processing.extract.config import ExtractionConfig, HardwareTier
from processing.extract.geometry.base import BaseLayoutSegmenter, BaseLineDetector
from processing.extract.pipeline import HandwritingExtractionPipeline
from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.schemas import Polygon


class MockLineDetector(BaseLineDetector):
    def detect_lines(self, image, non_text_mask=None):
        return [
            Polygon.from_bbox(50, 40, 200, 70),   # Heading
            Polygon.from_bbox(40, 90, 250, 120),  # Line
        ]


class MockLayoutSegmenter(BaseLayoutSegmenter):
    def segment(self, image):
        return []


class MockLineRecognizer(BaseLineRecognizer):
    def transcribe_line(self, crop_pil, domain_glossary=None):
        return "Synthetic Transcribed Line Content"


def create_test_pdf(num_pages: int = 2) -> bytes:
    doc = pdfium.PdfDocument.new()
    for _ in range(num_pages):
        doc.new_page(400, 500)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_pipeline_process_multipage_pdf():
    pdf_bytes = create_test_pdf(num_pages=3)

    config = ExtractionConfig(
        tier=HardwareTier.TIER_3_EDGE_CPU,
        enable_dewarp=False,
        enable_clahe=False,
    )
    pipeline = HandwritingExtractionPipeline(
        config=config,
        layout_segmenter=MockLayoutSegmenter(),
        line_detector=MockLineDetector(),
        line_recognizer=MockLineRecognizer(),
    )

    progress_log = []
    def on_progress(cur, total):
        progress_log.append((cur, total))

    doc = pipeline.process_multipage(
        input_source=pdf_bytes,
        progress_callback=on_progress,
        document_id="doc_multipage_test",
    )

    # Verify multi-page Canonical Document
    assert doc.id == "doc_multipage_test"
    assert len(doc.pages) == 3
    assert doc.metadata.extra_metadata["total_pages"] == 3

    # Check progress callback logged 3 pages
    assert progress_log == [(1, 3), (2, 3), (3, 3)]

    # Check each page structure
    for idx, page in enumerate(doc.pages, start=1):
        assert page.page_number == idx
        assert page.source_media is not None
        assert page.source_media.media_type == "application/pdf"
        assert len(page.elements) >= 2


def test_pipeline_process_batch_images():
    img1 = Image.new("RGB", (200, 250), color="white")
    img2 = Image.new("RGB", (220, 270), color="white")

    config = ExtractionConfig(
        tier=HardwareTier.TIER_3_EDGE_CPU,
        enable_dewarp=False,
        enable_clahe=False,
    )
    pipeline = HandwritingExtractionPipeline(
        config=config,
        layout_segmenter=MockLayoutSegmenter(),
        line_detector=MockLineDetector(),
        line_recognizer=MockLineRecognizer(),
    )

    doc = pipeline.process_multipage(
        input_source=[img1, img2],
        document_id="batch_doc_test",
    )

    assert doc.id == "batch_doc_test"
    assert len(doc.pages) == 2
    assert doc.pages[0].page_number == 1
    assert doc.pages[1].page_number == 2
