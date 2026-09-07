from __future__ import annotations

import re
import statistics
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
        raw_pages = document.get("metadata", {}).get("raw_parser_output", {}).get("pages", {})
        result = []
        for table in tables:
            result.append(_docling_region_cells(table, raw_pages))
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


def _axis_boundaries(
    cells: list[dict[str, Any]],
    count: int,
    axis: str,
    outer_start: float,
    outer_end: float,
) -> list[float]:
    start_key, end_key = (("l", "r") if axis == "column" else ("t", "b"))
    index_key = "column_nums" if axis == "column" else "row_nums"
    centers: list[float | None] = []
    for index in range(count):
        candidates = []
        for cell in cells:
            if cell[index_key] == [index] and _area(cell["bbox"]) > 0:
                raw = cell["raw_bbox"]
                candidates.append((float(raw[start_key]) + float(raw[end_key])) / 2)
        centers.append(statistics.median(candidates) if candidates else None)
    known = [(index, value) for index, value in enumerate(centers) if value is not None]
    if not known:
        return [outer_start + (outer_end - outer_start) * index / count for index in range(count + 1)]
    for index, value in enumerate(centers):
        if value is not None:
            continue
        left = next(((i, v) for i, v in reversed(known) if i < index), None)
        right = next(((i, v) for i, v in known if i > index), None)
        if left and right:
            centers[index] = left[1] + (right[1] - left[1]) * (index - left[0]) / (right[0] - left[0])
        elif left:
            step = (left[1] - outer_start) / max(left[0] + 0.5, 0.5)
            centers[index] = left[1] + step * (index - left[0])
        else:
            step = (outer_end - right[1]) / max(count - right[0] - 0.5, 0.5)
            centers[index] = right[1] - step * (right[0] - index)
    numeric = [float(value) for value in centers]
    boundaries = [outer_start]
    boundaries.extend((numeric[index] + numeric[index + 1]) / 2 for index in range(count - 1))
    boundaries.append(outer_end)
    # Enforce monotonicity when sparse/tight text centers are noisy.
    epsilon = max((outer_end - outer_start) * 1e-6, 1e-9)
    for index in range(1, len(boundaries)):
        boundaries[index] = max(boundaries[index], boundaries[index - 1] + epsilon)
    boundaries[-1] = max(boundaries[-1], boundaries[-2] + epsilon)
    return boundaries


def _docling_region_cells(table: dict[str, Any], raw_pages: dict[str, Any]) -> list[dict[str, Any]]:
    cells = []
    for raw_cell in table.get("data", {}).get("table_cells", []):
        box = raw_cell.get("bbox") or {}
        row_nums = list(range(int(raw_cell.get("start_row_offset_idx", 0)), int(raw_cell.get("end_row_offset_idx", 0))))
        column_nums = list(range(int(raw_cell.get("start_col_offset_idx", 0)), int(raw_cell.get("end_col_offset_idx", 0))))
        numeric_box = [float(box.get(key, 0.0)) for key in ("l", "t", "r", "b")]
        if row_nums and column_nums:
            cells.append({
                "row_nums": row_nums, "column_nums": column_nums, "bbox": numeric_box,
                "raw_bbox": {key: float(box.get(key, 0.0)) for key in ("l", "t", "r", "b")},
            })
    if not cells:
        return []
    row_count = max(max(cell["row_nums"]) for cell in cells) + 1
    column_count = max(max(cell["column_nums"]) for cell in cells) + 1
    provenance = (table.get("prov") or [{}])[0]
    table_box = provenance.get("bbox", {})
    page_no = str(provenance.get("page_no", ""))
    page_height = float(raw_pages.get(page_no, {}).get("size", {}).get("height", 0.0))
    if table_box and page_height and table_box.get("coord_origin") == "BOTTOMLEFT":
        outer = [float(table_box["l"]), page_height - float(table_box["t"]),
                 float(table_box["r"]), page_height - float(table_box["b"])]
    else:
        valid = [cell["bbox"] for cell in cells if _area(cell["bbox"]) > 0]
        outer = [min(box[0] for box in valid), min(box[1] for box in valid),
                 max(box[2] for box in valid), max(box[3] for box in valid)]
    columns = _axis_boundaries(cells, column_count, "column", outer[0], outer[2])
    rows = _axis_boundaries(cells, row_count, "row", outer[1], outer[3])
    regions = [{
        "row_nums": cell["row_nums"],
        "column_nums": cell["column_nums"],
        "bbox": [columns[min(cell["column_nums"])], rows[min(cell["row_nums"])],
                 columns[max(cell["column_nums"]) + 1], rows[max(cell["row_nums"]) + 1]],
    } for cell in cells]
    return _normalize_cells(regions)


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
