"""Unit tests for Stage 1 Preprocessing: dewarping and CLAHE illumination."""

import cv2
import numpy as np
import pytest
from processing.extract.preprocessing import (
    apply_clahe_lab,
    dewarp_document,
    order_points,
    warp_perspective,
)


def test_order_points():
    # Unordered corners of a rectangle: (100, 200), (10, 20), (10, 200), (100, 20)
    pts = np.array([[100, 200], [10, 20], [10, 200], [100, 20]], dtype="float32")
    ordered = order_points(pts)

    # Expected: TL=(10, 20), TR=(100, 20), BR=(100, 200), BL=(10, 200)
    np.testing.assert_allclose(ordered[0], [10, 20])
    np.testing.assert_allclose(ordered[1], [100, 20])
    np.testing.assert_allclose(ordered[2], [100, 200])
    np.testing.assert_allclose(ordered[3], [10, 200])


def test_apply_clahe_lab():
    # Create synthetic dark/shadowed image
    img = np.full((100, 100, 3), 50, dtype=np.uint8)
    cv2.line(img, (20, 50), (80, 50), (255, 255, 255), 2)

    enhanced = apply_clahe_lab(img, clip_limit=2.0)
    assert enhanced.shape == img.shape
    assert enhanced.dtype == np.uint8
    # L channel equalization increases contrast of the line
    assert np.max(enhanced) >= np.max(img)


def test_warp_perspective():
    # Create white canvas with a black skewed quad
    canvas = np.ones((400, 400, 3), dtype=np.uint8) * 255
    src_corners = np.array(
        [[50, 60], [350, 40], [330, 360], [70, 340]],
        dtype="float32",
    )
    warped = warp_perspective(canvas, src_corners)
    assert warped.shape[0] > 0
    assert warped.shape[1] > 0


def test_dewarp_document_fallback():
    # Blank image with no edges/quads
    blank = np.zeros((200, 200, 3), dtype=np.uint8)
    result, was_dewarped = dewarp_document(blank)
    assert was_dewarped is False
    assert result.shape == blank.shape
