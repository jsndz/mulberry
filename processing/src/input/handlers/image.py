"""Raster image input handler for standard image formats and in-memory arrays."""

import io
from pathlib import Path
from typing import Any, Iterator, Union
import cv2
import numpy as np
from PIL import Image

from processing.input.exceptions import CorruptDocumentError
from processing.input.handlers.base import BaseInputHandler
from processing.input.models import PageInput

SUPPORTED_RASTER_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".webp", ".tiff", ".tif", ".bmp"
}


class RasterImageHandler(BaseInputHandler):
    """Handles standard raster formats (PNG, JPEG, WebP, TIFF, BMP, NumPy, PIL)."""

    def can_handle(self, source: Any) -> bool:
        if isinstance(source, (Image.Image, np.ndarray)):
            return True
        if isinstance(source, (str, Path)):
            ext = Path(source).suffix.lower()
            return ext in SUPPORTED_RASTER_EXTENSIONS
        if isinstance(source, (bytes, memoryview)):
            # Check magic bytes for JPEG, PNG, WEBP, BMP, TIFF
            b = bytes(source[:12])
            if b.startswith(b"\xff\xd8\xff"):  # JPEG
                return True
            if b.startswith(b"\x89PNG\r\n\x1a\n"):  # PNG
                return True
            if b.startswith(b"RIFF") and b[8:12] == b"WEBP":  # WEBP
                return True
            if b.startswith(b"BM"):  # BMP
                return True
            if b.startswith((b"II*\x00", b"MM\x00*")):  # TIFF (non-DNG)
                return True
        return False

    def extract_pages(self, source: Any, **kwargs: Any) -> Iterator[PageInput]:
        source_path = None
        media_type = "image/png"

        if isinstance(source, (str, Path)):
            p = Path(source).resolve()
            if not p.exists():
                raise FileNotFoundError(f"Image file not found: {p}")
            source_path = str(p)
            ext = p.suffix.lower().lstrip(".")
            media_type = f"image/{'jpeg' if ext in ('jpg', 'jpeg') else ext}"
            try:
                pil_img = Image.open(p).convert("RGB")
            except Exception as e:
                raise CorruptDocumentError(f"Could not open image file '{p}': {e}", original_exception=e) from e

        elif isinstance(source, Image.Image):
            pil_img = source.convert("RGB")
        elif isinstance(source, np.ndarray):
            if source.ndim == 2:
                bgr = cv2.cvtColor(source, cv2.COLOR_GRAY2BGR)
                rgb = cv2.cvtColor(source, cv2.COLOR_GRAY2RGB)
            elif source.shape[2] == 4:
                bgr = cv2.cvtColor(source, cv2.COLOR_BGRA2BGR)
                rgb = cv2.cvtColor(source, cv2.COLOR_BGRA2RGB)
            else:
                bgr = source
                rgb = cv2.cvtColor(source, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb)
        elif isinstance(source, (bytes, memoryview)):
            try:
                pil_img = Image.open(io.BytesIO(source)).convert("RGB")
            except Exception as e:
                raise CorruptDocumentError(f"Could not decode image bytes: {e}", original_exception=e) from e
        else:
            raise CorruptDocumentError(f"Unsupported raster image source type: {type(source)}")

        w, h = pil_img.size
        rgb_arr = np.array(pil_img)
        bgr_arr = cv2.cvtColor(rgb_arr, cv2.COLOR_RGB2BGR)

        dpi = kwargs.get("dpi") or pil_img.info.get("dpi", (300, 300))[0]
        if isinstance(dpi, tuple):
            dpi = int(dpi[0])
        elif dpi is not None:
            dpi = int(dpi)

        yield PageInput(
            page_number=1,
            total_pages=1,
            image_bgr=bgr_arr,
            pil_image=pil_img,
            width=w,
            height=h,
            media_type=media_type,
            source_file=source_path,
            dpi=dpi,
        )
