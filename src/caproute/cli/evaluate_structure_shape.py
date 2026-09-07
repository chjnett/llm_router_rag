from __future__ import annotations

import argparse
import json
from pathlib import Path

from caproute.cli.compare_p0 import _latest_prediction_windows, _load_predictions
from caproute.core.io import write_json
from caproute.evaluation.structure_shape import (
    ground_truth_shapes,
    prediction_shapes,
    shape_similarity,
    structure_files_for_page,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="outputs/p0")
    parser.add_argument("--detection-root", required=True)
    parser.add_argument("--structure-root", required=True)
    parser.add_argument("--expected", type=int, default=300)
    parser.add_argument("--output", default="outputs/p0/structure_shape_comparison.json")
    args = parser.parse_args()

    parsers = {
        name: _load_predictions(_latest_prediction_windows(Path(args.output_root), name))
        for name in ("pymupdf", "docling")
    }
    keys = sorted(set(parsers["pymupdf"]) & set(parsers["docling"]))
    scores: dict[str, list[float]] = {"pymupdf": [], "docling": []}
    missing_ground_truth = []
    for document_id, page_index in keys:
        paths = structure_files_for_page(
            args.detection_root, args.structure_root, document_id, int(page_index)
        )
        truth = ground_truth_shapes(paths)
        if len(truth) != len(paths):
            missing_ground_truth.append({"document_id": document_id, "page_index": page_index})
            continue
        for name, rows in parsers.items():
            score = shape_similarity(truth, prediction_shapes(rows[(document_id, page_index)]))
            if score is not None:
                scores[name].append(score)
    result = {
        "metric": "row_column_shape_similarity",
        "warning": "Conservative P0 diagnostic, not GriTS; excludes cell spans, locations, and content.",
        "paired_items": len(keys),
        "evaluated_items": min(len(values) for values in scores.values()),
        "missing_ground_truth": missing_ground_truth,
        "means": {
            name: sum(values) / len(values) if values else None
            for name, values in scores.items()
        },
        "p0_gate": "HOLD",
    }
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if len(keys) != args.expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
