"""Comprehensive Unit Tests for Mulberry OCR Subsystem."""

import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from processing.ocr import (
    OCRService,
    OCRConfig,
    BoundingBox,
    TextRegion,
    DeviceType,
    OCRRuntime,
    RuntimeSelector,
    SystemCapabilities,
    OCRError,
    InvalidImageError,
    GPUUnavailableError,
    UnsupportedRuntimeError,
)


def create_synthetic_text_image(text: str = "Mulberry OCR Test", width: int = 500, height: int = 150) -> Image.Image:
    """Helper to generate a clean synthetic text image for deterministic OCR testing."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), text, fill=(0, 0, 0))
    return img


class TestOCRModelsAndConfig:
    def test_bounding_box_validation(self):
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0

        with pytest.raises(ValueError):
            BoundingBox(x=0.0, y=0.0, width=-5.0, height=10.0)

    def test_text_region_validation(self):
        region = TextRegion(
            text="Hello",
            bbox=BoundingBox(x=0.0, y=0.0, width=50.0, height=20.0),
            confidence=0.95,
        )
        assert region.text == "Hello"
        assert region.confidence == 0.95

        with pytest.raises(ValueError):
            TextRegion(
                text="Bad",
                bbox=BoundingBox(x=0.0, y=0.0, width=50.0, height=20.0),
                confidence=1.5,
            )

    def test_ocr_config_defaults(self):
        config = OCRConfig()
        assert config.device == DeviceType.AUTO
        assert config.runtime == OCRRuntime.AUTO
        assert config.language == "en"
        assert config.drop_score == 0.5


class TestRuntimeSelector:
    def test_detect_capabilities(self):
        caps = RuntimeSelector.inspect_system()
        assert isinstance(caps, SystemCapabilities)
        assert isinstance(caps.has_gpu, bool)
        assert isinstance(caps.installed_runtimes, list)

    def test_resolve_cpu_auto_runtime(self):
        config = OCRConfig(device=DeviceType.CPU, runtime=OCRRuntime.AUTO)
        device, runtime, gpu_name = RuntimeSelector.resolve_configuration(config)
        assert device == DeviceType.CPU
        assert runtime in [OCRRuntime.ONNX, OCRRuntime.PADDLE, OCRRuntime.OPENVINO]

    def test_unsupported_runtime_raises_error(self, monkeypatch):
        # Mock detect_runtimes to report OPENVINO as False
        monkeypatch.setattr(RuntimeSelector, "detect_runtimes", lambda: {OCRRuntime.OPENVINO: False})
        config = OCRConfig(runtime=OCRRuntime.OPENVINO)
        with pytest.raises(UnsupportedRuntimeError):
            RuntimeSelector.resolve_configuration(config)

    def test_gpu_unavailable_raises_error(self, monkeypatch):
        # Mock detect_gpu to report False
        monkeypatch.setattr(RuntimeSelector, "detect_gpu", lambda: (False, None))
        config = OCRConfig(device=DeviceType.GPU)
        with pytest.raises(GPUUnavailableError):
            RuntimeSelector.resolve_configuration(config)


class TestOCRServiceExecution:
    @pytest.fixture(scope="module")
    def ocr_service(self):
        """Reusable OCRService instance (loaded once for test module)."""
        config = OCRConfig(device=DeviceType.CPU, runtime=OCRRuntime.ONNX, drop_score=0.2)
        return OCRService(config)

    def test_cpu_execution_and_properties(self, ocr_service):
        assert ocr_service.device == DeviceType.CPU
        assert ocr_service.runtime in [OCRRuntime.ONNX, OCRRuntime.PADDLE, OCRRuntime.OPENVINO]

    def test_full_page_ocr(self, ocr_service):
        pil_img = create_synthetic_text_image("Mulberry Engine")
        results = ocr_service.process(pil_img)
        assert isinstance(results, list)
        assert len(results) >= 1
        found_texts = [r.text for r in results]
        assert any("Mulberry" in text or "Engine" in text for text in found_texts)

        for reg in results:
            assert isinstance(reg.bbox, BoundingBox)
            assert reg.bbox.x >= 0
            assert reg.bbox.y >= 0
            assert reg.bbox.width > 0
            assert reg.bbox.height > 0
            assert 0.0 <= reg.confidence <= 1.0

    def test_bounding_box_region_ocr_and_coordinate_translation(self, ocr_service):
        # Create larger canvas (800x400) and place text at offset (200, 150)
        full_img = Image.new("RGB", (800, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(full_img)
        draw.text((220, 170), "Cropped OCR Target", fill=(0, 0, 0))

        # Define sub-bounding box around text region (x=200, y=150, width=400, height=100)
        sub_bbox = BoundingBox(x=200.0, y=150.0, width=400.0, height=100.0)

        results = ocr_service.process(full_img, bbox=sub_bbox)
        assert len(results) >= 1

        for reg in results:
            # Verify coordinates were translated back to full image space (>= 200 for x, >= 150 for y)
            assert reg.bbox.x >= 180.0
            assert reg.bbox.y >= 140.0
            assert reg.bbox.x + reg.bbox.width <= 800.0

    def test_blank_empty_image(self, ocr_service):
        blank_img = Image.new("RGB", (300, 300), color=(255, 255, 255))
        results = ocr_service.process(blank_img)
        assert isinstance(results, list)
        assert len(results) == 0

    def test_empty_crop_bbox(self, ocr_service):
        img = create_synthetic_text_image()
        empty_bbox = BoundingBox(x=10.0, y=10.0, width=0.0, height=0.0)
        results = ocr_service.process(img, bbox=empty_bbox)
        assert len(results) == 0

    def test_invalid_image_inputs(self, ocr_service):
        with pytest.raises(InvalidImageError):
            ocr_service.process("non_existent_file_path_12345.png")

        with pytest.raises(InvalidImageError):
            ocr_service.process(b"corrupted_bytes_data")

        with pytest.raises(InvalidImageError):
            ocr_service.process(np.array([]))

    def test_numpy_array_input(self, ocr_service):
        pil_img = create_synthetic_text_image("Array Test")
        np_img = np.array(pil_img)
        results = ocr_service.process(np_img)
        assert len(results) >= 1
