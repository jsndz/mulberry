Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.Design the canonical JSON/document model for Mulberry.

Context:
Mulberry is a local-first desktop application built with:
- React + TypeScript for the UI
- Tauri/Rust as the desktop/native layer
- Python as the processing engine
- Pydantic for Python data models

Purpose:
Mulberry takes handwritten images or PDFs and converts them into digital notes.

Processing flow:

Input images/PDF
→ page splitter
→ text detection + OCR
→ diagram detection
→ diagram classification
→ layout/position analysis
→ canonical document representation
→ Markdown/PDF exporters
→ UI editor

Requirements:

1. Every image represents one page.
2. Every PDF page is treated as an individual page.
3. A page contains ordered elements.
4. Elements can currently be:
   - Text
   - Diagram
5. Text must support:
   - heading
   - paragraph
   - bullet
   - numbered list
   - extracted content
   - confidence score
   - exact bounding box/position
6. Position must contain:
   - x
   - y
   - width
   - height
7. Diagrams have two categories:
   - structured
   - illustrated
8. Structured diagrams should represent primitives such as:
   - boxes
   - circles
   - lines
   - arrows
   - labels
   - nodes/connections
   Their positions and dimensions must be preserved.
9. Illustrated diagrams represent complex drawings that cannot reliably be reconstructed.
   They should preserve a reference to the original cropped image.
10. The model must preserve enough layout information to reproduce the document reasonably accurately in PDF and display it in the editor.
11. OCR and diagram detection may have confidence scores.
12. The canonical representation must be independent of OCR/AI implementation.
13. Markdown and PDF exporters should consume only the canonical representation.
14. The schema should be extensible for future element types such as tables, equations, images, etc.
15. Avoid putting implementation-specific information into the canonical model.
16. The model should work naturally with Python/Pydantic.
17. Consider how the same model will eventually be consumed by the React frontend.

Design goals:
- Simple
- Strongly typed
- Extensible
- Easy to validate
- Easy to serialize/deserialize
- Suitable for versioning later
- Avoid unnecessary complexity

Please provide:

1. The proposed JSON schema.
2. Python Pydantic models.
3. TypeScript types for the React frontend.
4. One realistic example containing:
   - heading
   - paragraph
   - bullet list
   - structured diagram
   - illustrated diagram
5. Explain the major design decisions.
6. Identify any ambiguities or design decisions that should be resolved before implementation.

Do not implement OCR, diagram detection, exporters, or UI. Focus only on designing the canonical document model.