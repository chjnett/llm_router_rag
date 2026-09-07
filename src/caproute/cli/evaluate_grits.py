from __future__ import annotations

import argparse
import json
from pathlib import Path

from caproute.cli.compare_p0 import _latest_prediction_windows, _load_predictions
from caproute.core.io import write_json
from caproute.evaluation.grits import grits_loc, grits_top
from caproute.evaluation.structure_shape import ground_truth_cells, prediction_table_cells, structure_files_for_page


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="outputs/p0")
    parser.add_argument("--detection-root", required=True)
    parser.add_argument("--structure-root", required=True)
    parser.add_argument("--expected", type=int, default=300)
    parser.add_argument("--output", default="outputs/p0/grits_top_loc_comparison.json")
    args = parser.parse_args()
    rows = {
        name: _load_predictions(_latest_prediction_windows(Path(args.output_root), name))
        for name in ("pymupdf", "docling")
    }
    keys = sorted(set(rows["pymupdf"]) & set(rows["docling"]))
    metrics = {name: {"grits_top": [], "grits_loc": []} for name in rows}
    skipped = []
    tables_evaluated = 0
    for document_id, page_index in keys:
        paths = structure_files_for_page(args.detection_root, args.structure_root, document_id, int(page_index))
        if not paths or any(not path.exists() for path in paths):
            skipped.append({"document_id": document_id, "page_index": page_index, "reason": "missing_structure_xml"})
            continue
        truth_tables = [ground_truth_cells(path) for path in paths]
        tables_evaluated += len(truth_tables)
        for name, parser_rows in rows.items():
            predicted_tables = prediction_table_cells(parser_rows[(document_id, page_index)])
            for index in range(max(len(truth_tables), len(predicted_tables))):
                truth = truth_tables[index] if index < len(truth_tables) else []
                prediction = predicted_tables[index] if index < len(predicted_tables) else []
                metrics[name]["grits_top"].append(grits_top(truth, prediction)[0])
                metrics[name]["grits_loc"].append(grits_loc(truth, prediction)[0])
    result = {
        "implementation": "GriTS factored 2D-MSS compatible with Microsoft Table Transformer src/grits.py",
        "scope": "GriTS_Top and normalized GriTS_Loc; content words not downloaded",
        "paired_pages": len(keys),
        "evaluated_pages": len(keys) - len(skipped),
        "ground_truth_tables": tables_evaluated,
        "skipped_pages": skipped,
        "parsers": {
            name: {metric: _mean(values) for metric, values in parser_metrics.items()}
            for name, parser_metrics in metrics.items()
        },
        "p0_gate": "REVIEW",
    }
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if len(keys) != args.expected:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
