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
from caproute.evaluation.retrieval import mean_metrics


FEATURE_NAMES = (
    "candidate_log", "question_tokens", "mentions_table", "mentions_visual",
    "caption_top", "caption_margin", "caption_entropy",
    "strong_top", "strong_margin", "strong_entropy",
    "top_difference", "margin_difference", "entropy_difference",
)


def inference_features(row: dict) -> list[float]:
    question = row["question"].casefold()
    caption = row["caption_signal"]
    strong = row["colsmol_signal"]
    return [
        math.log1p(row["candidate_images"]),
        float(len(re.findall(r"\w+", question))),
        float(any(term in question for term in ("table", "tabular", "row", "column"))),
        float(any(term in question for term in ("figure", "graph", "chart", "plot", "image", "diagram"))),
        caption["top_score"], caption["top_margin"], caption["normalized_entropy"],
        strong["top_score"], strong["top_margin"], strong["normalized_entropy"],
        strong["top_score"] - caption["top_score"],
        strong["top_margin"] - caption["top_margin"],
        strong["normalized_entropy"] - caption["normalized_entropy"],
    ]


def selected_metrics(rows: list[dict], probabilities: np.ndarray, threshold: float) -> tuple[dict, float]:
    route = probabilities >= threshold
    metrics = [row["colsmol"] if selected else row["caption"] for row, selected in zip(rows, route)]
    return mean_metrics(metrics), float(route.mean())


def choose_threshold(rows: list[dict], probabilities: np.ndarray, max_route_rate: float) -> tuple[float, dict, float]:
    candidates = sorted({float(value) for value in probabilities}, reverse=True) + [float("inf")]
    feasible = []
    for threshold in candidates:
        metrics, route_rate = selected_metrics(rows, probabilities, threshold)
        if route_rate <= max_route_rate:
            feasible.append((metrics["mrr"], metrics["recall_at_1"], -route_rate, threshold, metrics, route_rate))
    _, _, _, threshold, metrics, route_rate = max(feasible)
    return threshold, metrics, route_rate


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit a frozen SPIQA caption-to-ColSmol selector")
    parser.add_argument("--config", default="configs/p1v_spiqa_colsmol_selector.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    train = json.loads(Path(config["train_results"]).read_text(encoding="utf-8"))["questions"]
    calibration_path = config.get("calibration_results", config["train_results"])
    calibration = json.loads(Path(calibration_path).read_text(encoding="utf-8"))["questions"]
    test = json.loads(Path(config["test_results"]).read_text(encoding="utf-8"))["questions"]
    x_train = np.asarray([inference_features(row) for row in train], dtype=np.float64)
    x_calibration = np.asarray([inference_features(row) for row in calibration], dtype=np.float64)
    x_test = np.asarray([inference_features(row) for row in test], dtype=np.float64)
    y_train = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in train], dtype=np.int64)
    y_calibration = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in calibration], dtype=np.int64)
    y_test = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in test], dtype=np.int64)
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(C=float(config["policy"]["regularization_c"]), random_state=int(config["seed"])),
    )
    model.fit(x_train, y_train)
    train_probability = model.predict_proba(x_train)[:, 1]
    calibration_probability = model.predict_proba(x_calibration)[:, 1]
    test_probability = model.predict_proba(x_test)[:, 1]
    threshold, calibration_selected, calibration_route_rate = choose_threshold(
        calibration, calibration_probability, float(config["policy"]["max_train_route_rate"])
    )
    train_selected, train_route_rate = selected_metrics(train, train_probability, threshold)
    test_selected, test_route_rate = selected_metrics(test, test_probability, threshold)
    train_caption = mean_metrics([row["caption"] for row in train])
    calibration_caption = mean_metrics([row["caption"] for row in calibration])
    test_caption = mean_metrics([row["caption"] for row in test])
    test_strong = mean_metrics([row["colsmol"] for row in test])
    test_oracle = mean_metrics([row["oracle_selective"] for row in test])
    gate = config["gate"]
    gate_passed = (
        test_selected["recall_at_1"] - test_caption["recall_at_1"] >= float(gate["min_test_recall_at_1_gain"])
        and test_selected["mrr"] - test_caption["mrr"] >= float(gate["min_test_mrr_gain"])
        and test_route_rate <= float(gate["max_test_route_rate"])
    )
    classifier = model.named_steps["logisticregression"]
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "feature_names": FEATURE_NAMES,
        "threshold": threshold,
        "train": {"questions": len(train), "positive_rate": float(y_train.mean()),
                  "auc": float(roc_auc_score(y_train, train_probability)), "caption": train_caption,
                  "selected": train_selected, "route_rate": train_route_rate},
        "calibration": {"questions": len(calibration), "positive_rate": float(y_calibration.mean()),
                        "auc": float(roc_auc_score(y_calibration, calibration_probability)),
                        "caption": calibration_caption, "selected": calibration_selected,
                        "route_rate": calibration_route_rate},
        "test": {"questions": len(test), "positive_rate": float(y_test.mean()),
                 "auc": float(roc_auc_score(y_test, test_probability)), "caption": test_caption,
                 "always_colsmol": test_strong, "oracle": test_oracle,
                 "selected": test_selected, "route_rate": test_route_rate},
        "coefficients": dict(zip(FEATURE_NAMES, [float(value) for value in classifier.coef_[0]])),
        "gate_passed": gate_passed,
    }
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2))
    raise SystemExit(0 if gate_passed else 2)


if __name__ == "__main__":
    main()
