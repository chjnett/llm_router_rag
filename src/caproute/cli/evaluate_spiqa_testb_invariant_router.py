from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from caproute.cli.screen_scivqa_invariant_router import INVARIANT_FEATURE_NAMES, invariant_features
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


def probabilities(rows: list[dict], lock: dict) -> np.ndarray:
    if tuple(lock["feature_names"]) != INVARIANT_FEATURE_NAMES:
        raise ValueError("Frozen invariant feature contract mismatch")
    features = np.asarray([invariant_features(row) for row in rows], dtype=np.float64)
    normalized = (features - np.asarray(lock["scaler_mean"])) / np.asarray(lock["scaler_scale"])
    logits = normalized @ np.asarray(lock["coefficients"]) + float(lock["intercept"])
    return 1.0 / (1.0 + np.exp(-np.clip(logits, -50, 50)))


def main() -> None:
    parser = argparse.ArgumentParser(description="Diagnose the frozen R5 router on SPIQA test-B")
    parser.add_argument("--config", default="configs/r6_spiqa_testb_router_diagnostic.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    lock_path = Path(config["policy_lock"])
    results_path = Path(config["retrieval_results"])
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    retrieval = json.loads(results_path.read_text(encoding="utf-8"))
    rows = retrieval["questions"]
    scores = probabilities(rows, lock)
    routed = scores >= float(lock["threshold"])
    selected = mean_metrics([
        row["colsmol" if route else "caption"] for row, route in zip(rows, routed)
    ])
    strong = mean_metrics([row["colsmol"] for row in rows])
    saving = 1.0 - float(routed.mean())
    gate = lock["frozen_gate"]
    quality_pass = (
        selected["recall_at_1"] / strong["recall_at_1"] >= float(gate["min_r1_retention"])
        and selected["mrr"] / strong["mrr"] >= float(gate["min_mrr_retention"])
    )
    cost_pass = saving >= float(gate["min_realized_strong_query_saving"])
    retrieval_ready = bool(retrieval["summary"]["gate_passed"])
    output = {
        "status": "diagnostic_only" if not retrieval_ready else "external_certification",
        "reason": None if retrieval_ready else "The frozen retrieval-readiness gate failed before routing.",
        "config_sha256": config_hash(config),
        "policy_lock_sha256": sha256_file(lock_path),
        "retrieval_results_sha256": sha256_file(results_path),
        "questions": len(rows),
        "threshold": lock["threshold"],
        "retrieval_summary": retrieval["summary"],
        "caption": mean_metrics([row["caption"] for row in rows]),
        "always_strong": strong,
        "selected": selected,
        "strong_route_rate": float(routed.mean()),
        "realized_strong_query_saving": saving,
        "quality_gate_passed": quality_pass,
        "cost_gate_passed": cost_pass,
        "retrieval_readiness_gate_passed": retrieval_ready,
        "certification_gate_passed": retrieval_ready and quality_pass and cost_pass,
    }
    target = Path(config["outputs"]["artifact"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
