"""Exceptions for the Input & Page Splitter module."""

from typing import Optional


class InputProcessingError(Exception):
    """Base exception for input ingestion and page splitting errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.original_exception = original_exception


class UnsupportedInputFormatError(InputProcessingError):
    """Raised when an unrecognized or unsupported media format is supplied."""
    pass


class CorruptDocumentError(InputProcessingError):
    """Raised when an image or PDF document is malformed or unreadable."""
    pass
