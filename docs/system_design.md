

## 1. Problem

Handwritten notes are useful but difficult to search, edit, organize, and share.

A typical input might contain:

- Handwritten paragraphs
- Headings
- Bullet points
- Numbered lists
- Mathematical or textual content
- Simple diagrams
- Complex drawings or illustrations
- A mixture of text and diagrams on the same page

Mulberry should convert this into a digital representation while preserving the original structure and spatial relationship as much as reasonably possible.

For example:

```text
Handwritten Page
      |
      v
Page Analysis
      |
      +---- Text ------> OCR
      |
      +---- Diagram ---> Diagram Detection
      |
      v
Canonical JSON
      |
      +----> Markdown
      |
      +----> PDF
      |
      v
Editable / Reviewable UI
```

---

# 2. Goals

## Primary goals

1. Accept handwritten images and PDFs.
2. Treat each image or PDF page as an individual processing page.
3. Extract handwritten text using OCR.
4. Detect diagrams independently from text.
5. Classify diagrams into:
   - Structured diagrams
   - Illustrated/complex diagrams
6. Convert structured diagrams into a digital representation.
7. Preserve complex diagrams as image crops.
8. Preserve text and diagram positioning.
9. Store the processed page in a canonical JSON representation.
10. Allow the user to review and edit the generated content.
11. Generate Markdown.
12. Generate PDF.
13. Run locally on the user's laptop.
14. Keep the processing architecture modular so OCR/vision models can be replaced later.

## Non-goals for the first version

The initial version does not require:

- User accounts
- Cloud storage
- Multi-user collaboration
- Remote processing
- Distributed services
- Cloud databases
- Large-scale infrastructure
- Strict processing-time guarantees
- Strict limits on text size

The architecture should remain extensible enough that these can be added later if required.

---

# 3. Functional Requirements

## FR1 — Input

The application should accept:

- Individual image files
- Multiple images
- PDF files

Each image represents one page.

For a PDF:

```text
PDF
 |
 +-- Page 1
 +-- Page 2
 +-- Page 3
 ...
```

Each page is processed independently.

---

## FR2 — Text Detection

For every page, Mulberry should:

1. Detect handwritten text.
2. Extract the text using OCR.
3. Identify basic structure where possible.

Examples of structure:

- Heading
- Paragraph
- Bullet point
- Numbered list
- Text block

The extracted text should also contain positional information.

---

## FR3 — Diagram Detection

Mulberry should identify regions that appear to be diagrams.

A diagram is first represented by its bounding region:

```text
x
y
width
height
```

The cropped diagram can then be analyzed separately.

---

## FR4 — Diagram Classification

Diagrams are divided into two broad categories.

### Structured diagrams

These are diagrams that can reasonably be represented using digital primitives.

Examples:

- Boxes
- Lines
- Arrows
- Nodes
- Simple shapes
- Flowcharts
- Simple system diagrams
- Simple relationship diagrams

These can be converted into a structured representation.

For example:

```text
Box A -----> Box B
```

can become a structured diagram containing:

```text
Node A
Node B
Arrow A -> B
```

A representation such as Mermaid may be used during export where appropriate.

### Illustrated diagrams

These are diagrams where reconstructing the exact visual structure would be unreliable or unnecessarily complicated.

Examples include:

- Anatomy drawings
- Artistic drawings
- Irregular illustrations
- Detailed sketches
- Complex handwritten figures

These should be preserved as an image crop.

The original image is therefore retained rather than attempting an inaccurate reconstruction.

---

# 4. Complexity / Classification Strategy

Diagram complexity should not be treated as a subjective "simple vs complex" decision.

Instead, the system should determine whether a diagram can be reliably represented using a known set of primitives.

A structured diagram might contain:

```text
Box
Circle
Line
Arrow
Text label
Connector
```

If the vision/diagram parser can confidently identify these elements, the diagram can be represented structurally.

If confidence is low, the safer behavior is:

```text
Diagram -> Preserve original crop
```

This prevents the system from producing an incorrect diagram.

The canonical representation can therefore contain:

```text
type: "structured"
```

or:

```text
type: "illustrated"
```

---

# 5. Position and Layout

Position is an important part of Mulberry.

The application should not only understand:

