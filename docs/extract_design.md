# Hierarchical Context-Driven Handwriting Extraction Architecture (HCD-HTR)

This production architecture implements a decoupled, 4-stage pipeline: **Document Ingestion & Dewarping**, **Polygonal Geometry & Layout Detection**, **Dynamic Context Retrieval**, and **Context-Conditioned Line Recognition & Assembly**.

---

## 1. System Topology & Data Flow

```
                                [ Smartphone Capture / Raw Scan ]
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Stage 1: Document Conditioning & Preprocessing│
                        │ - 4-Point Perspective Transform (Dewarping)   │
                        │ - CLAHE Illumination & Contrast Flattening     │
                        └───────────────────────┬───────────────────────┘
                                                │
                 ┌──────────────────────────────┴──────────────────────────────┐
                 ▼                                                             ▼
  ┌──────────────────────────────┐                              ┌──────────────────────────────┐
  │ Stage 2: Geometric Path      │                              │ Stage 3: Semantic Path       │
  │ (Layout & Polygon Detection) │                              │ (Global Context & Glossary)  │
  │                              │                              │                              │
  │ - Surya Layout / DBNet       │                              │ - Scout Pass: Top 25% Image  │
  │ - Isolates Diagram Regions   │                              │ - Infers Subject / Topic     │
  │ - Generates Oriented Line    │                              │ - SQLite Context DB Query:   │
  │   Polygons [(x1,y1)...(x4,y4)│                              │   * Domain Glossary / Terms  │
  │ - Natural Reading Order Sort │                              │   * Author Handwriting Map   │
  └──────────────┬───────────────┘                              └──────────────┬───────────────┘
                 │                                                             │
                 └──────────────────────────────┬──────────────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Stage 4: Line Recognition Engine              │
                        │ - Crop Padded Line Strips                     │
                        │ - Model: Qwen2.5-VL-7B (bfloat16, temp=0.0)   │
                        │ - Prompt conditioned on Domain Glossary       │
                        │ - Emits verbatim transcribed text             │
                        └───────────────────────┬───────────────────────┘
                                                │
                                                ▼
                        ┌───────────────────────────────────────────────┐
                        │ Stage 5: Structural Alignment & Assembly      │
                        │ - Map text strings to Line Polygons           │
                        │ - Bind separate Diagram metadata              │
                        │ - Output strict Production JSON schema        │
                        └───────────────────────────────────────────────┘

```

---

## 2. Detailed Component Specifications

### Stage 1: Document Conditioning & Preprocessing

Raw smartphone captures introduce barrel distortion, perspective skew, and uneven shadows.

1. **Perspective Rectification:**
* Run morphological edge detection on downscaled canvas to find the outer notebook contour.
* Compute the convex hull and identify the 4 principal corners.
* Apply an OpenCV homography transformation (`cv2.warpPerspective`) to project the notebook into a planar, top-down orientation.


2. **Illumination Flattening (CLAHE):**
* Convert image to the LAB color space.
* Apply Contrast Limited Adaptive Histogram Equalization (CLAHE) with `clipLimit=2.0`, `tileGridSize=(8,8)` exclusively to the $L$ (Luminance) channel.
* Merge and convert back to RGB. This balances overhead lighting, eliminates phone shadows, and sharpens ink strokes without thresholding out faint pen strokes.



---

### Stage 2: Geometric Path (Layout & Polygonal Line Detection)

Rather than word-level bounding boxes (which break on cursive ligatures) or axis-aligned boxes (which cross drifting lines), geometry is anchored using **4-point line polygons**.

1. **Diagram & Non-Text Segmentation:**
* **Model:** Surya Layout or YOLO-DocLayNet.
* Detects tables, hand-drawn flowcharts, connector arrows, and pre-printed branding (e.g., notebook headers).
* Masks out non-text visual components into independent graphic nodes to prevent diagram strokes from being parsed as hyphens or noise.


2. **Line Polygon Extraction:**
* **Model:** Surya Text Detection (SegFormer backbone) or PaddleOCR DBNet.
* Produces tight, oriented bounding polygons `[(x1, y1), (x2, y2), (x3, y3), (x4, y4)]` for every text line.
* **Reading-Order Topological Sort:** Calculates the vertical center-of-mass ($\bar{y}$) and horizontal indentation ($\bar{x}$) per polygon to establish the document's true visual hierarchy (Title $\rightarrow$ Headings $\rightarrow$ Body paragraphs $\rightarrow$ Indented bullet points).



---

### Stage 3: Semantic Path (Dynamic Context Engine)

This stage prevents generative token substitution (e.g., converting *"write or error"* into *"write operation"*).

1. **Macro Scout Sweep:**
* A fast visual sweep processes the top 25% of the page to detect primary header anchors (e.g., *"Distributed System Engineering"*, *"CAP Theory"*).


