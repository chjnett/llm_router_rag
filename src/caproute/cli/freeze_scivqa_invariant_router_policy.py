from __future__ import annotations

import argparse
import json
from pathlib import Path

from caproute.cli.screen_scivqa_invariant_router import INVARIANT_FEATURE_NAMES
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the R5 invariant router before external evaluation")
    parser.add_argument("--config", default="configs/r5_scivqa_invariant_router_lock.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    screen_path = Path(config["screen_artifact"])
    screen = json.loads(screen_path.read_text(encoding="utf-8"))
    candidate = screen["best_development_candidate"]
    if not candidate or not candidate["feasible"]:
        raise RuntimeError("The development screen has no feasible candidate to freeze")
    if tuple(screen["feature_names"]) != INVARIANT_FEATURE_NAMES:
        raise ValueError("Invariant feature contract changed after development screening")
    output = {
        "status": "frozen_before_external_holdout",
        "config": config,
        "config_sha256": config_hash(config),
        "screen_artifact_sha256": sha256_file(screen_path),
        "development_results_sha256": screen["development_results_sha256"],
        "feature_names": list(INVARIANT_FEATURE_NAMES),
        "causal_contract": screen["causal_contract"],
        "regularization_c": candidate["c"],
        "positive_class_weight": candidate["positive_weight"],
        "scaler_mean": candidate["scaler_mean"],
        "scaler_scale": candidate["scaler_scale"],
        "coefficients": candidate["coefficients"],
        "intercept": candidate["intercept"],
        "threshold": candidate["threshold"],
        "frozen_gate": config["gate"],
        "prohibitions": [
            "Do not evaluate or tune this policy on the previously opened SciVQA test.",
            "Do not change features, coefficients, threshold, or gates after opening the new holdout.",
        ],
    }
    target = Path(config["outputs"]["policy_lock"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), "threshold": output["threshold"], "gate": output["frozen_gate"]}, indent=2))


if __name__ == "__main__":
    main()
