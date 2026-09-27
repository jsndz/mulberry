"""Centralized configuration for Mulberry OCR service supporting decoupled detection and recognition."""

import os
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class DeviceType(str, Enum):
    """Target hardware execution device."""

    AUTO = "auto"
    CPU = "cpu"
    GPU = "gpu"


class DetectorBackend(str, Enum):
    """Supported text detection model backends."""

    PADDLE = "paddle"


class RecognizerBackend(str, Enum):
    """Supported text recognition model backends."""

    TROCR = "trocr"
    PADDLE = "paddle"


class DetectionRuntime(str, Enum):
    """Inference engine runtime backend for text detection."""

    AUTO = "auto"
    PADDLE = "paddle"
    ONNX = "onnx"
    OPENVINO = "openvino"


class RecognitionRuntime(str, Enum):
    """Inference engine runtime backend for text recognition."""

    AUTO = "auto"
    PYTORCH = "pytorch"
    PADDLE = "paddle"
    ONNX = "onnx"


class OCRRuntime(str, Enum):
    """Legacy/unified inference engine runtime backend alias."""

    AUTO = "auto"
    PADDLE = "paddle"
    ONNX = "onnx"
    OPENVINO = "openvino"


class ImagePreprocessingConfig(BaseModel):
    """Optional image preprocessing options suitable for handwritten notes."""

    enable_denoise: bool = Field(
        default=False,
        description="Apply mild bilateral/Gaussian denoising suitable for handwritten text",
    )
    enable_contrast_norm: bool = Field(
        default=False,
        description="Apply CLAHE contrast normalization without destructive binarization",
    )
    enable_deskew: bool = Field(
        default=False,
        description="Estimate rotation angle and deskew page image",
    )
    max_dimension: Optional[int] = Field(
        default=None,
        description="Optional maximum pixel dimension for scaling input image",
    )
    enable_tiling: bool = Field(
        default=False,
        description="Enable patch-based tiling for ultra-high-resolution images without quality loss",
    )
    tile_size: int = Field(
        default=1024,
        description="Maximum tile dimension in pixels",
    )
    tile_overlap: int = Field(
        default=128,
        description="Border overlap pixels between adjacent tiles",
    )
    nms_iou_threshold: float = Field(
        default=0.4,
        description="IoU threshold for Non-Maximum Suppression (NMS) deduplication across tile boundaries",
    )


class OCRConfig(BaseModel):
    """Explicit, centralized configuration for the Mulberry OCR Service."""

    device: DeviceType = Field(
        default=DeviceType.AUTO,
        description="Target device for inference: 'auto', 'cpu', or 'gpu'",
    )
    detector_backend: DetectorBackend = Field(
        default=DetectorBackend.PADDLE,
        description="Backend engine for text detection (e.g. 'paddle')",
    )
    recognizer_backend: RecognizerBackend = Field(
        default=RecognizerBackend.TROCR,
        description="Backend engine for text recognition (e.g. 'trocr', 'paddle')",
    )
    detection_runtime: DetectionRuntime = Field(
        default=DetectionRuntime.AUTO,
        description="Target runtime engine for text detection: 'auto', 'paddle', 'onnx', 'openvino'",
    )
    recognition_runtime: RecognitionRuntime = Field(
        default=RecognitionRuntime.AUTO,
        description="Target runtime engine for text recognition: 'auto', 'pytorch', 'paddle', 'onnx'",
    )
    runtime: OCRRuntime = Field(
        default=OCRRuntime.AUTO,
        description="Legacy global runtime parameter (maps to detection/recognition runtime)",
    )
    trocr_model_name: str = Field(
        default="microsoft/trocr-base-handwritten",
        description="HuggingFace model ID or path for TrOCR recognition",
    )
    language: str = Field(
        default="en",
        description="Target OCR language code e.g. 'en', 'ch', 'fr'",
    )
    use_orientation: bool = Field(
        default=True,
        description="Enable text orientation/angle classification and rotation correction",
    )
    use_angle_cls: bool = Field(
        default=True,
        description="Backward compatibility alias for use_orientation",
    )
    drop_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold to accept text region",
    )
    cpu_threads: int = Field(
        default_factory=lambda: min(8, max(1, os.cpu_count() or 1)),
        description="Number of CPU threads allocated for inference",
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Optional custom model name or directory path override",
    )
    preprocessing: ImagePreprocessingConfig = Field(
        default_factory=ImagePreprocessingConfig,
        description="Preprocessing configuration options",
    )
    extra_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary backend-specific parameter overrides",
    )

    @field_validator("drop_score")
    @classmethod
    def validate_drop_score(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("drop_score must be between 0.0 and 1.0")
        return v
