"""Reading-order topological sort for oriented polygons."""

from typing import List
from processing.extract.schemas import Polygon


def sort_lines_reading_order(
    polygons: List[Polygon],
    line_overlap_ratio: float = 0.5,
) -> List[Polygon]:
    """
    Sorts 4-point line polygons into natural reading order (top-to-bottom, left-to-right).

    Uses center-of-mass vertical position (y_bar) and horizontal indentation (x_bar):
    1. Sorts polygons by their vertical center of mass.
    2. Clusters polygons that fall into the same horizontal line band based on dynamic height tolerance.
    3. Sorts polygons within each line cluster from left to right.
    4. Flattens into a single ordered list reflecting document visual hierarchy.
    """
    if not polygons:
        return []

    if len(polygons) == 1:
        return list(polygons)

    # Initial sort by vertical center of mass
    sorted_by_y = sorted(polygons, key=lambda p: p.y_bar)

    lines: List[List[Polygon]] = []

    for poly in sorted_by_y:
        p_bbox = poly.to_bbox()
        p_height = max(1.0, p_bbox[3] - p_bbox[1])
        p_y = poly.y_bar
        placed = False

        for line in lines:
            line_y_avg = sum(p.y_bar for p in line) / float(len(line))
            line_h_avg = sum(p.to_bbox()[3] - p.to_bbox()[1] for p in line) / float(len(line))
            tolerance = max(8.0, line_h_avg * line_overlap_ratio)

            if abs(p_y - line_y_avg) <= tolerance:
                line.append(poly)
                placed = True
                break

        if not placed:
            lines.append([poly])

    # Sort lines vertically by top-most element or average y
    lines.sort(key=lambda line: sum(p.y_bar for p in line) / float(len(line)))

    # Sort elements within each line horizontally (left-to-right)
    ordered: List[Polygon] = []
    for line in lines:
        line_sorted = sorted(line, key=lambda p: p.x_bar)
        ordered.extend(line_sorted)

    return ordered
