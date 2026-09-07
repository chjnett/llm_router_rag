from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _page_number(path: Path) -> int:
    match = re.search(r"_(\d+)\.xml$", path.name)
    if not match:
        raise ValueError(f"Cannot parse page number: {path}")
    return int(match.group(1))


def structure_files_for_page(
    detection_root: str | Path,
    structure_root: str | Path,
    document_id: str,
    page_index: int,
) -> list[Path]:
    """Map a page's tables to document-order PubTables structure XML files."""
    page_files = sorted(
        Path(detection_root).glob(f"{document_id}_*.xml"),
        key=_page_number,
    )
    first_index = 0
    table_count = 0
    found = False
    for page_file in page_files:
        count = sum(
            obj.findtext("name") in {"table", "table rotated"}
            for obj in ET.parse(page_file).getroot().findall("object")
        )
        if _page_number(page_file) == page_index:
            table_count = count
            found = True
            break
        first_index += count
    if not found:
        return []
    return [
        Path(structure_root) / f"{document_id}_table_{index}.xml"
        for index in range(first_index, first_index + table_count)
    ]


def ground_truth_shapes(paths: list[Path]) -> list[dict[str, int]]:
    shapes = []
    for path in paths:
        if not path.exists():
            continue
        names = [obj.findtext("name", "") for obj in ET.parse(path).getroot().findall("object")]
        shapes.append({
            "row_count": names.count("table row"),
            "column_count": names.count("table column"),
        })
    return shapes


def prediction_shapes(row: dict[str, Any]) -> list[dict[str, int]]:
    blocks = [
        block
        for page in row["document"].get("pages", [])
        for block in page.get("blocks", [])
        if block.get("type") == "table"
    ]
    shapes = []
    for block in blocks:
        metadata = block.get("metadata", {})
        if metadata.get("row_count") is not None and metadata.get("column_count") is not None:
            shapes.append({
                "row_count": int(metadata["row_count"]),
                "column_count": int(metadata["column_count"]),
            })
    if shapes or row["document"].get("source_parser") != "docling":
        return shapes

    # Backward-compatible extraction from P0 Docling raw cache.
    raw_tables = row["document"].get("metadata", {}).get("raw_parser_output", {}).get("tables", [])
    for table in raw_tables:
        cells = table.get("data", {}).get("table_cells", [])
        shapes.append({
            "row_count": max((int(cell.get("end_row_offset_idx", 0)) for cell in cells), default=0),
            "column_count": max((int(cell.get("end_col_offset_idx", 0)) for cell in cells), default=0),
        })
    return shapes


def _ratio(left: int, right: int) -> float:
    return 1.0 if left == right == 0 else min(left, right) / max(left, right)


def shape_similarity(truth: list[dict[str, int]], prediction: list[dict[str, int]]) -> float | None:
    if not truth and not prediction:
        return None
    scores = []
    for index in range(max(len(truth), len(prediction))):
        if index >= len(truth) or index >= len(prediction):
            scores.append(0.0)
            continue
        scores.append((_ratio(truth[index]["row_count"], prediction[index]["row_count"]) +
                       _ratio(truth[index]["column_count"], prediction[index]["column_count"])) / 2)
    return sum(scores) / len(scores)
