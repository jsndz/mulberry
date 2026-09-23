"""Schema export, TypeScript generator, and realistic document sample builder for Canonical JSON model."""

import json
from pathlib import Path
from typing import Dict, Any

from processing.canonical.document import Document, Page, DocumentMetadata
from processing.canonical.common import BoundingBox, Color, CoordinateUnit, SourceMedia
from processing.canonical.text import TextElement, TextKind, TextStyle
from processing.canonical.diagram import (
    DiagramElement,
    DiagramCategory,
    BoxPrimitive,
    CirclePrimitive,
    ArrowPrimitive,
    LabelPrimitive,
    ConnectionPrimitive,
    StructuredDiagramData,
    IllustratedDiagramData,
)


def generate_json_schema() -> Dict[str, Any]:
    """Generate canonical JSON schema for Mulberry Document model."""
    return Document.model_json_schema()


def create_realistic_example() -> Document:
    """Construct a comprehensive realistic Mulberry document containing:
    - Heading
    - Paragraph
    - Bullet list
    - Numbered list
    - Structured diagram (with primitives & connections)
    - Illustrated diagram (with cropped image reference)
    """
    doc = Document(
        id="doc_sample_2026_001",
        version="1.0",
        metadata=DocumentMetadata(
            title="System Architecture & Flow Notes",
            author="Jaison",
            source_file="architecture_notes_page1.pdf",
            generator_version="0.1.0",
            extra_metadata={"ocr_engine": "mulberry-ocr-v1", "language": "en"},
        ),
        pages=[
            Page(
                page_number=1,
                width=1200.0,
                height=1600.0,
                unit=CoordinateUnit.PX,
                source_media=SourceMedia(
                    file_path="architecture_notes_page1.pdf",
                    media_type="application/pdf",
                    original_page_number=1,
                    dpi=300,
                ),
                elements=[
                    TextElement(
                        id="elem_head_1",
                        kind=TextKind.HEADING,
                        heading_level=1,
                        content="Mulberry Processing Pipeline",
                        position=BoundingBox(x=100.0, y=80.0, width=800.0, height=50.0, unit=CoordinateUnit.PX),
                        confidence=0.98,
                        style=TextStyle(
                            font_family="Inter",
                            font_size=28.0,
                            font_weight="bold",
                            color=Color(hex="#1E293B", alpha=1.0),
                        ),
                    ),
                    TextElement(
                        id="elem_para_1",
                        kind=TextKind.PARAGRAPH,
                        content="Mulberry ingests handwritten document scans and converts them into structured digital notes. Below is the active pipeline flow:",
                        position=BoundingBox(x=100.0, y=140.0, width=1000.0, height=40.0, unit=CoordinateUnit.PX),
                        confidence=0.95,
                        style=TextStyle(
                            font_family="Inter",
                            font_size=16.0,
                            italic=False,
                            color=Color(hex="#334155", alpha=1.0),
                        ),
                    ),
                    TextElement(
                        id="elem_bullet_1",
                        kind=TextKind.BULLET,
                        list_level=1,
                        content="Page Splitter & Preprocessing",
                        position=BoundingBox(x=120.0, y=190.0, width=600.0, height=25.0, unit=CoordinateUnit.PX),
                        confidence=0.96,
                    ),
                    TextElement(
                        id="elem_bullet_2",
                        kind=TextKind.BULLET,
                        list_level=1,
                        content="Text OCR & Region Detection",
                        position=BoundingBox(x=120.0, y=220.0, width=600.0, height=25.0, unit=CoordinateUnit.PX),
                        confidence=0.94,
                    ),
                    TextElement(
                        id="elem_bullet_3",
                        kind=TextKind.BULLET,
                        list_level=1,
                        content="Diagram Detection & Vectorization",
                        position=BoundingBox(x=120.0, y=250.0, width=600.0, height=25.0, unit=CoordinateUnit.PX),
                        confidence=0.93,
                    ),
                    DiagramElement(
                        id="elem_diag_struct_1",
                        category=DiagramCategory.STRUCTURED,
                        position=BoundingBox(x=100.0, y=300.0, width=1000.0, height=450.0, unit=CoordinateUnit.PX),
                        confidence=0.92,
                        structured_data=StructuredDiagramData(
                            primitives=[
                                BoxPrimitive(
                                    id="box_input",
                                    position=BoundingBox(x=120.0, y=330.0, width=180.0, height=80.0, unit=CoordinateUnit.PX),
                                    label="Input PDF / Image",
                                    fill_color=Color(hex="#DBEAFE", alpha=1.0),
                                    stroke_color=Color(hex="#2563EB", alpha=1.0),
                                    stroke_width=2.0,
                                    corner_radius=8.0,
                                    confidence=0.97,
                                ),
                                BoxPrimitive(
                                    id="box_ocr",
                                    position=BoundingBox(x=410.0, y=330.0, width=180.0, height=80.0, unit=CoordinateUnit.PX),
                                    label="Layout Analysis & OCR",
                                    fill_color=Color(hex="#E0E7FF", alpha=1.0),
                                    stroke_color=Color(hex="#4F46E5", alpha=1.0),
                                    stroke_width=2.0,
                                    corner_radius=8.0,
                                    confidence=0.95,
                                ),
                                CirclePrimitive(
                                    id="circle_canonical",
                                    position=BoundingBox(x=710.0, y=330.0, width=100.0, height=80.0, unit=CoordinateUnit.PX),
                                    label="Canonical Model",
                                    fill_color=Color(hex="#DCFCE7", alpha=1.0),
                                    stroke_color=Color(hex="#16A34A", alpha=1.0),
                                    stroke_width=2.0,
                                    confidence=0.91,
                                ),
                                ArrowPrimitive(
                                    id="arrow_1",
                                    start_point={"x": 300.0, "y": 370.0},
                                    end_point={"x": 410.0, "y": 370.0},
                                    has_head_at_end=True,
                                    label="Extracts",
                                    stroke_color=Color(hex="#64748B", alpha=1.0),
                                    stroke_width=2.0,
                                    confidence=0.94,
                                ),
                                ArrowPrimitive(
                                    id="arrow_2",
                                    start_point={"x": 590.0, "y": 370.0},
                                    end_point={"x": 710.0, "y": 370.0},
                                    has_head_at_end=True,
                                    label="Serializes",
                                    stroke_color=Color(hex="#64748B", alpha=1.0),
                                    stroke_width=2.0,
                                    confidence=0.93,
                                ),
                                LabelPrimitive(
                                    id="lbl_diag_caption",
                                    text="Figure 1: Automated Document Processing Flow",
                                    position=BoundingBox(x=120.0, y=710.0, width=600.0, height=30.0, unit=CoordinateUnit.PX),
                                    font_size=14.0,
                                    color=Color(hex="#475569", alpha=1.0),
                                    confidence=0.96,
                                ),
                                ConnectionPrimitive(
                                    id="conn_1",
                                    source_node_id="box_input",
                                    target_node_id="box_ocr",
                                    connection_type="arrow",
                                    label="Raw Media",
                                    directional=True,
                                ),
                                ConnectionPrimitive(
                                    id="conn_2",
                                    source_node_id="box_ocr",
                                    target_node_id="circle_canonical",
                                    connection_type="arrow",
                                    label="JSON Data",
                                    directional=True,
                                ),
                            ]
                        ),
                    ),
                    TextElement(
                        id="elem_head_2",
                        kind=TextKind.HEADING,
                        heading_level=2,
                        content="Handwritten Concept Sketch",
                        position=BoundingBox(x=100.0, y=780.0, width=600.0, height=35.0, unit=CoordinateUnit.PX),
                        confidence=0.97,
                        style=TextStyle(
                            font_family="Inter",
                            font_size=22.0,
                            font_weight="bold",
                            color=Color(hex="#1E293B", alpha=1.0),
                        ),
                    ),
                    DiagramElement(
                        id="elem_diag_illust_1",
                        category=DiagramCategory.ILLUSTRATED,
                        position=BoundingBox(x=100.0, y=830.0, width=900.0, height=500.0, unit=CoordinateUnit.PX),
                        confidence=0.89,
                        illustrated_data=IllustratedDiagramData(
                            image_ref="assets/crops/sketch_crop_001.png",
                            mime_type="image/png",
                            width=900.0,
                            height=500.0,
                            caption="Hand-drawn schematic of Mulberry UI mockup.",
                            alt_text="A complex handwritten draft illustrating the dual pane editor and sidebar layout.",
                        ),
                    ),
                    TextElement(
                        id="elem_num_1",
                        kind=TextKind.NUMBERED_LIST,
                        list_level=1,
                        list_index=1,
                        content="Validate canonical JSON structure against schema.",
                        position=BoundingBox(x=100.0, y=1360.0, width=800.0, height=25.0, unit=CoordinateUnit.PX),
                        confidence=0.99,
                    ),
                    TextElement(
                        id="elem_num_2",
                        kind=TextKind.NUMBERED_LIST,
                        list_level=1,
                        list_index=2,
                        content="Render visual nodes in React canvas editor.",
                        position=BoundingBox(x=100.0, y=1390.0, width=800.0, height=25.0, unit=CoordinateUnit.PX),
                        confidence=0.98,
                    ),
                ],
            )
        ],
    )
    return doc
