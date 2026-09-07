from __future__ import annotations

import random
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from caproute.parsers.base import DocumentInput

import pymupdf


@dataclass
class PubTablesSample:
    item: DocumentInput
    image_path: Path
    ground_truth: dict[str, Any]


def _document_id(file_name: str) -> str:
    stem = Path(file_name).stem
    official = re.match(r"^(PMC\d+)_\d+$", stem, re.I)
    if official:
        return official.group(1)
    return re.split(r"[_-](?:page|table)[_-]?\d+", stem, maxsplit=1, flags=re.I)[0]


def load_pubtables_subset(
    annotations: str | Path,
    split_file: str | Path,
    image_root: str | Path,
    pdf_root: str | Path | None,
    limit: int,
    seed: int,
    document_level: bool = True,
    exclude_document_ids: set[str] | None = None,
) -> list[PubTablesSample]:
    """Load the official PubTables-1M PASCAL VOC page-detection release."""
    annotation_root = Path(annotations)
    rows = [
        line.strip()
        for line in Path(split_file).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rng = random.Random(seed)
    rng.shuffle(rows)
    selected: list[PubTablesSample] = []
    seen_documents: set[str] = set()
    excluded = exclude_document_ids or set()
    for relative_annotation in rows:
        xml_path = Path(relative_annotation)
        if not xml_path.is_absolute():
            candidate = annotation_root / xml_path
            xml_path = candidate if candidate.exists() else annotation_root / xml_path.name
        root = ET.parse(xml_path).getroot()
        file_name = root.findtext("filename") or f"{xml_path.stem}.jpg"
        document_id = _document_id(file_name)
        if document_id in excluded:
            continue
        if document_level and document_id in seen_documents:
            continue
        image_path = Path(image_root) / file_name
        source_path = image_path
        if pdf_root:
            candidate = Path(pdf_root) / f"{document_id}.pdf"
            if candidate.exists():
                source_path = candidate
        table_boxes: list[list[float]] = []
        for obj in root.findall("object"):
            if (obj.findtext("name") or "").lower() != "table":
                continue
            box = obj.find("bndbox")
            if box is not None:
                table_boxes.append(
                    [float(box.findtext(key, "0")) for key in ("xmin", "ymin", "xmax", "ymax")]
                )
        page_match = re.search(
            r"(?:[_-]page[_-]?|^PMC\d+_)(\d+)$", Path(file_name).stem, re.I
        )
        page_index = int(page_match.group(1)) if page_match else None
        if source_path.suffix.lower() == ".pdf" and page_index is not None:
            with pymupdf.open(source_path) as pdf:
                if page_index >= len(pdf):
                    # The current PMC article version can differ from the
                    # historical version used to build PubTables-1M.
                    continue
        item = DocumentInput(
            document_id=document_id,
            source_path=source_path,
            page_index=page_index if source_path.suffix.lower() == ".pdf" else None,
            metadata={"annotation_path": str(xml_path), "file_name": file_name},
        )
        selected.append(
            PubTablesSample(item, image_path, {"table_boxes_xyxy": table_boxes})
        )
        seen_documents.add(document_id)
        if len(selected) >= limit:
            break
    return selected
