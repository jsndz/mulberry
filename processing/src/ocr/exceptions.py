"""Actionable custom exceptions for Mulberry OCR module."""


class OCRError(Exception):
    """Base exception for all Mulberry OCR errors."""

    pass


class MissingModelError(OCRError):
    """Raised when an OCR model asset file or directory is missing or corrupt."""

    pass


class UnsupportedRuntimeError(OCRError):
    """Raised when a requested inference runtime (paddle, onnx, openvino) is unavailable."""

    pass


class GPUUnavailableError(OCRError):
    """Raised when GPU device is explicitly requested but CUDA/GPU acceleration is unavailable."""

    pass


class InvalidImageError(OCRError):
    """Raised when the input image is invalid, corrupted, empty, or unreadable."""

    pass


class OCRInitializationError(OCRError):
    """Raised when the OCR backend fails to initialize."""

    pass
