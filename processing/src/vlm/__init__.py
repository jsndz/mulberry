"""Mulberry Vision-Language Model (VLM) Module.

Provides handwritten document comprehension and structural text extraction using Qwen3-VL.
"""

from processing.vlm.config import VLMConfig
from processing.vlm.exceptions import (
    InferenceError,
    InvalidImageError,
    MalformedOutputError,
    ModelLoadError,
    SchemaValidationError,
    VLMError,
)
from processing.vlm.prompts import VLM_SYSTEM_PROMPT, VLM_USER_PROMPT
from processing.vlm.runtime import RuntimeInfo, detect_device, detect_dtype, get_runtime_info
from processing.vlm.schemas import (
    VLMBlock,
    VLMBlockType,
    VLMListItem,
    VLMStructuredOutput,
)
from processing.vlm.service import VLMService

__all__ = [
    "VLMService",
    "VLMConfig",
    "VLMBlock",
    "VLMBlockType",
    "VLMListItem",
    "VLMStructuredOutput",
    "RuntimeInfo",
    "detect_device",
    "detect_dtype",
    "get_runtime_info",
    "VLMError",
    "ModelLoadError",
    "InvalidImageError",
    "InferenceError",
    "MalformedOutputError",
    "SchemaValidationError",
    "VLM_SYSTEM_PROMPT",
    "VLM_USER_PROMPT",
]
