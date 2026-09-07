from __future__ import annotations

from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser


class DoclingParser(DocumentParser):
    name = "docling"
    role = "strong"

    def __init__(self, options=None) -> None:
        super().__init__(options)
        try:
            import docling
            from docling.document_converter import DocumentConverter
        except ImportError as error:
            raise RuntimeError("Docling is optional; install with: pip install -e .[strong]") from error
        self.version = getattr(docling, "__version__", "unknown")
        self._converter = DocumentConverter()

    def parse(self, item: DocumentInput) -> CanonicalDocument:
        converted = self._converter.convert(str(item.source_path))
        document = converted.document
        target_page_no = item.page_index + 1 if item.page_index is not None else None

        def belongs_to_target(element) -> bool:
            if target_page_no is None:
                return True
            provenance = getattr(element, "prov", []) or []
            return any(getattr(entry, "page_no", None) == target_page_no for entry in provenance)

        blocks: list[Block] = []
        for number, text_item in enumerate(getattr(document, "texts", [])):
            if not belongs_to_target(text_item):
                continue
            text = getattr(text_item, "text", "")
            blocks.append(Block(f"text-{number}", "text", [0, 0, 0, 0], text, None))
        for number, table in enumerate(getattr(document, "tables", [])):
            if not belongs_to_target(table):
                continue
            blocks.append(Block(f"table-{number}", "table", [0, 0, 0, 0], "", None))
        # P0 preserves raw Docling export for later lossless canonical mapping work.
        raw = document.export_to_dict()
        return CanonicalDocument(
            item.document_id, str(item.source_path), self.name, self.version,
            "strong", [CanonicalPage(item.page_index or 0, 0, 0, blocks)],
            {"requested_page": item.page_index, "raw_parser_output": raw},
        )


def build_parser(name: str, options=None) -> DocumentParser:
    if name == "docling":
        return DoclingParser(options)
    if name == "pymupdf":
        from caproute.parsers.cheap import PyMuPDFParser
        return PyMuPDFParser(options)
    raise ValueError(f"Unknown parser: {name}")
