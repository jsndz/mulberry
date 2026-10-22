"""Unit tests for exporter dispatcher."""

import pytest
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.canonical.text import TextElement, TextKind
from processing.canonical.common import BoundingBox
from processing.exporters.dispatcher import export_document, get_exporter
from processing.exporters.markdown import MarkdownExporter
from processing.exporters.pdf import PdfExporter


@pytest.fixture
def minimal_doc() -> Document:
    return Document(
        id="doc_dispatcher_01",
        metadata=DocumentMetadata(title="Test Doc"),
        pages=[
            Page(
                page_number=1,
                width=800,
                height=1000,
                elements=[
                    TextElement(
                        id="t1",
                        kind=TextKind.HEADING,
                        heading_level=1,
                        content="Header One",
                        position=BoundingBox(x=0, y=0, width=400, height=50),
                    ),
                    TextElement(
                        id="t2",
                        kind=TextKind.PARAGRAPH,
                        content="Some body text.",
                        position=BoundingBox(x=0, y=60, width=400, height=30),
                    ),
                ],
            )
        ],
    )


def test_get_exporter():
    assert isinstance(get_exporter("markdown"), MarkdownExporter)
    assert isinstance(get_exporter("md"), MarkdownExporter)
    assert isinstance(get_exporter("pdf"), PdfExporter)
    assert isinstance(get_exporter("PDF"), PdfExporter)

    with pytest.raises(ValueError, match="Unsupported export format"):
        get_exporter("docx")


def test_export_document_markdown(minimal_doc: Document, tmp_path):
    # In-memory
    md_str = export_document(minimal_doc, format="markdown")
    assert isinstance(md_str, str)
    assert "# Header One" in md_str
    assert "Some body text." in md_str

    # File write
    out_file = tmp_path / "out.md"
    res = export_document(minimal_doc, format="md", output_path=out_file)
    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == res


def test_export_document_pdf(minimal_doc: Document, tmp_path):
    # In-memory
    pdf_bytes = export_document(minimal_doc, format="pdf")
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b"%PDF-")

    # File write
    out_pdf = tmp_path / "out.pdf"
    res = export_document(minimal_doc, format="pdf", output_path=out_pdf)
    assert out_pdf.exists()
    assert out_pdf.read_bytes() == res


def test_cli_export_command(minimal_doc: Document, tmp_path):
    import argparse
    import json
    from processing.cli import run_export_document

    doc_json = tmp_path / "doc.json"
    doc_json.write_text(minimal_doc.model_dump_json(), encoding="utf-8")

    out_md = tmp_path / "doc.md"
    args = argparse.Namespace(
        file=doc_json,
        format="markdown",
        output=out_md,
    )
    run_export_document(args)
    assert out_md.exists()
    assert "Header One" in out_md.read_text(encoding="utf-8")

    out_pdf = tmp_path / "doc.pdf"
    args_pdf = argparse.Namespace(
        file=doc_json,
        format="pdf",
        output=out_pdf,
    )
    run_export_document(args_pdf)
    assert out_pdf.exists()
    assert out_pdf.read_bytes().startswith(b"%PDF-")

