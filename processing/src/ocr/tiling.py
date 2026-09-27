"""Tile-based high-resolution image chunking and Non-Maximum Suppression (NMS) for Mulberry OCR."""

import logging
from typing import List, Tuple
import numpy as np

from processing.ocr.models import BoundingBox, DetectedRegion

logger = logging.getLogger(__name__)


def generate_tiles(
    img_bgr: np.ndarray, tile_size: int = 1024, overlap: int = 128
) -> List[Tuple[np.ndarray, float, float]]:
    """Split a high-resolution image into overlapping tile patches with global pixel offsets.

    Args:
        img_bgr: Full-resolution input image BGR array.
        tile_size: Maximum width/height of each tile.
        overlap: Border overlap pixels between adjacent tiles to prevent cutting text lines.

    Returns:
        List of tuples: (tile_crop_bgr, offset_x, offset_y)
    """
    h, w = img_bgr.shape[:2]
    if w <= tile_size and h <= tile_size:
        return [(img_bgr, 0.0, 0.0)]

    stride = max(64, tile_size - overlap)
    tiles: List[Tuple[np.ndarray, float, float]] = []

    y = 0
    while y < h:
        y_end = min(h, y + tile_size)
        y_start = max(0, y_end - tile_size) if (y_end == h and h > tile_size) else y

        x = 0
        while x < w:
            x_end = min(w, x + tile_size)
            x_start = max(0, x_end - tile_size) if (x_end == w and w > tile_size) else x

            tile_crop = img_bgr[y_start:y_end, x_start:x_end]
            tiles.append((tile_crop, float(x_start), float(y_start)))

            if x_end >= w:
                break
            x += stride

        if y_end >= h:
            break
        y += stride

    logger.info(
        f"Generated {len(tiles)} tiles ({tile_size}x{tile_size} px, overlap={overlap} px) for image ({w}x{h} px)"
    )
    return tiles


def compute_iou(box1: BoundingBox, box2: BoundingBox) -> float:
    """Compute Intersection over Union (IoU) score between two bounding boxes."""
    x1 = max(box1.x, box2.x)
    y1 = max(box1.y, box2.y)
    x2 = min(box1.x + box1.width, box2.x + box2.width)
    y2 = min(box1.y + box1.height, box2.y + box2.height)

    inter_w = max(0.0, x2 - x1)
    inter_h = max(0.0, y2 - y1)
    inter_area = inter_w * inter_h

    area1 = box1.width * box1.height
    area2 = box2.width * box2.height
    union_area = area1 + area2 - inter_area

    if union_area <= 0.0:
        return 0.0
    return inter_area / union_area


def suppress_duplicate_detections(
    regions: List[DetectedRegion], iou_threshold: float = 0.4
) -> List[DetectedRegion]:
    """Perform Non-Maximum Suppression (NMS) to merge/deduplicate detections across tile seams."""
    if not regions:
        return []

    # Sort regions by detection confidence descending
    sorted_regions = sorted(regions, key=lambda r: r.confidence, reverse=True)
    kept_regions: List[DetectedRegion] = []

    for candidate in sorted_regions:
        duplicate = False
        for kept in kept_regions:
            if compute_iou(candidate.bbox, kept.bbox) >= iou_threshold:
                duplicate = True
                break
        if not duplicate:
            kept_regions.append(candidate)

    return kept_regions
