from __future__ import annotations

from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser


class PDFPlumberParser(DocumentParser):
    name = "pdfplumber"
    role = "cheap"
    adapter_version = "1"

    def __init__(self, options=None) -> None:
        super().__init__(options)
        import pdfplumber
        self._pdfplumber = pdfplumber
        self.version = pdfplumber.__version__

    def parse(self, item: DocumentInput) -> CanonicalDocument:
        pages = []
        with self._pdfplumber.open(item.source_path) as document:
            indices = range(len(document.pages)) if item.page_index is None else [item.page_index]
            for index in indices:
                page = document.pages[index]
                blocks = []
                text = page.extract_text() or ""
                if text.strip():
                    blocks.append(Block(f"p{index}-text", "text", [0, 0, page.width, page.height], text.strip(), 1.0))
                settings = dict(self.options.get("table_settings", {}))
                for number, table in enumerate(page.find_tables(table_settings=settings)):
                    rows = table.rows
                    grid = [[list(cell) if cell is not None else None for cell in row.cells] for row in rows]
                    blocks.append(Block(
                        f"p{index}-table-{number}", "table", list(table.bbox), "", None,
                        {"row_count": len(rows), "column_count": max((len(row.cells) for row in rows), default=0),
                         "cells": table.extract(), "grid_cell_bboxes": grid},
                    ))
                pages.append(CanonicalPage(index, float(page.width), float(page.height), blocks))
        return CanonicalDocument(item.document_id, str(item.source_path), self.name, self.version,
                                 "cheap", pages, {"requested_page": item.page_index})
