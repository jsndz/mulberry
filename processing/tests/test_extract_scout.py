"""Unit tests for Stage 3 Macro Scout Sweep."""

import numpy as np
import pytest
from processing.extract.context.db import ContextDatabase
from processing.extract.context.retriever import ContextRetriever
from processing.extract.context.scout import MacroScoutSweep


def test_scout_crop_dimensions():
    canvas = np.zeros((1000, 800, 3), dtype=np.uint8)
    scout = MacroScoutSweep(scout_ratio=0.25)
    crop = scout.crop_scout_region(canvas)

    assert crop.shape == (250, 800, 3)


def test_scout_context_resolution():
    db = ContextDatabase(":memory:")
    db.seed_defaults()
    retriever = ContextRetriever(db=db)
    scout = MacroScoutSweep(retriever=retriever)

    canvas = np.zeros((800, 600, 3), dtype=np.uint8)
    crop = scout.crop_scout_region(canvas)

    ctx = scout.analyze_scout_crop(
        crop=crop,
        ocr_text_hint="1. CAP Theory: Distributed Systems",
        manual_glossary=["Paxos", "Raft"],
    )

    assert ctx["detected_topic"] == "Distributed Systems"
    assert "CAP Theory" in ctx["glossary"]
    assert "Paxos" in ctx["glossary"]
    assert "Raft" in ctx["glossary"]
    assert len(ctx["glossary_string"]) > 0
