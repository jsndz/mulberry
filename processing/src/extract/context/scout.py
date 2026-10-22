"""Macro Scout Sweep on top canvas region for fast subject and glossary inference."""

from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image

from processing.extract.context.retriever import ContextRetriever


class MacroScoutSweep:
    """
    Executes a fast visual sweep over the top portion of the document (default 25%)
    to detect header anchors, infer the subject topic, and inject the matching domain lexicon.
    """

    def __init__(
        self,
        retriever: Optional[ContextRetriever] = None,
        scout_ratio: float = 0.25,
    ) -> None:
        self.retriever = retriever or ContextRetriever()
        self.scout_ratio = scout_ratio

    def crop_scout_region(self, canvas: np.ndarray) -> np.ndarray:
        """Crops the top scout portion of the canvas."""
        h = canvas.shape[0]
        scout_h = max(10, int(h * self.scout_ratio))
        return canvas[0:scout_h, :]

    def analyze_scout_crop(
        self,
        crop: np.ndarray,
        ocr_text_hint: Optional[str] = None,
        author_id: Optional[str] = None,
        manual_glossary: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Infers subject / topic from header anchors and retrieves dynamic lexicon from Context DB.

        Returns:
            Dict containing:
            - 'detected_topic': str or None
            - 'glossary': List[str]
            - 'glossary_string': str
            - 'homoglyph_rules': Dict[str, str]
        """
        # Resolve context using header text hint
        context = self.retriever.resolve_context(
            inferred_topic_or_text=ocr_text_hint,
            author_id=author_id,
            manual_glossary=manual_glossary,
        )

        return context
