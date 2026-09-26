"""CLI entry point for Mulberry Processing Tooling."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image

from processing.canonical.exporter import (
    generate_json_schema,
    create_realistic_example,
)
from processing.canonical.document import Document, Page
from processing.canonical.element import TextElement, DiagramElement
from processing.canonical.text import TextKind
from processing.canonical.diagram import DiagramCategory
from processing.canonical.common import BoundingBox, CoordinateUnit
from processing.ocr import OCRService, OCRConfig, DeviceType, OCRRuntime, TextRegion
from processing.diagram import get_detector, draw_diagram_boxes


def export_artifacts(base_dir: Path) -> None:
    """Generate and write schema.json and example.json."""
    processing_dir = base_dir / "processing"
    processing_dir.mkdir(parents=True, exist_ok=True)

    # 1. JSON Schema
    schema = generate_json_schema()
    schema_path = processing_dir / "schema.json"
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"✅ Generated JSON Schema: {schema_path}")

    # 2. Realistic Example JSON
    example_doc = create_realistic_example()
    example_path = processing_dir / "example.json"
    with open(example_path, "w", encoding="utf-8") as f:
        f.write(example_doc.model_dump_json(indent=2))
    print(f"✅ Generated Realistic Example Document: {example_path}")


def draw_label(
    img: np.ndarray,
    text: str,
    xmin: int,
    ymin: int,
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int] = (255, 255, 255),
) -> None:
    """Draw a text label with solid background on OpenCV image."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.45
    thickness = 1
    (t_w, t_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
    label_ymin = max(ymin - t_h - baseline - 4, 0)
    cv2.rectangle(
        img,
        (xmin, label_ymin),
        (xmin + t_w + 6, label_ymin + t_h + baseline + 4),
        bg_color,
        cv2.FILLED,
    )
    cv2.putText(
        img,
        text,
        (xmin + 3, label_ymin + t_h + 2),
        font,
        font_scale,
        text_color,
        thickness,
        cv2.LINE_AA,
    )


def annotate_image(
    image_path: Path,
    output_path: Path,
    text_regions: Optional[List[TextRegion]] = None,
    diagram_detections: Optional[List[Dict[str, Any]]] = None,
) -> Path:
    """Draw OCR and/or Diagram bounding boxes onto the image and save output."""
    img = cv2.imread(str(image_path))
    if img is None:
        pil_img = Image.open(image_path).convert("RGB")
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    # 1. Draw Text Regions (OCR) in Blue (BGR: 255, 128, 0)
    if text_regions:
        for reg in text_regions:
            xmin = int(round(reg.bbox.x))
            ymin = int(round(reg.bbox.y))
            xmax = int(round(reg.bbox.x + reg.bbox.width))
            ymax = int(round(reg.bbox.y + reg.bbox.height))

            cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (255, 128, 0), 2)
            label = f"OCR: {reg.text} ({reg.confidence:.2f})"
            draw_label(img, label, xmin, ymin, bg_color=(255, 128, 0), text_color=(255, 255, 255))

    # 2. Draw Diagram Detections in Green (BGR: 0, 255, 0)
    if diagram_detections:
        for det in diagram_detections:
            box = det.get("box", [])
            if len(box) == 4:
                xmin, ymin, xmax, ymax = [int(round(c)) for c in box]
                cv2.rectangle(img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
                conf = det.get("confidence", 0.0)
                label = f"Diagram: {conf:.2f}"
                draw_label(img, label, xmin, ymin, bg_color=(0, 255, 0), text_color=(0, 0, 0))

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), img)
    return output_path


