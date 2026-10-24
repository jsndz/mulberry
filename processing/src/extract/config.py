"""Configuration and hardware tier definitions for HCD-HTR extraction pipeline."""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class HardwareTier(str, Enum):
    """Hardware execution tiers defining model and pipeline tradeoffs."""

    TIER_1_MAX_ACCURACY = "tier_1_max_accuracy"  # 16-24 GB VRAM: Surya + Qwen2.5-VL-7B
    TIER_2_BALANCED = "tier_2_balanced"          # 6-12 GB VRAM: DiT/DBNet + TrOCR / Qwen-3B
    TIER_3_EDGE_CPU = "tier_3_edge_cpu"          # CPU/4GB: YOLO + DBNet CPU + TrOCR ONNX/INT8


def detect_hardware_tier() -> HardwareTier:
    """Automatically detect the best HardwareTier based on available VRAM and CUDA support.

    - >= 15 GB VRAM: TIER_1_MAX_ACCURACY (Full 7B VLM)
    - 5.5 to 15 GB VRAM: TIER_2_BALANCED (TrOCR GPU / 3B VLM)
    - < 5.5 GB VRAM or CPU: TIER_3_EDGE_CPU (Lightweight CPU)
    """
    try:
        import torch

        if not torch.cuda.is_available():
            return HardwareTier.TIER_3_EDGE_CPU

        total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        if total_vram_gb >= 15.0:
            return HardwareTier.TIER_1_MAX_ACCURACY
        elif total_vram_gb >= 5.5:
            return HardwareTier.TIER_2_BALANCED
        else:
            return HardwareTier.TIER_3_EDGE_CPU
    except Exception:
        return HardwareTier.TIER_3_EDGE_CPU


class ExtractionConfig(BaseModel):
    """Configuration settings for HandwritingExtractionPipeline."""

    tier: HardwareTier = Field(
        default_factory=detect_hardware_tier,
        description="Target execution tier controlling speed vs. accuracy tradeoffs.",
    )
    vlm_model_id: str = Field(
        default="Qwen/Qwen2.5-VL-7B-Instruct",
        description="VLM model identifier for Stage 4 line recognition."
    )
    yolo_model_path: str = Field(
        default="yolov8n.pt",
        description="Weights for lightweight fallback non-text detector."
    )
    dit_model_id: Optional[str] = Field(
        default=None,
        description="Optional weights for HuggingFace DiT layout detector.",
    )
    context_db_path: Optional[str] = Field(
        default=None,
        description="Path to SQLite context database (defaults to in-memory or standard path)."
    )

    # Preprocessing settings
    enable_dewarp: bool = Field(
        default=True,
        description="Whether to perform 4-point perspective dewarping."
    )
    enable_clahe: bool = Field(
        default=True,
        description="Whether to apply CLAHE illumination flattening in LAB space."
    )
    clahe_clip_limit: float = Field(default=2.0, ge=0.5, le=10.0)
    clahe_tile_grid_size: tuple[int, int] = Field(default=(8, 8))

    # Cropping margins
    pad_y: int = Field(default=6, ge=0, description="Vertical padding for line crops (px)")
    pad_x: int = Field(default=12, ge=0, description="Horizontal padding for line crops (px)")

    # Macro scout sweep
    scout_ratio: float = Field(
        default=0.25,
        ge=0.05,
        le=0.50,
        description="Fraction of top canvas to inspect for macro scout topic inferencing."
    )

    # Hardware device override
    device: Optional[str] = Field(
        default=None,
        description="Explicit device override ('cuda', 'cpu', 'mps'). If None, automatically detected."
    )

    # Visual debugging
    debug_dir: Optional[str] = Field(
        default=None,
        description="Directory to save visual debug artifacts for each stage (Stage 1-5 crops & overlays)."
    )
