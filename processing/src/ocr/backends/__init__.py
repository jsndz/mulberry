"""OCR model backends for text detection, recognition, and orientation classification."""

from processing.ocr.backends.detectors.base import BaseTextDetector
from processing.ocr.backends.detectors.paddle import PaddleTextDetector
from processing.ocr.backends.recognizers.base import BaseTextRecognizer, TextResult
from processing.ocr.backends.recognizers.paddle import PaddleTextRecognizer
from processing.ocr.backends.recognizers.trocr import TrOCRTextRecognizer
from processing.ocr.backends.orientation.base import BaseOrientationClassifier
from processing.ocr.backends.orientation.paddle import PaddleOrientationClassifier

__all__ = [
    "BaseTextDetector",
    "PaddleTextDetector",
    "BaseTextRecognizer",
    "TextResult",
    "PaddleTextRecognizer",
    "TrOCRTextRecognizer",
    "BaseOrientationClassifier",
    "PaddleOrientationClassifier",
]
