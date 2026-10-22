"""Unit tests for Stage 4 Line Recognition and Cropping."""

from unittest.mock import MagicMock
import numpy as np
from PIL import Image
import pytest

from processing.extract.recognition import (
    SYSTEM_PROMPT,
    QwenVLRecognizer,
    crop_line_strip,
    format_recognition_prompt,
)
from processing.extract.schemas import Polygon


def test_crop_line_strip_padding_and_bounds():
    canvas = np.zeros((400, 500, 3), dtype=np.uint8)
    poly = Polygon.from_bbox(50.0, 100.0, 200.0, 130.0)

    # pad_y=6, pad_x=12
    crop, bbox = crop_line_strip(canvas, poly, pad_y=6, pad_x=12)

    # Expected: xmin = 50-12=38, xmax = 200+12=212, ymin = 100-6=94, ymax = 130+6=136
    assert bbox == [38.0, 94.0, 212.0, 136.0]
    assert crop.shape == (136 - 94, 212 - 38, 3)


def test_crop_line_strip_boundary_clamping():
    canvas = np.zeros((200, 200, 3), dtype=np.uint8)
    # Box near edges
    poly = Polygon.from_bbox(2.0, 3.0, 198.0, 197.0)
    crop, bbox = crop_line_strip(canvas, poly, pad_y=10, pad_x=10)

    assert bbox == [0.0, 0.0, 200.0, 200.0]
    assert crop.shape == (200, 200, 3)


def test_format_recognition_prompt():
    prompt_no_glossary = format_recognition_prompt(None)
    assert "Transcribe the text in this handwritten strip verbatim." in prompt_no_glossary
    assert "Domain Vocabulary:" not in prompt_no_glossary

    prompt_with_glossary = format_recognition_prompt(["CAP Theory", "Consistency"])
    assert "Domain Vocabulary: CAP Theory, Consistency" in prompt_with_glossary


def test_qwen_vl_recognizer_with_mock_model():
    mock_manager = MagicMock()
    mock_manager.generate.return_value = "Every read receives most recent write or error."

    recognizer = QwenVLRecognizer(model_manager=mock_manager)
    img = Image.new("RGB", (100, 30), color="white")

    result = recognizer.transcribe_line(img, domain_glossary=["CAP Theory", "Consistency"])
    assert result == "Every read receives most recent write or error."

    # Verify generate called with greedy temperature=0.0 and glossary prompt
    call_kwargs = mock_manager.generate.call_args[1]
    assert call_kwargs["temperature"] == 0.0
    assert call_kwargs["do_sample"] is False
    assert "CAP Theory, Consistency" in call_kwargs["prompt"]
    assert call_kwargs["system_prompt"] == SYSTEM_PROMPT
