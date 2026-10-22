"""TrOCR and lightweight OCR fallback recognition engine."""

import logging
from typing import List, Optional
from PIL import Image

from processing.extract.recognition.base import BaseLineRecognizer

logger = logging.getLogger("mulberry.extract.recognition.trocr")


class TrOCRRecognizer(BaseLineRecognizer):
    """
    Tier 2 / Tier 3 Line Recognizer leveraging Mulberry's TrOCRTextRecognizer backend.
    """

    def __init__(self, model_name: str = "microsoft/trocr-base-handwritten") -> None:
        self.model_name = model_name
        self._recognizer = None
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            from processing.ocr.config import DeviceType, OCRConfig
            from processing.ocr.backends.recognizers.trocr import TrOCRTextRecognizer

            config = OCRConfig(trocr_model_name=self.model_name)
            self._recognizer = TrOCRTextRecognizer(config=config, device=DeviceType.AUTO)
            self._loaded = True
        except Exception as e:
            logger.warning(f"Could not load TrOCR backend: {e}")
            self._loaded = False

    def transcribe_line(
        self,
        crop_pil: Image.Image,
        domain_glossary: Optional[List[str]] = None,
    ) -> str:
        self._ensure_loaded()
        if not self._loaded or self._recognizer is None:
            return ""

        try:
            import cv2
            import numpy as np

            rgb = np.array(crop_pil.convert("RGB"))
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            result = self._recognizer.recognize_crop(bgr)
            return result.text.strip()
        except Exception as e:
            logger.error(f"TrOCR recognition failed: {e}")
            return ""
