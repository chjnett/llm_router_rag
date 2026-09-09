from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from caproute.cli.freeze_spiqa_early_router_policy import routed_metrics, select_threshold
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


INVARIANT_FEATURE_NAMES = (
    "question_log_tokens",
    "question_token_diversity",
    "mentions_table",
    "mentions_visual",
    "caption_top",
    "caption_margin",
    "caption_entropy",
)


def invariant_features(row: dict) -> list[float]:
    tokens = re.findall(r"\w+", row["question"].casefold())
    caption = row["caption_signal"]
    return [
        math.log1p(len(tokens)),
        len(set(tokens)) / max(len(tokens), 1),
        float(any(term in tokens for term in ("table", "tabular", "row", "column"))),
        float(any(term in tokens for term in ("figure", "graph", "chart", "plot", "image", "diagram"))),
        float(caption["top_score"]),
        float(caption["top_margin"]),
        float(caption["normalized_entropy"]),
    ]


def paper_split(rows: list[dict], seed: int, train_fraction: float) -> tuple[list[dict], list[dict]]:
    papers = sorted({row["paper_id"] for row in rows})
    ranked = sorted(
        papers,
        key=lambda paper: hashlib.sha256(f"{seed}:{paper}".encode("utf-8")).hexdigest(),
    )
    cutoff = max(1, min(len(ranked) - 1, round(len(ranked) * train_fraction)))
    train_papers = set(ranked[:cutoff])
    return (
        [row for row in rows if row["paper_id"] in train_papers],
        [row for row in rows if row["paper_id"] not in train_papers],
    )


def fit_variant(train: list[dict], calibration: list[dict], config: dict, c: float, positive_weight: float) -> dict:
    x_train = np.asarray([invariant_features(row) for row in train], dtype=np.float64)
    x_calibration = np.asarray([invariant_features(row) for row in calibration], dtype=np.float64)
    y_train = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in train], dtype=np.int64)
    y_calibration = np.asarray(
        [row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in calibration], dtype=np.int64
    )
    model = make_pipeline(
        StandardScaler(),
        LogisticRegression(
            C=c,
            class_weight={0: 1.0, 1: positive_weight},
            random_state=int(config["seed"]),
            max_iter=2000,
        ),
    )
    model.fit(x_train, y_train)
    train_probability = model.predict_proba(x_train)[:, 1]
    calibration_probability = model.predict_proba(x_calibration)[:, 1]
    try:
        threshold, selected, route_rate = select_threshold(
            calibration, calibration_probability, config["gate"]
        )
    except RuntimeError:
        return {"c": c, "positive_weight": positive_weight, "feasible": False}
    scaler = model.named_steps["standardscaler"]
    classifier = model.named_steps["logisticregression"]
    train_selected, train_route_rate = routed_metrics(train, train_probability, threshold)
    strong = mean_metrics([row["colsmol"] for row in calibration])
    return {
        "c": c,
        "positive_weight": positive_weight,
        "feasible": True,
        "threshold": threshold,
        "train_auc": float(roc_auc_score(y_train, train_probability)),
        "calibration_auc": float(roc_auc_score(y_calibration, calibration_probability)),
        "train_selected": train_selected,
        "train_strong_route_rate": train_route_rate,
        "calibration_selected": selected,
        "calibration_always_strong": strong,
        "calibration_strong_route_rate": route_rate,
        "calibration_strong_query_saving": 1.0 - route_rate,
        "calibration_r1_retention": selected["recall_at_1"] / strong["recall_at_1"],
        "calibration_mrr_retention": selected["mrr"] / strong["mrr"],
        "scaler_mean": [float(value) for value in scaler.mean_],
        "scaler_scale": [float(value) for value in scaler.scale_],
        "coefficients": [float(value) for value in classifier.coef_[0]],
        "intercept": float(classifier.intercept_[0]),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Screen corpus-size invariant Cheap-only routers")
    parser.add_argument("--config", default="configs/r5_scivqa_invariant_router_screen.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    source = Path(config["development_results"])
    rows = json.loads(source.read_text(encoding="utf-8"))["questions"]
    train, calibration = paper_split(rows, int(config["seed"]), float(config["split"]["train_fraction"]))
    variants = [
        fit_variant(train, calibration, config, float(c), float(weight))
        for c in config["screen"]["regularization_c"]
        for weight in config["screen"]["positive_class_weight"]
    ]
    feasible = [variant for variant in variants if variant["feasible"]]
    best = None
    if feasible:
        best_mrr = max(item["calibration_selected"]["mrr"] for item in feasible)
        statistically_tied = [
            item for item in feasible
            if best_mrr - item["calibration_selected"]["mrr"] <= 1e-4
        ]
        best = max(
            statistically_tied,
            key=lambda item: (
                item["calibration_strong_query_saving"],
                -item["positive_weight"],
                -item["c"],
            ),
        )
    output = {
        "status": "development_only_not_a_policy_lock",
        "config": config,
        "config_sha256": config_hash(config),
        "development_results_sha256": sha256_file(source),
        "feature_names": INVARIANT_FEATURE_NAMES,
        "causal_contract": "No corpus size or Strong-derived feature is consumed before routing.",
        "split": {
            "train_questions": len(train),
            "train_papers": len({row["paper_id"] for row in train}),
            "calibration_questions": len(calibration),
            "calibration_papers": len({row["paper_id"] for row in calibration}),
            "paper_overlap": len({row["paper_id"] for row in train} & {row["paper_id"] for row in calibration}),
        },
        "variants": variants,
        "best_development_candidate": best,
        "next_gate": "Freeze one candidate before acquiring a new unopened external holdout.",
    }
    target = Path(config["outputs"]["artifact"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), "best": best, "split": output["split"]}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
