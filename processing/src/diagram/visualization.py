"""Visualization utilities for diagram detection results."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger("mulberry.diagram.visualization")


def draw_diagram_boxes(
    image_input: Union[str, Path, np.ndarray, Image.Image],
    detections: List[Dict[str, Any]],
    output_path: Union[str, Path],
    box_color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2,
    draw_labels: bool = True,
) -> str:
    """
    OpenCV utility function that takes the original image and the coordinate list,
    draws solid bounding boxes around the detected diagram regions, and saves the
    verified visual output to a new image file.

    Args:
        image_input: Image file path, NumPy array (BGR), or PIL Image.
        detections: List of dicts structured as [{"box": [xmin, ymin, xmax, ymax], "confidence": float}]
        output_path: Path where the verified image with bounding boxes will be saved.
        box_color: Solid bounding box color in BGR format (default: green (0, 255, 0)).
        thickness: Line thickness for solid bounding boxes.
        draw_labels: Whether to overlay confidence scores on top of boxes.

    Returns:
        Absolute string path to the saved output image file.
    """
    if isinstance(image_input, (str, Path)):
        img = cv2.imread(str(image_input))
        if img is None:
            raise ValueError(f"Unable to read image from path: {image_input}")
    elif isinstance(image_input, Image.Image):
        img = cv2.cvtColor(np.array(image_input.convert("RGB")), cv2.COLOR_RGB2BGR)
    elif isinstance(image_input, np.ndarray):
        img = image_input.copy()
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")

    for det in detections:
        box = det.get("box", [])
        if len(box) != 4:
            continue

        xmin, ymin, xmax, ymax = [int(round(c)) for c in box]
        confidence = det.get("confidence", 0.0)

        # Draw solid bounding box
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), box_color, thickness)

        if draw_labels:
            label_text = f"Diagram: {confidence:.2f}"
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            font_thickness = 1
            (t_width, t_height), baseline = cv2.getTextSize(label_text, font, font_scale, font_thickness)

            label_ymin = max(ymin - t_height - baseline - 4, 0)
            cv2.rectangle(
                img,
                (xmin, label_ymin),
                (xmin + t_width + 6, label_ymin + t_height + baseline + 4),
                box_color,
                cv2.FILLED,
            )
            cv2.putText(
                img,
                label_text,
                (xmin + 3, label_ymin + t_height + 2),
                font,
                font_scale,
                (0, 0, 0),  # Black text on solid background
                font_thickness,
                cv2.LINE_AA,
            )

    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)
    success = cv2.imwrite(str(out_file), img)
    if not success:
        raise RuntimeError(f"Failed to save visual output to {out_file}")

    logger.info(f"Verified visual output saved to: {out_file}")
    return str(out_file)