> What text exists?

It should also understand:

> Where is that text located on the page?

For example:

```text
+-----------------------------------+
|              TITLE                |
|                                   |
| Paragraph 1                       |
|                                   |
| [ Box A ] ---> [ Box B ]          |
|                                   |
| Paragraph 2                       |
+-----------------------------------+
```

The canonical representation should therefore contain positional information.

Typical fields include:

```text
x
y
width
height
```

Coordinates should use a consistent coordinate system.

---

# 6. Canonical JSON

The processing pipeline should end by producing a canonical JSON representation.

This is the central internal representation of Mulberry.

The important design principle is:

```text
Input formats
     |
     v
Processing
     |
     v
Canonical JSON
     |
     +----> Markdown
     |
     +----> PDF
```

The exporters should not need to understand OCR or image-processing details.

They only need to understand the canonical document model.

A simplified example:

```json
{
  "document": {
    "pages": [
      {
        "pageNumber": 1,
        "width": 1200,
        "height": 1600,
        "elements": [
          {
            "type": "text",
            "content": "Introduction",
            "role": "heading",
            "position": {
              "x": 100,
              "y": 80,
              "width": 500,
              "height": 80
            }
          },
          {
            "type": "text",
            "content": "This is a handwritten paragraph.",
            "role": "paragraph",
            "position": {
              "x": 100,
              "y": 200,
              "width": 700,
              "height": 150
            }
          },
          {
            "type": "diagram",
            "diagramType": "structured",
            "position": {
              "x": 100,
              "y": 400,
              "width": 800,
              "height": 500
            },
            "elements": [
              {
                "type": "box",
                "id": "A",
                "x": 100,
                "y": 100,
                "width": 200,
                "height": 100
              },
              {
                "type": "box",
                "id": "B",
                "x": 500,
                "y": 100,
                "width": 200,
                "height": 100
              },
              {
                "type": "arrow",
                "from": "A",
                "to": "B"
              }
            ]
          },
          {
            "type": "diagram",
            "diagramType": "illustrated",
            "position": {
              "x": 100,
              "y": 1000,
              "width": 900,
              "height": 500
            },
            "image": "diagram-crop.png"
          }
        ]
      }
    ]
  }
}
```

This is an illustrative schema, not a final schema.

The exact schema should evolve as implementation begins.

---

# 7. Processing Pipeline

The core processing pipeline is:

```text
Input
  |
  v
Input Parser
  |
  v
Page Splitter
  |
  +-----------------------------+
  |                             |
  v                             v
Text Detection              Diagram Detection
  |                             |
  v                             v
OCR                         Diagram Analysis
  |                             |
  +-------------+---------------+
                |
                v
       Layout / Position Merge
                |
                v
        Canonical JSON
                |
        +-------+-------+
        |               |
        v               v
   Markdown           PDF
```

---

# 8. Page Processing

Every page should be processed independently.

For example:

```text
Input PDF
   |
   +-- Page 1 -> Pipeline -> JSON
   +-- Page 2 -> Pipeline -> JSON
   +-- Page 3 -> Pipeline -> JSON
```

This gives several benefits:

- Easier error handling
- Easier progress reporting
- Easier debugging
- Independent page reprocessing
- Better future parallelization

The final document combines the processed pages.

---

# 9. Text Processing

The text processing pipeline can eventually contain:

```text
Image
  |
  v
Image Preprocessing
  |
  v
Text Detection
  |
  v
OCR
  |
  v
Text Structure Analysis
  |
  v
Text Elements
```

Possible preprocessing steps include:

- Resizing
- Noise reduction
- Contrast adjustment
- Deskewing
- Cropping

The exact preprocessing and OCR implementation should remain replaceable.

---

# 10. Diagram Processing

The diagram pipeline can be:

```text
Page
 |
 v
Diagram Detection
 |
 v
Bounding Box
 |
 v
Crop Diagram
 |
 v
Diagram Classification
 |
 +--------------------+
 |                    |
 v                    v
Structured        Illustrated
 |                    |
 v                    v
Primitive          Preserve
Detection          Image Crop
 |
 v
Structured Diagram
```

Structured diagrams can then be converted to a suitable representation for rendering/export.

