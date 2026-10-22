"""Hugging Face model lifecycle management and inference for Mulberry VLM module."""

from typing import Any, Dict, Optional
from PIL import Image
import torch

from processing.vlm.config import VLMConfig
from processing.vlm.exceptions import InferenceError, ModelLoadError
from processing.vlm.runtime import RuntimeInfo, get_runtime_info


class VLMModelManager:
    """Manages lazy-loading, caching, device placement, and token generation for Qwen VL models."""

    _instance: Optional["VLMModelManager"] = None
    _cached_model_name: Optional[str] = None

    def __init__(self, config: Optional[VLMConfig] = None) -> None:
        self.config = config or VLMConfig()
        self.runtime_info: RuntimeInfo = get_runtime_info(
            preferred_device=self.config.device,
            preferred_dtype=self.config.dtype,
        )
        self.model: Any = None
        self.processor: Any = None
        self._is_loaded = False

    @classmethod
    def get_singleton(cls, config: Optional[VLMConfig] = None) -> "VLMModelManager":
        """Get or initialize the shared singleton instance ensuring model is loaded only once."""
        cfg = config or VLMConfig()
        if cls._instance is None or cls._cached_model_name != cfg.model_name:
            cls._instance = cls(cfg)
            cls._cached_model_name = cfg.model_name
        return cls._instance

    @property
    def is_loaded(self) -> bool:
        """Check whether model and processor weights are currently loaded in memory."""
        return self._is_loaded and self.model is not None and self.processor is not None

    def load(self) -> None:
        """Load the VLM model and processor weights once into memory/GPU."""
        if self.is_loaded:
            return

        try:
            from transformers import AutoModelForCausalLM, AutoModelForImageTextToText, AutoProcessor
        except ImportError as e:
            raise ModelLoadError(
                "Transformers is not installed. Please install transformers to use VLM module.",
                original_exception=e,
            ) from e

        try:
            # 1. Load AutoProcessor
            processor_kwargs: Dict[str, Any] = {
                "trust_remote_code": self.config.trust_remote_code,
            }
            if self.config.min_pixels:
                processor_kwargs["min_pixels"] = self.config.min_pixels
            if self.config.max_pixels:
                processor_kwargs["max_pixels"] = self.config.max_pixels

            self.processor = AutoProcessor.from_pretrained(
                self.config.model_name,
                **processor_kwargs,
            )

            # 2. Load Vision-Language Model
            model_kwargs: Dict[str, Any] = {
                "dtype": self.runtime_info.dtype,
                "trust_remote_code": self.config.trust_remote_code,
                "low_cpu_mem_usage": True,
                **self.config.extra_model_kwargs,
            }

            if self.runtime_info.device.startswith("cuda"):
                model_kwargs["device_map"] = "auto"
            else:
                model_kwargs["device_map"] = "cpu"

            try:
                # Primary Auto class for vision2seq / vision-language models
                self.model = AutoModelForImageTextToText.from_pretrained(
                    self.config.model_name,
                    **model_kwargs,
                )
            except Exception:
                # Fallback to AutoModelForCausalLM if ImageTextToText is unsupported by model arch
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.model_name,
                    **model_kwargs,
                )

            self.model.eval()
            self._is_loaded = True

        except Exception as e:
            self._is_loaded = False
            self.model = None
            self.processor = None
            raise ModelLoadError(
                f"Failed to load VLM model '{self.config.model_name}' on device '{self.runtime_info.device}': {e}",
                original_exception=e,
            ) from e

    def generate(
        self,
        image: Image.Image,
        prompt: str,
        system_prompt: Optional[str] = None,
        **override_kwargs: Any,
    ) -> str:
        """Run vision-language model generation on the given image and prompt."""
        if not self.is_loaded:
            self.load()

        try:
            # Prepare conversation messages
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "image": image},
                        {"type": "text", "text": prompt},
                    ],
                }
            )

            # Format input using processor chat template
            text_prompt = self.processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

            # Build inputs with image
            inputs = self.processor(
                text=[text_prompt],
                images=[image],
                padding=True,
                return_tensors="pt",
            )

            # Move inputs to device
            target_device = getattr(self.model, "device", None) or self.runtime_info.device
            inputs = {k: v.to(target_device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

            # Setup generation configuration
            gen_kwargs = {
                "max_new_tokens": override_kwargs.get("max_new_tokens", self.config.max_new_tokens),
                "temperature": override_kwargs.get("temperature", self.config.temperature),
                "top_p": override_kwargs.get("top_p", self.config.top_p),
                "repetition_penalty": override_kwargs.get("repetition_penalty", self.config.repetition_penalty),
                "do_sample": override_kwargs.get("do_sample", self.config.do_sample),
            }

            # Run inference
            with torch.inference_mode():
                output_ids = self.model.generate(**inputs, **gen_kwargs)

            # Extract generated tokens (strip input tokens)
            input_len = inputs["input_ids"].shape[1]
            generated_ids = output_ids[:, input_len:]

            output_text = self.processor.batch_decode(
                generated_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return output_text.strip()

        except Exception as e:
            raise InferenceError(
                f"VLM model inference failed: {e}",
                original_exception=e,
            ) from e

    def unload(self) -> None:
        """Unload model from memory and release GPU VRAM."""
        self.model = None
        self.processor = None
        self._is_loaded = False
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass
