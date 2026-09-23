"""Schema export, TypeScript generator, and realistic document sample builder."""

import json
from pathlib import Path
from typing import Dict, Any

from processing.models.document import Document, Page, DocumentMetadata
from processing.models.common import BoundingBox, Color, CoordinateUnit, SourceMedia
from processing.models.text import TextElement, TextKind, TextStyle
from processing.models.diagram import (
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
                    # 1. Heading
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
                    # 2. Paragraph
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
                    # 3. Bullet list items
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
                    # 4. Structured Diagram (Flowchart / Architecture)
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
                    # 5. Heading for Illustrated Section
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
                    # 6. Illustrated Diagram
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
                    # 7. Numbered List Section
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


def generate_typescript_definitions() -> str:
    """Generate matching TypeScript type definitions for frontend React applications."""
    return """/**
 * Mulberry Canonical Document Model TypeScript Definitions
 * Auto-aligned with Pydantic V2 Document Schema
 */

export type CoordinateUnit = 'px' | 'pt' | 'normalized' | 'mm' | 'in';

export interface Point {
  x: number;
  y: number;
}

export interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
  unit?: CoordinateUnit;
}

export interface Color {
  hex: string;
  alpha?: number;
}

export interface SourceMedia {
  file_path?: string;
  media_type: string;
  original_page_number?: number;
  dpi?: number;
}

// --- Text Element ---

export type TextKind = 'heading' | 'paragraph' | 'bullet' | 'numbered_list';

export interface TextStyle {
  font_family?: string;
  font_size?: number;
  font_weight?: string;
  italic?: boolean;
  color?: Color;
}

export interface TextElement {
  id: string;
  type: 'text';
  kind: TextKind;
  content: string;
  position: BoundingBox;
  confidence?: number;
  heading_level?: number;
  list_level?: number;
  list_index?: number;
  style?: TextStyle;
  metadata?: Record<string, unknown>;
}

// --- Diagram Primitives ---

export type DiagramPrimitiveType = 'box' | 'circle' | 'line' | 'arrow' | 'label' | 'connection';

export interface BasePrimitive {
  id: string;
  confidence?: number;
}

export interface BoxPrimitive extends BasePrimitive {
  primitive_type: 'box';
  position: BoundingBox;
  label?: string;
  fill_color?: Color;
  stroke_color?: Color;
  stroke_width?: number;
  corner_radius?: number;
}

export interface CirclePrimitive extends BasePrimitive {
  primitive_type: 'circle';
  position: BoundingBox;
  label?: string;
  fill_color?: Color;
  stroke_color?: Color;
  stroke_width?: number;
}

export interface LinePrimitive extends BasePrimitive {
  primitive_type: 'line';
  points: Point[];
  stroke_color?: Color;
  stroke_width?: number;
  style?: string;
}

export interface ArrowPrimitive extends BasePrimitive {
  primitive_type: 'arrow';
  start_point: Point;
  end_point: Point;
  has_head_at_start?: boolean;
  has_head_at_end?: boolean;
  label?: string;
  stroke_color?: Color;
  stroke_width?: number;
}

export interface LabelPrimitive extends BasePrimitive {
  primitive_type: 'label';
  text: string;
  position: BoundingBox;
  font_size?: number;
  color?: Color;
}

export interface ConnectionPrimitive extends BasePrimitive {
  primitive_type: 'connection';
  source_node_id: string;
  target_node_id: string;
  connection_type?: string;
  label?: string;
  directional?: boolean;
}

export type DiagramPrimitive =
  | BoxPrimitive
  | CirclePrimitive
  | LinePrimitive
  | ArrowPrimitive
  | LabelPrimitive
  | ConnectionPrimitive;

// --- Diagram Element ---

export type DiagramCategory = 'structured' | 'illustrated';

export interface StructuredDiagramData {
  primitives: DiagramPrimitive[];
}

export interface IllustratedDiagramData {
  image_ref: string;
  mime_type?: string;
  width?: number;
  height?: number;
  caption?: string;
  alt_text?: string;
}

export interface DiagramElement {
  id: string;
  type: 'diagram';
  category: DiagramCategory;
  position: BoundingBox;
  confidence?: number;
  structured_data?: StructuredDiagramData;
  illustrated_data?: IllustratedDiagramData;
  metadata?: Record<string, unknown>;
}

// --- Future Extensibility Stubs ---

export interface ImageElement {
  id: string;
  type: 'image';
  position: BoundingBox;
  confidence?: number;
  image_ref: string;
  caption?: string;
  metadata?: Record<string, unknown>;
}

export interface TableElement {
  id: string;
  type: 'table';
  position: BoundingBox;
  confidence?: number;
  headers: string[];
  rows: string[][];
  caption?: string;
  metadata?: Record<string, unknown>;
}

export interface EquationElement {
  id: string;
  type: 'equation';
  position: BoundingBox;
  confidence?: number;
  latex: string;
  display_mode: boolean;
  metadata?: Record<string, unknown>;
}

// Discriminated Polymorphic Document Element Union
export type DocumentElement =
  | TextElement
  | DiagramElement
  | ImageElement
  | TableElement
  | EquationElement;

// --- Page & Document Root ---

export interface Page {
  page_number: number;
  width: number;
  height: number;
  unit: CoordinateUnit;
  source_media?: SourceMedia;
  elements: DocumentElement[];
}

export interface DocumentMetadata {
  title?: string;
  author?: string;
  created_at?: string;
  updated_at?: string;
  source_file?: string;
  generator_version: string;
  extra_metadata?: Record<string, unknown>;
}

export interface Document {
  version: string;
  id: string;
  metadata: DocumentMetadata;
  pages: Page[];
}
"""
