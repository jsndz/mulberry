"""Real-time stage-by-stage diagnostics and execution reporter for HCD-HTR Extraction."""

import sys
from typing import Any, Dict, List, Optional


class StageReporter:
    """Formats and prints real-time stage execution diagnostics to stdout/stderr.
    
    Provides transparent visibility into all 5 extraction stages:
    - Stage 1: Document Conditioning & Preprocessing (Dewarping, CLAHE, Dimensions)
    - Stage 2: Geometric Path (Layout/Diagram Segmentation, Line Detection, 2D Reading Order)
    - Stage 3: Semantic Path (Macro Scout Sweep, Topic Identification, Domain Vocabulary)
    - Stage 4: Context-Conditioned Line Strip Recognition (Transcriptions preview)
    - Stage 5: Structural Alignment & Assembly (Blocks hierarchy)
    """

    def __init__(self, verbose: bool = False, quiet: bool = False, stream=None) -> None:
        self.verbose = verbose
        self.quiet = quiet
        self.stream = stream or sys.stdout

    def on_stage_event(
        self,
        stage_num: int,
        stage_name: str,
        status: str,
        details: Dict[str, Any],
    ) -> None:
        """Handler for stage callbacks dispatched from HandwritingExtractionPipeline."""
        if self.quiet:
            return

        if status == "start":
            self._print_stage_start(stage_num, stage_name, details)
        elif status == "completed":
            self._print_stage_completed(stage_num, stage_name, details)
        elif status == "error":
            self._print_stage_error(stage_num, stage_name, details)

    def _print(self, text: str = "") -> None:
        print(text, file=self.stream, flush=True)

    def _print_stage_start(self, stage_num: int, stage_name: str, details: Dict[str, Any]) -> None:
        if self.verbose:
            self._print(f"⏳ Starting [Stage {stage_num}/5] {stage_name}...")

    def _print_stage_completed(self, stage_num: int, stage_name: str, details: Dict[str, Any]) -> None:
        self._print(f"┌── [Stage {stage_num}/5] {stage_name}")

        if stage_num == 1:
            orig = details.get("orig_size", (0, 0))
            proc = details.get("processed_size", orig)
            dewarp = details.get("dewarp_applied", False)
            clahe = details.get("clahe_applied", False)

            self._print(f"│  • Input dimensions: {orig[0]}x{orig[1]} px (BGR)")
            if dewarp:
                self._print(f"│  • Perspective dewarping: Applied (dewarped to {proc[0]}x{proc[1]} px)")
            else:
                self._print(f"│  • Perspective dewarping: Skipped / No distortion detected")

            if clahe:
                self._print(f"│  • Illumination (CLAHE): Applied (flattened shadow gradients in LAB space)")
            else:
                self._print(f"│  • Illumination (CLAHE): Disabled")

            self._print(f"│  • Canvas output: {proc[0]}x{proc[1]} px")

        elif stage_num == 2:
            segmenter = details.get("layout_segmenter", "DiagramLayoutSegmenter")
            non_text_count = details.get("non_text_count", 0)
            non_text_types = details.get("non_text_types", [])
            detector = details.get("line_detector", "BaseLineDetector")
            fallback_used = details.get("line_detector_fallback", False)
            fallback_reason = details.get("line_detector_fallback_reason")
            lines_detected = details.get("detected_lines_count", 0)
            lines_sorted = details.get("sorted_lines_count", 0)

            self._print(f"│  • Layout segmenter: {segmenter}")
            if non_text_count > 0:
                self._print(f"│    └─ Non-text elements: {non_text_count} detected ({', '.join(non_text_types)})")
            else:
                self._print(f"│    └─ Non-text elements: 0 detected (diagrams/tables/sketches)")

            self._print(f"│  • Line detector: {detector}")
            if fallback_used:
                self._print(f"│    ⚠️ FALLBACK ACTIVE: Fell back to MorphologyLineDetector ({fallback_reason})")
            self._print(f"│    └─ Detected lines: {lines_detected} line polygons")
            if lines_detected == 0:
                self._print(f"│    ⚠️ WARNING: 0 line polygons detected! Check contrast or detector configuration.")
            else:
                self._print(f"│  • Reading order: {lines_sorted} lines topologically sorted (top-to-bottom, left-to-right)")

        elif stage_num == 3:
            topic = details.get("detected_topic")
            glossary_count = details.get("domain_glossary_count", 0)
            sample = details.get("domain_glossary_sample", [])
            scout_crop = details.get("scout_crop_shape")

            if scout_crop:
                self._print(f"│  • Macro scout sweep: Analyzed top region ({scout_crop[1]}x{scout_crop[0]} px)")
            if topic:
                self._print(f"│  • Detected topic: \"{topic}\"")
            else:
                self._print(f"│  • Detected topic: None (no header keywords identified)")

            if glossary_count > 0:
                sample_str = ", ".join(f"'{g}'" for g in sample[:5])
                if glossary_count > 5:
                    sample_str += f", +{glossary_count - 5} more"
                self._print(f"│  • Domain vocabulary: {glossary_count} terms retrieved ({sample_str})")
            else:
                self._print(f"│  • Domain vocabulary: None retrieved")

        elif stage_num == 4:
            recognizer = details.get("recognizer", "BaseLineRecognizer")
            lines = details.get("transcriptions", [])
            num_lines = len(lines)

            self._print(f"│  • Recognizer engine: {recognizer}")
            self._print(f"│  • Transcribed {num_lines} line strips:")

            max_show = num_lines if (self.verbose or num_lines <= 30) else 15
            for i in range(min(num_lines, max_show)):
                snippet = lines[i].replace("\n", " ").strip()
                if len(snippet) > 75 and not self.verbose:
                    snippet = snippet[:72] + "..."
                self._print(f"│    [{i+1:02d}/{num_lines:02d}] \"{snippet}\"")

            if num_lines > max_show:
                self._print(f"│    ... ({num_lines - max_show} more lines transcribed, use --verbose to view all) ...")

        elif stage_num == 5:
            aligner = details.get("aligner", "StructuralAligner")
            num_blocks = details.get("num_blocks", 0)
            blocks = details.get("blocks_summary", [])

            self._print(f"│  • Structural aligner: {aligner}")
            self._print(f"│  • Assembled {num_blocks} semantic blocks:")

            for b in blocks[:15]:
                b_type = b.get("type", "paragraph")
                level = b.get("level")
                prefix = f"H{level}" if b_type == "heading" else b_type.capitalize()
                content = (b.get("content") or "").replace("\n", " ").strip()
                if len(content) > 70 and not self.verbose:
                    content = content[:67] + "..."
                line_info = f" ({b.get('num_lines')} lines)" if b_type == "paragraph" and b.get("num_lines", 0) > 1 else ""
                self._print(f"│    ├─ [{prefix}{line_info}] {content}")

            if len(blocks) > 15:
                self._print(f"│    └─ ... ({len(blocks) - 15} more blocks) ...")

        artifacts = details.get("artifacts", [])
        if artifacts:
            self._print("│  • Visual debug artifacts saved:")
            for art in artifacts:
                self._print(f"│    └─ {art}")

        self._print(f"└── ✅ Stage {stage_num} Complete\n")

    def _print_stage_error(self, stage_num: int, stage_name: str, details: Dict[str, Any]) -> None:
        self._print(f"\n┌── [Stage {stage_num}/5] {stage_name}")
        err = details.get("error", "Unknown error")
        exc_type = details.get("exception_type", "Exception")
        self._print(f"│  ❌ STAGE {stage_num} FAILED: [{exc_type}] {err}")
        self._print(f"└── ❌ Stage {stage_num} Terminated\n")