2. **Context Database Architecture (SQLite):**

```sql
CREATE TABLE domain_lexicons (
    topic_id TEXT PRIMARY KEY,
    topic_name TEXT,
    keywords TEXT,       -- JSON array of technical terms
    phrases TEXT         -- JSON array of canonical definitions
);

CREATE TABLE author_profiles (
    user_id TEXT PRIMARY KEY,
    homoglyph_rules TEXT, -- e.g., '{"c_looks_like": "e", "v_looks_like": "r"}'
    writing_quirks TEXT
);

```

3. **Dynamic Context Query:**
* When the scout identifies `"Distributed Systems"`, the database injects the target lexicon into memory:
```python
glossary = [
    "CAP Theory", "Consistency", "Availability", "Partition Tolerance",
    "network partition", "receives", "most recent write", "or error", "node"
]

```





---

### Stage 4: Context-Conditioned Line Recognition

Lines are cropped dynamically from the preprocessed canvas and transcribed in batch or sequence.

1. **Padded Polygonal Crop:**
* Each line strip is cropped with a dynamic margin (top/bottom: +6px, left/right: +12px) to preserve ascending strokes ($b, d, h$) and descending strokes ($g, j, p, y$).


2. **Vision-Language Model Execution:**
* **Model:** `Qwen2.5-VL-7B-Instruct` loaded in `bfloat16` with FlashAttention-2.
* **Inference Strategy:** Greedy decoding (`temperature=0.0`, `do_sample=False`).
* **Prompt Template:**
```text
You are a verbatim OCR transcription engine.
Domain Context: {glossary_string}

Task: Transcribe the text from this image strip exactly as written.
Rules:
- Output ONLY the literal text shown in the image.
- Never summarize, correct spelling, or invent words.
- If handwriting matches a domain term, prioritize the exact domain term over generic phrases.

```





---

### Stage 5: Structural Alignment & Final Deliverable

The text emitted by Stage 4 is bound directly to the spatial coordinates generated in Stage 2. Because bounding coordinates are derived from the Stage 2 polygon detector, **spatial positions are guaranteed to reflect the physical ink layout**.

#### Output Schema

```json
{
  "document_id": "doc_dist_sys_001",
  "metadata": {
    "detected_topic": "Distributed System Engineering",
    "canvas_dimensions": {
      "width": 3072,
      "height": 4096,
      "unit": "px"
    }
  },
  "non_text_elements": [
    {
      "id": "meta_box_01",
      "type": "preprinted_header",
      "polygon": [[2210, 80], [2850, 92], [2845, 230], [2205, 218]],
      "metadata": { "brand": "YOUVA", "fields": ["Date", "Page No", "Days"] }
    }
  ],
  "text_blocks": [
    {
      "id": "block_01",
      "type": "heading",
      "level": 1,
      "content": "Distributed System Engineering",
      "polygon": [[520, 140], [1820, 155], [1815, 240], [515, 225]]
    },
    {
      "id": "block_02",
      "type": "heading",
      "level": 2,
      "content": "1. CAP Theory:",
      "polygon": [[240, 280], [890, 288], [885, 360], [235, 352]]
    },
    {
      "id": "block_03",
      "type": "paragraph",
      "lines": [
        {
          "line_id": "line_03_01",
          "content": "Every read receives most recent write or error.",
          "polygon": [[320, 840], [2140, 855], [2135, 925], [315, 910]]
        },
        {
          "line_id": "line_03_02",
          "content": "Meaning any system when performed to ask to read",
          "polygon": [[340, 930], [2160, 942], [2155, 1010], [335, 998]]
        }
      ]
    }
  ]
}

```

---

## 3. End-to-End Orchestrator (Python)

