"""Unit tests for SQLite ContextDatabase and ContextRetriever."""

import pytest
from processing.extract.context.db import ContextDatabase
from processing.extract.context.retriever import ContextRetriever


def test_context_db_initialization_and_seeding():
    db = ContextDatabase(":memory:")
    db.seed_defaults()

    # Verify seeded topic
    dist = db.get_domain_lexicon("dist_sys")
    assert dist is not None
    assert dist["topic_name"] == "Distributed Systems"
    assert "CAP Theory" in dist["keywords"]
    assert "Consensus" in [k.capitalize() for k in dist["keywords"]]


def test_find_lexicon_by_topic_or_text():
    db = ContextDatabase(":memory:")
    db.seed_defaults()

    # Query with header text
    res = db.find_lexicon_by_topic_or_text("Notes on Distributed Systems and CAP Theorem")
    assert res is not None
    assert res["topic_id"] == "dist_sys"

    res_ml = db.find_lexicon_by_topic_or_text("Lecture on Backpropagation and Gradient Descent")
    assert res_ml is not None
    assert res_ml["topic_id"] == "ml_ai"

    # Query with non-matching text
    res_none = db.find_lexicon_by_topic_or_text("Cooking recipes for apple pie")
    assert res_none is None


def test_author_profile_storage():
    db = ContextDatabase(":memory:")
    homoglyphs = {"c_looks_like": "e", "v_looks_like": "r"}
    db.add_author_profile("user_42", homoglyphs, "Writes in small cursive script")

    profile = db.get_author_profile("user_42")
    assert profile is not None
    assert profile["user_id"] == "user_42"
    assert profile["homoglyph_rules"]["c_looks_like"] == "e"
    assert "cursive" in profile["writing_quirks"]


def test_context_retriever():
    retriever = ContextRetriever()
    # Test topic resolution
    context = retriever.resolve_context(
        inferred_topic_or_text="CAP Theory and distributed nodes",
        manual_glossary=["custom_term_1"],
    )

    assert context["detected_topic"] == "Distributed Systems"
    assert "custom_term_1" in context["glossary"]
    assert "CAP Theory" in context["glossary"]
    assert "custom_term_1, " in context["glossary_string"]
