"""Unit tests for Input & Page Splitter: raster images, DNG, and multi-page PDFs."""

import io
from pathlib import Path
import numpy as np
from PIL import Image
import pypdfium2 as pdfium
import pytest

from processing.input import (
    CorruptDocumentError,
    DocumentInputSplitter,
    PdfHandler,
    RasterImageHandler,
    UnsupportedInputFormatError,
)


def create_synthetic_pdf(num_pages: int = 2) -> bytes:
    """Helper to create a small valid multi-page PDF in memory."""
    doc = pdfium.PdfDocument.new()
    for _ in range(num_pages):
        doc.new_page(300, 400)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def test_raster_image_handler_pil_and_numpy():
    handler = RasterImageHandler()

    # 1. PIL Image
    pil_img = Image.new("RGB", (200, 150), color="white")
    assert handler.can_handle(pil_img) is True

    pages = list(handler.extract_pages(pil_img))
    assert len(pages) == 1
    page = pages[0]
    assert page.page_number == 1
    assert page.total_pages == 1
    assert page.width == 200
    assert page.height == 150
    assert page.image_bgr.shape == (150, 200, 3)

    # 2. NumPy array
    arr = np.zeros((100, 120, 3), dtype=np.uint8)
    assert handler.can_handle(arr) is True
    pages_arr = list(handler.extract_pages(arr))
    assert len(pages_arr) == 1
    assert pages_arr[0].width == 120
    assert pages_arr[0].height == 100


def test_raster_image_handler_files(tmp_path: Path):
    handler = RasterImageHandler()

    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (160, 180), color="blue")
    img.save(img_path)

    assert handler.can_handle(img_path) is True
    pages = list(handler.extract_pages(img_path))
    assert len(pages) == 1
    assert pages[0].width == 160
    assert pages[0].height == 180
    assert pages[0].source_file == str(img_path.resolve())


def test_pdf_handler_multipage():
    handler = PdfHandler()
    pdf_bytes = create_synthetic_pdf(num_pages=3)

    assert handler.can_handle(pdf_bytes) is True

    pages = list(handler.extract_pages(pdf_bytes, dpi=144))
    assert len(pages) == 3

    for idx, page in enumerate(pages, start=1):
        assert page.page_number == idx
        assert page.total_pages == 3
        assert page.media_type == "application/pdf"
        assert page.dpi == 144
        assert page.width > 0
        assert page.height > 0
        assert page.image_bgr is not None


def test_document_input_splitter_auto_detection():
    splitter = DocumentInputSplitter()

    # 1. Image source
    pil_img = Image.new("RGB", (50, 50), color="red")
    pages_img = list(splitter.split(pil_img))
    assert len(pages_img) == 1
    assert pages_img[0].page_number == 1

    # 2. PDF source
    pdf_bytes = create_synthetic_pdf(num_pages=2)
    pages_pdf = list(splitter.split(pdf_bytes))
    assert len(pages_pdf) == 2
    assert pages_pdf[0].page_number == 1
    assert pages_pdf[1].page_number == 2

    # 3. Batch list source
    batch = [
        Image.new("RGB", (40, 40), color="green"),
        Image.new("RGB", (60, 60), color="yellow"),
    ]
    pages_batch = list(splitter.split(batch))
    assert len(pages_batch) == 2
    assert pages_batch[0].page_number == 1
    assert pages_batch[1].page_number == 2


def test_unsupported_input_format():
    splitter = DocumentInputSplitter()
    with pytest.raises(UnsupportedInputFormatError):
        list(splitter.split(12345))  # invalid integer type
