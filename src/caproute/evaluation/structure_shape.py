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


def _bbox(node: ET.Element) -> list[float]:
    box = node.find("bndbox")
    if box is None:
        return [0.0, 0.0, 0.0, 0.0]
    return [float(box.findtext(key, "0")) for key in ("xmin", "ymin", "xmax", "ymax")]


def _intersection(left: list[float], right: list[float]) -> list[float]:
    return [max(left[0], right[0]), max(left[1], right[1]), min(left[2], right[2]), min(left[3], right[3])]


def _area(box: list[float]) -> float:
    return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])


def _normalize_cells(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    valid = [cell["bbox"] for cell in cells if _area(cell["bbox"]) > 0]
    if not valid:
        return cells
    bounds = [
        min(box[0] for box in valid), min(box[1] for box in valid),
        max(box[2] for box in valid), max(box[3] for box in valid),
    ]
    width, height = max(bounds[2] - bounds[0], 1e-9), max(bounds[3] - bounds[1], 1e-9)
    result = []
    for cell in cells:
        box = cell["bbox"]
        normalized = [
            (box[0] - bounds[0]) / width, (box[1] - bounds[1]) / height,
            (box[2] - bounds[0]) / width, (box[3] - bounds[1]) / height,
        ] if _area(box) > 0 else [0.0, 0.0, 0.0, 0.0]
        result.append({**cell, "bbox": normalized})
    return result


def ground_truth_cells(path: Path) -> list[dict[str, Any]]:
    root = ET.parse(path).getroot()
    objects = [(obj.findtext("name", ""), _bbox(obj)) for obj in root.findall("object")]
    rows = sorted((box for name, box in objects if name == "table row"), key=lambda box: box[1] + box[3])
    columns = sorted((box for name, box in objects if name == "table column"), key=lambda box: box[0] + box[2])
    spanning = [box for name, box in objects if name in {"table spanning cell", "table projected row header"}]
    occupied: set[tuple[int, int]] = set()
    cells: list[dict[str, Any]] = []
    for span in spanning:
        row_nums = [index for index, row in enumerate(rows) if _area(_intersection(span, [span[0], row[1], span[2], row[3]])) / max(_area([span[0], row[1], span[2], row[3]]), 1e-9) >= 0.5]
        column_nums = [index for index, column in enumerate(columns) if _area(_intersection(span, [column[0], span[1], column[2], span[3]])) / max(_area([column[0], span[1], column[2], span[3]]), 1e-9) >= 0.5]
        slots = {(row, column) for row in row_nums for column in column_nums}
        if slots and not slots & occupied:
            occupied.update(slots)
            cells.append({
                "row_nums": row_nums,
                "column_nums": column_nums,
                "bbox": [min(columns[c][0] for c in column_nums), min(rows[r][1] for r in row_nums),
                         max(columns[c][2] for c in column_nums), max(rows[r][3] for r in row_nums)],
            })
    for row_num, row in enumerate(rows):
        for column_num, column in enumerate(columns):
            if (row_num, column_num) not in occupied:
                cells.append({"row_nums": [row_num], "column_nums": [column_num], "bbox": _intersection(row, column)})
    return _normalize_cells(cells)


def prediction_table_cells(row: dict[str, Any]) -> list[list[dict[str, Any]]]:
    document = row["document"]
    if document.get("source_parser") == "docling":
        tables = document.get("metadata", {}).get("raw_parser_output", {}).get("tables", [])
        result = []
        for table in tables:
            cells = []
            for cell in table.get("data", {}).get("table_cells", []):
                box = cell.get("bbox") or {}
                cells.append({
                    "row_nums": list(range(int(cell.get("start_row_offset_idx", 0)), int(cell.get("end_row_offset_idx", 0)))),
                    "column_nums": list(range(int(cell.get("start_col_offset_idx", 0)), int(cell.get("end_col_offset_idx", 0)))),
                    "bbox": [float(box.get(key, 0.0)) for key in ("l", "t", "r", "b")],
                })
            result.append(_normalize_cells([cell for cell in cells if cell["row_nums"] and cell["column_nums"]]))
        return result

    result = []
    blocks = [block for page in document.get("pages", []) for block in page.get("blocks", []) if block.get("type") == "table"]
    for block in blocks:
        metadata = block.get("metadata", {})
        grid = metadata.get("grid_cell_bboxes", [])
        cells = []
        for row_num in range(int(metadata.get("row_count", len(grid)))):
            row_boxes = grid[row_num] if row_num < len(grid) else []
            for column_num in range(int(metadata.get("column_count", len(row_boxes)))):
                box = row_boxes[column_num] if column_num < len(row_boxes) else None
                cells.append({
                    "row_nums": [row_num], "column_nums": [column_num],
                    "bbox": list(box) if box is not None else [0.0, 0.0, 0.0, 0.0],
                })
        result.append(_normalize_cells(cells))
    return result


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
