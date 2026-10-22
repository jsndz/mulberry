"""Unit tests for PdfExporter."""

import pypdfium2 as pdfium
import pytest

from processing.canonical.common import BoundingBox
from processing.canonical.diagram import DiagramCategory, DiagramElement
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.canonical.element import EquationElement, TableElement
from processing.canonical.text import TextElement, TextKind
from processing.exporters.options import PdfExportOptions
from processing.exporters.pdf import PdfExporter


@pytest.fixture
def sample_document() -> Document:
    return Document(
        id="doc_test_002",
        metadata=DocumentMetadata(
            title="Computational Geometry Notes",
            author="Carl Friedrich Gauss",
            source_file="gauss_notes.pdf",
        ),
        pages=[
            Page(
                page_number=1,
                width=1000.0,
                height=1400.0,
                elements=[
                    TextElement(
                        id="t1",
                        kind=TextKind.HEADING,
                        heading_level=1,
                        content="Convex Hull Algorithms",
                        position=BoundingBox(x=0, y=0, width=500, height=50),
                    ),
                    TextElement(
                        id="t2",
                        kind=TextKind.PARAGRAPH,
                        content="Graham scan computes the convex hull of n points in O(n log n) time.",
                        position=BoundingBox(x=0, y=60, width=500, height=40),
                    ),
                    TextElement(
                        id="t3",
                        kind=TextKind.BULLET,
                        list_level=1,
                        content="Find point with lowest y-coordinate",
                        position=BoundingBox(x=0, y=110, width=500, height=25),
                    ),
                    TextElement(
                        id="t4",
                        kind=TextKind.NUMBERED_LIST,
                        list_level=1,
                        list_index=1,
                        content="Sort points by polar angle",
                        position=BoundingBox(x=0, y=140, width=500, height=25),
                    ),
                    EquationElement(
                        id="eq1",
                        latex="ccw(p1, p2, p3) = (x2 - x1)(y3 - y1) - (y2 - y1)(x3 - x1)",
                        display_mode=True,
                        position=BoundingBox(x=0, y=170, width=500, height=30),
                    ),
                    TableElement(
                        id="tbl1",
                        headers=["Algorithm", "Time", "Dimensions"],
                        rows=[
                            ["Graham Scan", "O(n log n)", "2D"],
                            ["Quickhull", "O(n log n)", "2D / 3D"],
                        ],
                        caption="Convex Hull Benchmarks",
                        position=BoundingBox(x=0, y=210, width=500, height=80),
                    ),
                    DiagramElement(
                        id="diag1",
                        category=DiagramCategory.STRUCTURED,
                        position=BoundingBox(x=0, y=300, width=500, height=200),
                    ),
                ],
            ),
            Page(
                page_number=2,
                width=1000.0,
                height=1400.0,
                elements=[
                    TextElement(
                        id="t5",
                        kind=TextKind.HEADING,
                        heading_level=2,
                        content="Applications",
                        position=BoundingBox(x=0, y=0, width=500, height=40),
                    ),
                    TextElement(
                        id="t6",
                        kind=TextKind.PARAGRAPH,
                        content="Used in collision detection and image processing.",
                        position=BoundingBox(x=0, y=50, width=500, height=30),
                    ),
                ],
            ),
        ],
    )


def test_pdf_export_default(sample_document: Document):
    exporter = PdfExporter()
    pdf_bytes = exporter.export(sample_document)

    # Valid PDF magic header
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")

    # Inspect rendered PDF with pdfium
    pdf_doc = pdfium.PdfDocument(pdf_bytes)
    assert len(pdf_doc) == 2

    # Verify searchable text on Page 1
    page1_text = pdf_doc[0].get_textpage().get_text_range()
    assert "Convex Hull Algorithms" in page1_text
    assert "Graham scan computes" in page1_text
    assert "Find point with lowest y-coordinate" in page1_text
    assert "Sort points by polar angle" in page1_text
    assert "ccw(p1, p2, p3)" in page1_text
    assert "Convex Hull Benchmarks" in page1_text
    assert "Page 1 of 2" in page1_text

    # Verify searchable text on Page 2
    page2_text = pdf_doc[1].get_textpage().get_text_range()
    assert "Applications" in page2_text
    assert "collision detection" in page2_text
    assert "Page 2 of 2" in page2_text


def test_pdf_export_to_file_and_options(sample_document: Document, tmp_path):
    exporter = PdfExporter()
    out_pdf = tmp_path / "notes_export.pdf"

    opts = PdfExportOptions(
        page_size="LETTER",
        margin_pt=24.0,
        include_page_numbers=False,
    )

    pdf_bytes = exporter.export(sample_document, output_path=out_pdf, options=opts)

    assert out_pdf.exists()
    assert out_pdf.stat().st_size > 0
    assert out_pdf.read_bytes() == pdf_bytes

    pdf_doc = pdfium.PdfDocument(out_pdf)
    assert len(pdf_doc) == 2

    page1_text = pdf_doc[0].get_textpage().get_text_range()
    assert "Convex Hull Algorithms" in page1_text
    # When page numbers disabled, "Page 1 of 2" footer is omitted
    assert "Page 1 of 2" not in page1_text
