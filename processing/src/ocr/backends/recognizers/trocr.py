"""TrOCR text recognizer implementation for handwritten text."""

import logging
import cv2 as cv
import numpy as np
from PIL import Image

from processing.ocr.backends.recognizers.base import BaseTextRecognizer, TextResult
from processing.ocr.config import DeviceType, OCRConfig
from processing.ocr.exceptions import MissingModelError, OCRInitializationError

logger = logging.getLogger(__name__)


class TrOCRTextRecognizer(BaseTextRecognizer):
    """TrOCR Transformer-based handwriting text recognizer backend."""

    def __init__(self, config: OCRConfig, device: DeviceType):
        self.config = config
        self.device_type = device
        self.model_name = config.trocr_model_name or "microsoft/trocr-base-handwritten"
        self._processor = None
        self._model = None
        self._device = "cpu"

        self._init_backend()

    def _init_backend(self) -> None:
        try:
            import torch
            from transformers import (
                RobertaTokenizer,
                TrOCRProcessor,
                VisionEncoderDecoderModel,
                ViTImageProcessor,
            )

            self._device = "cuda" if self.device_type == DeviceType.GPU and torch.cuda.is_available() else "cpu"
            logger.info(
                f"Initializing TrOCRTextRecognizer [Model: '{self.model_name}', Device: {self._device}]..."
            )

            # Initialize processor with robust fallback for fast/slow tokenizers
            try:
                self._processor = TrOCRProcessor.from_pretrained(self.model_name)
            except Exception:
                img_proc = ViTImageProcessor.from_pretrained(self.model_name)
                tok = RobertaTokenizer.from_pretrained(self.model_name)
                self._processor = TrOCRProcessor(image_processor=img_proc, tokenizer=tok)

            self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self._model.to(self._device)
            self._model.eval()

            logger.info("TrOCRTextRecognizer successfully initialized.")
        except ImportError as e:
            raise MissingModelError(
                f"TrOCR backend requires 'torch' and 'transformers' packages: {e}"
            ) from e
        except Exception as e:
            logger.error(f"Failed to initialize TrOCR recognizer: {e}")
            raise OCRInitializationError(f"Failed to initialize TrOCR recognizer: {e}") from e

    def recognize_crop(self, crop_bgr: np.ndarray) -> TextResult:
        if self._model is None or self._processor is None:
            raise OCRInitializationError("TrOCR recognizer is not initialized.")

        if crop_bgr is None or crop_bgr.size == 0 or crop_bgr.shape[0] < 2 or crop_bgr.shape[1] < 2:
            return TextResult(text="", confidence=0.0, recognizer_name="trocr")

        try:
            import torch

            # Convert BGR OpenCV image to PIL RGB Image
            rgb_arr = cv.cvtColor(crop_bgr, cv.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_arr)

            pixel_values = self._processor(images=pil_img, return_tensors="pt").pixel_values
            pixel_values = pixel_values.to(self._device)

            with torch.no_grad():
                generated_outputs = self._model.generate(
                    pixel_values,
                    max_new_tokens=64,
                    return_dict_in_generate=True,
                    output_scores=True,
                )

            generated_ids = generated_outputs.sequences
            decoded_text = self._processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()

            # Estimate confidence from token scores if available
            confidence = 0.90
            if hasattr(generated_outputs, "scores") and generated_outputs.scores:
                try:
                    scores_list = [
                        torch.softmax(score_tensor, dim=-1).max().item()
                        for score_tensor in generated_outputs.scores
                    ]
                    if scores_list:
                        confidence = float(np.mean(scores_list))
                except Exception:
                    confidence = 0.90

            confidence = min(1.0, max(0.0, float(confidence)))
            return TextResult(text=decoded_text, confidence=confidence, recognizer_name="trocr")
        except Exception as e:
            logger.warning(f"Error during TrOCR inference: {e}")
            return TextResult(text="", confidence=0.0, recognizer_name="trocr")
