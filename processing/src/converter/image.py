"""Unified image format converter module supporting DNG and standard raster image types."""

import logging
from pathlib import Path
from typing import List, Optional, Union
import numpy as np
from PIL import Image

from processing.converter.dng import (
    convert_dng_to_png,
    dng_bytes_to_png_bytes,
    dng_to_numpy,
)

logger = logging.getLogger(__name__)

SUPPORTED_RAW_EXTENSIONS = {".dng", ".raw", ".cr2", ".nef", ".arw", ".orf", ".rw2"}


def is_raw_format(image_input: Union[str, Path, bytes]) -> bool:
    """Check if the input is a RAW/DNG format by file extension or header."""
    if isinstance(image_input, (str, Path)):
        ext = Path(image_input).suffix.lower()
        return ext in SUPPORTED_RAW_EXTENSIONS
    elif isinstance(image_input, (bytes, memoryview)):
        # Check for TIFF/DNG magic bytes (II*\x00 or MM\x00*)
        header = bytes(image_input[:4])
        return header in (b"II*\x00", b"MM\x00*")
    return False


class ImageConverter:
    """Unified Image Format Converter."""

    @staticmethod
    def dng_to_png(
        input_path: Union[str, Path, bytes],
        output_path: Optional[Union[str, Path]] = None,
        use_camera_wb: bool = True,
        half_size: bool = False,
    ) -> Path:
        """Convert a DNG image to PNG format."""
        return convert_dng_to_png(
            input_path=input_path,
            output_path=output_path,
            use_camera_wb=use_camera_wb,
            half_size=half_size,
        )

    @classmethod
    def convert(
        cls,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        target_format: str = "png",
        **kwargs,
    ) -> Path:
        """Convert any supported image file (DNG, JPEG, TIFF, WEBP, BMP) to a target format.

        Args:
            input_path: Path to source image file.
            output_path: Path for output image. Defaults to input path with target format extension.
            target_format: Output image format e.g. 'png', 'jpeg', 'webp'.
            **kwargs: Extra parameters passed to converter engines (e.g. use_camera_wb).

        Returns:
            Path pointing to the written output image file.
        """
        in_path = Path(input_path).resolve()
        if not in_path.exists():
            raise FileNotFoundError(f"Input image file not found at '{in_path}'")

        target_fmt = target_format.lower().lstrip(".")
        format_map = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP", "tiff": "TIFF", "tif": "TIFF", "bmp": "BMP"}
        pil_format = format_map.get(target_fmt, target_fmt.upper())

        if output_path is None:
            out_path = in_path.with_suffix(f".{target_fmt}")
        else:
            out_path = Path(output_path).resolve()

        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle RAW/DNG input files
        if is_raw_format(in_path):
            if target_fmt == "png":
                return convert_dng_to_png(
                    input_path=in_path,
                    output_path=out_path,
                    use_camera_wb=kwargs.get("use_camera_wb", True),
                    half_size=kwargs.get("half_size", False),
                )
            else:
                # Convert DNG to numpy RGB first, then save to requested format
                rgb = dng_to_numpy(
                    in_path,
                    use_camera_wb=kwargs.get("use_camera_wb", True),
                    output_bgr=False,
                )
                pil_img = Image.fromarray(rgb)
                pil_img.save(out_path, format=pil_format)
                logger.info(f"Converted DNG image to '{target_fmt}': '{out_path}'")
                return out_path

        # Handle standard raster image formats (PIL / Pillow)
        try:
            with Image.open(in_path) as img:
                if img.mode in ("RGBA", "P") and target_fmt in ("jpeg", "jpg"):
                    img = img.convert("RGB")
                img.save(out_path, format=pil_format)
            logger.info(f"Converted image '{in_path.name}' to '{out_path.name}'")
            return out_path
        except Exception as e:
            logger.error(f"Failed to convert image '{in_path}': {e}")
            raise ValueError(f"Failed to convert image '{in_path}': {e}") from e

    @classmethod
    def convert_directory(
        cls,
        input_dir: Union[str, Path],
        output_dir: Optional[Union[str, Path]] = None,
        target_format: str = "png",
        extensions: Optional[List[str]] = None,
    ) -> List[Path]:
        """Convert all matching image files in a directory to target format."""
        in_dir = Path(input_dir).resolve()
        if not in_dir.exists() or not in_dir.is_dir():
            raise FileNotFoundError(f"Input directory not found: '{in_dir}'")

        out_dir = Path(output_dir).resolve() if output_dir else in_dir
        out_dir.mkdir(parents=True, exist_ok=True)

        valid_exts = [e.lower().lstrip(".") for e in (extensions or ["dng", "raw", "jpg", "jpeg", "tif", "tiff", "webp"])]
        converted_files: List[Path] = []

        for file_path in in_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower().lstrip(".") in valid_exts:
                target_file = out_dir / f"{file_path.stem}.{target_format.lower().lstrip('.')}"
                res_path = cls.convert(file_path, target_file, target_format=target_format)
                converted_files.append(res_path)

        return converted_files


def convert_image(
    input_path: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    target_format: str = "png",
) -> Path:
    """Convenience functional wrapper for image conversion."""
    return ImageConverter.convert(input_path, output_path=output_path, target_format=target_format)
