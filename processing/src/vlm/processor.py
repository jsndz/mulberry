"""Text and multimodal input/output processing for Mulberry VLM module."""

import json
import re
from typing import Any, Dict, List, Optional
from PIL import Image
from pydantic import ValidationError

from processing.vlm.exceptions import MalformedOutputError, SchemaValidationError
from processing.vlm.schemas import VLMStructuredOutput


class VLMOutputProcessor:
    """Handles prompt construction, raw model output cleanup, JSON extraction, and schema validation."""

    @staticmethod
    def prepare_messages(
        image: Image.Image,
        prompt: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Construct standard Qwen multimodal conversation messages."""
        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        user_content: List[Dict[str, Any]] = [
            {"type": "image", "image": image},
            {"type": "text", "text": prompt},
        ]
        messages.append({"role": "user", "content": user_content})
        return messages

    @staticmethod
    def extract_json_string(raw_text: str) -> str:
        """Extract valid JSON string from raw model generation, handling markdown blocks and thinking tokens."""
        text = raw_text.strip()

        # 1. Remove <think>...</think> reasoning traces if present
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        # 2. Extract content from ```json ... ``` or ``` ... ``` markdown fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, flags=re.IGNORECASE)
        if fence_match:
            return fence_match.group(1).strip()

        # 3. Locate the outermost curly braces { ... }
        start_idx = text.find("{")
        end_idx = text.rfind("}")
        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            return text[start_idx : end_idx + 1].strip()

        return text

    def parse_and_validate(self, raw_output: str) -> VLMStructuredOutput:
        """Parse raw model output text and validate it against the canonical VLM schema.

        Raises:
            MalformedOutputError: If JSON syntax is invalid.
            SchemaValidationError: If JSON data fails Pydantic schema validation.
        """
        json_str = self.extract_json_string(raw_output)

        try:
            parsed_data = json.loads(json_str)
        except Exception as e:
            raise MalformedOutputError(
                f"Failed to parse VLM output as JSON: {raw_output[:200]}...",
                original_exception=e,
            ) from e

        if not isinstance(parsed_data, dict):
            raise MalformedOutputError(
                f"Expected JSON object at top level, got {type(parsed_data).__name__}"
            )

        try:
            return VLMStructuredOutput.model_validate(parsed_data)
        except ValidationError as e:
            raise SchemaValidationError(
                f"VLM structured output failed schema validation: {e}",
                original_exception=e,
            ) from e
