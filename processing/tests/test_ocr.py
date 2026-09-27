"""Comprehensive Unit Tests for Mulberry Decoupled OCR Subsystem."""

import pytest
import numpy as np
from PIL import Image, ImageDraw

from processing.ocr import (
    OCRService,
    OCRConfig,
    BoundingBox,
    DetectedRegion,
    TextRegion,
    DeviceType,
    DetectorBackend,
    RecognizerBackend,
    DetectionRuntime,
    RecognitionRuntime,
    OCRRuntime,
    ImagePreprocessingConfig,
    RuntimeSelector,
    ResolvedRuntimeConfig,
    SystemCapabilities,
    normalize_image,
    preprocess_image,
    assign_reading_order,
    BaseTextDetector,
    BaseTextRecognizer,
    TextResult,
    BaseOrientationClassifier,
    OCRError,
    InvalidImageError,
    GPUUnavailableError,
    UnsupportedRuntimeError,
    MissingModelError,
)


def create_synthetic_text_image(text: str = "Mulberry OCR Test", width: int = 500, height: int = 150) -> Image.Image:
    """Helper to generate a clean synthetic text image for deterministic OCR testing."""
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), text, fill=(0, 0, 0))
    return img


# Mock Detector and Recognizer for unit testing without downloading full neural models
class DummyTextDetector(BaseTextDetector):
    def __init__(self, detected_items=None):
        self.detected_items = detected_items or [
            DetectedRegion(
                polygon=[[20.0, 30.0], [180.0, 30.0], [180.0, 70.0], [20.0, 70.0]],
                bbox=BoundingBox(x=20.0, y=30.0, width=160.0, height=40.0),
                confidence=0.92,
            )
        ]

    def detect(self, image_bgr: np.ndarray) -> list[DetectedRegion]:
        return self.detected_items


class DummyTextRecognizer(BaseTextRecognizer):
    def __init__(self, text="Handwritten Note", confidence=0.95, recognizer_name="trocr"):
        self.text = text
        self.confidence = confidence
        self.recognizer_name = recognizer_name

    def recognize_crop(self, crop_bgr: np.ndarray) -> TextResult:
        return TextResult(text=self.text, confidence=self.confidence, recognizer_name=self.recognizer_name)


class TestOCRModelsAndConfig:
    def test_bounding_box_validation(self):
        bbox = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        assert bbox.x == 10.0
        assert bbox.y == 20.0
        assert bbox.width == 100.0
        assert bbox.height == 50.0

        with pytest.raises(ValueError):
            BoundingBox(x=0.0, y=0.0, width=-5.0, height=10.0)

    def test_detected_region_validation(self):
        poly = [[10.0, 10.0], [50.0, 10.0], [50.0, 30.0], [10.0, 30.0]]
        bbox = BoundingBox(x=10.0, y=10.0, width=40.0, height=20.0)
        det = DetectedRegion(polygon=poly, bbox=bbox, confidence=0.88)
        assert det.confidence == 0.88
        assert det.polygon == poly

    def test_text_region_canonical_schema(self):
        region = TextRegion(
            id="ocr_text_1",
            text="Heading 1",
            confidence=0.96,
            polygon=[[10.0, 10.0], [100.0, 10.0], [100.0, 40.0], [10.0, 40.0]],
            bbox=BoundingBox(x=10.0, y=10.0, width=90.0, height=30.0),
            recognizer="trocr",
            reading_order=0,
            handwriting=True,
        )
        assert region.id == "ocr_text_1"
        assert region.text == "Heading 1"
        assert region.recognizer == "trocr"
        assert region.reading_order == 0
        assert region.handwriting is True

        with pytest.raises(ValueError):
            TextRegion(
                text="Bad",
                confidence=1.5,
                bbox=BoundingBox(x=0.0, y=0.0, width=50.0, height=20.0),
            )

    def test_ocr_config_defaults(self):
        config = OCRConfig()
        assert config.device == DeviceType.AUTO
        assert config.detector_backend == DetectorBackend.PADDLE
        assert config.recognizer_backend == RecognizerBackend.TROCR
        assert config.drop_score == 0.5
        assert config.preprocessing.enable_denoise is False


class TestRuntimeSelector:
    def test_detect_capabilities(self):
        caps = RuntimeSelector.inspect_system()
        assert isinstance(caps, SystemCapabilities)
        assert isinstance(caps.has_gpu, bool)
        assert isinstance(caps.has_paddle, bool)

    def test_resolve_cpu_auto_runtime(self):
        config = OCRConfig(device=DeviceType.CPU, recognizer_backend=RecognizerBackend.PADDLE)
        resolved = RuntimeSelector.resolve_configuration(config)
        assert isinstance(resolved, ResolvedRuntimeConfig)
        assert resolved.device == DeviceType.CPU
        assert resolved.detection_runtime in [DetectionRuntime.PADDLE, DetectionRuntime.ONNX, DetectionRuntime.OPENVINO]

    def test_unsupported_runtime_raises_error(self, monkeypatch):
        monkeypatch.setattr(RuntimeSelector, "detect_runtimes", lambda: {
            "paddle": False, "onnx": False, "openvino": False, "torch": False, "transformers": False
        })
        config = OCRConfig(detection_runtime=DetectionRuntime.PADDLE)
        with pytest.raises(UnsupportedRuntimeError):
            RuntimeSelector.resolve_configuration(config)

    def test_gpu_unavailable_raises_error(self, monkeypatch):
        monkeypatch.setattr(RuntimeSelector, "detect_gpu", lambda: (False, None))
        config = OCRConfig(device=DeviceType.GPU)
        with pytest.raises(GPUUnavailableError):
            RuntimeSelector.resolve_configuration(config)

    def test_trocr_missing_torch_raises_error(self, monkeypatch):
        monkeypatch.setattr(RuntimeSelector, "detect_runtimes", lambda: {
            "paddle": True, "onnx": True, "openvino": False, "torch": False, "transformers": False
        })
        config = OCRConfig(recognizer_backend=RecognizerBackend.TROCR)
        with pytest.raises(UnsupportedRuntimeError):
            RuntimeSelector.resolve_configuration(config)


