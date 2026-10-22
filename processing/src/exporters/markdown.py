"""Markdown document exporter for Canonical Document."""

from pathlib import Path
from typing import List, Optional, Union
import yaml

from processing.canonical.document import Document, Page
from processing.canonical.text import TextElement, TextKind
from processing.canonical.element import TableElement, EquationElement, ImageElement
from processing.exporters.base import BaseExporter
from processing.exporters.options import MarkdownExportOptions


class MarkdownExporter(BaseExporter[MarkdownExportOptions]):
    """Exports Canonical Document to GitHub Flavored Markdown (GFM)."""

    def export(
        self,
        document: Document,
        output_path: Optional[Union[str, Path]] = None,
        options: Optional[MarkdownExportOptions] = None,
    ) -> str:
        """Export canonical document to Markdown string or file."""
        opts = options or MarkdownExportOptions()
        chunks: List[str] = []

        # 1. Frontmatter
        if opts.include_frontmatter:
            frontmatter_data = {}
            if document.metadata.title:
                frontmatter_data["title"] = document.metadata.title
            if document.metadata.author:
                frontmatter_data["author"] = document.metadata.author
            if document.metadata.created_at:
                frontmatter_data["date"] = document.metadata.created_at.isoformat()
            if document.metadata.source_file:
                frontmatter_data["source"] = document.metadata.source_file
            if document.metadata.generator_version:
                frontmatter_data["generator_version"] = document.metadata.generator_version
            if document.metadata.extra_metadata:
                frontmatter_data["metadata"] = document.metadata.extra_metadata

            if frontmatter_data:
                fm_str = yaml.dump(
                    frontmatter_data,
                    sort_keys=False,
                    default_flow_style=False,
                    allow_unicode=True,
                ).strip()
                chunks.append(f"---\n{fm_str}\n---\n")

        # 2. Pages
        rendered_pages: List[str] = []
        for page in document.pages:
            page_content = self._render_page(page, opts)
            if page_content:
                rendered_pages.append(page_content)

        if rendered_pages:
            chunks.append(opts.page_break_marker.join(rendered_pages))

        result_md = "\n".join(chunks).strip() + "\n"

        if output_path:
            self._write_output(result_md, output_path)

        return result_md

    def _render_page(self, page: Page, opts: MarkdownExportOptions) -> str:
        """Render a single canonical Page to Markdown."""
        page_blocks: List[str] = []

        if opts.include_page_numbers:
            page_blocks.append(f"<!-- Page {page.page_number} -->")

        prev_kind: Optional[TextKind] = None

        for elem in page.elements:
            elem_type = getattr(elem, "type", None)

            if elem_type == "text" and isinstance(elem, TextElement):
                block = self._render_text_element(elem)
                if block:
                    # Compact consecutive list items
                    is_current_list = elem.kind in (TextKind.BULLET, TextKind.NUMBERED_LIST)
                    is_prev_list = prev_kind in (TextKind.BULLET, TextKind.NUMBERED_LIST)
                    if is_current_list and is_prev_list and page_blocks:
                        page_blocks[-1] += "\n" + block
                    else:
                        page_blocks.append(block)
                prev_kind = elem.kind

            elif elem_type == "table" and isinstance(elem, TableElement):
                table_md = self._render_table_element(elem)
                if table_md:
                    page_blocks.append(table_md)
                prev_kind = None

            elif elem_type == "equation" and isinstance(elem, EquationElement):
                eq_md = self._render_equation_element(elem)
                if eq_md:
                    page_blocks.append(eq_md)
                prev_kind = None

            elif elem_type == "image" and isinstance(elem, ImageElement):
                caption = elem.caption or "Image"
                page_blocks.append(f"![{caption}]({elem.image_ref})")
                prev_kind = None

            elif elem_type == "diagram":
                # Diagrams are ignored for now per user instruction
                if opts.annotate_skipped_diagrams:
                    page_blocks.append(f"<!-- diagram: {elem.id} -->")
                prev_kind = None

        return "\n\n".join(page_blocks).strip()

    def _render_text_element(self, elem: TextElement) -> str:
        """Render a TextElement to markdown."""
        content = elem.content.strip()
        if not content:
            return ""

        if elem.kind == TextKind.HEADING:
            level = elem.heading_level or 1
            hashes = "#" * max(1, min(level, 6))
            return f"{hashes} {content}"

        elif elem.kind == TextKind.BULLET:
            indent = "  " * max(0, (elem.list_level or 1) - 1)
            return f"{indent}* {content}"

        elif elem.kind == TextKind.NUMBERED_LIST:
            indent = "  " * max(0, (elem.list_level or 1) - 1)
            idx = elem.list_index if elem.list_index is not None else 1
            return f"{indent}{idx}. {content}"

        else:  # TextKind.PARAGRAPH or fallback
            return content

    def _render_table_element(self, elem: TableElement) -> str:
        """Render TableElement as GitHub Flavored Markdown table."""
        lines: List[str] = []
        headers = elem.headers or []
        rows = elem.rows or []

        if not headers and rows:
            # Generate generic column headers if missing
            col_count = max(len(r) for r in rows)
            headers = [f"Col {i + 1}" for i in range(col_count)]

        if headers:
            lines.append("| " + " | ".join(h.replace("|", "\\|") for h in headers) + " |")
            lines.append("| " + " | ".join("---" for _ in headers) + " |")

        for row in rows:
            # Pad row if shorter than headers
            padded = list(row) + [""] * max(0, len(headers) - len(row))
            lines.append("| " + " | ".join(str(c).replace("|", "\\|") for c in padded[:len(headers)]) + " |")

        if elem.caption:
            lines.append(f"\n*Table: {elem.caption}*")

        return "\n".join(lines)

    def _render_equation_element(self, elem: EquationElement) -> str:
        """Render EquationElement as LaTeX block or inline."""
        latex = elem.latex.strip()
        if elem.display_mode:
            return f"$$\n{latex}\n$$"
        return f"${latex}$"
