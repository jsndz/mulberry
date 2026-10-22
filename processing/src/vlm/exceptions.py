"""Exceptions for the Mulberry VLM (Vision-Language Model) processing module."""


class VLMError(Exception):
    """Base exception for all VLM-related failures."""

    def __init__(self, message: str, original_exception: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_exception = original_exception

    def __str__(self) -> str:
        if self.original_exception is not None:
            return f"{self.message} (Caused by: {type(self.original_exception).__name__}: {self.original_exception})"
        return self.message


class ModelLoadError(VLMError):
    """Raised when the VLM model or processor weights fail to load or initialize."""
    pass


class InvalidImageError(VLMError):
    """Raised when the input image is invalid, corrupt, unreadable, or missing."""
    pass


class InferenceError(VLMError):
    """Raised when VLM model generation/inference fails (e.g., CUDA OOM, runtime failure)."""
    pass


class MalformedOutputError(VLMError):
    """Raised when the model output cannot be parsed as valid JSON or formatted content."""
    pass


class SchemaValidationError(VLMError):
    """Raised when parsed VLM output does not satisfy the structured canonical schema."""
    pass
