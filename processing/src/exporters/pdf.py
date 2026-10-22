"""Searchable PDF document exporter using ReportLab Platypus."""

import html
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from processing.canonical.document import Document, Page
from processing.canonical.element import EquationElement, ImageElement, TableElement
from processing.canonical.text import TextElement, TextKind
from processing.exporters.base import BaseExporter
from processing.exporters.options import PdfExportOptions

PAGE_SIZES: Dict[str, Tuple[float, float]] = {
    "A4": A4,
    "LETTER": LETTER,
}


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas for dynamic total page counting and running headers/footers."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_decorations(self, total_pages: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748B"))

        # Footer: "Page X of Y"
        page_str = f"Page {self._pageNumber} of {total_pages}"
        width, height = self._pagesize
        self.drawRightString(width - 36, 20, page_str)

        # Subtle footer separator
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(36, 32, width - 36, 32)

        self.restoreState()


class PdfExporter(BaseExporter[PdfExportOptions]):
    """Exports Canonical Document to a clean, searchable, multi-page PDF."""

    def export(
        self,
        document: Document,
        output_path: Optional[Union[str, Path]] = None,
        options: Optional[PdfExportOptions] = None,
    ) -> bytes:
        """Export canonical document to PDF bytes or file."""
        opts = options or PdfExportOptions()
        buf = io.BytesIO()

        pagesize = PAGE_SIZES.get(opts.page_size.upper(), A4)
        margin = opts.margin_pt

        doc = SimpleDocTemplate(
            buf,
            pagesize=pagesize,
            leftMargin=margin,
            rightMargin=margin,
            topMargin=margin,
            bottomMargin=margin + 12.0,  # extra space for running footer
            title=document.metadata.title or "Mulberry Document",
            author=document.metadata.author or "Mulberry",
        )

        styles = self._create_styles(opts)
        story: List[Any] = []

        # 1. Document Title & Subtitle Banner (if present)
        if document.metadata.title:
            story.append(Paragraph(html.escape(document.metadata.title), styles["DocTitle"]))
            subtitle_parts: List[str] = []
            if document.metadata.author:
                subtitle_parts.append(f"Author: {html.escape(document.metadata.author)}")
            if document.metadata.created_at:
                subtitle_parts.append(document.metadata.created_at.strftime("%Y-%m-%d"))
            if subtitle_parts:
                story.append(
                    Paragraph(" &bull; ".join(subtitle_parts), styles["DocSubtitle"])
                )
            story.append(Spacer(1, 14))

        # 2. Iterate pages and elements
        for page_idx, page in enumerate(document.pages):
            if page_idx > 0 and opts.page_break_between_pages:
                story.append(PageBreak())

            for elem in page.elements:
                elem_type = getattr(elem, "type", None)

                if elem_type == "text" and isinstance(elem, TextElement):
                    flowable = self._create_text_flowable(elem, styles)
                    if flowable:
                        story.append(flowable)

                elif elem_type == "table" and isinstance(elem, TableElement):
                    flowables = self._create_table_flowables(elem, styles, doc.width)
                    story.extend(flowables)

                elif elem_type == "equation" and isinstance(elem, EquationElement):
                    eq_flowable = self._create_equation_flowable(elem, styles)
                    if eq_flowable:
                        story.append(eq_flowable)

                elif elem_type == "image" and isinstance(elem, ImageElement):
                    img_flowable = self._create_image_flowable(elem, styles, doc.width)
                    if img_flowable:
                        story.append(img_flowable)

                elif elem_type == "diagram":
                    # Silently skip diagrams per specification
                    continue

        # Build document with or without NumberedCanvas
        canvasmaker = NumberedCanvas if opts.include_page_numbers else canvas.Canvas
        doc.build(story, canvasmaker=canvasmaker)

        pdf_bytes = buf.getvalue()

        if output_path:
            self._write_output(pdf_bytes, output_path)

        return pdf_bytes

    def _create_styles(self, opts: PdfExportOptions) -> Dict[str, ParagraphStyle]:
        """Construct custom typography stylesheet for document elements."""
        base_styles = getSampleStyleSheet()
        custom_styles: Dict[str, ParagraphStyle] = {}

        custom_styles["DocTitle"] = ParagraphStyle(
            "DocTitle",
            parent=base_styles["Title"],
            fontName=opts.heading_font_name,
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            alignment=0,  # Left-aligned
            spaceAfter=4,
        )

        custom_styles["DocSubtitle"] = ParagraphStyle(
            "DocSubtitle",
            parent=base_styles["Normal"],
            fontName=opts.font_name,
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=6,
        )

        custom_styles["H1"] = ParagraphStyle(
            "CustomH1",
            fontName=opts.heading_font_name,
            fontSize=17,
            leading=21,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True,
        )

        custom_styles["H2"] = ParagraphStyle(
            "CustomH2",
            fontName=opts.heading_font_name,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#1E293B"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True,
        )

        custom_styles["H3"] = ParagraphStyle(
            "CustomH3",
            fontName=opts.heading_font_name,
            fontSize=11.5,
            leading=15,
            textColor=colors.HexColor("#334155"),
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True,
        )

        custom_styles["Body"] = ParagraphStyle(
            "CustomBody",
            fontName=opts.font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=6,
        )

        custom_styles["Bullet"] = ParagraphStyle(
            "CustomBullet",
            fontName=opts.font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=16,
            firstLineIndent=-12,
            spaceAfter=3,
        )

        custom_styles["Numbered"] = ParagraphStyle(
            "CustomNumbered",
            fontName=opts.font_name,
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=18,
            firstLineIndent=-14,
            spaceAfter=3,
        )

        custom_styles["Equation"] = ParagraphStyle(
            "CustomEquation",
            fontName="Courier",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#0F172A"),
            backColor=colors.HexColor("#F8FAFC"),
            borderColor=colors.HexColor("#E2E8F0"),
            borderWidth=0.5,
            borderPadding=6,
            spaceBefore=6,
            spaceAfter=8,
            alignment=1,  # Centered
        )

        custom_styles["TableHead"] = ParagraphStyle(
            "TableHead",
            fontName=opts.heading_font_name,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#0F172A"),
        )

        custom_styles["TableCell"] = ParagraphStyle(
            "TableCell",
            fontName=opts.font_name,
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#334155"),
        )

        custom_styles["Caption"] = ParagraphStyle(
            "CustomCaption",
            fontName=opts.font_name,
            fontSize=8.5,
            leading=11,
            fontStyle="italic",
            textColor=colors.HexColor("#64748B"),
            spaceBefore=3,
            spaceAfter=8,
        )

        return custom_styles

    def _create_text_flowable(
        self, elem: TextElement, styles: Dict[str, ParagraphStyle]
    ) -> Optional[Paragraph]:
        """Convert a TextElement to a ReportLab Paragraph."""
        raw_text = elem.content.strip()
        if not raw_text:
            return None

        escaped_text = html.escape(raw_text)

        if elem.kind == TextKind.HEADING:
            level = elem.heading_level or 1
            if level == 1:
                style = styles["H1"]
            elif level == 2:
                style = styles["H2"]
            else:
                style = styles["H3"]
            return Paragraph(escaped_text, style)

        elif elem.kind == TextKind.BULLET:
            level = max(1, elem.list_level or 1)
            bullet_indent = 16 * level
            custom_bullet = ParagraphStyle(
                f"BulletL{level}",
                parent=styles["Bullet"],
                leftIndent=bullet_indent,
                firstLineIndent=-12,
            )
            return Paragraph(f"&bull;&nbsp;&nbsp;{escaped_text}", custom_bullet)

        elif elem.kind == TextKind.NUMBERED_LIST:
            level = max(1, elem.list_level or 1)
            idx = elem.list_index if elem.list_index is not None else 1
            num_indent = 18 * level
            custom_num = ParagraphStyle(
                f"NumberedL{level}",
                parent=styles["Numbered"],
                leftIndent=num_indent,
                firstLineIndent=-14,
            )
            return Paragraph(f"{idx}.&nbsp;{escaped_text}", custom_num)

        else:  # TextKind.PARAGRAPH
            return Paragraph(escaped_text, styles["Body"])

    def _create_table_flowables(
        self, elem: TableElement, styles: Dict[str, ParagraphStyle], max_width: float
    ) -> List[Any]:
        """Convert a TableElement to a ReportLab Table."""
        flowables: List[Any] = []
        data: List[List[Paragraph]] = []

        headers = elem.headers or []
        rows = elem.rows or []

        if not headers and not rows:
            return flowables

        if not headers and rows:
            headers = [f"Col {i + 1}" for i in range(max(len(r) for r in rows))]

        col_count = len(headers)

        # Header row
        header_row = [Paragraph(html.escape(h), styles["TableHead"]) for h in headers]
        data.append(header_row)

        # Data rows
        for row in rows:
            padded = list(row) + [""] * max(0, col_count - len(row))
            data_row = [
                Paragraph(html.escape(str(c)), styles["TableCell"]) for c in padded[:col_count]
            ]
            data.append(data_row)

        col_width = max_width / max(1, col_count)
        table = Table(data, colWidths=[col_width] * col_count)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F5F9")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        flowables.append(Spacer(1, 4))
        flowables.append(table)

        if elem.caption:
            caption_p = Paragraph(f"<i>Table: {html.escape(elem.caption)}</i>", styles["Caption"])
            flowables.append(caption_p)
        else:
            flowables.append(Spacer(1, 6))

        return flowables

    def _create_equation_flowable(
        self, elem: EquationElement, styles: Dict[str, ParagraphStyle]
    ) -> Paragraph:
        """Render LaTeX equation as styled block paragraph."""
        escaped_latex = html.escape(elem.latex.strip())
        return Paragraph(escaped_latex, styles["Equation"])

    def _create_image_flowable(
        self, elem: ImageElement, styles: Dict[str, ParagraphStyle], max_width: float
    ) -> Optional[Any]:
        """Render image if file exists on disk, or placeholder caption."""
        img_path = Path(elem.image_ref)
        if img_path.is_file():
            try:
                from reportlab.platypus import Image as RLImage

                return RLImage(str(img_path), width=min(max_width, 400))
            except Exception:
                pass

        # Fallback placeholder
        caption = elem.caption or elem.image_ref
        return Paragraph(f"[Image: {html.escape(caption)}]", styles["Caption"])
