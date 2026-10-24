# Mulberry Document Processing Pipeline

The `processing` package is the core document intelligence engine for Mulberry. It handles multi-format ingestion (PNG, JPEG, WebP, TIFF, BMP, RAW/DNG, and multi-page PDFs), HCD-HTR handwriting extraction, diagram detection, OCR, and document exporters (Markdown and Searchable PDF).

---

## Quickstart

Ensure you have [`uv`](https://docs.astral.sh/uv/) installed.

```bash
cd processing
uv sync
```

---

## CLI Commands

The unified CLI tool (`processing`) allows executing individual stages or running the complete extraction and export pipeline end-to-end.

---

### 1. Handwriting Extraction & Export (`extract`)

Executes the 5-stage Hierarchical Context-Driven Handwriting Extraction (HCD-HTR) pipeline on any image or multi-page PDF, with direct export to Markdown or PDF.

#### Extract and Export Image to Markdown:
```bash
uv run processing extract ../test_data/op.png --export markdown
```
> Extracts handwriting and saves `../test_data/op.md` with YAML frontmatter, headings, paragraphs, and lists.

#### Custom Markdown Destination:
```bash
uv run processing extract ../test_data/op.png --export markdown --export-out ./notes.md
```

#### Extract and Export Image to Searchable PDF:
```bash
uv run processing extract ../test_data/op.png --export pdf --export-out ./notes.pdf
```

#### Multi-Page PDF Extraction:
```bash
uv run processing extract ../test_data/lecture_notes.pdf --export markdown --export-out ./lecture.md
```
> Streams and processes each page independently at 300 DPI, inserting `\n\n---\n\n` markdown page breaks between pages.

#### Hardware Execution Tiers:
```bash
# Tier 1 (Default): Maximum accuracy using Qwen2.5-VL-7B (requires GPU)
uv run processing extract note.png --tier tier_1_max_accuracy --export markdown

# Tier 2: Balanced speed and memory using 3B/TrOCR
uv run processing extract note.png --tier tier_2_balanced --export markdown

# Tier 3: Edge CPU / Lightweight (runs on CPU without heavy GPU requirements)
uv run processing extract note.png --tier tier_3_edge_cpu --export markdown
```

#### Options for `extract`:
- `--export {markdown,md,pdf}`: Target export format.
- `--export-out <path>`: Custom destination path for exported file.
- `-c, --canonical <path>`: Path to save Mulberry Canonical Document JSON.
- `-o, --output <path>`: Path to save HCD-HTR production JSON schema.
- `--dpi <int>`: PDF rasterization resolution (default: `300`).
- `--device {auto,cpu,cuda}`: Execution device.
- `--db <path>`: Custom SQLite context & lexicon database path.
- `--no-dewarp`: Disable 4-point perspective dewarping.
- `--no-clahe`: Disable CLAHE illumination flattening.

---

### 2. Document Exporters (`export`)

Converts existing canonical Document JSON files to Markdown or PDF, or prints Markdown directly to stdout.

#### Print Markdown directly to terminal:
```bash
uv run processing export doc.json -f markdown
```

#### Export to Markdown file:
```bash
uv run processing export doc.json -f markdown -o output.md
```

#### Export to Searchable PDF:
```bash
uv run processing export doc.json -f pdf -o output.pdf
```

#### Generate JSON Schema Artifacts:
```bash
# Generates schema.json and example.json in processing/
uv run processing export
```

---

### 3. Text OCR (`ocr`)
Detects text bounding boxes and runs handwriting/print recognition (TrOCR / PaddleOCR).

```bash
uv run processing ocr ../test_data/op.png -o ocr_annotated.png -j ocr.json
```
- `--recognizer {trocr,paddle}`: `trocr` for handwriting, `paddle` for printed documents
- `--tiling`: High-resolution sliding window tiling
- `--contrast-norm`: CLAHE contrast enhancement for faint pencil/ink
- `--denoise`: Denoise filter for low-light scans

---

### 4. Diagram Detection (`diagram`)
Detects hand-drawn diagrams, schematics, and flowchart regions using YOLO.

```bash
uv run processing diagram ../test_data/op.png -o diagram_annotated.png -j diagram.json
```
- `--conf <float>`: Confidence threshold (default: `0.25`)
- `--device {auto,cpu,cuda}`: Execution device

---

### 5. RAW & Format Conversion (`convert`)
Converts camera RAW images (`.dng`, `.cr2`, etc.) or standard images into target formats.

```bash
uv run processing convert ../test_data/1.dng -o ../test_data/1.png -f png
```

---

### 6. Validate Document JSON (`validate`)
Validates a JSON file against Mulberry's canonical Pydantic document schema.

```bash
uv run processing validate result_doc.json
```

---

## Running Automated Tests

Run the full pytest suite (109 tests across all modules):

```bash
uv run pytest
```