```python
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from surya.detection import batch_text_detection
from surya.model.detection.segformer import load_model as load_det_model, load_processor as load_det_proc

class HandwritingExtractionPipeline:
    def __init__(self, vlm_model_id: str = "Qwen/Qwen2.5-VL-7B-Instruct"):
        # 1. Geometry Detector (Surya)
        self.det_processor = load_det_proc()
        self.det_model = load_det_model()

        # 2. Recognition VLM (Qwen2.5-VL)
        self.vlm_processor = AutoProcessor.from_pretrained(
            vlm_model_id,
            min_pixels=256 * 28 * 28,
            max_pixels=1024 * 28 * 28
        )
        self.vlm = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            vlm_model_id,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            attn_implementation="flash_attention_2"
        )

    def preprocess_image(self, bgr_img: np.ndarray) -> np.ndarray:
        """Applies CLAHE illumination flattening to equalize shadows."""
        lab = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        balanced_bgr = cv2.cvtColor(cv2.merge((cl, a, b)), cv2.COLOR_LAB2BGR)
        return balanced_bgr

    def extract_line_polygons(self, pil_img: Image.Image) -> list:
        """Extracts reading-order-sorted polygonal line segments."""
        preds = batch_text_detection([pil_img], self.det_model, self.det_processor)
        boxes = preds[0].bboxes
        
        # Sort lines vertically by the top-left y-coordinate
        sorted_boxes = sorted(boxes, key=lambda b: (b[1], b[0]))
        return sorted_boxes

    def transcribe_line(self, crop_pil: Image.Image, domain_glossary: list[str]) -> str:
        """Transcribes a single line strip conditioned on the retrieved glossary."""
        glossary_ctx = ", ".join(domain_glossary)
        prompt = (
            f"Transcribe the text in this handwritten strip verbatim.\n"
            f"Domain Vocabulary: {glossary_ctx}\n"
            f"Output ONLY the text. Never normalize or change words."
        )

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": crop_pil},
                    {"type": "text", "text": prompt}
                ]
            }
        ]

        text = self.vlm_processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.vlm_processor(text=[text], images=[crop_pil], return_tensors="pt").to(self.vlm.device)

        with torch.no_grad():
            output_ids = self.vlm.generate(
                **inputs,
                do_sample=False,
                temperature=0.0,
                max_new_tokens=128
            )

        transcription = self.vlm_processor.batch_decode(
            output_ids[:, inputs.input_ids.shape[1]:],
            skip_special_tokens=True
        )[0].strip()

        return transcription

    def process_document(self, image_path: str, domain_glossary: list[str]) -> dict:
        raw_bgr = cv2.imread(image_path)
        h, w, _ = raw_bgr.shape
        clean_bgr = self.preprocess_image(raw_bgr)
        page_pil = Image.fromarray(cv2.cvtColor(clean_bgr, cv2.COLOR_BGR2RGB))

        # Detect line geometries
        line_boxes = self.extract_line_polygons(page_pil)
        lines_output = []

        for idx, box in enumerate(line_boxes):
            # Convert polygon bounds to bounding box with padding
            xmin, ymin, xmax, ymax = int(box[0]), int(box[1]), int(box[2]), int(box[3])
            pad_y, pad_x = 6, 10
            crop = clean_bgr[max(0, ymin - pad_y):min(h, ymax + pad_y), max(0, xmin - pad_x):min(w, xmax + pad_x)]
            
            if crop.size == 0:
                continue

            crop_pil = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
            transcribed_text = self.transcribe_line(crop_pil, domain_glossary)

            lines_output.append({
                "line_id": f"line_{idx + 1:03d}",
                "content": transcribed_text,
                "bbox": [xmin, ymin, xmax, ymax]
            })

        return {
            "page_dimensions": {"width": w, "height": h},
            "lines": lines_output
        }

```

---

## 4. Failure Mode Mitigations

| Failure Mode | Root Cause | Structural Mitigation in Pipeline |
| --- | --- | --- |
| **Cursive Ligatures Split** | Word detectors divide connected pen strokes. | **Line-level framing:** Segmenting entire lines bypasses intra-word gaps completely. |
| **Generative Word Swaps** | VLM defaults to common conversational patterns (`"write operation"`). | **Domain DB conditioning:** Glossary strings injected directly into the decoding prompt anchor the candidate space. |
| **Coordinate Collapse (`0.0`)** | Pure generative VLMs fail to output reliable coordinates in standard chat mode. | **Deterministic CV Geometry:** Line polygons are calculated natively by the layout detector prior to token generation. |
| **Drifting / Skewed Lines** | Handwriting ascends/descends relative to paper rules. | **Oriented Polygons:** The detector models contours directly rather than fitting horizontal axis-aligned boxes. |



Tier,Target Hardware,Latency / Page,Layout / Detection,Recognition Engine,Context Reconciler
Tier 1: Maximum Accuracy (Recommended),"16 GB – 24 GB VRAM (RTX 3090/4090, A10)",~6–10 sec,Surya Layout + Det,Qwen2.5-VL-7B-Instruct,Context Prompt Injection (Direct)
Tier 2: Balanced / Production Throughput,"8 GB – 12 GB VRAM (RTX 3060/4070, T4)",~3–5 sec,PaddleOCR (DBNet PP-OCRv4),Qwen2.5-VL-3B or TrOCR-Large,Qwen2.5-3B-Instruct (Text-only)
Tier 3: Edge / CPU-Only / Low-Resource,"CPU or 4 GB VRAM (M-series Mac, GTX 1650)",~8–15 sec,PaddleOCR (det_only),TrOCR-base-handwritten (ONNX / INT8),Llama-3.2-1B-Instruct


If Context Prompt Injection is not there use Qwen2.5-3B-Instruct (Text-only)