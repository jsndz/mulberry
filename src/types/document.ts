/**
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
