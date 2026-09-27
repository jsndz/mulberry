"""PaddleOCR text recognizer implementation."""

import logging
import numpy as np

from processing.ocr.backends.recognizers.base import BaseTextRecognizer, TextResult
from processing.ocr.config import DeviceType, OCRConfig, RecognitionRuntime
from processing.ocr.exceptions import OCRInitializationError

logger = logging.getLogger(__name__)


class PaddleTextRecognizer(BaseTextRecognizer):
    """PaddleOCR Text Recognizer Backend."""

    def __init__(self, config: OCRConfig, device: DeviceType, runtime: RecognitionRuntime):
        self.config = config
        self.device = device
        self.runtime = runtime
        self._engine = None
        self._init_backend()

    def _init_backend(self) -> None:
        try:
            from paddleocr import PaddleOCR
            import paddle

            has_paddle_gpu = (
                hasattr(paddle, "is_compiled_with_cuda")
                and paddle.is_compiled_with_cuda()
                and (not hasattr(paddle.device, "cuda") or paddle.device.cuda.device_count() > 0)
            )
            device_str = "gpu" if (self.device == DeviceType.GPU and has_paddle_gpu) else "cpu"
            engine_str = "onnxruntime" if self.runtime == RecognitionRuntime.ONNX else None

            kwargs = {
                "lang": self.config.language,
                "device": device_str,
                "cpu_threads": self.config.cpu_threads,
                "use_textline_orientation": False,
                "enable_mkldnn": False,
            }

            if engine_str:
                kwargs["engine"] = engine_str

            if self.config.extra_params:
                kwargs.update(self.config.extra_params)

            logger.info(f"Initializing PaddleTextRecognizer (device={device_str})...")
            self._engine = PaddleOCR(**kwargs)
        except Exception as e:
            logger.error(f"Failed to initialize PaddleTextRecognizer: {e}")
            raise OCRInitializationError(f"Failed to initialize PaddleTextRecognizer: {e}") from e

    def recognize_crop(self, crop_bgr: np.ndarray) -> TextResult:
        if self._engine is None:
            raise OCRInitializationError("PaddleTextRecognizer engine is not initialized.")

        if crop_bgr is None or crop_bgr.size == 0 or crop_bgr.shape[0] < 2 or crop_bgr.shape[1] < 2:
            return TextResult(text="", confidence=0.0, recognizer_name="paddle")

        try:
            results = list(self._engine.predict(crop_bgr))
            if not results:
                return TextResult(text="", confidence=0.0, recognizer_name="paddle")

            for page in results:
                if isinstance(page, dict):
                    texts = page.get("rec_texts") or page.get("rec_text") or []
                    scores = page.get("rec_scores") or page.get("rec_score") or []

                    if texts:
                        text_str = str(texts[0]).strip()
                        conf_val = float(scores[0]) if scores else 1.0
                        return TextResult(
                            text=text_str,
                            confidence=min(1.0, max(0.0, conf_val)),
                            recognizer_name="paddle",
                        )
                elif isinstance(page, list):
                    for item in page:
                        if isinstance(item, list) and len(item) >= 2:
                            text_score = item[1]
                            if isinstance(text_score, (list, tuple)) and len(text_score) >= 2:
                                text_str = str(text_score[0]).strip()
                                score_val = float(text_score[1])
                                return TextResult(
                                    text=text_str,
                                    confidence=min(1.0, max(0.0, score_val)),
                                    recognizer_name="paddle",
                                )

            return TextResult(text="", confidence=0.0, recognizer_name="paddle")
        except Exception as e:
            logger.warning(f"Error during PaddleTextRecognizer execution: {e}")
            return TextResult(text="", confidence=0.0, recognizer_name="paddle")
