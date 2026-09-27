"""Unit tests for tile-based chunking and NMS deduplication."""

import numpy as np
import pytest

from processing.ocr import (
    BoundingBox,
    DetectedRegion,
    OCRConfig,
    OCRService,
    generate_tiles,
    suppress_duplicate_detections,
)


class TestTilingAndNMS:
    def test_generate_tiles_small_image(self):
        img = np.full((500, 500, 3), 255, dtype=np.uint8)
        tiles = generate_tiles(img, tile_size=1024, overlap=128)
        assert len(tiles) == 1
        assert tiles[0][1] == 0.0
        assert tiles[0][2] == 0.0

    def test_generate_tiles_large_image(self):
        # 2500 x 2500 px image
        img = np.full((2500, 2500, 3), 255, dtype=np.uint8)
        tiles = generate_tiles(img, tile_size=1024, overlap=128)
        assert len(tiles) > 1

        # Check tile offsets cover full image
        max_x_offset = max(t[1] for t in tiles)
        max_y_offset = max(t[2] for t in tiles)
        assert max_x_offset > 1000
        assert max_y_offset > 1000

    def test_nms_suppression_duplicate_boxes(self):
        box1 = BoundingBox(x=10.0, y=10.0, width=100.0, height=40.0)
        box2 = BoundingBox(x=12.0, y=11.0, width=98.0, height=39.0)  # Near identical overlap
        box3 = BoundingBox(x=300.0, y=300.0, width=50.0, height=20.0)  # Disjoint box

        det1 = DetectedRegion(polygon=[[10.0, 10.0], [110.0, 10.0], [110.0, 50.0], [10.0, 50.0]], bbox=box1, confidence=0.95)
        det2 = DetectedRegion(polygon=[[12.0, 11.0], [110.0, 11.0], [110.0, 50.0], [12.0, 50.0]], bbox=box2, confidence=0.85)
        det3 = DetectedRegion(polygon=[[300.0, 300.0], [350.0, 300.0], [350.0, 320.0], [300.0, 320.0]], bbox=box3, confidence=0.90)

        results = suppress_duplicate_detections([det1, det2, det3], iou_threshold=0.4)
        assert len(results) == 2
        # det1 should be kept over det2 because det1 has higher confidence (0.95 vs 0.85)
        assert results[0].confidence == 0.95
        assert results[1].confidence == 0.90
