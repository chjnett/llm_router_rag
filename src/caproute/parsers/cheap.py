from __future__ import annotations

import pymupdf as fitz

from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser


class PyMuPDFParser(DocumentParser):
    name = "pymupdf"
    role = "cheap"
    version = getattr(fitz, "VersionBind", "unknown")
    adapter_version = "3"

    def __init__(self, options=None, name: str = "pymupdf") -> None:
        super().__init__(options)
        self.name = name

    def parse(self, item: DocumentInput) -> CanonicalDocument:
        document = fitz.open(item.source_path)
        indices = range(len(document)) if item.page_index is None else [item.page_index]
        pages: list[CanonicalPage] = []
        for index in indices:
            page = document[index]
            blocks: list[Block] = []
            for number, raw in enumerate(page.get_text("blocks", sort=True)):
                x0, y0, x1, y1, text = raw[:5]
                if text.strip():
                    blocks.append(Block(f"p{index}-text-{number}", "text", [x0, y0, x1, y1], text.strip(), 1.0))
            if self.options.get("detect_tables", True) and hasattr(page, "find_tables"):
                try:
                    settings = dict(self.options.get("table_settings", {}))
                    for number, table in enumerate(page.find_tables(**settings).tables):
                        blocks.append(Block(
                            f"p{index}-table-{number}", "table", list(table.bbox), "", None,
                            {
                                "row_count": int(table.row_count),
                                "column_count": int(table.col_count),
                                "cells": table.extract(),
                                "grid_cell_bboxes": [
                                    [list(cell) if cell is not None else None for cell in row.cells]
                                    for row in table.rows
                                ],
                            },
                        ))
                except Exception as error:
                    # Text extraction remains valid; preserve the optional detector warning.
                    blocks.append(Block(f"p{index}-warning", "unknown", [0, 0, 0, 0], "", None, {"table_error": repr(error)}))
            pages.append(CanonicalPage(index, float(page.rect.width), float(page.rect.height), blocks))
        return CanonicalDocument(
            item.document_id, str(item.source_path), self.name, self.version,
            "cheap", pages, {"requested_page": item.page_index},
        )
