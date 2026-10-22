"""Base exporter interface and abstract contracts."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Optional, TypeVar, Union

from processing.canonical.document import Document

TOptions = TypeVar("TOptions")


class BaseExporter(ABC, Generic[TOptions]):
    """Abstract base class for all canonical Document exporters."""

    @abstractmethod
    def export(
        self,
        document: Document,
        output_path: Optional[Union[str, Path]] = None,
        options: Optional[TOptions] = None,
    ) -> Union[str, bytes]:
        """Export a canonical Document to a target file path or in-memory format.

        Args:
            document: Canonical Document model instance.
            output_path: Optional destination file path. If None, returns in-memory result.
            options: Optional format-specific export options.

        Returns:
            str for text-based exporters (Markdown, HTML), bytes for binary (PDF).
        """
        pass

    def _write_output(self, content: Union[str, bytes], output_path: Union[str, Path]) -> None:
        """Helper to write string or binary output to disk, creating parent directories if needed."""
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            dest.write_text(content, encoding="utf-8")
        else:
            dest.write_bytes(content)
