"""4-Point Perspective Transform and Dewarping for skewed smartphone note captures."""

from typing import Optional, Tuple
import cv2
import numpy as np


def order_points(pts: np.ndarray) -> np.ndarray:
    """
    Order coordinates consistently in clockwise order:
    [0]: Top-Left, [1]: Top-Right, [2]: Bottom-Right, [3]: Bottom-Left
    """
    rect = np.zeros((4, 2), dtype="float32")

    # Sum of (x + y): top-left has smallest sum, bottom-right has largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # Diff of (y - x): top-right has smallest diff, bottom-left has largest diff
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    return rect


def detect_document_corners(
    img_bgr: np.ndarray,
    downscale_max: int = 1000,
    min_area_ratio: float = 0.20,
) -> Optional[np.ndarray]:
    """
    Detect the 4 principal corners of the document/notebook page using morphological contours.

    Returns:
        np.ndarray of shape (4, 2) with corners in original coordinate scale, or None if not found.
    """
    orig_h, orig_w = img_bgr.shape[:2]
    max_dim = max(orig_h, orig_w)
    scale = 1.0

    if max_dim > downscale_max:
        scale = downscale_max / float(max_dim)
        new_w, new_h = int(round(orig_w * scale)), int(round(orig_h * scale))
        canvas = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        canvas = img_bgr.copy()

    gray = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Edge detection with morphological closing to bridge stroke gaps
    edges = cv2.Canny(blurred, 50, 200)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    canvas_area = canvas.shape[0] * canvas.shape[1]
    sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

    for cnt in sorted_contours[:5]:
        area = cv2.contourArea(cnt)
        if area < (canvas_area * min_area_ratio):
            break

        # Check convex hull
        hull = cv2.convexHull(cnt)
        peri = cv2.arcLength(hull, True)
        approx = cv2.approxPolyDP(hull, 0.02 * peri, True)

        if len(approx) == 4:
            pts = approx.reshape(4, 2).astype("float32")
            # Rescale points back to original image dimensions
            pts_orig = pts / scale
            return order_points(pts_orig)

    return None


def warp_perspective(img_bgr: np.ndarray, ordered_corners: np.ndarray) -> np.ndarray:
    """
    Project quadrilateral region into planar, top-down perspective via homography.
    """
    (tl, tr, br, bl) = ordered_corners

    # Compute width of new image
    width_a = np.linalg.norm(br - bl)
    width_b = np.linalg.norm(tr - tl)
    max_w = max(int(width_a), int(width_b))

    # Compute height of new image
    height_a = np.linalg.norm(tr - br)
    height_b = np.linalg.norm(tl - bl)
    max_h = max(int(height_a), int(height_b))

    if max_w <= 10 or max_h <= 10:
        return img_bgr

    dst = np.array(
        [
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1],
        ],
        dtype="float32",
    )

    m = cv2.getPerspectiveTransform(ordered_corners, dst)
    warped = cv2.warpPerspective(img_bgr, m, (max_w, max_h), flags=cv2.INTER_CUBIC)
    return warped


def dewarp_document(img_bgr: np.ndarray) -> Tuple[np.ndarray, bool]:
    """
    Attempts 4-point perspective dewarping. If corners cannot be safely determined,
    gracefully returns original image.

    Returns:
        Tuple of (dewarped_image, was_dewarped: bool)
    """
    corners = detect_document_corners(img_bgr)
    if corners is None:
        return img_bgr, False

    try:
        warped = warp_perspective(img_bgr, corners)
        return warped, True
    except Exception:
        return img_bgr, False