def run_ocr_command(args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"❌ Error: Image file not found at '{image_path}'", file=sys.stderr)
        sys.exit(1)

    device = DeviceType(args.device.lower()) if args.device else DeviceType.AUTO
    runtime = OCRRuntime(args.runtime.lower()) if args.runtime else OCRRuntime.AUTO

    config = OCRConfig(device=device, runtime=runtime, drop_score=args.drop_score)
    service = OCRService(config)

    print(f"🔍 Running OCR on '{image_path.name}' [Device: {service.device.value}, Runtime: {service.runtime.value}]...")
    results = service.process(image_path)

    # Format output JSON
    json_output = [
        {
            "text": reg.text,
            "box": [reg.bbox.x, reg.bbox.y, reg.bbox.width, reg.bbox.height],
            "confidence": round(reg.confidence, 4),
        }
        for reg in results
    ]

    json_str = json.dumps(json_output, indent=2)
    print("\n--- OCR JSON OUTPUT ---")
    print(json_str)

    # Save JSON file
    out_json_path = (
        Path(args.output_json) if args.output_json else image_path.parent / f"{image_path.stem}_ocr.json"
    )
    with open(out_json_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Save Annotated Image
    out_img_path = (
        Path(args.output_image)
        if args.output_image
        else image_path.parent / f"{image_path.stem}_ocr_annotated.png"
    )
    annotated_path = annotate_image(image_path, out_img_path, text_regions=results)

    print(f"\n✅ OCR JSON saved to: {out_json_path}")
    print(f"✅ Annotated image saved to: {annotated_path}")


def run_diagram_command(args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"❌ Error: Image file not found at '{image_path}'", file=sys.stderr)
        sys.exit(1)

    force_device = args.device.lower() if args.device and args.device != "auto" else None
    detector = get_detector(force_device=force_device)

    print(f"🎨 Running Diagram Detection on '{image_path.name}'...")
    pil_img = Image.open(image_path).convert("RGB")
    detections = detector.predict(pil_img, conf_threshold=args.conf)

    json_str = json.dumps(detections, indent=2)
    print("\n--- Diagram Detection JSON OUTPUT ---")
    print(json_str)

    # Save JSON file
    out_json_path = (
        Path(args.output_json) if args.output_json else image_path.parent / f"{image_path.stem}_diagram.json"
    )
    with open(out_json_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Save Annotated Image
    out_img_path = (
        Path(args.output_image)
        if args.output_image
        else image_path.parent / f"{image_path.stem}_diagram_annotated.png"
    )
    annotated_path = draw_diagram_boxes(image_path, detections, out_img_path)

    print(f"\n✅ Diagram JSON saved to: {out_json_path}")
    print(f"✅ Annotated image saved to: {annotated_path}")


def run_pipeline_command(args: argparse.Namespace) -> None:
    image_path = Path(args.image).resolve()
    if not image_path.exists():
        print(f"❌ Error: Image file not found at '{image_path}'", file=sys.stderr)
        sys.exit(1)

    print(f"🚀 Running Complete Pipeline (OCR + Diagram Detection) on '{image_path.name}'...")

    # 1. Run OCR
    device_val = args.device.lower() if args.device else "auto"
    device = DeviceType(device_val) if device_val in [d.value for d in DeviceType] else DeviceType.AUTO
    service = OCRService(OCRConfig(device=device))
    ocr_results = service.process(image_path)

    # 2. Run Diagram Detector
    force_device = args.device.lower() if args.device and args.device != "auto" else None
    detector = get_detector(force_device=force_device)
    pil_img = Image.open(image_path).convert("RGB")
    img_w, img_h = pil_img.size
    diagram_results = detector.predict(pil_img, conf_threshold=args.conf)

    # 3. Assemble Canonical Document
    elements = []
    for i, reg in enumerate(ocr_results):
        elements.append(
            TextElement(
                id=f"ocr_text_{i+1}",
                kind=TextKind.PARAGRAPH,
                content=reg.text,
                position=BoundingBox(
                    x=reg.bbox.x,
                    y=reg.bbox.y,
                    width=reg.bbox.width,
                    height=reg.bbox.height,
                    unit=CoordinateUnit.PX,
                ),
                confidence=reg.confidence,
            )
        )

    for j, det in enumerate(diagram_results):
        box = det.get("box", [0, 0, 0, 0])
        elements.append(
            DiagramElement(
                id=f"diagram_{j+1}",
                category=DiagramCategory.STRUCTURED,
                position=BoundingBox(
                    x=box[0],
                    y=box[1],
                    width=max(0.0, box[2] - box[0]),
                    height=max(0.0, box[3] - box[1]),
                    unit=CoordinateUnit.PX,
                ),
                confidence=det.get("confidence", 0.0),
            )
        )

    doc = Document(
        id=f"doc_{image_path.stem}",
        pages=[Page(page_number=1, width=float(img_w), height=float(img_h), elements=elements)],
    )

    doc_json_str = doc.model_dump_json(indent=2)
    print("\n--- Canonical Document JSON OUTPUT ---")
    print(doc_json_str)

    # Save Document JSON
    out_json_path = (
        Path(args.output_json) if args.output_json else image_path.parent / f"{image_path.stem}_doc.json"
    )
    with open(out_json_path, "w", encoding="utf-8") as f:
        f.write(doc_json_str)

    # Save Combined Annotated Image
    out_img_path = (
        Path(args.output_image)
        if args.output_image
        else image_path.parent / f"{image_path.stem}_annotated.png"
    )
    annotated_path = annotate_image(
        image_path, out_img_path, text_regions=ocr_results, diagram_detections=diagram_results
    )

    print(f"\n✅ Canonical Document JSON saved to: {out_json_path}")
    print(f"✅ Combined Annotated image saved to: {annotated_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Mulberry Processing Tooling CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. export
    export_parser = subparsers.add_parser("export", help="Export JSON schema and example JSON")
    export_parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Root workspace directory",
    )

    # 2. validate
    val_parser = subparsers.add_parser("validate", help="Validate a JSON document file")
    val_parser.add_argument("file", type=Path, help="Path to JSON file to validate")

    # 3. ocr
    ocr_parser = subparsers.add_parser("ocr", help="Test OCR model on an image and generate annotated image + JSON")
    ocr_parser.add_argument("image", type=Path, help="Path to input image file")
    ocr_parser.add_argument("-o", "--output-image", type=Path, help="Path to save annotated image")
    ocr_parser.add_argument("-j", "--output-json", type=Path, help="Path to save output JSON")
    ocr_parser.add_argument("--device", choices=["auto", "cpu", "gpu"], default="auto", help="Execution device")
    ocr_parser.add_argument("--runtime", choices=["auto", "paddle", "onnx", "openvino"], default="auto", help="OCR inference runtime")
    ocr_parser.add_argument("--drop-score", type=float, default=0.5, help="Confidence threshold drop score")

    # 4. diagram
    diag_parser = subparsers.add_parser("diagram", help="Test Diagram Detector model on an image and generate annotated image + JSON")
    diag_parser.add_argument("image", type=Path, help="Path to input image file")
    diag_parser.add_argument("-o", "--output-image", type=Path, help="Path to save annotated image")
    diag_parser.add_argument("-j", "--output-json", type=Path, help="Path to save output JSON")
    diag_parser.add_argument("--device", choices=["auto", "cpu", "cuda"], default="auto", help="Execution device")
    diag_parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")

    # 5. pipeline
    pipe_parser = subparsers.add_parser("pipeline", help="Run full pipeline (OCR + Diagram) on an image and generate canonical Document JSON + annotated image")
    pipe_parser.add_argument("image", type=Path, help="Path to input image file")
    pipe_parser.add_argument("-o", "--output-image", type=Path, help="Path to save combined annotated image")
    pipe_parser.add_argument("-j", "--output-json", type=Path, help="Path to save canonical Document JSON")
    pipe_parser.add_argument("--device", choices=["auto", "cpu", "gpu", "cuda"], default="auto", help="Execution device")
    pipe_parser.add_argument("--conf", type=float, default=0.25, help="Diagram confidence threshold")

    args = parser.parse_args()

    if args.command == "export":
        root_path = getattr(args, "root", Path(__file__).resolve().parents[3])
        export_artifacts(root_path)
    elif args.command == "validate":
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                data = json.load(f)
            doc = Document.model_validate(data)
            print(f"✅ Validation successful: '{args.file}' is a valid Mulberry Document (id={doc.id}).")
        except Exception as e:
            print(f"❌ Validation failed for '{args.file}':\n{e}", file=sys.stderr)
            sys.exit(1)
    elif args.command == "ocr":
        run_ocr_command(args)
    elif args.command == "diagram":
        run_diagram_command(args)
    elif args.command == "pipeline":
        run_pipeline_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
