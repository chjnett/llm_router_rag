from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


EARLY_FEATURE_NAMES = (
    "candidate_log",
    "question_tokens",
    "mentions_table",
    "mentions_visual",
    "caption_top",
    "caption_margin",
    "caption_entropy",
)


def early_features(row: dict) -> list[float]:
    question = row["question"].casefold()
    caption = row["caption_signal"]
    return [
        math.log1p(row["candidate_images"]),
        float(len(re.findall(r"\w+", question))),
        float(any(term in question for term in ("table", "tabular", "row", "column"))),
        float(any(term in question for term in ("figure", "graph", "chart", "plot", "image", "diagram"))),
        caption["top_score"],
        caption["top_margin"],
        caption["normalized_entropy"],
    ]


def routed_metrics(rows: list[dict], probabilities: np.ndarray, threshold: float) -> tuple[dict, float]:
    routed = probabilities >= threshold
    metrics = [row["colsmol" if route else "caption"] for row, route in zip(rows, routed)]
    return mean_metrics(metrics), float(routed.mean())


def select_threshold(rows: list[dict], probabilities: np.ndarray, gate: dict) -> tuple[float, dict, float]:
    always_strong = mean_metrics([row["colsmol"] for row in rows])
    feasible = []
    for threshold in sorted({float(value) for value in probabilities}, reverse=True) + [float("inf")]:
        metrics, route_rate = routed_metrics(rows, probabilities, threshold)
        if (
            route_rate <= float(gate["max_strong_route_rate"])
            and metrics["recall_at_1"] / always_strong["recall_at_1"] >= float(gate["min_r1_retention"])
            and metrics["mrr"] / always_strong["mrr"] >= float(gate["min_mrr_retention"])
        ):
            feasible.append((metrics["mrr"], metrics["recall_at_1"], -route_rate, threshold, metrics, route_rate))
    if not feasible:
        raise RuntimeError("No calibration threshold satisfies the frozen quality/cost gate")
    _, _, _, threshold, metrics, route_rate = max(feasible)
    return threshold, metrics, route_rate


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit and lock a causally valid Cheap-only early router")
    parser.add_argument("--config", default="configs/r4_spiqa_early_router_lock.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    train_path = Path(config["train_results"])
    calibration_path = Path(config["calibration_results"])
    train = json.loads(train_path.read_text(encoding="utf-8"))["questions"]
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))["questions"]
    x_train = np.asarray([early_features(row) for row in train], dtype=np.float64)
    x_calibration = np.asarray([early_features(row) for row in calibration], dtype=np.float64)
    y_train = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in train], dtype=np.int64)
    y_calibration = np.asarray(
        [row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in calibration], dtype=np.int64
    )
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=float(config["policy"]["regularization_c"]), random_state=int(config["seed"])),
    )
    model.fit(x_train, y_train)
    train_probability = model.predict_proba(x_train)[:, 1]
    calibration_probability = model.predict_proba(x_calibration)[:, 1]
    threshold, calibration_selected, calibration_route_rate = select_threshold(
        calibration, calibration_probability, config["gate"]
    )
    train_selected, train_route_rate = routed_metrics(train, train_probability, threshold)
    scaler = model.named_steps["standardscaler"]
    classifier = model.named_steps["logisticregression"]
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "train_results_sha256": sha256_file(train_path),
        "calibration_results_sha256": sha256_file(calibration_path),
        "feature_names": EARLY_FEATURE_NAMES,
        "causal_contract": "No ColSmol-derived feature is consumed before the route decision.",
        "scaler_mean": [float(value) for value in scaler.mean_],
        "scaler_scale": [float(value) for value in scaler.scale_],
        "coefficients": [float(value) for value in classifier.coef_[0]],
        "intercept": float(classifier.intercept_[0]),
        "threshold": threshold,
        "train": {
            "questions": len(train),
            "positive_rate": float(y_train.mean()),
            "auc": float(roc_auc_score(y_train, train_probability)),
            "caption": mean_metrics([row["caption"] for row in train]),
            "always_strong": mean_metrics([row["colsmol"] for row in train]),
            "selected": train_selected,
            "strong_route_rate": train_route_rate,
        },
        "calibration": {
            "questions": len(calibration),
            "positive_rate": float(y_calibration.mean()),
            "auc": float(roc_auc_score(y_calibration, calibration_probability)),
            "caption": mean_metrics([row["caption"] for row in calibration]),
            "always_strong": mean_metrics([row["colsmol"] for row in calibration]),
            "selected": calibration_selected,
            "strong_route_rate": calibration_route_rate,
            "realized_strong_query_saving": 1.0 - calibration_route_rate,
        },
        "next_test": "katebor/SciVQA test; manifest and labels must remain unopened until this lock is committed",
    }
    target = Path(config["outputs"]["policy_lock"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2))


if __name__ == "__main__":
    main()
