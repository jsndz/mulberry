"""Padded polygonal line strip cropper for handwritten text line recognition."""

from typing import List, Tuple
import cv2
import numpy as np
from PIL import Image

from processing.extract.schemas import Polygon


def crop_line_strip(
    canvas_bgr: np.ndarray,
    polygon: Polygon,
    pad_y: int = 6,
    pad_x: int = 12,
) -> Tuple[np.ndarray, List[float]]:
    """
    Crops a line strip dynamically from the canvas using its bounding polygon.

    Adds dynamic padding (top/bottom: +pad_y, left/right: +pad_x) to preserve
    ascending strokes (b, d, h, l, t) and descending strokes (g, j, p, q, y).

    Returns:
        Tuple of (cropped_bgr_array, effective_bbox: [xmin, ymin, xmax, ymax])
    """
    h, w = canvas_bgr.shape[:2]
    raw_bbox = polygon.to_bbox()
    xmin, ymin, xmax, ymax = raw_bbox

    # Apply padding and clamp to canvas bounds
    padded_xmin = max(0, int(round(xmin)) - pad_x)
    padded_ymin = max(0, int(round(ymin)) - pad_y)
    padded_xmax = min(w, int(round(xmax)) + pad_x)
    padded_ymax = min(h, int(round(ymax)) + pad_y)

    effective_bbox = [float(padded_xmin), float(padded_ymin), float(padded_xmax), float(padded_ymax)]

    if padded_xmax <= padded_xmin or padded_ymax <= padded_ymin:
        # Return tiny dummy crop if degenerate
        return np.zeros((10, 10, 3), dtype=np.uint8), effective_bbox

    crop = canvas_bgr[padded_ymin:padded_ymax, padded_xmin:padded_xmax].copy()
    return crop, effective_bbox
