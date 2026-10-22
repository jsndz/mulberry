"""End-to-End Orchestrator for Hierarchical Context-Driven Handwriting Extraction (HCD-HTR)."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import cv2
import numpy as np
from PIL import Image

from processing.canonical.common import CoordinateUnit, SourceMedia
from processing.canonical.document import Document, DocumentMetadata, Page
from processing.extract.assembly.aligner import StructuralAligner
from processing.extract.config import ExtractionConfig, HardwareTier
from processing.extract.context.db import ContextDatabase
from processing.extract.context.retriever import ContextRetriever
from processing.extract.context.scout import MacroScoutSweep
from processing.extract.geometry.base import BaseLayoutSegmenter, BaseLineDetector
from processing.extract.geometry.layout import DiagramLayoutSegmenter
from processing.extract.geometry.line_detector import get_line_detector
from processing.extract.geometry.topological_sort import sort_lines_reading_order
from processing.extract.preprocessing.dewarp import dewarp_document
from processing.extract.preprocessing.illumination import apply_clahe_lab
from processing.extract.recognition.base import BaseLineRecognizer
from processing.extract.recognition.cropper import crop_line_strip
from processing.extract.recognition.trocr_recognizer import TrOCRRecognizer
from processing.extract.recognition.vlm_recognizer import QwenVLRecognizer
from processing.extract.schemas import ExtractionDocument
from processing.input import DocumentInputSplitter, PageInput
from processing.ocr.preprocessing import normalize_image

logger = logging.getLogger("mulberry.extract.pipeline")


class HandwritingExtractionPipeline:
    """
    Decoupled 5-stage HCD-HTR pipeline uniting Document Ingestion & Dewarping,
    Polygonal Layout & Line Detection, Dynamic Context Retrieval, and
    Context-Conditioned Line Recognition & Assembly.
    """

    def __init__(
        self,
        config: Optional[ExtractionConfig] = None,
        layout_segmenter: Optional[BaseLayoutSegmenter] = None,
        line_detector: Optional[BaseLineDetector] = None,
        context_retriever: Optional[ContextRetriever] = None,
        line_recognizer: Optional[BaseLineRecognizer] = None,
        aligner: Optional[StructuralAligner] = None,
    ) -> None:
        self.config = config or ExtractionConfig()

        # Stage 2: Geometric Segmenter & Line Detector
        self.layout_segmenter = layout_segmenter or DiagramLayoutSegmenter(
            force_device=self.config.device,
        )
        self.line_detector = line_detector or get_line_detector(
            tier=self.config.tier.value if hasattr(self.config.tier, "value") else str(self.config.tier),
        )

        # Stage 3: Semantic Path (SQLite Context DB & Scout)
        context_db = ContextDatabase(self.config.context_db_path)
        self.context_retriever = context_retriever or ContextRetriever(db=context_db)
        self.scout = MacroScoutSweep(
            retriever=self.context_retriever,
            scout_ratio=self.config.scout_ratio,
        )

        # Stage 4: Recognition Engine
        if line_recognizer is not None:
            self.line_recognizer = line_recognizer
        elif self.config.tier == HardwareTier.TIER_1_MAX_ACCURACY:
            self.line_recognizer = QwenVLRecognizer(
                model_name=self.config.vlm_model_id,
                device=self.config.device,
            )
        else:
            self.line_recognizer = TrOCRRecognizer()

        # Stage 5: Structural Aligner
        self.aligner = aligner or StructuralAligner()

    def process_document(
        self,
        image_input: Union[str, Path, Image.Image, np.ndarray],
        manual_glossary: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        document_id: Optional[str] = None,
    ) -> ExtractionDocument:
        """
        Executes the full 5-stage HCD-HTR extraction on an input document image.
        """
        # Load and normalize image into standard BGR format
        raw_bgr, orig_w, orig_h = normalize_image(image_input)

        # -------------------------------------------------------------
        # Stage 1: Document Conditioning & Preprocessing
        # -------------------------------------------------------------
        was_dewarped = False
        processed_bgr = raw_bgr.copy()

        if self.config.enable_dewarp:
            processed_bgr, was_dewarped = dewarp_document(processed_bgr)

        if self.config.enable_clahe:
            processed_bgr = apply_clahe_lab(
                processed_bgr,
                clip_limit=self.config.clahe_clip_limit,
                tile_grid_size=self.config.clahe_tile_grid_size,
            )

        cur_h, cur_w = processed_bgr.shape[:2]

        # -------------------------------------------------------------
        # Stage 2: Geometric Path (Layout & Polygonal Line Detection)
        # -------------------------------------------------------------
        # 2a. Isolate non-text regions (diagrams, tables, flowcharts, preprinted headers)
        non_text_elements = self.layout_segmenter.segment(processed_bgr)
        non_text_mask = DiagramLayoutSegmenter.create_non_text_mask((cur_h, cur_w), non_text_elements)

        # 2b. Extract oriented 4-point line polygons
        detected_polygons = self.line_detector.detect_lines(processed_bgr, non_text_mask=non_text_mask)

        # 2c. Reading-Order Topological Sort
        sorted_polygons = sort_lines_reading_order(detected_polygons)

        # -------------------------------------------------------------
        # Stage 3: Semantic Path (Macro Scout & Dynamic Context Engine)
        # -------------------------------------------------------------
        scout_crop = self.scout.crop_scout_region(processed_bgr)
        scout_context = self.scout.analyze_scout_crop(
            crop=scout_crop,
            author_id=author_id,
            manual_glossary=manual_glossary,
        )
        detected_topic = scout_context.get("detected_topic")
        domain_glossary = scout_context.get("glossary", [])

        # -------------------------------------------------------------
        # Stage 4: Context-Conditioned Line Recognition
        # -------------------------------------------------------------
        crops_pil: List[Image.Image] = []
        for poly in sorted_polygons:
            crop_bgr, _ = crop_line_strip(
                processed_bgr,
                poly,
                pad_y=self.config.pad_y,
                pad_x=self.config.pad_x,
            )
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            crops_pil.append(Image.fromarray(crop_rgb))

        transcriptions = self.line_recognizer.batch_transcribe(
            crops_pil,
            domain_glossary=domain_glossary,
        )

        # -------------------------------------------------------------
        # Stage 5: Structural Alignment & Assembly
        # -------------------------------------------------------------
        extraction_doc = self.aligner.assemble(
            polygons=sorted_polygons,
            transcriptions=transcriptions,
            canvas_width=cur_w,
            canvas_height=cur_h,
            non_text_elements=non_text_elements,
            detected_topic=detected_topic,
            document_id=document_id,
            extra_metadata={
                "dewarp_applied": was_dewarped,
                "tier": str(self.config.tier),
                "num_lines": len(sorted_polygons),
                "num_non_text": len(non_text_elements),
            },
        )

        return extraction_doc

    def process_multipage(
        self,
        input_source: Union[str, Path, bytes, Image.Image, np.ndarray, List[Any]],
        manual_glossary: Optional[List[str]] = None,
        author_id: Optional[str] = None,
        document_id: Optional[str] = None,
        dpi: int = 300,
        progress_callback: Optional[Any] = None,
    ) -> Document:
        """
        Process any input (single image, RAW/DNG, multi-page PDF, or list of files)
        and assemble the extracted results into a unified multi-page canonical Document.
        """
        from uuid import uuid4

        splitter = DocumentInputSplitter()
        pages: List[Page] = []
        doc_id = document_id or f"doc_{uuid4().hex[:8]}"
        overall_topic: Optional[str] = None

        pages_stream = list(splitter.split(input_source, dpi=dpi))
        total_pages = len(pages_stream)

        for page_input in pages_stream:
            # Run extraction on individual page canvas
            extraction = self.process_document(
                image_input=page_input.image_bgr,
                manual_glossary=manual_glossary,
                author_id=author_id,
                document_id=f"{doc_id}_p{page_input.page_number}",
            )

            if overall_topic is None and extraction.metadata.detected_topic:
                overall_topic = extraction.metadata.detected_topic

            canonical_single = extraction.to_canonical_document()
            page = canonical_single.pages[0]
            page.page_number = page_input.page_number
            page.source_media = SourceMedia(
                file_path=page_input.source_file,
                media_type=page_input.media_type,
                original_page_number=page_input.metadata.get("original_page_number", page_input.page_number),
                dpi=page_input.dpi,
            )
            pages.append(page)

            if progress_callback is not None:
                try:
                    progress_callback(page_input.page_number, total_pages)
                except Exception as e:
                    logger.warning(f"Error executing progress callback: {e}")

        source_file_str = str(input_source) if isinstance(input_source, (str, Path)) else None

        return Document(
            id=doc_id,
            metadata=DocumentMetadata(
                title=overall_topic,
                source_file=source_file_str,
                generator_version="HCD-HTR-1.0",
                extra_metadata={
                    "total_pages": total_pages,
                    "tier": str(self.config.tier),
                },
            ),
            pages=pages,
        )
