"""Unit tests for Mulberry Image Format Converter module (DNG to PNG, etc.)."""

import pytest
from pathlib import Path
from PIL import Image
import numpy as np

from processing.converter import (
    ImageConverter,
    convert_dng_to_png,
    dng_bytes_to_png_bytes,
    dng_to_numpy,
    convert_image,
    is_raw_format,
)


def create_synthetic_png(path: Path, width: int = 100, height: int = 100) -> Path:
    """Helper to generate a synthetic PNG image."""
    img = Image.new("RGB", (width, height), color=(100, 150, 200))
    img.save(path, format="PNG")
    return path


class TestImageConverter:
    def test_is_raw_format_extension_detection(self):
        assert is_raw_format("photo.dng") is True
        assert is_raw_format("photo.DNG") is True
        assert is_raw_format(Path("image.cr2")) is True
        assert is_raw_format("image.jpg") is False
        assert is_raw_format("image.png") is False

    def test_is_raw_format_header_detection(self):
        # TIFF / DNG magic headers
        assert is_raw_format(b"II*\x00\x08\x00\x00\x00") is True
        assert is_raw_format(b"MM\x00*\x00\x00\x00\x08") is True
        assert is_raw_format(b"\x89PNG\r\n\x1a\n") is False

    def test_standard_format_conversion(self, tmp_path):
        input_png = tmp_path / "test.png"
        create_synthetic_png(input_png)

        # Convert PNG to JPEG
        output_jpeg = tmp_path / "test.jpeg"
        res_path = ImageConverter.convert(input_png, output_jpeg, target_format="jpeg")
        assert res_path.exists()
        assert res_path.suffix == ".jpeg"

        # Verify converted image can be opened
        with Image.open(res_path) as img:
            assert img.format in ("JPEG", "JPG")
            assert img.size == (100, 100)

    def test_convert_image_convenience_function(self, tmp_path):
        input_png = tmp_path / "sample.png"
        create_synthetic_png(input_png)

        output_jpg = tmp_path / "sample.jpg"
        res = convert_image(input_png, output_jpg, target_format="jpg")
        assert res.exists()
        assert res.suffix == ".jpg"

    def test_missing_input_raises_exception(self):
        with pytest.raises(FileNotFoundError):
            ImageConverter.convert("non_existent_file_12345.dng")

    def test_convert_directory(self, tmp_path):
        src_dir = tmp_path / "src_images"
        out_dir = tmp_path / "out_images"
        src_dir.mkdir()

        create_synthetic_png(src_dir / "img1.png")
        create_synthetic_png(src_dir / "img2.png")

        converted = ImageConverter.convert_directory(src_dir, out_dir, target_format="jpeg", extensions=["png"])
        assert len(converted) == 2
        for p in converted:
            assert p.exists()
            assert p.suffix == ".jpeg"
