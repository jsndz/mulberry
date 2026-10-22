"""Data models for Input Ingestion and Page Splitting."""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field


class InputType(str, Enum):
    """Categorized input media types."""

    RASTER_IMAGE = "raster_image"    # PNG, JPEG, WEBP, TIFF, BMP
    RAW_CAMERA = "raw_camera"        # DNG, CR2, NEF, ARW, etc.
    PDF_DOCUMENT = "pdf_document"    # Multi-page PDF
    IN_MEMORY = "in_memory"          # NumPy array or PIL Image


class PageInput(BaseModel):
    """Normalized single-page representation ready for HCD-HTR processing."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    page_number: int = Field(..., ge=1, description="1-indexed page number")
    total_pages: int = Field(..., ge=1, description="Total number of pages in the source document")
    image_bgr: np.ndarray = Field(..., description="OpenCV BGR numpy array")
    pil_image: Image.Image = Field(..., description="PIL RGB Image")
    width: int = Field(..., gt=0, description="Image width in pixels")
    height: int = Field(..., gt=0, description="Image height in pixels")
    media_type: str = Field(..., description="Media MIME type, e.g. application/pdf, image/png")
    source_file: Optional[str] = Field(default=None, description="Source file path if from disk")
    dpi: Optional[int] = Field(default=None, ge=1, description="Resolution DPI if known")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary format metadata")
