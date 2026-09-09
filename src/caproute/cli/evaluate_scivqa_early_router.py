from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from caproute.cli.evaluate_spiqa_locked_selector import exact_mcnemar_p_value, paired_bootstrap
from caproute.cli.freeze_spiqa_early_router_policy import EARLY_FEATURE_NAMES, early_features, routed_metrics
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


def early_probabilities(rows: list[dict], lock: dict) -> np.ndarray:
    if tuple(lock["feature_names"]) != EARLY_FEATURE_NAMES:
        raise ValueError("Policy feature contract does not match the Cheap-only early router")
    features = np.asarray([early_features(row) for row in rows], dtype=np.float64)
    normalized = (features - np.asarray(lock["scaler_mean"])) / np.asarray(lock["scaler_scale"])
    logits = normalized @ np.asarray(lock["coefficients"]) + float(lock["intercept"])
    return 1.0 / (1.0 + np.exp(-logits))


def main() -> None:
    parser = argparse.ArgumentParser(description="One-shot evaluation of the locked Cheap-only router")
    parser.add_argument("--config", default="configs/r4_scivqa_early_router_certification.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    lock_path = Path(config["policy_lock"])
    results_path = Path(config["external_results"])
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    external = json.loads(results_path.read_text(encoding="utf-8"))
    rows = external["questions"]
    probabilities = early_probabilities(rows, lock)
    threshold = float(lock["threshold"])
    routed = probabilities >= threshold
    selected, route_rate = routed_metrics(rows, probabilities, threshold)
    caption = mean_metrics([row["caption"] for row in rows])
    strong = mean_metrics([row["colsmol"] for row in rows])
    oracle = mean_metrics([row["oracle_selective"] for row in rows])

    selected_r1 = np.asarray([
        row["colsmol" if route else "caption"]["recall_at_1"] for row, route in zip(rows, routed)
    ])
    strong_r1 = np.asarray([row["colsmol"]["recall_at_1"] for row in rows])
    selected_mrr = np.asarray([
        row["colsmol" if route else "caption"]["mrr"] for row, route in zip(rows, routed)
    ])
    strong_mrr = np.asarray([row["colsmol"]["mrr"] for row in rows])
    strong_only = int(np.sum((strong_r1 == 1) & (selected_r1 == 0)))
    selected_only = int(np.sum((strong_r1 == 0) & (selected_r1 == 1)))
    visual = np.asarray([row["qa_pair_type"].endswith(" visual") for row in rows])
    groups = {"visual": visual, "non_visual": ~visual}
    route_by_group = {name: float(routed[mask].mean()) for name, mask in groups.items()}

    saving = 1.0 - route_rate
    r1_retention = selected["recall_at_1"] / strong["recall_at_1"]
    mrr_retention = selected["mrr"] / strong["mrr"]
    peak_vram = external["summary"].get("peak_vram_allocated_bytes")
    gate = config["gate"]
    quality_gate = (
        r1_retention >= float(gate["min_r1_retention"])
        and mrr_retention >= float(gate["min_mrr_retention"])
    )
    cost_gate = saving >= float(gate["min_realized_strong_query_saving"])
    resource_gate = peak_vram is not None and peak_vram <= int(gate["max_peak_vram_bytes"])
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "policy_lock_sha256": sha256_file(lock_path),
        "external_results_sha256": sha256_file(results_path),
        "questions": len(rows),
        "threshold": threshold,
        "causal_contract": lock["causal_contract"],
        "caption": caption,
        "always_strong": strong,
        "oracle": oracle,
        "selected": selected,
        "strong_route_rate": route_rate,
        "realized_strong_query_saving": saving,
        "route_by_question_signal": route_by_group,
        "quality_retention": {"recall_at_1": r1_retention, "mrr": mrr_retention},
        "peak_vram_allocated_bytes": peak_vram,
        "quality_gate_passed": quality_gate,
        "cost_gate_passed": cost_gate,
        "resource_gate_passed": resource_gate,
        "gate_passed": quality_gate and cost_gate and resource_gate,
        "uncertainty_vs_always_strong": {
            "recall_at_1_difference": paired_bootstrap(
                selected_r1 - strong_r1, int(config["bootstrap_samples"]), int(config["seed"])
            ),
            "mrr_difference": paired_bootstrap(
                selected_mrr - strong_mrr, int(config["bootstrap_samples"]), int(config["seed"]) + 1
            ),
            "strong_only_correct": strong_only,
            "selected_only_correct": selected_only,
            "mcnemar_exact_p": exact_mcnemar_p_value(strong_only, selected_only),
        },
        "cost_scope": (
            "The early decision consumes only query, corpus-size, and Caption scores. Queries routed to "
            "Caption can causally skip ColSmol query encoding and MaxSim. The offline certification file "
            "contains both paths solely to score the fixed counterfactual policy."
        ),
    }
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2, ensure_ascii=False))
    raise SystemExit(0 if output["gate_passed"] else 2)


if __name__ == "__main__":
    main()
