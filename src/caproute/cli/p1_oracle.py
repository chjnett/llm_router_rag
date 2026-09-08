from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from caproute.cli.compare_p0 import _latest_prediction_windows, _load_predictions
from caproute.core.config import config_hash, load_config
from caproute.core.io import write_json, write_jsonl
from caproute.evaluation.grits import grits_loc, grits_top
from caproute.evaluation.structure_shape import ground_truth_cells, prediction_table_cells, structure_files_for_page


def parser_page_metrics(truth_tables: list[list[dict]], predicted_tables: list[list[dict]]) -> dict[str, Any]:
    top_scores, loc_scores = [], []
    for index in range(max(len(truth_tables), len(predicted_tables))):
        truth = truth_tables[index] if index < len(truth_tables) else []
        prediction = predicted_tables[index] if index < len(predicted_tables) else []
        top_scores.append(float(grits_top(truth, prediction)[0]))
        loc_scores.append(float(grits_loc(truth, prediction)[0]))
    return {
        "expected_table_count": len(truth_tables),
        "predicted_table_count": len(predicted_tables),
        "exact_table_count": len(truth_tables) == len(predicted_tables),
        "grits_top_mean": sum(top_scores) / len(top_scores) if top_scores else None,
        "grits_loc_mean": sum(loc_scores) / len(loc_scores) if loc_scores else None,
    }


def is_sufficient(metrics: dict[str, Any], rule: dict[str, Any]) -> bool:
    if rule.get("require_exact_table_count", True) and not metrics["exact_table_count"]:
        return False
    return (
        metrics["grits_top_mean"] is not None
        and metrics["grits_loc_mean"] is not None
        and metrics["grits_top_mean"] >= float(rule["min_grits_top"])
        and metrics["grits_loc_mean"] >= float(rule["min_grits_loc"])
    )


def main() -> None:
    cli = argparse.ArgumentParser()
    cli.add_argument("--config", default="configs/p1_oracle.yaml")
    args = cli.parse_args()
    config_path = Path(args.config).resolve()
    root = config_path.parent.parent
    cfg = load_config(config_path)
    dataset, prediction_cfg = cfg["dataset"], cfg["predictions"]
    parsers = {
        role: _load_predictions(_latest_prediction_windows(
            root / prediction_cfg.get(f"{role}_output_root", prediction_cfg["output_root"]),
            prediction_cfg[f"{role}_parser"],
        ))
        for role in ("cheap", "strong")
    }
    keys = sorted(set(parsers["cheap"]) & set(parsers["strong"]))
    labels, not_evaluable = [], []
    for document_id, page_index in keys:
        paths = structure_files_for_page(
            root / dataset["detection_root"], root / dataset["structure_root"], document_id, int(page_index)
        )
        if not paths or any(not path.exists() for path in paths):
            not_evaluable.append({"document_id": document_id, "page_index": page_index, "reason": "missing_structure_xml"})
            continue
        truth = [ground_truth_cells(path) for path in paths]
        metrics = {
            role: parser_page_metrics(truth, prediction_table_cells(rows[(document_id, page_index)]))
            for role, rows in parsers.items()
        }
        cheap_pass = is_sufficient(metrics["cheap"], cfg["sufficiency"])
        strong_pass = is_sufficient(metrics["strong"], cfg["sufficiency"])
        capability = (
            "cheap_sufficient" if cheap_pass and strong_pass else
            "strong_regression" if cheap_pass else
            "strong_needed" if strong_pass else
            "both_fail"
        )
        labels.append({
            "document_id": document_id, "page_index": page_index,
            "capability_label": capability,
            "cheap_sufficient": cheap_pass, "strong_sufficient": strong_pass,
            "oracle_route": "cheap" if cheap_pass else "strong", "metrics": metrics,
        })

    count = len(labels)
    counts = {name: sum(row["capability_label"] == name for row in labels) for name in (
        "cheap_sufficient", "strong_needed", "both_fail", "strong_regression"
    )}
    cheap_pass_count = sum(row["cheap_sufficient"] for row in labels)
    strong_pass_count = sum(row["strong_sufficient"] for row in labels)
    union_pass_count = sum(row["cheap_sufficient"] or row["strong_sufficient"] for row in labels)
    cheap_cost, strong_cost = float(cfg["cost"]["cheap_ms_p50"]), float(cfg["cost"]["strong_ms_p50"])
    ratio = cheap_cost / strong_cost
    normalized_cost = (cheap_pass_count * cheap_cost + (count - cheap_pass_count) * strong_cost) / (count * strong_cost)
    saving = 1 - normalized_cost
    gate_checks = {
        "oracle_saving": saving >= float(cfg["gate"]["min_oracle_saving"]),
        "cost_ratio": ratio < float(cfg["gate"]["max_cheap_strong_cost_ratio"]),
        "strong_improves_coverage": strong_pass_count > cheap_pass_count,
    }
    summary = {
        "config_path": str(config_path), "config_hash": config_hash(cfg),
        "expected_pages": int(dataset["expected_pages"]), "paired_pages": len(keys),
        "evaluable_pages": count, "not_evaluable_pages": len(not_evaluable),
        "sufficiency_rule": cfg["sufficiency"], "counts": counts,
        "rates": {
            **{name: value / count for name, value in counts.items()},
            "cheap_sufficient": cheap_pass_count / count,
            "strong_sufficient": strong_pass_count / count,
            "oracle_sufficient": union_pass_count / count,
        },
        "cost": {
            "cheap_ms_p50": cheap_cost, "strong_ms_p50": strong_cost,
            "cheap_strong_ratio": ratio, "oracle_normalized_cost": normalized_cost,
            "oracle_saving": saving,
            "assumption": "zero-cost pre-routing oracle; P2 router overhead excluded",
        },
        "gate_checks": gate_checks, "p1_gate": "PASS" if all(gate_checks.values()) else "FAIL",
        "not_evaluable": not_evaluable,
    }
    output = root / cfg["outputs"]["root"]
    write_json(output / "oracle_summary.json", summary)
    write_jsonl(output / "capability_labels.jsonl", labels)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if len(keys) != int(dataset["expected_pages"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
