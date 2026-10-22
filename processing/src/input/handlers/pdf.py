"""Multi-page PDF document input handler using Google PDFium."""

import io
from pathlib import Path
from typing import Any, Iterator, Union
import cv2
import numpy as np
from PIL import Image

from processing.input.exceptions import CorruptDocumentError
from processing.input.handlers.base import BaseInputHandler
from processing.input.models import PageInput


class PdfHandler(BaseInputHandler):
    """
    Handles multi-page PDF documents.
    Extracts and rasterizes pages independently at target DPI (default: 300 DPI)
    without loading entire multi-page document pixel buffers into memory simultaneously.
    """

    def can_handle(self, source: Any) -> bool:
        if isinstance(source, (str, Path)):
            return Path(source).suffix.lower() == ".pdf"
        if isinstance(source, (bytes, memoryview)):
            return bytes(source[:5]) == b"%PDF-"
        return False

    def extract_pages(self, source: Any, **kwargs: Any) -> Iterator[PageInput]:
        try:
            import pypdfium2 as pdfium
        except ImportError as e:
            raise ImportError(
                "pypdfium2 is required for PDF ingestion. Install with: uv add pypdfium2"
            ) from e

        source_path = None
        pdf_doc = None

        try:
            if isinstance(source, (str, Path)):
                p = Path(source).resolve()
                if not p.exists():
                    raise FileNotFoundError(f"PDF file not found: {p}")
                source_path = str(p)
                pdf_doc = pdfium.PdfDocument(p)
            elif isinstance(source, (bytes, memoryview)):
                pdf_doc = pdfium.PdfDocument(io.BytesIO(source))
            else:
                raise CorruptDocumentError(f"Unsupported PDF source type: {type(source)}")

            total_pages = len(pdf_doc)
            target_dpi = int(kwargs.get("dpi", 300))
            # Standard PDF resolution is 72 pt/inch
            scale = target_dpi / 72.0

            for idx in range(total_pages):
                page = pdf_doc.get_page(idx)
                # Render page at high DPI to preserve handwriting strokes
                rendered = page.render(scale=scale)
                pil_img = rendered.to_pil().convert("RGB")
                page.close()

                w, h = pil_img.size
                rgb_arr = np.array(pil_img)
                bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

                yield PageInput(
                    page_number=idx + 1,
                    total_pages=total_pages,
                    image_bgr=bgr_arr,
                    pil_image=pil_img,
                    width=w,
                    height=h,
                    media_type="application/pdf",
                    source_file=source_path,
                    dpi=target_dpi,
                    metadata={"original_page_number": idx + 1},
                )

        except Exception as e:
            if not isinstance(e, (FileNotFoundError, CorruptDocumentError)):
                raise CorruptDocumentError(f"Failed to process PDF document: {e}", original_exception=e) from e
            raise
        finally:
            if pdf_doc is not None:
                try:
                    pdf_doc.close()
                except Exception:
                    pass
