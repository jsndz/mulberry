"""Dynamic context resolver and glossary retrieval engine."""

from typing import Any, Dict, List, Optional
from processing.extract.context.db import ContextDatabase


class ContextRetriever:
    """Queries and formats domain vocabulary and author profiles for VLM prompt injection."""

    def __init__(self, db: Optional[ContextDatabase] = None) -> None:
        self.db = db or ContextDatabase()
        self.db.seed_defaults()

    def resolve_context(
        self,
        inferred_topic_or_text: Optional[str] = None,
        author_id: Optional[str] = None,
        manual_glossary: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Resolves domain glossary keywords/phrases and author homoglyph rules.

        Returns:
            Dict containing:
            - 'detected_topic': str or None
            - 'glossary': List[str]
            - 'glossary_string': str (comma-separated for prompt injection)
            - 'homoglyph_rules': Dict[str, str]
        """
        glossary: List[str] = []
        detected_topic: Optional[str] = None
        homoglyph_rules: Dict[str, str] = {}

        # 1. Manual glossary takes initial priority if provided
        if manual_glossary:
            glossary.extend(manual_glossary)

        # 2. Dynamic lookup from SQLite context DB based on inferred scout text / topic
        if inferred_topic_or_text:
            match = self.db.find_lexicon_by_topic_or_text(inferred_topic_or_text)
            if match:
                detected_topic = match["topic_name"]
                for kw in match.get("keywords", []):
                    if kw not in glossary:
                        glossary.append(kw)

        # 3. Lookup author quirks/homoglyph rules if author_id provided
        if author_id:
            profile = self.db.get_author_profile(author_id)
            if profile and "homoglyph_rules" in profile:
                homoglyph_rules = profile["homoglyph_rules"]

        return {
            "detected_topic": detected_topic,
            "glossary": glossary,
            "glossary_string": ", ".join(glossary) if glossary else "",
            "homoglyph_rules": homoglyph_rules,
        }
