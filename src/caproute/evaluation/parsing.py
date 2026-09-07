from __future__ import annotations

from statistics import mean
from typing import Any

from caproute.ir.schema import CanonicalDocument


def evaluate_document(document: CanonicalDocument, ground_truth: dict[str, Any]) -> dict[str, float | None]:
    blocks = [block for page in document.pages for block in page.blocks]
    text_blocks = [block for block in blocks if block.type in {"text", "title", "caption"}]
    tables = [block for block in blocks if block.type == "table"]
    expected_tables = len(
        ground_truth.get("table_boxes_xyxy", ground_truth.get("table_boxes_xywh", []))
    )
    detected = len(tables)
    table_count_f1 = None
    if expected_tables or detected:
        precision = min(expected_tables, detected) / detected if detected else 0.0
        recall = min(expected_tables, detected) / expected_tables if expected_tables else 0.0
        table_count_f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "text_characters": float(sum(len(block.text) for block in text_blocks)),
        "text_block_count": float(len(text_blocks)),
        "detected_table_count": float(detected),
        "expected_table_count": float(expected_tables),
        "table_count_f1_proxy": table_count_f1,
    }


def aggregate_quality(rows: list[dict[str, Any]]) -> dict[str, float | None]:
    def average(key: str):
        values = [float(row[key]) for row in rows if row.get(key) is not None]
        return mean(values) if values else None
    return {
        "items": len(rows),
        "text_characters_mean": average("text_characters"),
        "table_count_f1_proxy_mean": average("table_count_f1_proxy"),
        "warning": "P0 proxy metric; not official GriTS.",
    }
