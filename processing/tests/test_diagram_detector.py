"""Unit tests for Mulberry Diagram Detection System."""

import tempfile
from pathlib import Path

import cv2
import numpy as np

from PIL import Image
import pytest
import torch

from processing.diagram import (
    BaseDiagramDetector,
    DiTDiagramDetector,
    YOLODiagramDetector,
    check_gpu_availability,
    draw_diagram_boxes,
    get_detector,
    DiagramDetectionRegion,
)


def create_synthetic_diagram_image(width: int = 400, height: int = 400) -> Image.Image:
    """Creates a synthetic image with a simple drawn box flowchart/diagram."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([50, 50, 200, 200], outline=(0, 0, 0), width=3)
    draw.rectangle([220, 220, 350, 350], outline=(0, 0, 0), width=3)
    draw.line([200, 125, 220, 285], fill=(0, 0, 0), width=2)
    return img


class TestDiagramDetector:
    def test_diagram_detection_region_model(self):
        region = DiagramDetectionRegion(box=[10.0, 20.0, 100.0, 200.0], confidence=0.92, label="figure")
        assert region.box == [10.0, 20.0, 100.0, 200.0]
        assert region.confidence == 0.92
        assert region.to_dict() == {"box": [10.0, 20.0, 100.0, 200.0], "confidence": 0.92}

        # Invalid box dimensions
        with pytest.raises(ValueError):
            DiagramDetectionRegion(box=[100.0, 20.0, 10.0, 200.0], confidence=0.5)

    def test_hardware_check(self):
        gpu_avail = check_gpu_availability()
        assert isinstance(gpu_avail, bool)
        assert gpu_avail == torch.cuda.is_available()

    def test_get_detector_factory_cpu(self):
        detector = get_detector(force_device="cpu")
        assert isinstance(detector, BaseDiagramDetector)
        assert isinstance(detector, YOLODiagramDetector)

    def test_yolo_detector_predict_format(self):
        detector = get_detector(force_device="cpu")
        test_img = create_synthetic_diagram_image()

        results = detector.predict(test_img, conf_threshold=0.01)
        assert isinstance(results, list)

        for item in results:
            assert "box" in item
            assert "confidence" in item
            assert isinstance(item["box"], list)
            assert len(item["box"]) == 4
            xmin, ymin, xmax, ymax = item["box"]
            assert xmin <= xmax
            assert ymin <= ymax
            assert isinstance(item["confidence"], float)

    def test_draw_diagram_boxes_utility(self):
        test_img = create_synthetic_diagram_image()
        detections = [
            {"box": [50.0, 50.0, 200.0, 200.0], "confidence": 0.88},
            {"box": [220.0, 220.0, 350.0, 350.0], "confidence": 0.95},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            out_path = Path(tmpdir) / "annotated.png"
            result_path = draw_diagram_boxes(test_img, detections, out_path)
            assert Path(result_path).exists()

            loaded_img = cv2.imread(result_path)
            assert loaded_img is not None
            assert loaded_img.shape[0] == 400
            assert loaded_img.shape[1] == 400

    def test_invalid_image_inputs(self):
        detector = get_detector(force_device="cpu")
        with pytest.raises(Exception):
            detector.predict("non_existent_file_path_xyz.png")

        with pytest.raises(TypeError):
            draw_diagram_boxes(12345, [], "out.png")
