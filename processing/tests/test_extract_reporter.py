"""Tests for StageReporter and stage callback telemetry in HCD-HTR extraction."""

import io
from unittest.mock import MagicMock
import numpy as np
import pytest

from processing.extract.config import ExtractionConfig, HardwareTier
from processing.extract.geometry.base import BaseLayoutSegmenter, BaseLineDetector
from processing.extract.pipeline import HandwritingExtractionPipeline
from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.reporter import StageReporter
from processing.extract.schemas import NonTextElement, Polygon


class MockSegmenter(BaseLayoutSegmenter):
    def segment(self, image):
        return [
            NonTextElement(
                id="fig_1",
                type="diagram",
                polygon=Polygon.from_bbox(10, 10, 100, 100).to_list(),
            )
        ]


class MockDetector(BaseLineDetector):
    def detect_lines(self, image, non_text_mask=None):
        return [
            Polygon.from_bbox(50, 120, 400, 150),
            Polygon.from_bbox(50, 160, 400, 190),
        ]


class MockRecognizer(BaseLineRecognizer):
    def transcribe_line(self, crop_pil, domain_glossary=None):
        return "Transcribed Line Sample"


def test_stage_reporter_formatting():
    output = io.StringIO()
    reporter = StageReporter(verbose=True, stream=output)

    # Stage 1
    reporter.on_stage_event(1, "Preprocessing & Conditioning", "completed", {
        "orig_size": (1000, 2000),
        "processed_size": (1000, 2000),
        "dewarp_applied": True,
        "clahe_applied": True,
    })

    # Stage 2
    reporter.on_stage_event(2, "Geometric Layout & Line Detection", "completed", {
        "layout_segmenter": "DiagramLayoutSegmenter",
        "non_text_count": 1,
        "non_text_types": ["diagram"],
        "line_detector": "PaddleDBNetLineDetector",
        "line_detector_fallback": False,
        "detected_lines_count": 2,
        "sorted_lines_count": 2,
    })

    # Stage 3
    reporter.on_stage_event(3, "Semantic Macro Scout & Context", "completed", {
        "scout_crop_shape": (150, 1000),
        "detected_topic": "Distributed Systems",
        "domain_glossary_count": 3,
        "domain_glossary_sample": ["CAP", "PACELC", "Consensus"],
    })

    # Stage 4
    reporter.on_stage_event(4, "Context-Conditioned Line Recognition", "completed", {
        "recognizer": "TrOCRRecognizer",
        "num_lines": 2,
        "transcriptions": ["Line One Content", "Line Two Content"],
    })

    # Stage 5
    reporter.on_stage_event(5, "Structural Alignment & Assembly", "completed", {
        "aligner": "StructuralAligner",
        "num_blocks": 2,
        "blocks_summary": [
            {"type": "heading", "level": 1, "content": "Line One Content"},
            {"type": "paragraph", "level": None, "content": "Line Two Content", "num_lines": 1},
        ],
    })

    text = output.getvalue()
    assert "[Stage 1/5] Preprocessing & Conditioning" in text
    assert "Perspective dewarping: Applied" in text
    assert "[Stage 2/5] Geometric Layout & Line Detection" in text
    assert "Detected lines: 2 line polygons" in text
    assert "[Stage 3/5] Semantic Macro Scout & Context" in text
    assert 'Detected topic: "Distributed Systems"' in text
    assert "[Stage 4/5] Context-Conditioned Line Recognition" in text
    assert 'Line One Content' in text
    assert "[Stage 5/5] Structural Alignment & Assembly" in text
    assert "Assembled 2 semantic blocks" in text


def test_stage_reporter_quiet_mode():
    output = io.StringIO()
    reporter = StageReporter(quiet=True, stream=output)

    reporter.on_stage_event(1, "Preprocessing & Conditioning", "completed", {})
    assert output.getvalue() == ""


