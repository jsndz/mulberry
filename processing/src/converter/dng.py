"""DNG (Digital Negative) RAW image conversion module."""

import io
import logging
from pathlib import Path
from typing import Optional, Union
import cv2 as cv
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


def dng_to_numpy(
    dng_input: Union[str, Path, bytes],
    use_camera_wb: bool = True,
    half_size: bool = False,
    output_bgr: bool = True,
) -> np.ndarray:
    """Decode a DNG image (file path or raw bytes) into an OpenCV numpy array.

    Args:
        dng_input: Path to DNG file or raw bytes of DNG file.
        use_camera_wb: Use camera white balance settings if available.
        half_size: Process at half resolution for faster decoding.
        output_bgr: Return array in OpenCV BGR format if True, else RGB format.

    Returns:
        np.ndarray containing 3-channel image data (uint8).

    Raises:
        FileNotFoundError: If dng_input file path does not exist.
        ValueError: If dng_input is invalid or decoding fails.
    """
    try:
        import rawpy
    except ImportError as e:
        raise ImportError(
            "DNG conversion requires the 'rawpy' library. Install it via 'pip install rawpy'."
        ) from e

    raw_obj = None
    try:
        if isinstance(dng_input, (str, Path)):
            path = Path(dng_input)
            if not path.exists():
                raise FileNotFoundError(f"DNG image file not found at '{path}'")
            raw_obj = rawpy.imread(str(path))
        elif isinstance(dng_input, (bytes, memoryview)):
            raw_obj = rawpy.imread(io.BytesIO(dng_input))
        else:
            raise ValueError(f"Unsupported DNG input type: {type(dng_input)}")

        rgb = raw_obj.postprocess(use_camera_wb=use_camera_wb, half_size=half_size)

        if output_bgr:
            return cv.cvtColor(rgb, cv.COLOR_RGB2BGR)
        return rgb
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Failed to decode DNG image: {e}")
        raise ValueError(f"Failed to decode DNG image data: {e}") from e
    finally:
        if raw_obj is not None:
            try:
                raw_obj.close()
            except Exception:
                pass


def convert_dng_to_png(
    input_path: Union[str, Path, bytes],
    output_path: Optional[Union[str, Path]] = None,
    use_camera_wb: bool = True,
    half_size: bool = False,
    compress_level: int = 6,
) -> Path:
    """Convert a DNG image file or raw bytes into a PNG file on disk.

    Args:
        input_path: Path to input DNG file or raw DNG bytes.
        output_path: Destination path for output PNG file. Defaults to same path with .png extension.
        use_camera_wb: Use camera white balance settings.
        half_size: Process at half resolution for faster decoding.
        compress_level: PNG compression level (0-9).

    Returns:
        Path pointing to the written output PNG file.
    """
    if output_path is None:
        if isinstance(input_path, (str, Path)):
            output_path = Path(input_path).with_suffix(".png")
        else:
            raise ValueError("output_path must be specified when input is raw bytes.")
    else:
        output_path = Path(output_path)

    rgb = dng_to_numpy(
        input_path, use_camera_wb=use_camera_wb, half_size=half_size, output_bgr=False
    )
    pil_img = Image.fromarray(rgb)

    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pil_img.save(output_path, format="PNG", compress_level=compress_level)
    logger.info(f"Successfully converted DNG to PNG: '{output_path}'")
    return output_path


def dng_bytes_to_png_bytes(
    dng_bytes: bytes,
    use_camera_wb: bool = True,
    compress_level: int = 6,
) -> bytes:
    """Convert raw DNG bytes into PNG formatted image bytes in memory."""
    rgb = dng_to_numpy(
        dng_bytes, use_camera_wb=use_camera_wb, output_bgr=False
    )
    pil_img = Image.fromarray(rgb)

    buf = io.BytesIO()
    pil_img.save(buf, format="PNG", compress_level=compress_level)
    return buf.getvalue()
