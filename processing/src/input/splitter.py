"""Unified document input dispatcher and streaming page splitter."""

from pathlib import Path
from typing import Any, Iterator, List, Optional, Union
import numpy as np
from PIL import Image

from processing.input.exceptions import UnsupportedInputFormatError
from processing.input.handlers.base import BaseInputHandler
from processing.input.handlers.image import RasterImageHandler
from processing.input.handlers.pdf import PdfHandler
from processing.input.handlers.raw import RawDngHandler
from processing.input.models import PageInput


class DocumentInputSplitter:
    """
    Unified dispatcher that ingests diverse media types (Raster images, RAW/DNG, PDFs, in-memory)
    and splits/normalizes them into a streaming sequence of PageInput objects.
    """

    def __init__(self, handlers: Optional[List[BaseInputHandler]] = None) -> None:
        self.handlers = handlers or [
            RawDngHandler(),
            PdfHandler(),
            RasterImageHandler(),
        ]

    def get_handler_for_source(self, source: Any) -> BaseInputHandler:
        """Find the registered handler that can process the given input."""
        for handler in self.handlers:
            if handler.can_handle(source):
                return handler
        raise UnsupportedInputFormatError(f"No suitable input handler found for source: {type(source)} ({source})")

    def split(
        self,
        source: Union[str, Path, bytes, Image.Image, np.ndarray, List[Any]],
        dpi: int = 300,
        **kwargs: Any,
    ) -> Iterator[PageInput]:
        """
        Extract and yield normalized PageInput objects from single files, streams, or multi-item batches.

        Yields:
            PageInput instances representing individual pages.
        """
        # Handle batch of inputs (e.g. list of image paths or array of images)
        if isinstance(source, (list, tuple)) and not isinstance(source, (bytes, memoryview)):
            total_items = len(source)
            page_counter = 1
            for item in source:
                handler = self.get_handler_for_source(item)
                for page in handler.extract_pages(item, dpi=dpi, **kwargs):
                    # Re-index for continuous multi-page sequence
                    yield PageInput(
                        page_number=page_counter,
                        total_pages=total_items,
                        image_bgr=page.image_bgr,
                        pil_image=page.pil_image,
                        width=page.width,
                        height=page.height,
                        media_type=page.media_type,
                        source_file=page.source_file,
                        dpi=page.dpi,
                        metadata=page.metadata,
                    )
                    page_counter += 1
            return

        # Single file, stream, or in-memory object
        handler = self.get_handler_for_source(source)
        yield from handler.extract_pages(source, dpi=dpi, **kwargs)
