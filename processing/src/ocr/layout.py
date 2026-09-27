"""Spatial reading-order and layout analysis stage for Mulberry OCR results."""

from typing import List
from processing.ocr.models import TextRegion


def assign_reading_order(regions: List[TextRegion]) -> List[TextRegion]:
    """Sort text regions into natural top-to-bottom, left-to-right reading order.

    Algorithm:
    1. Sort regions vertically by top y-coordinate.
    2. Group regions that overlap vertically or lie on the same horizontal text line.
    3. Sort regions within each line group from left to right by x-coordinate.
    4. Assign 0-indexed integer `reading_order` to each region.
    5. Return updated list of TextRegion items with original coordinates preserved.
    """
    if not regions:
        return []

    # Sort initially by top y coordinate
    sorted_by_y = sorted(regions, key=lambda r: r.bbox.y)

    lines: List[List[TextRegion]] = []
    for region in sorted_by_y:
        placed = False
        r_y_center = region.bbox.y + (region.bbox.height / 2.0)
        r_height = max(1.0, region.bbox.height)

        for line in lines:
            # Check overlap against average vertical center of current line
            line_y_centers = [r.bbox.y + (r.bbox.height / 2.0) for r in line]
            line_avg_center = sum(line_y_centers) / float(len(line_y_centers))
            line_avg_height = sum(r.bbox.height for r in line) / float(len(line))

            # Vertical tolerance threshold: half of average line height
            tolerance = max(8.0, line_avg_height * 0.5)

            if abs(r_y_center - line_avg_center) <= tolerance:
                line.append(region)
                placed = True
                break

        if not placed:
            lines.append([region])

    # Sort lines top-to-bottom, and sort items within each line left-to-right
    lines.sort(key=lambda line: sum(r.bbox.y for r in line) / float(len(line)))

    ordered_regions: List[TextRegion] = []
    reading_order_idx = 0

    for line in lines:
        line_sorted = sorted(line, key=lambda r: r.bbox.x)
        for reg in line_sorted:
            # Create updated TextRegion copy with assigned reading order
            updated_reg = reg.model_copy(update={"reading_order": reading_order_idx})
            ordered_regions.append(updated_reg)
            reading_order_idx += 1

    return ordered_regions
