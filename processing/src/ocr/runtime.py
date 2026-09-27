"""Hardware capabilities detection and independent inference runtime resolution."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from processing.ocr.config import (
    DeviceType,
    DetectionRuntime,
    OCRConfig,
    OCRRuntime,
    RecognitionRuntime,
    RecognizerBackend,
)
from processing.ocr.exceptions import GPUUnavailableError, UnsupportedRuntimeError

logger = logging.getLogger(__name__)


@dataclass
class ResolvedRuntimeConfig:
    """Explicit resolved runtime configuration for detection and recognition."""

    device: DeviceType
    detection_runtime: DetectionRuntime
    recognition_runtime: RecognitionRuntime
    gpu_name: Optional[str] = None


@dataclass
class SystemCapabilities:
    """Discovered host system hardware and installed packages."""

    has_gpu: bool
    gpu_name: Optional[str]
    has_paddle: bool
    has_onnx: bool
    has_openvino: bool
    has_torch: bool
    has_transformers: bool


class RuntimeSelector:
    """Hardware and independent runtime selection layer.

    Keeps hardware detection decoupled from OCR model inference logic.
    """

    @staticmethod
    def detect_gpu() -> Tuple[bool, Optional[str]]:
        """Detect whether usable GPU acceleration is available."""
        # 1. Check PyTorch CUDA
        try:
            import torch

            if torch.cuda.is_available():
                name = (
                    torch.cuda.get_device_name(0)
                    if torch.cuda.device_count() > 0
                    else "CUDA GPU"
                )
                return True, f"PyTorch CUDA ({name})"
        except Exception:
            pass

        # 2. Check PaddlePaddle CUDA support
        try:
            import paddle

            if hasattr(paddle, "is_compiled_with_cuda") and paddle.is_compiled_with_cuda():
                gpu_count = (
                    paddle.device.cuda.device_count()
                    if hasattr(paddle.device, "cuda")
                    else 0
                )
                if gpu_count > 0 or paddle.is_compiled_with_cuda():
                    return True, "NVIDIA CUDA (Paddle)"
        except Exception:
            pass

        # 3. Check ONNX Runtime GPU Execution Providers
        try:
            import onnxruntime as ort

            providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in providers or "ROCMExecutionProvider" in providers:
                return True, f"ONNX Runtime Provider ({providers[0]})"
        except Exception:
            pass

        return False, None

    @staticmethod
    def detect_runtimes() -> Dict[str, bool]:
        """Detect which inference packages and backends are installed."""
        available: Dict[str, bool] = {
            "paddle": False,
            "onnx": False,
            "openvino": False,
            "torch": False,
            "transformers": False,
        }

        # Check Paddle
        try:
            import paddle  # noqa: F401
            import paddleocr  # noqa: F401

            available["paddle"] = True
        except ImportError:
            available["paddle"] = False

        # Check ONNX Runtime
        try:
            import onnxruntime  # noqa: F401

            available["onnx"] = True
        except ImportError:
            try:
                import rapidocr_onnxruntime  # noqa: F401

                available["onnx"] = True
            except ImportError:
                available["onnx"] = False

        # Check OpenVINO
        try:
            import openvino  # noqa: F401

            available["openvino"] = True
        except ImportError:
            try:
                import rapidocr_openvino  # noqa: F401

                available["openvino"] = True
            except ImportError:
                available["openvino"] = False

        # Check PyTorch & Transformers
        try:
            import torch  # noqa: F401

            available["torch"] = True
        except ImportError:
            available["torch"] = False

        try:
            import transformers  # noqa: F401

            available["transformers"] = True
        except ImportError:
            available["transformers"] = False

        return available

    @classmethod
    def inspect_system(cls) -> SystemCapabilities:
        """Inspect host environment and return system capabilities."""
        has_gpu, gpu_name = cls.detect_gpu()
        runtimes = cls.detect_runtimes()

        return SystemCapabilities(
            has_gpu=has_gpu,
            gpu_name=gpu_name,
            has_paddle=runtimes["paddle"],
            has_onnx=runtimes["onnx"],
            has_openvino=runtimes["openvino"],
            has_torch=runtimes["torch"],
            has_transformers=runtimes["transformers"],
        )

    @classmethod
    def resolve_configuration(cls, config: OCRConfig) -> ResolvedRuntimeConfig:
        """Resolve requested OCRConfig into explicit hardware device and independent runtimes.

        Raises:
            GPUUnavailableError: If GPU was requested but no GPU is available.
            UnsupportedRuntimeError: If explicit requested runtime or package is missing.
        """
        has_gpu, gpu_name = cls.detect_gpu()
        runtimes = cls.detect_runtimes()

        # 1. Resolve Device (GPU vs CPU)
        resolved_device: DeviceType
        if config.device == DeviceType.GPU:
            if not has_gpu:
                raise GPUUnavailableError(
                    "DeviceType.GPU was explicitly requested, but no usable CUDA or GPU backend was detected."
                )
            resolved_device = DeviceType.GPU
        elif config.device == DeviceType.CPU:
            resolved_device = DeviceType.CPU
        else:  # AUTO
            resolved_device = DeviceType.GPU if has_gpu else DeviceType.CPU

        # Handle legacy runtime config override if detection_runtime is AUTO
        det_runtime_req = config.detection_runtime
        if det_runtime_req == DetectionRuntime.AUTO and config.runtime != OCRRuntime.AUTO:
            det_runtime_req = DetectionRuntime(config.runtime.value)

        # 2. Resolve Detection Runtime
        resolved_det_runtime: DetectionRuntime
        if det_runtime_req != DetectionRuntime.AUTO:
            if not runtimes.get(det_runtime_req.value, False):
                raise UnsupportedRuntimeError(
                    f"Detection runtime '{det_runtime_req.value}' was requested, but required dependencies are not installed."
                )
            resolved_det_runtime = det_runtime_req
        else:  # AUTO
            if runtimes.get("paddle", False):
                resolved_det_runtime = DetectionRuntime.PADDLE
            elif runtimes.get("onnx", False):
                resolved_det_runtime = DetectionRuntime.ONNX
            elif runtimes.get("openvino", False):
                resolved_det_runtime = DetectionRuntime.OPENVINO
            else:
                raise UnsupportedRuntimeError(
                    "No supported text detection engine (paddle, onnx, openvino) is installed."
                )

        # 3. Resolve Recognition Runtime
        resolved_rec_runtime: RecognitionRuntime
        if config.recognizer_backend == RecognizerBackend.TROCR:
            # TrOCR requires PyTorch and Transformers
            if not (runtimes.get("torch", False) and runtimes.get("transformers", False)):
                raise UnsupportedRuntimeError(
                    "TrOCR recognition backend requested, but PyTorch ('torch') or HuggingFace ('transformers') is not installed."
                )
            resolved_rec_runtime = RecognitionRuntime.PYTORCH
        else:
            # Paddle or other recognizer
            if config.recognition_runtime != RecognitionRuntime.AUTO:
                resolved_rec_runtime = config.recognition_runtime
            elif runtimes.get("paddle", False):
                resolved_rec_runtime = RecognitionRuntime.PADDLE
            elif runtimes.get("onnx", False):
                resolved_rec_runtime = RecognitionRuntime.ONNX
            else:
                resolved_rec_runtime = RecognitionRuntime.PADDLE

        logger.info(
            f"Resolved OCR Runtime Configuration: device={resolved_device.value} (gpu={gpu_name or 'N/A'}), "
            f"detection_runtime={resolved_det_runtime.value}, recognition_runtime={resolved_rec_runtime.value}"
        )

        return ResolvedRuntimeConfig(
            device=resolved_device,
            detection_runtime=resolved_det_runtime,
            recognition_runtime=resolved_rec_runtime,
            gpu_name=gpu_name if resolved_device == DeviceType.GPU else None,
        )
