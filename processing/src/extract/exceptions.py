"""Custom exceptions for the Mulberry HCD-HTR extraction pipeline."""

from typing import Optional


class ExtractionError(Exception):
    """Base exception for all extraction-related errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class PreprocessingError(ExtractionError):
    """Raised when document conditioning, perspective dewarp, or CLAHE fails."""
    pass


class GeometryError(ExtractionError):
    """Raised when layout segmentation or line polygon detection fails."""
    pass


class ContextError(ExtractionError):
    """Raised when SQLite context lookup or scout topic inferencing fails."""
    pass


class RecognitionError(ExtractionError):
    """Raised when line recognition or VLM inference fails."""
    pass


class AssemblyError(ExtractionError):
    """Raised when structural alignment, block assembly, or schema export fails."""
    pass
