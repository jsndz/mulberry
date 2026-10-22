"""Runtime device and precision detection for the Mulberry VLM module."""

from dataclasses import dataclass
from typing import Optional, Union
import torch


@dataclass(frozen=True)
class RuntimeInfo:
    """Encapsulates runtime device and precision capabilities."""

    device: str
    dtype: torch.dtype
    cuda_available: bool
    gpu_name: Optional[str] = None
    vram_gb: Optional[float] = None

    def __repr__(self) -> str:
        gpu_str = f", GPU='{self.gpu_name}' ({self.vram_gb:.2f} GB)" if self.gpu_name else ""
        return f"RuntimeInfo(device='{self.device}', dtype={self.dtype}, cuda_available={self.cuda_available}{gpu_str})"


def is_cuda_available() -> bool:
    """Check if CUDA GPU acceleration is available."""
    try:
        return torch.cuda.is_available() and torch.cuda.device_count() > 0
    except Exception:
        return False


def detect_device(preferred_device: Optional[str] = None) -> str:
    """Detect and select the optimal execution device.

    Args:
        preferred_device: Explicit device string ("cuda", "cpu", "auto") or None for auto.

    Returns:
        Device string ("cuda" or "cpu").
    """
    if preferred_device is not None:
        clean_dev = preferred_device.strip().lower()
        if clean_dev.startswith("cuda") or clean_dev == "gpu":
            if is_cuda_available():
                return "cuda"
            # Fall back gracefully to cpu if cuda was requested but is not available
            return "cpu"
        if clean_dev == "cpu":
            return "cpu"
        if clean_dev == "auto":
            return "cuda" if is_cuda_available() else "cpu"

    return "cuda" if is_cuda_available() else "cpu"


def detect_dtype(device: str, preferred_dtype: Optional[Union[str, torch.dtype]] = None) -> torch.dtype:
    """Detect and select the optimal floating point precision (dtype) for the selected device.

    Args:
        device: Target execution device ('cuda' or 'cpu').
        preferred_dtype: Explicit dtype request (e.g. 'bfloat16', 'float16', 'float32', torch.bfloat16)

    Returns:
        torch.dtype: Optimal torch precision.
    """
    if preferred_dtype is not None:
        if isinstance(preferred_dtype, torch.dtype):
            return preferred_dtype
        dtype_str = str(preferred_dtype).strip().lower()
        if "bfloat16" in dtype_str or "bf16" in dtype_str:
            return torch.bfloat16
        if "float16" in dtype_str or "fp16" in dtype_str or "half" in dtype_str:
            return torch.float16
        if "float32" in dtype_str or "fp32" in dtype_str:
            return torch.float32

    # Automatic selection based on device
    if device.startswith("cuda"):
        try:
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
        except Exception:
            pass
        return torch.float16

    # CPU fallback defaults to float32 for maximum compatibility and precision
    return torch.float32


def get_runtime_info(
    preferred_device: Optional[str] = None,
    preferred_dtype: Optional[Union[str, torch.dtype]] = None,
) -> RuntimeInfo:
    """Determine complete runtime capabilities and target configuration.

    Args:
        preferred_device: Explicit device preference.
        preferred_dtype: Explicit dtype preference.

    Returns:
        RuntimeInfo with device, dtype, and GPU information.
    """
    cuda_avail = is_cuda_available()
    device = detect_device(preferred_device)
    dtype = detect_dtype(device, preferred_dtype)

    gpu_name: Optional[str] = None
    vram_gb: Optional[float] = None

    if cuda_avail and device.startswith("cuda"):
        try:
            device_idx = 0
            gpu_name = torch.cuda.get_device_name(device_idx)
            total_bytes = torch.cuda.get_device_properties(device_idx).total_memory
            vram_gb = total_bytes / (1024**3)
        except Exception:
            pass

    return RuntimeInfo(
        device=device,
        dtype=dtype,
        cuda_available=cuda_avail,
        gpu_name=gpu_name,
        vram_gb=vram_gb,
    )
