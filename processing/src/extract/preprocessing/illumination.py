"""CLAHE Illumination and Contrast Flattening in LAB space for handwriting notes."""

from typing import Tuple
import cv2
import numpy as np


def apply_clahe_lab(
    img_bgr: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE) exclusively
    to the L (Luminance) channel of LAB color space.

    Balances phone overhead shadows and enhances faint ink strokes without harsh binarization.
    """
    if img_bgr.size == 0 or len(img_bgr.shape) < 2:
        return img_bgr

    if len(img_bgr.shape) == 2:
        # Grayscale
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
        return clahe.apply(img_bgr)

    # Convert to LAB
    lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl = clahe.apply(l)

    merged = cv2.merge((cl, a, b))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)
