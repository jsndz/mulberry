"""Export utilities for HCD-HTR output schemas and Mulberry Canonical Documents."""

import json
from pathlib import Path
from typing import Optional, Union

from processing.canonical.document import Document
from processing.extract.schemas import ExtractionDocument


def export_to_json(
    extraction_doc: ExtractionDocument,
    output_path: Union[str, Path],
    indent: int = 2,
) -> Path:
    """Save ExtractionDocument as formatted JSON."""
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(extraction_doc.model_dump_json(indent=indent))
    return p


def export_to_canonical(
    extraction_doc: ExtractionDocument,
    output_path: Optional[Union[str, Path]] = None,
) -> Document:
    """Convert ExtractionDocument into Mulberry Canonical Document and optionally save."""
    canonical_doc = extraction_doc.to_canonical_document()
    if output_path is not None:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(canonical_doc.model_dump_json(indent=2))
    return canonical_doc
