from __future__ import annotations

from caproute.ir.schema import Block, CanonicalDocument, CanonicalPage
from caproute.parsers.base import DocumentInput, DocumentParser


class DoclingParser(DocumentParser):
    name = "docling"
    role = "strong"
    adapter_version = "2"

    def __init__(self, options=None) -> None:
        super().__init__(options)
        try:
            import docling
            from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.document_converter import DocumentConverter, PdfFormatOption
        except ImportError as error:
            raise RuntimeError("Docling is optional; install with: pip install -e .[strong]") from error
        self.version = getattr(docling, "__version__", "unknown")
        pipeline = PdfPipelineOptions()
        requested_device = str(self.options.get("device", "cuda")).lower()
        devices = {
            "cuda": AcceleratorDevice.CUDA,
            "cpu": AcceleratorDevice.CPU,
            "auto": AcceleratorDevice.AUTO,
        }
        if requested_device not in devices:
            raise ValueError(f"Unsupported Docling device: {requested_device}")
        pipeline.accelerator_options = AcceleratorOptions(
            num_threads=int(self.options.get("num_threads", 4)),
            device=devices[requested_device],
        )
        pipeline.do_ocr = bool(self.options.get("do_ocr", False))
        pipeline.do_table_structure = bool(self.options.get("do_table_structure", True))
        self._converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline)}
        )

    def parse(self, item: DocumentInput) -> CanonicalDocument:
        page_range = (
            (item.page_index + 1, item.page_index + 1)
            if item.page_index is not None
            else (1, 2**31 - 1)
        )
        converted = self._converter.convert(str(item.source_path), page_range=page_range)
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
            table_data = getattr(table, "data", None)
            cells = list(getattr(table_data, "table_cells", []) or [])
            row_count = max((getattr(cell, "end_row_offset_idx", 0) for cell in cells), default=0)
            column_count = max((getattr(cell, "end_col_offset_idx", 0) for cell in cells), default=0)
            blocks.append(Block(
                f"table-{number}", "table", [0, 0, 0, 0], "", None,
                {
                    "row_count": int(row_count),
                    "column_count": int(column_count),
                    "cell_count": len(cells),
                },
            ))
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
    if name == "pymupdf" or name.startswith("pymupdf_"):
        from caproute.parsers.cheap import PyMuPDFParser
        return PyMuPDFParser(options, name=name)
    raise ValueError(f"Unknown parser: {name}")
