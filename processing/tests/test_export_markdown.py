"""Unit tests for MarkdownExporter."""

import pytest
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.canonical.common import BoundingBox, CoordinateUnit
from processing.canonical.text import TextElement, TextKind
from processing.canonical.element import TableElement, EquationElement
from processing.canonical.diagram import DiagramElement, DiagramCategory
from processing.exporters.markdown import MarkdownExporter
from processing.exporters.options import MarkdownExportOptions


@pytest.fixture
def sample_document() -> Document:
    return Document(
        id="doc_test_001",
        metadata=DocumentMetadata(
            title="Lecture Notes: Algorithms",
            author="Ada Lovelace",
            source_file="notes.pdf",
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
                        content="Divide and Conquer",
                        position=BoundingBox(x=0, y=0, width=500, height=50),
                    ),
                    TextElement(
                        id="t2",
                        kind=TextKind.PARAGRAPH,
                        content="Merge Sort is an efficient sorting algorithm with O(n log n) runtime.",
                        position=BoundingBox(x=0, y=60, width=500, height=40),
                    ),
                    TextElement(
                        id="t3",
                        kind=TextKind.BULLET,
                        list_level=1,
                        content="Divide array into two halves",
                        position=BoundingBox(x=0, y=110, width=500, height=25),
                    ),
                    TextElement(
                        id="t4",
                        kind=TextKind.BULLET,
                        list_level=2,
                        content="Base case: single element is sorted",
                        position=BoundingBox(x=20, y=140, width=480, height=25),
                    ),
                    TextElement(
                        id="t5",
                        kind=TextKind.NUMBERED_LIST,
                        list_level=1,
                        list_index=1,
                        content="Step 1: Divide",
                        position=BoundingBox(x=0, y=170, width=500, height=25),
                    ),
                    TextElement(
                        id="t6",
                        kind=TextKind.NUMBERED_LIST,
                        list_level=1,
                        list_index=2,
                        content="Step 2: Conquer recursively",
                        position=BoundingBox(x=0, y=200, width=500, height=25),
                    ),
                    EquationElement(
                        id="eq1",
                        latex="T(n) = 2T(n/2) + O(n)",
                        display_mode=True,
                        position=BoundingBox(x=0, y=230, width=500, height=30),
                    ),
                    TableElement(
                        id="tbl1",
                        headers=["Algorithm", "Time Complexity", "Space Complexity"],
                        rows=[
                            ["Merge Sort", "O(n log n)", "O(n)"],
                            ["Quick Sort", "O(n log n)", "O(log n)"],
                        ],
                        caption="Sorting Performance",
                        position=BoundingBox(x=0, y=270, width=500, height=100),
                    ),
                    DiagramElement(
                        id="diag1",
                        category=DiagramCategory.STRUCTURED,
                        position=BoundingBox(x=0, y=380, width=500, height=200),
                    ),
                ],
            ),
            Page(
                page_number=2,
                width=1000.0,
                height=1400.0,
                elements=[
                    TextElement(
                        id="t7",
                        kind=TextKind.HEADING,
                        heading_level=2,
                        content="Conclusion",
                        position=BoundingBox(x=0, y=0, width=500, height=40),
                    ),
                    TextElement(
                        id="t8",
                        kind=TextKind.PARAGRAPH,
                        content="Merge Sort guarantees stable sorting.",
                        position=BoundingBox(x=0, y=50, width=500, height=30),
                    ),
                ],
            ),
        ],
    )


def test_markdown_export_default(sample_document: Document):
    exporter = MarkdownExporter()
    md = exporter.export(sample_document)

    # Frontmatter
    assert "Lecture Notes: Algorithms" in md
    assert "Ada Lovelace" in md

    # Headings
    assert "# Divide and Conquer" in md
    assert "## Conclusion" in md

    # Paragraphs & Lists
    assert "Merge Sort is an efficient sorting algorithm" in md
    assert "* Divide array into two halves" in md
    assert "  * Base case: single element is sorted" in md
    assert "1. Step 1: Divide" in md
    assert "2. Step 2: Conquer recursively" in md

    # Equation
    assert "$$\nT(n) = 2T(n/2) + O(n)\n$$" in md

    # Table
    assert "| Algorithm | Time Complexity | Space Complexity |" in md
    assert "| Merge Sort | O(n log n) | O(n) |" in md
    assert "*Table: Sorting Performance*" in md

    # Diagram is ignored
    assert "diag1" not in md

    # Page break delimiter between page 1 and page 2
    assert "---" in md


def test_markdown_export_options(sample_document: Document, tmp_path):
    exporter = MarkdownExporter()
    out_file = tmp_path / "exported.md"

    opts = MarkdownExportOptions(
        include_frontmatter=False,
        annotate_skipped_diagrams=True,
        include_page_numbers=True,
        page_break_marker="\n\n<!-- PB -->\n\n",
    )

    result = exporter.export(sample_document, output_path=out_file, options=opts)

    assert "author: Ada Lovelace" not in result
    assert "<!-- Page 1 -->" in result
    assert "<!-- Page 2 -->" in result
    assert "<!-- diagram: diag1 -->" in result
    assert "<!-- PB -->" in result

    # File on disk
    assert out_file.exists()
    assert out_file.read_text(encoding="utf-8") == result
