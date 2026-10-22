"""Abstract base interface for format-specific input handlers."""

from abc import ABC, abstractmethod
from typing import Any, Iterator
from processing.input.models import PageInput


class BaseInputHandler(ABC):
    """Abstract interface defining ingestion and page splitting for a category of input."""

    @abstractmethod
    def can_handle(self, source: Any) -> bool:
        """Return True if this handler can process the given input source."""
        pass

    @abstractmethod
    def extract_pages(self, source: Any, **kwargs: Any) -> Iterator[PageInput]:
        """
        Extract and yield normalized PageInput objects one by one.

        Yields:
            PageInput instances in reading/page order.
        """
        pass
