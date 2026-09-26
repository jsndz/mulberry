"""Data models for Diagram Detection module."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class DiagramDetectionRegion(BaseModel):
    """Clean representation of a detected diagram region with bounding box and confidence score."""

    box: List[float] = Field(
        ...,
        min_length=4,
        max_length=4,
        description="Bounding box coordinates [xmin, ymin, xmax, ymax] in pixels",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence score between 0.0 and 1.0",
    )
    label: Optional[str] = Field(
        default=None,
        description="Classification label associated with detected diagram region (e.g. 'figure', 'table')",
    )

    @field_validator("box")
    @classmethod
    def validate_box(cls, v: List[float]) -> List[float]:
        if len(v) != 4:
            raise ValueError("Bounding box must contain exactly 4 coordinates [xmin, ymin, xmax, ymax]")
        xmin, ymin, xmax, ymax = v
        if xmin > xmax:
            raise ValueError(f"xmin ({xmin}) cannot be greater than xmax ({xmax})")
        if ymin > ymax:
            raise ValueError(f"ymin ({ymin}) cannot be greater than ymax ({ymax})")
        return [round(float(c), 2) for c in v]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to standard output dictionary format: {"box": [...], "confidence": float}."""
        return {
            "box": self.box,
            "confidence": round(self.confidence, 4),
        }