def test_stage_reporter_error_event():
    output = io.StringIO()
    reporter = StageReporter(stream=output)

    reporter.on_stage_event(4, "Context-Conditioned Line Recognition", "error", {
        "error": "CUDA out of memory",
        "exception_type": "OutOfMemoryError",
    })

    text = output.getvalue()
    assert "STAGE 4 FAILED: [OutOfMemoryError] CUDA out of memory" in text


def test_pipeline_fires_stage_callbacks():
    events = []

    def callback(stage_num, stage_name, status, details):
        events.append((stage_num, stage_name, status))

    canvas = np.full((300, 400, 3), 255, dtype=np.uint8)
    config = ExtractionConfig(
        tier=HardwareTier.TIER_3_EDGE_CPU,
        enable_dewarp=False,
        enable_clahe=False,
    )

    pipeline = HandwritingExtractionPipeline(
        config=config,
        layout_segmenter=MockSegmenter(),
        line_detector=MockDetector(),
        line_recognizer=MockRecognizer(),
    )

    doc = pipeline.process_document(
        image_input=canvas,
        stage_callback=callback,
    )

    assert doc is not None
    completed_stages = [stage_num for stage_num, _, status in events if status == "completed"]
    assert completed_stages == [1, 2, 3, 4, 5]


def test_visual_debugger_artifacts(tmp_path):
    from processing.extract.visual_debugger import VisualDebugger

    debugger = VisualDebugger(tmp_path)
    canvas = np.full((300, 400, 3), 255, dtype=np.uint8)

    # Stage 1
    s1 = debugger.save_stage_1(canvas, was_dewarped=True, was_clahe=True)
    assert len(s1) == 1
    assert (tmp_path / "stage1_preprocessed.png").exists()

    # Stage 2
    polys = [Polygon.from_bbox(10, 20, 100, 40), Polygon.from_bbox(10, 60, 100, 80)]
    elems = [NonTextElement(id="e1", type="diagram", polygon=Polygon.from_bbox(150, 20, 250, 120).to_list())]
    mask = np.zeros((300, 400), dtype=np.uint8)
    mask[20:120, 150:250] = 255
    s2 = debugger.save_stage_2(canvas, elems, polys, non_text_mask=mask)
    assert (tmp_path / "stage2_layout_and_lines.png").exists()
    assert (tmp_path / "stage2_non_text_mask.png").exists()

    # Stage 3
    scout = canvas[:50, :]
    s3 = debugger.save_stage_3(scout, detected_topic="Test Topic")
    assert (tmp_path / "stage3_scout_crop.png").exists()

    # Stage 4
    crops = [np.full((30, 120, 3), 200, dtype=np.uint8), np.full((30, 120, 3), 220, dtype=np.uint8)]
    transcriptions = ["Line 1", "Line 2"]
    s4 = debugger.save_stage_4(crops, transcriptions)
    assert (tmp_path / "stage4_line_crops" / "line_001.png").exists()
    assert (tmp_path / "stage4_line_crops" / "line_002.png").exists()
    assert (tmp_path / "stage4_line_strip_sheet.png").exists()


def test_pipeline_generates_visual_artifacts_in_debug_dir(tmp_path):
    canvas = np.full((300, 400, 3), 255, dtype=np.uint8)
    config = ExtractionConfig(
        tier=HardwareTier.TIER_3_EDGE_CPU,
        enable_dewarp=False,
        enable_clahe=False,
    )

    pipeline = HandwritingExtractionPipeline(
        config=config,
        layout_segmenter=MockSegmenter(),
        line_detector=MockDetector(),
        line_recognizer=MockRecognizer(),
    )

    events = []

    def callback(stage_num, stage_name, status, details):
        if status == "completed":
            events.append((stage_num, details.get("artifacts", [])))

    doc = pipeline.process_document(
        image_input=canvas,
        stage_callback=callback,
        debug_dir=tmp_path,
    )

    assert doc is not None
    assert (tmp_path / "stage1_preprocessed.png").exists()
    assert (tmp_path / "stage2_layout_and_lines.png").exists()
    assert (tmp_path / "stage4_line_strip_sheet.png").exists()
    assert (tmp_path / "stage5_annotated_blocks.png").exists()

