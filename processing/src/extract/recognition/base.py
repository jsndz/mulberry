"""Abstract line recognition interface."""

from abc import ABC, abstractmethod
from typing import List, Optional
from PIL import Image


class BaseLineRecognizer(ABC):
    """Abstract interface for line strip transcription engines."""

    @abstractmethod
    def transcribe_line(
        self,
        crop_pil: Image.Image,
        domain_glossary: Optional[List[str]] = None,
    ) -> str:
        """Transcribe text from a single line strip conditioned on the glossary."""
        pass

    def batch_transcribe(
        self,
        crops: List[Image.Image],
        domain_glossary: Optional[List[str]] = None,
    ) -> List[str]:
        """Transcribe a batch of line strips."""
        return [self.transcribe_line(c, domain_glossary=domain_glossary) for c in crops]
