"""Hardware capabilities detection and inference runtime selection."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple, List

from processing.ocr.config import DeviceType, OCRConfig, OCRRuntime
from processing.ocr.exceptions import GPUUnavailableError, UnsupportedRuntimeError

logger = logging.getLogger(__name__)


@dataclass
class SystemCapabilities:
    """Discovered system hardware and runtime capabilities."""

    has_gpu: bool
    gpu_name: Optional[str]
    installed_runtimes: List[OCRRuntime]


class RuntimeSelector:
    """Hardware and runtime selection layer.

    Keeps device/runtime capabilities detection decoupled from OCR inference logic.
    """

    @staticmethod
    def detect_gpu() -> Tuple[bool, Optional[str]]:
        """Detect whether usable GPU acceleration is available."""
        # 1. Check PaddlePaddle CUDA support
        try:
            import paddle

            if hasattr(paddle, "is_compiled_with_cuda") and paddle.is_compiled_with_cuda():
                gpu_count = paddle.device.cuda.device_count() if hasattr(paddle.device, "cuda") else 0
                if gpu_count > 0 or paddle.is_compiled_with_cuda():
                    return True, "NVIDIA CUDA (Paddle)"
        except Exception:
            pass

        # 2. Check ONNX Runtime GPU Execution Providers
        try:
            import onnxruntime as ort

            providers = ort.get_available_providers()
            if "CUDAExecutionProvider" in providers or "ROCMExecutionProvider" in providers:
                return True, f"ONNX Runtime Provider ({providers[0]})"
        except Exception:
            pass

        # 3. Check PyTorch CUDA
        try:
            import torch

            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "CUDA GPU"
                return True, f"PyTorch CUDA ({name})"
        except Exception:
            pass

        return False, None

    @staticmethod
    def detect_runtimes() -> Dict[OCRRuntime, bool]:
        """Detect which inference backends are installed and available."""
        available: Dict[OCRRuntime, bool] = {
            OCRRuntime.PADDLE: False,
            OCRRuntime.ONNX: False,
            OCRRuntime.OPENVINO: False,
        }

        # Check Paddle
        try:
            import paddle  # noqa: F401
            import paddleocr  # noqa: F401

            available[OCRRuntime.PADDLE] = True
        except ImportError:
            available[OCRRuntime.PADDLE] = False

        # Check ONNX Runtime
        try:
            import onnxruntime  # noqa: F401
            available[OCRRuntime.ONNX] = True
        except ImportError:
            try:
                import rapidocr_onnxruntime  # noqa: F401
                available[OCRRuntime.ONNX] = True
            except ImportError:
                available[OCRRuntime.ONNX] = False

        # Check OpenVINO
        try:
            import openvino  # noqa: F401
            available[OCRRuntime.OPENVINO] = True
        except ImportError:
            try:
                import rapidocr_openvino  # noqa: F401
                available[OCRRuntime.OPENVINO] = True
            except ImportError:
                available[OCRRuntime.OPENVINO] = False

        return available

    @classmethod
    def inspect_system(cls) -> SystemCapabilities:
        """Inspect the host environment and return full system capabilities."""
        has_gpu, gpu_name = cls.detect_gpu()
        runtime_dict = cls.detect_runtimes()
        installed_runtimes = [rt for rt, is_avail in runtime_dict.items() if is_avail]

        return SystemCapabilities(
            has_gpu=has_gpu,
            gpu_name=gpu_name,
            installed_runtimes=installed_runtimes,
        )

    @classmethod
    def resolve_configuration(
        cls, config: OCRConfig
    ) -> Tuple[DeviceType, OCRRuntime, Optional[str]]:
        """Resolve requested OCRConfig (including 'auto' parameters) into explicit device and runtime.

        Raises:
            GPUUnavailableError: If GPU was requested but no GPU is available.
            UnsupportedRuntimeError: If explicit runtime requested is not installed.
        """
        has_gpu, gpu_name = cls.detect_gpu()
        runtimes = cls.detect_runtimes()

        # 1. Resolve Device
        resolved_device: DeviceType
        if config.device == DeviceType.GPU:
            if not has_gpu:
                raise GPUUnavailableError(
                    "DeviceType.GPU was requested, but no usable CUDA or GPU backend was detected."
                )
            resolved_device = DeviceType.GPU
        elif config.device == DeviceType.CPU:
            resolved_device = DeviceType.CPU
        else:  # AUTO
            resolved_device = DeviceType.GPU if has_gpu else DeviceType.CPU

        # 2. Resolve Runtime
        resolved_runtime: OCRRuntime
        if config.runtime != OCRRuntime.AUTO:
            if not runtimes.get(config.runtime, False):
                raise UnsupportedRuntimeError(
                    f"Inference runtime '{config.runtime.value}' was requested, but required package dependencies are not installed."
                )
            resolved_runtime = config.runtime
        else:  # AUTO
            # Preference order: ONNX (for reliable CPU/GPU performance) -> PADDLE -> OPENVINO
            if runtimes.get(OCRRuntime.ONNX, False):
                resolved_runtime = OCRRuntime.ONNX
            elif runtimes.get(OCRRuntime.PADDLE, False):
                resolved_runtime = OCRRuntime.PADDLE
            elif runtimes.get(OCRRuntime.OPENVINO, False):
                resolved_runtime = OCRRuntime.OPENVINO
            else:
                raise UnsupportedRuntimeError(
                    "No supported OCR runtime (onnx, paddle, openvino) is installed in the environment."
                )

        logger.info(
            f"Resolved OCR hardware configuration: device={resolved_device.value} (gpu_name={gpu_name}), "
            f"runtime={resolved_runtime.value}"
        )
        return resolved_device, resolved_runtime, gpu_name
