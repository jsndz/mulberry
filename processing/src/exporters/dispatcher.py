"""Unified dispatcher and factory for document exporters."""

from pathlib import Path
from typing import Any, Dict, Optional, Type, Union

from processing.canonical.document import Document
from processing.exporters.base import BaseExporter
from processing.exporters.markdown import MarkdownExporter
from processing.exporters.options import MarkdownExportOptions, PdfExportOptions
from processing.exporters.pdf import PdfExporter

EXPORTER_REGISTRY: Dict[str, Type[BaseExporter[Any]]] = {
    "markdown": MarkdownExporter,
    "md": MarkdownExporter,
    "pdf": PdfExporter,
}


def get_exporter(format_name: str) -> BaseExporter[Any]:
    """Retrieve an exporter instance for the requested format name."""
    fmt = format_name.lower().strip()
    if fmt not in EXPORTER_REGISTRY:
        supported = ", ".join(sorted(set(EXPORTER_REGISTRY.keys())))
        raise ValueError(f"Unsupported export format '{format_name}'. Supported formats: {supported}")
    return EXPORTER_REGISTRY[fmt]()


def export_document(
    document: Document,
    format: str = "markdown",
    output_path: Optional[Union[str, Path]] = None,
    options: Optional[Union[MarkdownExportOptions, PdfExportOptions]] = None,
    **kwargs: Any,
) -> Union[str, bytes]:
    """Export a Canonical Document to the requested format.

    Args:
        document: Canonical Document instance.
        format: Target format ('markdown', 'md', 'pdf').
        output_path: Optional file path to write exported output.
        options: Optional typed export options.
        **kwargs: Arbitrary keyword arguments passed to options model if options is None.

    Returns:
        str for Markdown, bytes for PDF.
    """
    fmt = format.lower().strip()
    exporter = get_exporter(fmt)

    # Resolve options if kwargs provided and options is None
    if options is None and kwargs:
        if fmt in ("markdown", "md"):
            options = MarkdownExportOptions(**kwargs)
        elif fmt == "pdf":
            options = PdfExportOptions(**kwargs)

    return exporter.export(document, output_path=output_path, options=options)
