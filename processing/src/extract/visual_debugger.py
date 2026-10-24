"""Visual debugging and stage artifact generation for HCD-HTR extraction."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np

from processing.extract.schemas import ExtractionDocument, NonTextElement, Polygon

logger = logging.getLogger("mulberry.extract.visual_debugger")


class VisualDebugger:
    """Generates and persists visual diagnostic artifacts for each stage of HCD-HTR.

    Artifacts generated per stage:
    - Stage 1: 'stage1_preprocessed.png' (Dewarped & CLAHE illumination-flattened canvas)
    - Stage 2: 'stage2_layout_and_lines.png' (Non-text boxes + line polygons with reading-order badges)
               'stage2_non_text_mask.png' (Binary mask for excluded regions)
    - Stage 3: 'stage3_scout_crop.png' (Macro-scout header crop for topic detection)
    - Stage 4: 'stage4_line_crops/' (Individual cropped line strips)
               'stage4_line_strip_sheet.png' (Contact sheet comparing line crops vs transcriptions)
    - Stage 5: 'stage5_annotated_blocks.png' (Document canvas overlaid with semantic block hierarchy)
    """

    def __init__(self, debug_dir: Union[str, Path]) -> None:
        self.debug_dir = Path(debug_dir).resolve()
        self.debug_dir.mkdir(parents=True, exist_ok=True)

    def save_stage_1(
        self,
        processed_bgr: np.ndarray,
        was_dewarped: bool,
        was_clahe: bool,
    ) -> List[str]:
        """Save preprocessed canvas from Stage 1."""
        saved: List[str] = []
        out_path = self.debug_dir / "stage1_preprocessed.png"
        cv2.imwrite(str(out_path), processed_bgr)
        saved.append(str(out_path))
        return saved

    def save_stage_2(
        self,
        canvas_bgr: np.ndarray,
        non_text_elements: List[NonTextElement],
        sorted_polygons: List[Polygon],
        non_text_mask: Optional[np.ndarray] = None,
    ) -> List[str]:
        """Save layout elements and line polygons overlaid on canvas with reading-order badges."""
        saved: List[str] = []
        vis = canvas_bgr.copy()
        h, w = vis.shape[:2]

        # 1. Draw non-text elements (diagrams, tables, sketches)
        for elem in non_text_elements:
            pts = np.array(elem.polygon, dtype=np.int32)
            cv2.polylines(vis, [pts], isClosed=True, color=(0, 140, 255), thickness=3)
            # Label
            xmin = int(min(p[0] for p in elem.polygon))
            ymin = int(min(p[1] for p in elem.polygon))
            label = f"[{elem.type.upper()}]"
            cv2.putText(
                vis,
                label,
                (max(0, xmin), max(20, ymin - 6)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 140, 255),
                2,
                cv2.LINE_AA,
            )

        # 2. Draw line polygons with reading order sequence badges
        for idx, poly in enumerate(sorted_polygons):
            pts = np.array(poly.points, dtype=np.int32)
            cv2.polylines(vis, [pts], isClosed=True, color=(0, 220, 0), thickness=2)

            # Draw sequence index badge (1, 2, 3...) at the top-left vertex
            xmin, ymin, _, _ = poly.to_bbox()
            badge_text = str(idx + 1)
            badge_pos = (max(5, int(xmin)), max(18, int(ymin) - 4))
            
            # Badge background pill
            (t_w, t_h), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.rectangle(
                vis,
                (badge_pos[0] - 2, badge_pos[1] - t_h - 2),
                (badge_pos[0] + t_w + 2, badge_pos[1] + 2),
                (0, 180, 0),
                -1,
            )
            cv2.putText(
                vis,
                badge_text,
                badge_pos,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        out_path = self.debug_dir / "stage2_layout_and_lines.png"
        cv2.imwrite(str(out_path), vis)
        saved.append(str(out_path))

        # 3. Optional: save binary non-text mask if any non-text elements exist
        if non_text_mask is not None and np.any(non_text_mask > 0):
            mask_path = self.debug_dir / "stage2_non_text_mask.png"
            cv2.imwrite(str(mask_path), non_text_mask)
            saved.append(str(mask_path))

        return saved

    def save_stage_3(
        self,
        scout_crop: Optional[np.ndarray],
        detected_topic: Optional[str] = None,
    ) -> List[str]:
        """Save macro-scout header crop from Stage 3."""
        saved: List[str] = []
        if scout_crop is not None and scout_crop.size > 0:
            out_path = self.debug_dir / "stage3_scout_crop.png"
            cv2.imwrite(str(out_path), scout_crop)
            saved.append(str(out_path))
        return saved

    def save_stage_4(
        self,
        line_crops_bgr: List[np.ndarray],
        transcriptions: List[str],
    ) -> List[str]:
        """Save individual line crops and a combined contact sheet comparing crops to transcriptions."""
        saved: List[str] = []
        if not line_crops_bgr:
            return saved

        # 1. Save individual line strips into stage4_line_crops/
        crops_dir = self.debug_dir / "stage4_line_crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        for idx, crop in enumerate(line_crops_bgr):
            crop_path = crops_dir / f"line_{idx + 1:03d}.png"
            cv2.imwrite(str(crop_path), crop)

        saved.append(str(crops_dir))

        # 2. Build visual contact sheet (crop on left, transcribed text on right)
        sheet_path = self.debug_dir / "stage4_line_strip_sheet.png"
        try:
            self._generate_contact_sheet(line_crops_bgr, transcriptions, sheet_path)
            saved.append(str(sheet_path))
        except Exception as e:
            logger.warning(f"Failed to generate line strip contact sheet: {e}")

        return saved

    def save_stage_5(
        self,
        canvas_bgr: np.ndarray,
        extraction_doc: ExtractionDocument,
    ) -> List[str]:
        """Save document canvas overlaid with recognized semantic block hierarchy."""
        saved: List[str] = []
        vis = canvas_bgr.copy()

        # Colors: H1: purple, H2: orange, Paragraph: blue, List: teal, Default: gray
        type_colors = {
            "h1": (220, 20, 180),
            "h2": (0, 140, 255),
            "paragraph": (220, 100, 0),
            "list": (180, 180, 0),
            "diagram": (0, 0, 240),
        }

        for block in extraction_doc.text_blocks:
            b_type = (block.type or "paragraph").lower()
            if b_type == "heading" and block.level == 1:
                color = type_colors["h1"]
                prefix = "H1"
            elif b_type == "heading":
                color = type_colors["h2"]
                prefix = f"H{block.level or 2}"
            else:
                color = type_colors.get(b_type, (120, 120, 120))
                prefix = b_type.capitalize()

            if block.polygon:
                pts = np.array(block.polygon, dtype=np.int32)
                cv2.polylines(vis, [pts], isClosed=True, color=color, thickness=2)
                xmin = int(min(p[0] for p in block.polygon))
                ymin = int(min(p[1] for p in block.polygon))
            elif block.lines:
                all_pts = [pt for l in block.lines for pt in l.polygon]
                xmin = int(min(p[0] for p in all_pts))
                ymin = int(min(p[1] for p in all_pts))
                xmax = int(max(p[0] for p in all_pts))
                ymax = int(max(p[1] for p in all_pts))
                cv2.rectangle(vis, (xmin, ymin), (xmax, ymax), color, thickness=2)
            else:
                continue

            content = block.content or (block.lines[0].content if block.lines else "")
            short_content = content[:40] + "..." if len(content) > 40 else content
            label = f"[{prefix}] {short_content}"

            (t_w, t_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            label_ymin = max(18, ymin - 4)
            cv2.rectangle(
                vis,
                (max(0, xmin), label_ymin - t_h - 2),
                (max(0, xmin) + t_w + 4, label_ymin + 2),
                color,
                -1,
            )
            cv2.putText(
                vis,
                label,
                (max(2, xmin + 2), label_ymin),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        out_path = self.debug_dir / "stage5_annotated_blocks.png"
        cv2.imwrite(str(out_path), vis)
        saved.append(str(out_path))
        return saved

    def _generate_contact_sheet(
        self,
        crops_bgr: List[np.ndarray],
        transcriptions: List[str],
        output_path: Path,
    ) -> None:
        """Create a vertical contact sheet displaying line image crops next to transcriptions."""
        strip_h = 50
        max_crop_w = 650
        text_panel_w = 600
        total_w = max_crop_w + text_panel_w + 30

        rows: List[np.ndarray] = []

        for idx, (crop, text) in enumerate(zip(crops_bgr, transcriptions)):
            # Normalize crop height to strip_h preserving aspect ratio
            c_h, c_w = crop.shape[:2]
            scale = strip_h / max(c_h, 1)
            scaled_w = min(int(c_w * scale), max_crop_w)
            scaled_crop = cv2.resize(crop, (scaled_w, strip_h), interpolation=cv2.INTER_AREA)

            row = np.full((strip_h + 6, total_w, 3), 255, dtype=np.uint8)

            # Draw divider line between rows
            cv2.line(row, (0, strip_h + 5), (total_w, strip_h + 5), (230, 230, 230), 1)

            # Paste line crop at left
            row[3:3 + strip_h, 10:10 + scaled_w] = scaled_crop

            # Divider line between crop and text
            cv2.line(row, (max_crop_w + 15, 3), (max_crop_w + 15, strip_h + 3), (210, 210, 210), 1)

            # Text label
            label = f"[{idx + 1:02d}] {text}"
            cv2.putText(
                row,
                label,
                (max_crop_w + 25, int(strip_h * 0.65)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.48,
                (20, 20, 20),
                1,
                cv2.LINE_AA,
            )

            rows.append(row)

        if rows:
            sheet = np.vstack(rows)
            cv2.imwrite(str(output_path), sheet)
