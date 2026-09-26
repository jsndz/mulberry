Act as an expert computer vision engineer. Write a complete,  Python module for a dynamic "Diagram Detection System" that takes an image of handwritten notes as input and outputs the bounding box coordinates [xmin, ymin, xmax, ymax] of any flowcharts, box diagrams, or structured technical sketches found on the page.

The system must dynamically adapt to the underlying hardware execution environment using the following logic:

1. HARDWARE CHECK:
- Check if a CUDA-enabled NVIDIA GPU is available (`torch.cuda.is_available()`).

2. GPU PIPELINE (Highest Accuracy):
- If a GPU is available, initialize a Transformer-based Document Image Analysis model using Hugging Face 'transformers'. 
- Use Microsoft DiT (Document Image Transformer) over LayoutLMv3, as DiT handles raw visual/handwritten layouts natively without requiring an initial text OCR extraction step.
- Target the "microsoft/dit-base-finetuned-publaynet" weights.
- Parse the output objects and extract bounding box coordinates for regions classified as "figure" or "table" (which map to diagrams/flowcharts).

3. CPU PIPELINE (Efficient Fallback):
- If only a CPU is available, gracefully fall back to the lightweight Ultralytics YOLO framework (`yolov8n.pt` or `yolov11n.pt`).
- Run inference using a configurable confidence threshold (default to 0.25).
- Extract the raw bounding boxes for the detected objects.

4. SYSTEM INTERFACE & CLEAN OUTPUT:
- Structure the script with a factory function (e.g., `get_detector()`) that returns a unified layout engine interface.
- The prediction function must return a clean Python list of dictionaries, structured exactly like this:
  [{"box": [xmin, ymin, xmax, ymax], "confidence": float}]
- Include a separate utility function using OpenCV (`cv2`) that takes the original image and the coordinate list, draws solid bounding boxes around the detected diagram regions, and saves the verified visual output to a new image file.
- Ensure all required library imports (torch, transformers, ultralytics, cv2, PIL) are cleanly organized at the top.
