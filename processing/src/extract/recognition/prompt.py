"""Prompt formatting and context conditioning for VLM transcription."""

from typing import List, Optional


SYSTEM_PROMPT = """You are a verbatim OCR transcription engine.
Task: Transcribe the text from this image strip exactly as written.
Rules:
- Output ONLY the literal text shown in the image.
- Never summarize, correct spelling, or invent words.
- If handwriting matches a domain term, prioritize the exact domain term over generic phrases."""


def format_recognition_prompt(domain_glossary: Optional[List[str]] = None) -> str:
    """
    Constructs the prompt conditioned on the retrieved domain technical glossary.
    """
    if domain_glossary:
        glossary_string = ", ".join(domain_glossary)
        prompt = (
            f"Transcribe the text in this handwritten strip verbatim.\n"
            f"Domain Vocabulary: {glossary_string}\n"
            f"Output ONLY the text. Never normalize or change words."
        )
    else:
        prompt = (
            "Transcribe the text in this handwritten strip verbatim.\n"
            "Output ONLY the text. Never normalize or change words."
        )
    return prompt
