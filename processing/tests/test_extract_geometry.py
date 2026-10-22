"""Unit tests for Stage 2 Geometry: layout segmentation, line detection, and topological sorting."""

import cv2
import numpy as np
import pytest
from processing.extract.geometry import (
    MorphologyLineDetector,
    get_line_detector,
    sort_lines_reading_order,
)
from processing.extract.geometry.layout import DiagramLayoutSegmenter
from processing.extract.schemas import NonTextElement, Polygon


def test_topological_sort_natural_reading_order():
    # Construct 3 polygons in unnatural order:
    # 1. Line 2 left: y ~ 100, x ~ 20
    # 2. Line 1 (heading): y ~ 30, x ~ 50
    # 3. Line 2 right: y ~ 100, x ~ 200
    p_head = Polygon.from_bbox(50, 20, 300, 40)
    p_line2_left = Polygon.from_bbox(20, 90, 180, 110)
    p_line2_right = Polygon.from_bbox(200, 92, 350, 112)

    shuffled = [p_line2_right, p_head, p_line2_left]
    ordered = sort_lines_reading_order(shuffled)

    assert len(ordered) == 3
    # First should be the heading at y~30
    assert ordered[0].y_bar < 50
    # Second should be line 2 left
    assert ordered[1].x_bar < ordered[2].x_bar


def test_morphology_line_detector_on_synthetic_strokes():
    canvas = np.full((300, 400, 3), 255, dtype=np.uint8)

    # Draw 2 horizontal black handwritten line strokes
    cv2.putText(canvas, "Distributed Systems Engineering", (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(canvas, "1. CAP Theory Consistency Availability", (30, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

    detector = MorphologyLineDetector()
    polygons = detector.detect_lines(canvas)

    assert len(polygons) >= 2
    # Check bounds
    for poly in polygons:
        bbox = poly.to_bbox()
        assert bbox[0] >= 0
        assert bbox[1] >= 0


def test_non_text_mask_isolation():
    canvas_shape = (400, 400)
    diagram_poly = Polygon.from_bbox(100, 100, 250, 250)
    non_text = NonTextElement(
        id="diagram_01",
        type="diagram",
        polygon=diagram_poly.to_list(),
    )

    mask = DiagramLayoutSegmenter.create_non_text_mask(canvas_shape, [non_text])
    assert mask.shape == canvas_shape
    # Center of diagram should be masked
    assert mask[175, 175] == 255
    # Outside should be 0
    assert mask[20, 20] == 0
