"""Qwen2.5-VL Vision-Language line recognition engine with glossary conditioning."""

import logging
from typing import Any, List, Optional
from PIL import Image

from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.recognition.prompt import SYSTEM_PROMPT, format_recognition_prompt
from processing.vlm.config import VLMConfig
from processing.vlm.model import VLMModelManager

logger = logging.getLogger("mulberry.extract.recognition.vlm")


class QwenVLRecognizer(BaseLineRecognizer):
    """
    Tier 1 Recognition Engine: Qwen2.5-VL with FlashAttention-2, bfloat16,
    greedy decoding (temp=0.0), and technical glossary prompt conditioning.
    """

    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-VL-7B-Instruct",
        device: Optional[str] = None,
        model_manager: Optional[VLMModelManager] = None,
    ) -> None:
        self.model_name = model_name
        self.config = VLMConfig(
            model_name=model_name,
            device=device,
            temperature=0.0,
            do_sample=False,
            max_new_tokens=128,
        )
        self.model_manager = model_manager or VLMModelManager(self.config)

    def transcribe_line(
        self,
        crop_pil: Image.Image,
        domain_glossary: Optional[List[str]] = None,
    ) -> str:
        prompt = format_recognition_prompt(domain_glossary)

        # Cap max crop dimensions to prevent visual token explosion in VRAM
        max_dim = 1024
        if max(crop_pil.size) > max_dim:
            scale = max_dim / max(crop_pil.size)
            new_size = (max(1, int(crop_pil.size[0] * scale)), max(1, int(crop_pil.size[1] * scale)))
            crop_pil = crop_pil.resize(new_size, Image.Resampling.BILINEAR)

        try:
            output = self.model_manager.generate(
                image=crop_pil,
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
                temperature=0.0,
                do_sample=False,
                max_new_tokens=128,
            )
            return output.strip()
        except Exception as e:
            logger.error(f"VLM line transcription failed: {e}")
            return ""
