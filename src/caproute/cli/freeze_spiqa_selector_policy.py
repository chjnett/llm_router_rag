from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from caproute.cli.evaluate_spiqa_selector import FEATURE_NAMES, choose_threshold, inference_features, selected_metrics
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file
from caproute.evaluation.retrieval import mean_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze a SPIQA selector before certification")
    parser.add_argument("--config", default="configs/p1v_spiqa_colsmol_selector_lock.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    train_path = Path(config["train_results"])
    calibration_path = Path(config["calibration_results"])
    train = json.loads(train_path.read_text(encoding="utf-8"))["questions"]
    calibration = json.loads(calibration_path.read_text(encoding="utf-8"))["questions"]
    x_train = np.asarray([inference_features(row) for row in train])
    x_calibration = np.asarray([inference_features(row) for row in calibration])
    y_train = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in train], dtype=np.int64)
    y_calibration = np.asarray([row["colsmol"]["mrr"] > row["caption"]["mrr"] for row in calibration], dtype=np.int64)
    model = make_pipeline(StandardScaler(), LogisticRegression(
        C=float(config["policy"]["regularization_c"]), random_state=int(config["seed"])
    ))
    model.fit(x_train, y_train)
    train_probability = model.predict_proba(x_train)[:, 1]
    calibration_probability = model.predict_proba(x_calibration)[:, 1]
    threshold, calibration_selected, calibration_route_rate = choose_threshold(
        calibration, calibration_probability, float(config["policy"]["max_calibration_route_rate"])
    )
    train_selected, train_route_rate = selected_metrics(train, train_probability, threshold)
    scaler = model.named_steps["standardscaler"]
    classifier = model.named_steps["logisticregression"]
    output = {
        "config": config, "config_sha256": config_hash(config),
        "train_results_sha256": sha256_file(train_path),
        "calibration_results_sha256": sha256_file(calibration_path),
        "feature_names": FEATURE_NAMES,
        "scaler_mean": [float(value) for value in scaler.mean_],
        "scaler_scale": [float(value) for value in scaler.scale_],
        "coefficients": [float(value) for value in classifier.coef_[0]],
        "intercept": float(classifier.intercept_[0]), "threshold": float(threshold),
        "train": {"questions": len(train), "positive_rate": float(y_train.mean()),
                  "auc": float(roc_auc_score(y_train, train_probability)),
                  "caption": mean_metrics([row["caption"] for row in train]),
                  "selected": train_selected, "route_rate": train_route_rate},
        "calibration": {"questions": len(calibration), "positive_rate": float(y_calibration.mean()),
                        "auc": float(roc_auc_score(y_calibration, calibration_probability)),
                        "caption": mean_metrics([row["caption"] for row in calibration]),
                        "selected": calibration_selected, "route_rate": calibration_route_rate},
    }
    target = Path(config["outputs"]["root"]) / "policy_lock.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **output}, indent=2))


if __name__ == "__main__":
    main()
