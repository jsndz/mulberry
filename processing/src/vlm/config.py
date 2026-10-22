"""Configuration parameters for Mulberry VLM module."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union
import torch


@dataclass
class VLMConfig:
    """Configuration for VLM model loading, device selection, and inference parameters."""

    model_name: str = "Qwen/Qwen3-VL-4B-Instruct"
    device: Optional[str] = None  # None for auto-detection ('cuda' or 'cpu')
    dtype: Optional[Union[str, torch.dtype]] = None  # None for auto-detection (bf16/fp16 on CUDA, fp32 on CPU)

    # Generation parameters tuned for accurate handwriting transcription
    max_new_tokens: int = 4096
    temperature: float = 0.1
    top_p: float = 0.95
    repetition_penalty: float = 1.05
    do_sample: bool = False

    # Image resolution limits (in pixels) for Qwen-VL dynamic visual tokenization
    # Tuned for RTX 4060 8 GB VRAM budget while preserving fine stroke clarity
    min_pixels: int = 256 * 28 * 28
    max_pixels: int = 1280 * 28 * 28

    # Transformers loading options
    trust_remote_code: bool = True
    load_in_8bit: bool = False
    load_in_4bit: bool = False
    extra_model_kwargs: Dict[str, Any] = field(default_factory=dict)
