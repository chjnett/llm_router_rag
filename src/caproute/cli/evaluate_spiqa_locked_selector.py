from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from caproute.cli.evaluate_spiqa_selector import inference_features, selected_metrics
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


def locked_probabilities(rows: list[dict], lock: dict) -> np.ndarray:
    features = np.asarray([inference_features(row) for row in rows])
    normalized = (features - np.asarray(lock["scaler_mean"])) / np.asarray(lock["scaler_scale"])
    logits = normalized @ np.asarray(lock["coefficients"]) + float(lock["intercept"])
    return 1.0 / (1.0 + np.exp(-logits))


def paired_bootstrap(values: np.ndarray, samples: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    means = np.empty(samples, dtype=np.float64)
    for index in range(samples):
        means[index] = values[rng.integers(0, len(values), len(values))].mean()
    low, high = np.quantile(means, [0.025, 0.975])
    return {"mean": float(values.mean()), "ci95_low": float(low), "ci95_high": float(high)}


def exact_mcnemar_p_value(caption_only: int, selected_only: int) -> float:
    discordant = caption_only + selected_only
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, index) for index in range(min(caption_only, selected_only) + 1)) / 2 ** discordant
    return min(1.0, 2.0 * tail)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a locked SPIQA selector once")
    parser.add_argument("--config", default="configs/p1v_spiqa_colsmol_selector_certified.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    lock_path = Path(config["policy_lock"])
    test_path = Path(config["test_results"])
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    rows = json.loads(test_path.read_text(encoding="utf-8"))["questions"]
    probabilities = locked_probabilities(rows, lock)
    selected, route_rate = selected_metrics(rows, probabilities, float(lock["threshold"]))
    routed = probabilities >= float(lock["threshold"])
    caption_r1 = np.asarray([row["caption"]["recall_at_1"] for row in rows])
    selected_r1 = np.asarray([row["colsmol" if route else "caption"]["recall_at_1"]
                              for row, route in zip(rows, routed)])
    caption_mrr = np.asarray([row["caption"]["mrr"] for row in rows])
    selected_mrr = np.asarray([row["colsmol" if route else "caption"]["mrr"]
                               for row, route in zip(rows, routed)])
    caption_only = int(np.sum((caption_r1 == 1) & (selected_r1 == 0)))
    selected_only = int(np.sum((caption_r1 == 0) & (selected_r1 == 1)))
    caption = mean_metrics([row["caption"] for row in rows])
    always_colsmol = mean_metrics([row["colsmol"] for row in rows])
    oracle = mean_metrics([row["oracle_selective"] for row in rows])
    gate = config["gate"]
    gate_passed = (
        selected["recall_at_1"] - caption["recall_at_1"] >= float(gate["min_test_recall_at_1_gain"])
        and selected["mrr"] - caption["mrr"] >= float(gate["min_test_mrr_gain"])
        and route_rate <= float(gate["max_test_route_rate"])
    )
    output = {
        "config": config, "config_sha256": config_hash(config),
        "policy_lock_sha256": sha256_file(lock_path), "test_results_sha256": sha256_file(test_path),
        "questions": len(rows), "threshold": lock["threshold"], "caption": caption,
        "always_colsmol": always_colsmol, "oracle": oracle, "selected": selected,
        "route_rate": route_rate, "gate_passed": gate_passed,
        "uncertainty": {
            "recall_at_1_difference": paired_bootstrap(
                selected_r1 - caption_r1, int(config["bootstrap_samples"]), int(config["seed"])
            ),
            "mrr_difference": paired_bootstrap(
                selected_mrr - caption_mrr, int(config["bootstrap_samples"]), int(config["seed"]) + 1
            ),
            "caption_only_correct": caption_only,
            "selected_only_correct": selected_only,
            "mcnemar_exact_p": exact_mcnemar_p_value(caption_only, selected_only),
        },
    }
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2))
    raise SystemExit(0 if gate_passed else 2)


if __name__ == "__main__":
    main()