Mermaid is one possible output representation, particularly for flowcharts and graph-like diagrams.

It should not be treated as the canonical internal representation because not every structured diagram can necessarily be represented cleanly by Mermaid.

---

# 11. User Interface

The UI should allow the user to:

1. Select or drag-and-drop input files.
2. Start processing.
3. View processing progress.
4. View generated pages.
5. Review extracted text.
6. Edit extracted text.
7. Review detected diagrams.
8. Make corrections where necessary.
9. Export Markdown.
10. Export PDF.

The user remains the final reviewer because OCR and diagram detection can make mistakes.

A simplified UI flow:

```text
Upload
  |
  v
Processing
  |
  v
Review
  |
  +---- Edit Text
  |
  +---- Review Diagrams
  |
  v
Export
  |
  +---- Markdown
  |
  +---- PDF
```

---

# 12. Desktop Architecture

Mulberry is initially a local desktop application.

The proposed stack is:

```text
Tauri
  |
  +-- React + TypeScript
  |
  +-- Native/Desktop Layer
  |
  +-- Processing Engine
```

Tauri provides the desktop application shell and native integration.

React provides the user interface.

The processing engine handles CPU/GPU-heavy work such as:

- Image preprocessing
- OCR
- Diagram detection
- Vision/AI models
- Canonical JSON generation
- Export generation

---

# 13. Why Not Put Everything in React?

React should primarily handle the UI.

OCR and vision workloads can be computationally expensive and may require native or Python-based libraries and ML runtimes.

Keeping processing separate from the UI provides:

- Cleaner separation of concerns
- Better UI responsiveness
- Easier model replacement
- Easier testing
- Easier future migration to a server-based architecture

The processing engine should not depend on React.

---

# 14. Communication Between UI and Processing

The initial application does not need REST, HTTP, gRPC, or microservices.

The application can use Tauri's native command mechanism as the bridge.

Conceptually:

```text
React
  |
  | invoke()
  v
Tauri Command
  |
  v
Processing Engine
  |
  v
Canonical JSON
  |
  v
Tauri
  |
  v
React
```

This keeps the communication local.

The important distinction is:

```text
Separate modules/processes
        !=
Separate network services
```

Mulberry can remain one desktop application while maintaining a clean separation between the UI and processing code.

---

# 15. Proposed Project Structure

A possible structure is:

```text
mulberry/
│
├── src/
│   │
│   ├── ui/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── editor/
│   │   └── state/
│   │
│   ├── tauri/
│   │   ├── commands/
│   │   └── main.rs
│   │
│   └── processing/
│       │
│       ├── pipeline/
│       │
│       ├── page_splitter/
│       │
│       ├── preprocessing/
│       │
│       ├── ocr/
│       │
│       ├── diagram/
│       │   ├── structured/
│       │   └── illustrated/
│       │
│       ├── canonical/
│       │
│       └── exporters/
│           ├── markdown/
│           └── pdf/
│
├── models/
│
├── tests/
│
└── README.md
```

The exact directory layout can change based on the chosen processing language and libraries.

---

# 16. Processing Engine Design

The processing engine should be modular.

Conceptually:

```text
ProcessingEngine
    |
    +-- PageSplitter
    |
    +-- Preprocessor
    |
    +-- OCR
    |
    +-- DiagramDetector
    |
    +-- DiagramClassifier
    |
    +-- LayoutAnalyzer
    |
    +-- CanonicalDocumentBuilder
    |
    +-- MarkdownExporter
    |
    +-- PDFExporter
```

Each component should have a clear responsibility.

For example:

```text
OCR
 |
 +-- receives page/image
 +-- returns text regions
```

It should not directly generate Markdown.

Similarly:

```text
MarkdownExporter
 |
 +-- receives canonical JSON
 +-- generates Markdown
```

It should not perform OCR.

This makes the system easier to replace and test.

---

# 17. Model Abstraction

OCR and AI implementations should be hidden behind interfaces.

Conceptually:

```text
OCRProvider
    |
    +-- LocalOCR
    +-- FutureOCRModel
    +-- FutureCloudOCR
```

Similarly:

```text
DiagramAnalyzer
    |
    +-- StructuredDiagramAnalyzer
    +-- VisionModelAnalyzer
```

