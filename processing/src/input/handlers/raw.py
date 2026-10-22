"""Smartphone RAW / DNG input handler."""

from pathlib import Path
from typing import Any, Iterator
import cv2
import numpy as np
from PIL import Image

from processing.converter.dng import dng_to_numpy
from processing.converter.image import is_raw_format
from processing.input.exceptions import CorruptDocumentError
from processing.input.handlers.base import BaseInputHandler
from processing.input.models import PageInput


class RawDngHandler(BaseInputHandler):
    """Handles smartphone RAW/DNG captures (DNG, RAW, CR2, NEF, ARW, etc.)."""

    def can_handle(self, source: Any) -> bool:
        return is_raw_format(source)

    def extract_pages(self, source: Any, **kwargs: Any) -> Iterator[PageInput]:
        source_path = str(source) if isinstance(source, (str, Path)) else None
        try:
            # Decode using rawpy via Mulberry converter
            bgr_arr = dng_to_numpy(source, output_bgr=True)
            rgb_arr = cv2.cvtColor(bgr_arr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_arr)
        except Exception as e:
            raise CorruptDocumentError(f"Failed to decode RAW/DNG source: {e}", original_exception=e) from e

        h, w = bgr_arr.shape[:2]

        yield PageInput(
            page_number=1,
            total_pages=1,
            image_bgr=bgr_arr,
            pil_image=pil_img,
            width=w,
            height=h,
            media_type="image/x-adobe-dng",
            source_file=source_path,
            dpi=kwargs.get("dpi", 300),
        )
