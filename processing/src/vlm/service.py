"""Public VLM Service interface for the Mulberry document processing engine."""

from pathlib import Path
from typing import Any, Optional, Union
from PIL import Image

from processing.canonical.document import Document
from processing.vlm.config import VLMConfig
from processing.vlm.exceptions import InvalidImageError
from processing.vlm.model import VLMModelManager
from processing.vlm.processor import VLMOutputProcessor
from processing.vlm.prompts import VLM_SYSTEM_PROMPT, VLM_USER_PROMPT
from processing.vlm.schemas import VLMStructuredOutput


class VLMService:
    """High-level service providing handwritten document understanding using Qwen3-VL.

    Usage:
        ```python
        from processing.vlm.service import VLMService

        vlm = VLMService()
        doc = vlm.process("path/to/handwritten_note.jpg")
        print(doc.model_dump_json(indent=2))
        ```
    """

    def __init__(
        self,
        config: Optional[VLMConfig] = None,
        model_manager: Optional[VLMModelManager] = None,
        processor: Optional[VLMOutputProcessor] = None,
    ) -> None:
        self.config = config or VLMConfig()
        self.model_manager = model_manager or VLMModelManager.get_singleton(self.config)
        self.processor = processor or VLMOutputProcessor()

    @property
    def is_loaded(self) -> bool:
        """Check whether the underlying model is loaded."""
        return self.model_manager.is_loaded

    def load(self) -> None:
        """Explicitly load model weights into memory."""
        self.model_manager.load()

    def _load_and_validate_image(
        self, image_input: Union[str, Path, Image.Image]
    ) -> tuple[Image.Image, Optional[str]]:
        """Validate and load image from PIL Image or filesystem path."""
        source_path: Optional[str] = None

        if isinstance(image_input, (str, Path)):
            path = Path(image_input).resolve()
            if not path.exists():
                raise InvalidImageError(f"Image file not found at path: '{path}'")
            if not path.is_file():
                raise InvalidImageError(f"Path is not a regular file: '{path}'")

            source_path = str(path)
            try:
                pil_img = Image.open(path)
                pil_img.load()  # Ensure image data is read from disk
                pil_img = pil_img.convert("RGB")
            except Exception as e:
                raise InvalidImageError(
                    f"Failed to open/decode image file at '{path}': {e}",
                    original_exception=e,
                ) from e

        elif isinstance(image_input, Image.Image):
            try:
                pil_img = image_input.convert("RGB")
            except Exception as e:
                raise InvalidImageError(
                    f"Failed to convert PIL Image to RGB: {e}",
                    original_exception=e,
                ) from e
        else:
            raise InvalidImageError(
                f"Unsupported image input type: {type(image_input).__name__}. Expected PIL.Image, str, or Path."
            )

        if pil_img.width <= 0 or pil_img.height <= 0:
            raise InvalidImageError(
                f"Invalid image dimensions: {pil_img.width}x{pil_img.height}. Dimensions must be > 0."
            )

        return pil_img, source_path

    def process_structured(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **gen_kwargs: Any,
    ) -> VLMStructuredOutput:
        """Run VLM analysis on an image and return the intermediate validated VLMStructuredOutput."""
        pil_img, _ = self._load_and_validate_image(image)

        active_prompt = prompt or VLM_USER_PROMPT
        active_system_prompt = system_prompt or VLM_SYSTEM_PROMPT

        raw_output = self.model_manager.generate(
            image=pil_img,
            prompt=active_prompt,
            system_prompt=active_system_prompt,
            **gen_kwargs,
        )

        return self.processor.parse_and_validate(raw_output)

    def process(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        system_prompt: Optional[str] = None,
        doc_id: Optional[str] = None,
        **gen_kwargs: Any,
    ) -> Document:
        """Process a handwritten image and return a canonical Mulberry Document."""
        pil_img, source_file = self._load_and_validate_image(image)
        width, height = float(pil_img.width), float(pil_img.height)

        structured_output = self.process_structured(
            image=pil_img,
            prompt=prompt,
            system_prompt=system_prompt,
            **gen_kwargs,
        )

        return structured_output.to_canonical_document(
            width=width,
            height=height,
            doc_id=doc_id,
            source_file=source_file,
        )
