from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from caproute.cli.evaluate_spiqa_locked_selector import (
    exact_mcnemar_p_value,
    locked_probabilities,
    paired_bootstrap,
)
from caproute.cli.evaluate_spiqa_selector import selected_metrics
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the frozen SPIQA selector on SciVQA once")
    parser.add_argument("--config", default="configs/r3_scivqa_locked_selector.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    policy_path = Path(config["policy_lock"])
    results_path = Path(config["external_results"])
    lock = json.loads(policy_path.read_text(encoding="utf-8"))
    rows = json.loads(results_path.read_text(encoding="utf-8"))["questions"]
    probabilities = locked_probabilities(rows, lock)
    threshold = float(lock["threshold"])
    routed = probabilities >= threshold
    selected, route_rate = selected_metrics(rows, probabilities, threshold)
    caption = mean_metrics([row["caption"] for row in rows])
    strong = mean_metrics([row["colsmol"] for row in rows])
    oracle = mean_metrics([row["oracle_selective"] for row in rows])

    selected_r1 = np.asarray([row["colsmol" if route else "caption"]["recall_at_1"]
                              for row, route in zip(rows, routed)])
    strong_r1 = np.asarray([row["colsmol"]["recall_at_1"] for row in rows])
    selected_mrr = np.asarray([row["colsmol" if route else "caption"]["mrr"]
                               for row, route in zip(rows, routed)])
    strong_mrr = np.asarray([row["colsmol"]["mrr"] for row in rows])
    strong_only = int(np.sum((strong_r1 == 1) & (selected_r1 == 0)))
    selected_only = int(np.sum((strong_r1 == 0) & (selected_r1 == 1)))
    question_groups = {
        "visual": np.asarray([row["qa_pair_type"].endswith(" visual") for row in rows]),
        "non_visual": np.asarray([row["qa_pair_type"].endswith(" non-visual") for row in rows]),
    }
    route_by_group = {name: float(routed[mask].mean()) for name, mask in question_groups.items()}
    nominal_unselected_rate = 1.0 - route_rate
    realized_strong_query_saving = 0.0
    gate = config["gate"]
    quality_gate_passed = (
        selected["recall_at_1"] / strong["recall_at_1"] >= float(gate["min_r1_retention"])
        and selected["mrr"] / strong["mrr"] >= float(gate["min_mrr_retention"])
    )
    cost_gate_passed = realized_strong_query_saving >= float(gate["min_realized_strong_query_saving"])
    gate_passed = quality_gate_passed and cost_gate_passed
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "policy_lock_sha256": sha256_file(policy_path),
        "external_results_sha256": sha256_file(results_path),
        "questions": len(rows),
        "threshold": threshold,
        "caption": caption,
        "always_strong": strong,
        "oracle": oracle,
        "selected": selected,
        "strong_selection_rate": route_rate,
        "nominal_unselected_rate": nominal_unselected_rate,
        "realized_strong_query_saving": realized_strong_query_saving,
        "route_by_question_signal": route_by_group,
        "quality_retention": {
            "recall_at_1": selected["recall_at_1"] / strong["recall_at_1"],
            "mrr": selected["mrr"] / strong["mrr"],
        },
        "quality_gate_passed": quality_gate_passed,
        "cost_gate_passed": cost_gate_passed,
        "gate_passed": gate_passed,
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
            "The 13-feature policy consumes ColSmol score, margin, and entropy. It must run Strong query "
            "encoding and scoring before selection, so selection rate does not reduce Strong compute."
        ),
    }
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2))
    raise SystemExit(0 if gate_passed else 2)


if __name__ == "__main__":
    main()