class TestImagePreprocessing:
    def test_normalize_image_pil(self):
        pil_img = create_synthetic_text_image()
        img_bgr, w, h = normalize_image(pil_img)
        assert isinstance(img_bgr, np.ndarray)
        assert img_bgr.ndim == 3
        assert img_bgr.shape[2] == 3
        assert w == 500
        assert h == 150

    def test_normalize_image_invalid_raises_exception(self):
        with pytest.raises(InvalidImageError):
            normalize_image("non_existent_file_xyz_123.png")

        with pytest.raises(InvalidImageError):
            normalize_image(np.array([]))

    def test_preprocess_handwriting_options(self):
        img = np.full((200, 300, 3), 200, dtype=np.uint8)
        config = ImagePreprocessingConfig(
            enable_denoise=True,
            enable_contrast_norm=True,
            enable_deskew=True,
            max_dimension=150,
        )
        processed = preprocess_image(img, config)
        assert isinstance(processed, np.ndarray)
        assert max(processed.shape[:2]) <= 150


class TestReadingOrderLayout:
    def test_spatial_reading_order_assignment(self):
        # Create 3 regions out of order: bottom line, top-left, top-right
        r_bottom = TextRegion(
            id="1", text="Bottom Line", confidence=0.9,
            bbox=BoundingBox(x=10.0, y=200.0, width=100.0, height=20.0)
        )
        r_top_left = TextRegion(
            id="2", text="Top Left", confidence=0.9,
            bbox=BoundingBox(x=10.0, y=20.0, width=100.0, height=20.0)
        )
        r_top_right = TextRegion(
            id="3", text="Top Right", confidence=0.9,
            bbox=BoundingBox(x=150.0, y=20.0, width=100.0, height=20.0)
        )

        ordered = assign_reading_order([r_bottom, r_top_left, r_top_right])
        assert len(ordered) == 3
        assert ordered[0].text == "Top Left"
        assert ordered[0].reading_order == 0
        assert ordered[1].text == "Top Right"
        assert ordered[1].reading_order == 1
        assert ordered[2].text == "Bottom Line"
        assert ordered[2].reading_order == 2


class TestOCRServiceOrchestration:
    def test_service_with_mock_components(self, monkeypatch):
        # Inject mock detector and recognizer into OCRService
        service = OCRService(OCRConfig(device=DeviceType.CPU, recognizer_backend=RecognizerBackend.PADDLE))
        service._detector = DummyTextDetector()
        service._recognizer = DummyTextRecognizer(text="Mocked Note", recognizer_name="mock_rec")

        pil_img = create_synthetic_text_image()
        results = service.process(pil_img)

        assert len(results) == 1
        assert results[0].text == "Mocked Note"
        assert results[0].recognizer == "mock_rec"
        assert results[0].bbox.x == 20.0
        assert results[0].bbox.y == 30.0
        assert results[0].reading_order == 0

    def test_roi_cropping_and_coordinate_translation(self):
        service = OCRService(OCRConfig(device=DeviceType.CPU, recognizer_backend=RecognizerBackend.PADDLE))
        service._detector = DummyTextDetector([
            DetectedRegion(
                polygon=[[10.0, 10.0], [50.0, 10.0], [50.0, 30.0], [10.0, 30.0]],
                bbox=BoundingBox(x=10.0, y=10.0, width=40.0, height=20.0),
                confidence=0.9,
            )
        ])
        service._recognizer = DummyTextRecognizer(text="ROI Text")

        full_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        sub_roi = BoundingBox(x=200.0, y=150.0, width=300.0, height=200.0)

        results = service.process(full_img, bbox=sub_roi)
        assert len(results) == 1

        # Verify translated coordinates (200 + 10 = 210 for x, 150 + 10 = 160 for y)
        assert results[0].bbox.x == 210.0
        assert results[0].bbox.y == 160.0
        assert results[0].polygon[0] == [210.0, 160.0]

    def test_blank_image_returns_empty_list(self):
        service = OCRService(OCRConfig(device=DeviceType.CPU, recognizer_backend=RecognizerBackend.PADDLE))
        service._detector = DummyTextDetector(detected_items=[])
        blank_img = Image.new("RGB", (300, 300), color=(255, 255, 255))

        results = service.process(blank_img)
        assert isinstance(results, list)
        assert len(results) == 0
