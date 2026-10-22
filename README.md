# Mulberry

Mulberry is a local-first desktop application that converts handwritten notes into digital notes.

The input can be a set of handwritten images or a PDF containing handwritten pages. Mulberry analyzes each page, extracts handwritten text, detects diagrams, preserves their layout, and produces editable digital output.

Mulberry is designed as a local application initially. There is no requirement for a backend server, database, authentication system, or cloud infrastructure in the first version.

---

## Testing Each Module with an Image

The `processing` engine includes a unified CLI to test each processing module individually or together using an input image.

All commands are executed from the `processing/` directory using [`uv`](https://docs.astral.sh/uv/):

```bash
cd processing
```

### 1. Vision-Language Model (  )
Extracts handwritten text, structure (headings, paragraphs, bullet & numbered lists), and outputs a canonical Mulberry document JSON.

```bash
uv run python -m processing.cli vlm ../test_data/op.png -j result_doc.json
```
> **Options:**
> - `--device {auto,cpu,cuda}` (default: `auto`, automatically uses GPU if available with CPU offload)
> - `-j, --output-json <path>`: Path to save the resulting canonical JSON.

*Alternatively, use the standalone manual tester:*
```bash
uv run python manual_test_vlm.py ../test_data/op.png -o result.json
```

---

### 2. OCR (Optical Character Recognition)
Runs text region detection and handwriting recognition (TrOCR or PaddleOCR), generating both annotated images with bounding boxes and bounding box JSON.

```bash
uv run python -m processing.cli ocr ../test_data/op.png -o ocr_annotated.png -j ocr.json
```
> **Options:**
> - `--recognizer {trocr,paddle}` (default: `trocr` for handwriting, `paddle` for printed)
> - `--tiling`: Enable patch-based tiling for high-resolution images
> - `--contrast-norm`: Apply CLAHE contrast enhancement for faint pencil/ink
> - `--device {auto,cpu,gpu}`

---

### 3. Diagram Detection
Runs the YOLO-based diagram detector to identify diagrams, sketches, and flowchart regions.

```bash
uv run python -m processing.cli diagram ../test_data/op.png -o diag_annotated.png -j diagram.json
```
> **Options:**
> - `--conf 0.25`: Confidence threshold (default: `0.25`)
> - `--device {auto,cpu,cuda}`

---

### 4. Full Pipeline (OCR + Diagram → Canonical Document)
Combines OCR text extraction with diagram detection to build a full canonical Mulberry `Document` containing text elements and diagram elements.

```bash
uv run python -m processing.cli pipeline ../test_data/op.png -o pipeline_annotated.png -j pipeline_doc.json
```

---

### 5. Image & RAW Conversion
Converts RAW camera formats (`.dng`, `.cr2`, `.nef`) or standard formats to target image types (`png`, `jpg`, `webp`).

```bash
uv run python -m processing.cli convert ../test_data/1.dng -o ../test_data/1.png -f png
```

---

### 6. Validate Canonical JSON
Validates any generated document JSON file against Mulberry's canonical schema.

```bash
uv run python -m processing.cli validate result_doc.json
```

---

### 7. Run All Automated Tests
Runs the complete test suite (70+ unit tests across all modules):

```bash
uv run pytest
```