This allows Mulberry to change models without rewriting the rest of the application.

---

# 18. Output Generation

The canonical JSON is the source of truth for output generation.

## Markdown

The Markdown exporter converts:

```text
Canonical JSON
      |
      v
Markdown
```

Structured diagrams may be represented using Mermaid where appropriate.

Illustrated diagrams can be referenced as image assets.

Example:

```markdown
# Introduction

This is the extracted handwritten text.

```mermaid
flowchart LR
    A --> B
```

![Diagram](assets/diagram-1.png)
```

The exact Markdown representation will depend on the final document model.

## PDF

The PDF exporter converts the same canonical representation into a PDF while attempting to preserve:

- Text placement
- Diagram placement
- Page structure
- Diagram dimensions
- Relative layout

---

# 19. Error Handling

The system should expect imperfect input.

Examples:

- Blurry handwriting
- Low-resolution images
- Skewed pages
- Poor lighting
- Overlapping text and diagrams
- Incorrect OCR
- Incorrect diagram classification

The system should not silently assume that generated content is correct.

Instead, the UI should expose the generated result for user review.

A low-confidence diagram can safely fall back to:

```text
Original image crop
```

rather than generating an incorrect structured diagram.

---

# 20. Performance Considerations

There is currently no strict processing-time requirement.

However, processing should not block the UI.

The UI should receive progress updates such as:

```text
Processing document...
Page 3 / 12
Detecting diagrams...
Running OCR...
Generating output...
```

Potential future optimizations include:

- Parallel page processing
- Caching
- GPU acceleration
- Incremental processing
- Reprocessing only changed pages

These are optimization opportunities rather than initial requirements.

---

# 21. Main Architectural Decisions

The current design decisions are:

| Area | Decision |
|---|---|
| Application type | Local desktop application |
| Desktop framework | Tauri |
| UI | React + TypeScript |
| Backend/processing | Separate processing layer |
| Communication | Local Tauri commands |
| Network services | Not required initially |
| Database | Not required initially |
| Input | Images and PDFs |
| Processing unit | One page |
| Text extraction | OCR |
| Diagram extraction | Vision/diagram pipeline |
| Diagram types | Structured / Illustrated |
| Internal representation | Canonical JSON |
| Structured diagram output | Mermaid or another suitable renderer |
| Complex diagram output | Original image crop |
| Final outputs | Markdown + PDF |
| User correction | Supported |
| Cloud | Out of scope initially |

---

# 22. Future Evolution

The initial architecture deliberately avoids unnecessary distributed-system complexity.

If Mulberry later becomes a web application, the processing engine can be exposed behind an API:

```text
Current:

Tauri
  |
  +-- Processing Engine


Future:

Web UI
  |
  v
API Server
  |
  v
Processing Engine
```

The canonical JSON model and processing modules can remain largely independent of the UI.

Potential future features include:

- Cloud processing
- User accounts
- Document storage
- Collaborative editing
- Search
- AI-powered summarization
- Better handwriting recognition
- More sophisticated diagram reconstruction
- Multiple export formats
- Synchronization between devices

---

# 23. Development Philosophy

Mulberry should follow a simple principle:

> Build the smallest architecture that cleanly separates presentation, processing, and document representation.

The core boundary is:

```text
UI
 |
 v
Processing
 |
 v
Canonical JSON
 |
 +----> Markdown
 |
 +----> PDF
```

The canonical JSON acts as the contract between processing and output generation.

This allows the OCR model, diagram model, UI, and exporters to evolve independently.

---

# 24. Initial Implementation Order

A practical implementation sequence is:

1. Create Tauri + React application.
2. Implement file upload.
3. Implement image/PDF page splitting.
4. Define the canonical JSON schema.
5. Implement basic OCR.
6. Store OCR results in canonical JSON.
7. Implement basic diagram detection.
8. Add structured/illustrated diagram classification.
9. Preserve diagram bounding boxes and image crops.
10. Build the review/editor UI.
11. Implement Markdown export.
12. Implement PDF export.
13. Add confidence/error handling.
14. Optimize processing performance.
15. Improve diagram reconstruction and OCR accuracy.

The canonical document model should be designed early because it connects almost every major component of the system.
