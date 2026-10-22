"""Context-Conditioned Line Recognition Engine for HCD-HTR."""

from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.recognition.cropper import crop_line_strip
from processing.extract.recognition.prompt import (
    SYSTEM_PROMPT,
    format_recognition_prompt,
)
from processing.extract.recognition.trocr_recognizer import TrOCRRecognizer
from processing.extract.recognition.vlm_recognizer import QwenVLRecognizer

__all__ = [
    "BaseLineRecognizer",
    "crop_line_strip",
    "SYSTEM_PROMPT",
    "format_recognition_prompt",
    "QwenVLRecognizer",
    "TrOCRRecognizer",
]
