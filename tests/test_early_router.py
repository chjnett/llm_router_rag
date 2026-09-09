import numpy as np
import pytest

from caproute.cli.evaluate_scivqa_early_router import early_probabilities
from caproute.cli.freeze_spiqa_early_router_policy import early_features, routed_metrics


def _row(caption_mrr: float, strong_mrr: float) -> dict:
    metric_keys = {
        "recall_at_1": caption_mrr,
        "recall_at_5": caption_mrr,
        "recall_at_10": caption_mrr,
        "mrr": caption_mrr,
        "ndcg_at_5": caption_mrr,
    }
    strong = {key: strong_mrr for key in metric_keys}
    return {
        "question": "Which figure shows the result?",
        "candidate_images": 9,
        "caption_signal": {"top_score": 0.7, "top_margin": 0.1, "normalized_entropy": 0.9},
        "caption": metric_keys,
        "colsmol": strong,
    }


def test_early_features_do_not_require_strong_signal() -> None:
    features = early_features(_row(0.2, 0.8))
    assert len(features) == 7
    assert features[3] == 1.0


def test_routed_metrics_uses_strong_only_above_threshold() -> None:
    rows = [_row(1.0, 0.0), _row(0.0, 1.0)]
    metrics, route_rate = routed_metrics(rows, np.asarray([0.1, 0.9]), 0.5)
    assert metrics["mrr"] == 1.0
    assert route_rate == 0.5


def test_early_probabilities_rejects_changed_feature_contract() -> None:
    lock = {
        "feature_names": ["wrong"],
        "scaler_mean": [0.0] * 7,
        "scaler_scale": [1.0] * 7,
        "coefficients": [0.0] * 7,
        "intercept": 0.0,
    }
    with pytest.raises(ValueError, match="feature contract"):
        early_probabilities([_row(1.0, 0.0)], lock)
