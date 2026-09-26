"""Detector engines and hardware adaptation logic for diagram detection."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
import torch
import transformers
from transformers import AutoImageProcessor, AutoModelForObjectDetection
import ultralytics
from ultralytics import YOLO

from processing.diagram.models import DiagramDetectionRegion

logger = logging.getLogger("mulberry.diagram.detector")


def check_gpu_availability() -> bool:
    """
    Check if a CUDA-enabled NVIDIA GPU is available.

    Returns:
        True if torch.cuda.is_available() is True, else False.
    """
    gpu_available = torch.cuda.is_available()
    if gpu_available:
        device_name = torch.cuda.get_device_name(0)
        logger.info(f"CUDA-enabled NVIDIA GPU detected: {device_name}")
    else:
        logger.info("No CUDA GPU detected. Falling back to CPU execution.")
    return gpu_available


class BaseDiagramDetector(ABC):
    """Unified layout engine interface for diagram detection."""

    @abstractmethod
    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        conf_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run inference and return detected diagram bounding boxes.

        Args:
            image_input: Image file path, PIL Image, or NumPy BGR/RGB array.
            conf_threshold: Optional confidence threshold override.

        Returns:
            List of dictionaries formatted as:
            [{"box": [xmin, ymin, xmax, ymax], "confidence": float}]
        """
        pass

    def __call__(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        conf_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        return self.predict(image_input, conf_threshold=conf_threshold)


class DiTDiagramDetector(BaseDiagramDetector):
    """
    GPU PIPELINE (Highest Accuracy):
    Transformer-based Document Image Analysis model using Hugging Face 'transformers'.
    Uses Microsoft DiT (Document Image Transformer) ('microsoft/dit-base-finetuned-publaynet').
    DiT handles raw visual/handwritten layouts natively without requiring an initial text OCR step.
    Parses output objects and extracts bounding box coordinates for regions classified as "figure" or "table".
    """

    TARGET_LABELS = {"figure", "table", "diagram", "chart", "flowchart"}

    def __init__(
        self,
        model_name: str = "microsoft/dit-base-finetuned-publaynet",
        default_conf_threshold: float = 0.25,
        device: Optional[str] = None,
    ):
        self.model_name = model_name
        self.default_conf_threshold = default_conf_threshold
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        logger.info(f"Loading Hugging Face DiT model '{model_name}' on device '{self.device}'...")
        self.processor = AutoImageProcessor.from_pretrained(self.model_name)
        self.model = AutoModelForObjectDetection.from_pretrained(self.model_name).to(self.device)
        self.model.eval()

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        conf_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        threshold = conf_threshold if conf_threshold is not None else self.default_conf_threshold
        pil_image = _load_as_pil_image(image_input)
        width, height = pil_image.size

        inputs = self.processor(images=pil_image, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Target sizes format: (height, width)
        target_sizes = torch.tensor([[height, width]], device=self.device)

        results = self.processor.post_process_object_detection(
            outputs,
            threshold=threshold,
            target_sizes=target_sizes,
        )[0]

        id2label = self.model.config.id2label
        clean_detections: List[Dict[str, Any]] = []

        for score, label_id, box in zip(results["scores"], results["labels"], results["boxes"]):
            label_name = id2label[int(label_id.item())].lower()
            confidence = float(score.item())

            # Filter regions classified as "figure" or "table" (which map to diagrams/flowcharts)
            if any(target in label_name for target in self.TARGET_LABELS):
                xmin, ymin, xmax, ymax = [round(float(c), 2) for c in box.tolist()]
                # Clamp coordinates within valid image bounds
                xmin = max(0.0, min(float(width), xmin))
                ymin = max(0.0, min(float(height), ymin))
                xmax = max(0.0, min(float(width), xmax))
                ymax = max(0.0, min(float(height), ymax))

                region = DiagramDetectionRegion(
                    box=[xmin, ymin, xmax, ymax],
                    confidence=confidence,
                    label=label_name,
                )
                clean_detections.append(region.to_dict())

        return clean_detections


class YOLODiagramDetector(BaseDiagramDetector):
    """
    CPU PIPELINE (Efficient Fallback):
    If only a CPU is available, gracefully falls back to the lightweight Ultralytics YOLO framework
    (`yolov8n.pt` or `yolov11n.pt`).
    Runs inference using a configurable confidence threshold (default 0.25).
    Extracts raw bounding boxes for detected objects.
    """

    def __init__(
        self,
        model_name: str = "yolov8n.pt",
        default_conf_threshold: float = 0.25,
        device: str = "cpu",
    ):
        self.model_name = model_name
        self.default_conf_threshold = default_conf_threshold
        self.device = device

        logger.info(f"Loading Ultralytics YOLO model '{model_name}' on device '{self.device}'...")
        self.model = YOLO(self.model_name)

    def predict(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        conf_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        threshold = conf_threshold if conf_threshold is not None else self.default_conf_threshold
        pil_image = _load_as_pil_image(image_input)
        width, height = pil_image.size

        # Run inference using Ultralytics YOLO
        results = self.model.predict(
            source=pil_image,
            conf=threshold,
            device=self.device,
            verbose=False,
        )

        clean_detections: List[Dict[str, Any]] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                xyxy = box.xyxy[0].tolist()
                xmin, ymin, xmax, ymax = [round(float(c), 2) for c in xyxy]
                conf = round(float(box.conf[0].item()), 4)

                # Clamp bounds
                xmin = max(0.0, min(float(width), xmin))
                ymin = max(0.0, min(float(height), ymin))
                xmax = max(0.0, min(float(width), xmax))
                ymax = max(0.0, min(float(height), ymax))

                region = DiagramDetectionRegion(
                    box=[xmin, ymin, xmax, ymax],
                    confidence=conf,
                )
                clean_detections.append(region.to_dict())

        return clean_detections


def get_detector(
    force_device: Optional[str] = None,
    dit_model_name: str = "microsoft/dit-base-finetuned-publaynet",
    yolo_model_name: str = "yolov8n.pt",
    default_conf_threshold: float = 0.25,
) -> BaseDiagramDetector:
    """
    Factory function returning a unified diagram detector interface.

    Dynamically adapts to the hardware execution environment:
    - If CUDA-enabled GPU is available: initializes DiTDiagramDetector (Hugging Face DiT PubLayNet).
    - If CPU-only: gracefully falls back to YOLODiagramDetector (Ultralytics YOLO).

    Args:
        force_device: Optional override ('cuda' or 'cpu').
        dit_model_name: Hugging Face repository identifier for DiT weights.
        yolo_model_name: Ultralytics YOLO model weight file (e.g. 'yolov8n.pt' or 'yolov11n.pt').
        default_conf_threshold: Default inference confidence threshold.

    Returns:
        Instance conforming to BaseDiagramDetector interface.
    """
    if force_device:
        use_gpu = force_device.lower() in ("cuda", "gpu")
    else:
        use_gpu = torch.cuda.is_available()

    if use_gpu:
        try:
            logger.info("Initializing GPU Pipeline (Microsoft DiT Transformer)...")
            return DiTDiagramDetector(
                model_name=dit_model_name,
                default_conf_threshold=default_conf_threshold,
                device="cuda",
            )
        except Exception as err:
            logger.warning(
                f"Failed to initialize GPU DiT pipeline ({err}). "
                "Falling back to CPU YOLO pipeline."
            )
            return YOLODiagramDetector(
                model_name=yolo_model_name,
                default_conf_threshold=default_conf_threshold,
                device="cpu",
            )
    else:
        logger.info("Initializing CPU Pipeline (Ultralytics YOLO Fallback)...")
        return YOLODiagramDetector(
            model_name=yolo_model_name,
            default_conf_threshold=default_conf_threshold,
            device="cpu",
        )


def _load_as_pil_image(image_input: Union[str, Path, Image.Image, np.ndarray]) -> Image.Image:
    """Internal helper to safely load diverse image input formats into a PIL RGB Image."""
    if isinstance(image_input, Image.Image):
        return image_input.convert("RGB")
    elif isinstance(image_input, (str, Path)):
        p = Path(image_input)
        if not p.exists():
            raise FileNotFoundError(f"Image path does not exist: {p}")
        return Image.open(p).convert("RGB")
    elif isinstance(image_input, np.ndarray):
        if len(image_input.shape) == 3 and image_input.shape[2] == 3:
            rgb_arr = cv2.cvtColor(image_input, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_arr)
        else:
            return Image.fromarray(image_input).convert("RGB")
    else:
        raise TypeError(f"Unsupported image input type: {type(image_input)}")
