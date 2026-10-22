# Mulberry Document Processing Pipeline

The `processing` package is the core document intelligence engine for Mulberry. It handles image conversion, OCR, diagram detection, VLM-based handwritten note analysis, and serializing outputs into the Mulberry canonical document model.

---

## Quickstart

Ensure you have [`uv`](https://docs.astral.sh/uv/) installed.

```bash
cd processing
uv sync
```

---

## Testing Each Module with an Image

The unified CLI (`processing.cli`) allows testing individual modules or the entire end-to-end pipeline with an input image.

### 1. Vision-Language Model (`vlm`)
Extracts handwritten text and structure (headings, paragraphs, bullet lists, numbered lists) using `Qwen/Qwen3-VL-4B-Instruct` and outputs canonical Mulberry JSON.

```bash
uv run python -m processing.cli vlm ../test_data/op.png -j result_doc.json
```
- `--device {auto,cpu,cuda}` (default: `auto`, detects NVIDIA GPU and uses CPU offload if needed for 8GB VRAM)
- `-j, --output-json <path>`: Destination path for the canonical Document JSON

*Standalone manual runner:*
```bash
uv run python manual_test_vlm.py ../test_data/op.png -o result_doc.json
```

---

### 2. OCR (`ocr`)
Detects text bounding boxes and runs handwriting/print recognition (TrOCR / PaddleOCR).

```bash
uv run python -m processing.cli ocr ../test_data/op.png -o ocr_annotated.png -j ocr.json
```
- `--recognizer {trocr,paddle}`: `trocr` for handwriting, `paddle` for printed documents
- `--tiling`: High-resolution sliding window tiling
- `--contrast-norm`: CLAHE contrast enhancement for light/faint ink
- `--denoise`: Denoise filter for low-light scans

---

### 3. Diagram Detection (`diagram`)
Detects hand-drawn diagrams, schematics, and flowchart regions using YOLO.

```bash
uv run python -m processing.cli diagram ../test_data/op.png -o diagram_annotated.png -j diagram.json
```
- `--conf <float>`: Confidence threshold (default: `0.25`)
- `--device {auto,cpu,cuda}`: Execution device

---

### 4. Full Pipeline (`pipeline`)
Runs OCR and diagram detection concurrently on an image and merges results into a single canonical `Document` with visual annotations.

```bash
uv run python -m processing.cli pipeline ../test_data/op.png -o pipeline_annotated.png -j pipeline_doc.json
```

---

### 5. RAW & Format Conversion (`convert`)
Converts camera RAW images (`.dng`, `.cr2`, etc.) or standard images into target formats.

```bash
uv run python -m processing.cli convert ../test_data/1.dng -o ../test_data/1.png -f png
```

---

### 6. Validate Document JSON (`validate`)
Validates a JSON file against Mulberry's canonical Pydantic document schema.

```bash
uv run python -m processing.cli validate result_doc.json
```

---

### 7. Export Schema & Samples (`export`)
Regenerates `schema.json` and `example.json` based on the canonical Pydantic definitions.

```bash
uv run python -m processing.cli export
```

---

## Running Unit Tests

Run the full pytest suite (71 tests across all modules):

```bash
uv run pytest
```
