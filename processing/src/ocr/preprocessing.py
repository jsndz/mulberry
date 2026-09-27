"""Image format normalization and handwriting-oriented preprocessing for Mulberry OCR."""

import io
import logging
from pathlib import Path
from typing import Tuple, Union
import cv2 as cv
import numpy as np
from PIL import Image

from processing.ocr.config import ImagePreprocessingConfig
from processing.ocr.exceptions import InvalidImageError
from processing.converter.image import is_raw_format
from processing.converter.dng import dng_to_numpy

logger = logging.getLogger(__name__)


def normalize_image(
    image: Union[Image.Image, np.ndarray, str, Path, bytes]
) -> Tuple[np.ndarray, int, int]:
    """Convert input image from various formats into standard 3-channel OpenCV BGR ndarray.

    Supports PIL Image, OpenCV ndarray, file paths (including .dng RAW images), and raw bytes.

    Returns:
        Tuple of (img_bgr: np.ndarray, width: int, height: int)

    Raises:
        InvalidImageError: If image input is invalid, corrupted, or unreadable.
    """
    img_bgr: np.ndarray

    if isinstance(image, Image.Image):
        rgb_arr = np.array(image.convert("RGB"))
        img_bgr = cv.cvtColor(rgb_arr, cv.COLOR_RGB2BGR)
    elif isinstance(image, np.ndarray):
        if image.size == 0 or image.ndim < 2:
            raise InvalidImageError("Input numpy image array is empty or invalid.")
        if image.ndim == 2:
            img_bgr = cv.cvtColor(image, cv.COLOR_GRAY2BGR)
        elif image.ndim == 3 and image.shape[2] == 4:
            img_bgr = cv.cvtColor(image, cv.COLOR_BGRA2BGR)
        elif image.ndim == 3 and image.shape[2] == 3:
            img_bgr = image
        else:
            raise InvalidImageError(f"Unsupported image array shape: {image.shape}")
    elif isinstance(image, (bytes, memoryview)):
        # Check if bytes are DNG / RAW
        if is_raw_format(image):
            try:
                img_bgr = dng_to_numpy(image, output_bgr=True)
            except Exception as e:
                raise InvalidImageError(f"Could not decode RAW DNG image bytes: {e}") from e
        else:
            nparr = np.frombuffer(image, np.uint8)
            img_decoded = cv.imdecode(nparr, cv.IMREAD_COLOR)
            if img_decoded is None:
                try:
                    pil_img = Image.open(io.BytesIO(image)).convert("RGB")
                    img_bgr = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
                except Exception as e:
                    raise InvalidImageError(f"Could not decode image bytes: {e}") from e
            else:
                img_bgr = img_decoded
    elif isinstance(image, (str, Path)):
        path = Path(image)
        if not path.exists() or not path.is_file():
            raise InvalidImageError(f"Image file not found: '{path}'")
        
        # Check if file path is DNG / RAW format
        if is_raw_format(path):
            try:
                img_bgr = dng_to_numpy(path, output_bgr=True)
            except Exception as e:
                raise InvalidImageError(f"Could not decode RAW DNG file '{path}': {e}") from e
        else:
            img_read = cv.imread(str(path), cv.IMREAD_COLOR)
            if img_read is None:
                try:
                    pil_img = Image.open(path).convert("RGB")
                    img_bgr = cv.cvtColor(np.array(pil_img), cv.COLOR_RGB2BGR)
                except Exception as e:
                    raise InvalidImageError(f"Could not read image file '{path}': {e}") from e
            else:
                img_bgr = img_read
    else:
        raise InvalidImageError(f"Unsupported image input type: {type(image)}")

    h, w = img_bgr.shape[:2]
    if w <= 0 or h <= 0:
        raise InvalidImageError(f"Invalid image dimensions: width={w}, height={h}")

    return img_bgr, w, h


def deskew_image(img_bgr: np.ndarray) -> np.ndarray:
    """Estimate skew angle and deskew image via affine rotation."""
    gray = cv.cvtColor(img_bgr, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (5, 5), 0)
    thresh = cv.threshold(blurred, 0, 255, cv.THRESH_BINARY_INV + cv.THRESH_OTSU)[1]

    # Find coordinates of non-zero pixels
    pts = cv.findNonZero(thresh)
    if pts is None or len(pts) < 10:
        return img_bgr

    rect = cv.minAreaRect(pts)
    angle = rect[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Ignore trivial angles
    if abs(angle) < 0.5 or abs(angle) > 45.0:
        return img_bgr

    (h, w) = img_bgr.shape[:2]
    center = (w // 2, h // 2)
    M = cv.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv.warpAffine(
        img_bgr, M, (w, h), flags=cv.INTER_CUBIC, borderMode=cv.BORDER_REPLICATE
    )
    return rotated


def apply_contrast_normalization(img_bgr: np.ndarray) -> np.ndarray:
    """Apply CLAHE contrast normalization in LAB color space without binarization."""
    lab = cv.cvtColor(img_bgr, cv.COLOR_BGR2LAB)
    l, a, b = cv.split(lab)
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv.merge((cl, a, b))
    return cv.cvtColor(limg, cv.COLOR_LAB2BGR)


def preprocess_image(
    img_bgr: np.ndarray, config: ImagePreprocessingConfig
) -> np.ndarray:
    """Apply handwriting-friendly preprocessing transformations.

    Do NOT perform aggressive thresholding/binarization to preserve strokes.
    """
    processed = img_bgr.copy()

    # 1. Scaling / Resizing if max_dimension is specified
    if config.max_dimension and config.max_dimension > 0:
        h, w = processed.shape[:2]
        max_dim = max(h, w)
        if max_dim > config.max_dimension:
            scale = config.max_dimension / float(max_dim)
            new_w, new_h = int(round(w * scale)), int(round(h * scale))
            processed = cv.resize(processed, (new_w, new_h), interpolation=cv.INTER_AREA)

    # 2. Mild Denoising
    if config.enable_denoise:
        processed = cv.fastNlMeansDenoisingColored(processed, None, 5, 5, 7, 21)

    # 3. Contrast Normalization
    if config.enable_contrast_norm:
        processed = apply_contrast_normalization(processed)

    # 4. Deskewing
    if config.enable_deskew:
        processed = deskew_image(processed)

    return processed
