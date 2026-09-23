"""Centralized configuration for Mulberry OCR service."""

import os
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator


class DeviceType(str, Enum):
    """Target hardware execution device."""

    AUTO = "auto"
    CPU = "cpu"
    GPU = "gpu"


class OCRRuntime(str, Enum):
    """Inference engine runtime backend."""

    AUTO = "auto"
    PADDLE = "paddle"
    ONNX = "onnx"
    OPENVINO = "openvino"


class OCRConfig(BaseModel):
    """Explicit, centralized configuration for the Mulberry OCR Service."""

    device: DeviceType = Field(
        default=DeviceType.AUTO,
        description="Target device for inference: 'auto', 'cpu', or 'gpu'",
    )
    runtime: OCRRuntime = Field(
        default=OCRRuntime.AUTO,
        description="Target runtime engine: 'auto', 'paddle', 'onnx', or 'openvino'",
    )
    language: str = Field(
        default="en",
        description="Target OCR language code e.g. 'en', 'ch', 'fr'",
    )
    use_angle_cls: bool = Field(
        default=True,
        description="Enable text orientation/angle classification",
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
        description="Optional custom model name or directory path",
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
