# Mulberry

Mulberry is a local-first desktop application that converts handwritten notes into digital notes.

The input can be a set of handwritten images (PNG, JPEG, WebP, TIFF, smartphone RAW/DNG) or multi-page PDFs. Mulberry analyzes each page, extracts handwritten text, preserves layout hierarchy, and produces editable digital output (Markdown and searchable PDF).

Mulberry runs locally: there is no requirement for external servers, cloud databases, or subscription APIs.

---

## Quickstart & CLI Commands

All commands can be executed from the `processing/` directory using [`uv`](https://docs.astral.sh/uv/):

```bash
cd processing
uv sync
```

---

### 1. Extract Handwriting & Export Directly to Markdown / PDF (`extract`)

The `extract` command executes the full Hierarchical Context-Driven Handwriting Extraction (HCD-HTR) pipeline on any image or multi-page PDF, and can directly export the output to GitHub-Flavored Markdown or searchable PDF.

#### Convert an Image Directly to Markdown:
```bash
uv run processing extract ../test_data/op.png --export markdown
```
> Automatically extracts the handwriting and creates `../test_data/op.md` with formatted YAML frontmatter, headings, paragraphs, and list items.

#### Specify Custom Output Path:
```bash
uv run processing extract ../test_data/op.png --export markdown --export-out ./notes.md
```

#### Convert an Image Directly to Searchable PDF:
```bash
uv run processing extract ../test_data/op.png --export pdf --export-out ./notes.pdf
```

#### Process Multi-Page PDFs:
```bash
uv run processing extract ../test_data/lecture_notes.pdf --export markdown --export-out ./lecture.md
```
> Streams and processes each page independently at 300 DPI, inserting `\n\n---\n\n` markdown page breaks between pages.

#### Choose Hardware Execution Tier:
```bash
# Tier 1 (Default): Maximum accuracy using Qwen2.5-VL-7B (requires GPU)
uv run processing extract note.png --tier tier_1_max_accuracy --export markdown

# Tier 2: Balanced speed and memory using 3B/TrOCR
uv run processing extract note.png --tier tier_2_balanced --export markdown

# Tier 3: Edge CPU / Lightweight (runs purely on CPU without heavy GPU requirements)
uv run processing extract note.png --tier tier_3_edge_cpu --export markdown
```

#### Additional Flags for `extract`:
- `--export {markdown,md,pdf}`: Target export format.
- `--export-out <path>`: Custom destination path for exported Markdown or PDF.
- `-c, --canonical <path>`: Save the full canonical Mulberry document JSON.
- `-o, --output <path>`: Save HCD-HTR production JSON schema.
- `--dpi <int>`: Rasterization DPI for PDF pages (default: `300`).
- `--device {auto,cpu,cuda}`: Execution device.
- `--db <path>`: Custom SQLite context & lexicon database.
- `--no-dewarp`: Disable 4-point perspective dewarping.
- `--no-clahe`: Disable CLAHE illumination flattening.

---

### 2. Export Canonical Document JSON (`export`)

Converts an already extracted Mulberry Canonical Document JSON into Markdown or PDF, or prints Markdown directly to the terminal stdout.

#### Print Markdown directly to terminal:
```bash
uv run processing export doc.json -f markdown
```

#### Save Markdown to file:
```bash
uv run processing export doc.json -f markdown -o output.md
```

#### Export to Searchable PDF:
```bash
uv run processing export doc.json -f pdf -o output.pdf
```

#### Generate JSON Schema Artifacts:
```bash
# Generates schema.json and example.json
uv run processing export
```

---

### 3. OCR (Optical Character Recognition)
Runs text line detection and recognition (TrOCR or PaddleOCR), generating both annotated images with bounding boxes and bounding box JSON.

```bash
uv run processing ocr ../test_data/op.png -o ocr_annotated.png -j ocr.json
```
- `--recognizer {trocr,paddle}`: `trocr` for handwriting, `paddle` for printed
- `--tiling`: Enable patch-based tiling for high-resolution images
- `--contrast-norm`: Apply CLAHE contrast enhancement for faint pencil/ink
- `--device {auto,cpu,gpu}`

---

### 4. Diagram Detection
Runs the YOLO-based diagram detector to identify diagrams, sketches, and flowchart regions.

```bash
uv run processing diagram ../test_data/op.png -o diag_annotated.png -j diagram.json
```
- `--conf 0.25`: Confidence threshold (default: `0.25`)
- `--device {auto,cpu,cuda}`

---

### 5. Image & RAW Conversion
Converts RAW camera formats (`.dng`, `.cr2`, `.nef`) or standard formats to target image types (`png`, `jpg`, `webp`).

```bash
uv run processing convert ../test_data/1.dng -o ../test_data/1.png -f png
```

---

### 6. Validate Canonical JSON
Validates any generated document JSON file against Mulberry's canonical schema.

```bash
uv run processing validate result_doc.json
```

---

### 7. Run Automated Tests
Runs the complete test suite (109 unit and integration tests across all modules):

```bash
uv run pytest
```
