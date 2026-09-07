from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from caproute.core.io import read_json, write_json


def _latest_prediction_windows(output_root: Path, parser_name: str) -> list[Path]:
    """Return the latest prediction file for every sample offset."""
    candidates: dict[int, tuple[str, Path]] = {}
    for manifest_path in output_root.glob("*/run_manifest.json"):
        manifest = read_json(manifest_path)
        prediction_path = manifest_path.parent / "predictions" / f"{parser_name}.jsonl"
        if not prediction_path.exists():
            continue
        offset = int(manifest.get("dataset", {}).get("sample_offset", -1))
        run_id = manifest_path.parent.name
        previous = candidates.get(offset)
        if offset >= 0 and (previous is None or run_id > previous[0]):
            candidates[offset] = (run_id, prediction_path)
    return [row[1] for _, row in sorted(candidates.items())]


def _load_predictions(paths: list[Path]) -> dict[tuple[str, int | None], dict[str, Any]]:
    rows: dict[tuple[str, int | None], dict[str, Any]] = {}
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            document = row["document"]
            key = (document["document_id"], document.get("metadata", {}).get("requested_page"))
            rows[key] = row
    return rows


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="outputs/p0")
    parser.add_argument("--cheap", default="pymupdf")
    parser.add_argument("--strong", default="docling")
    parser.add_argument("--expected", type=int, default=300)
    parser.add_argument("--output", default="outputs/p0/p0_comparison.json")
    args = parser.parse_args()

    output_root = Path(args.output_root)
    cheap_paths = _latest_prediction_windows(output_root, args.cheap)
    strong_paths = _latest_prediction_windows(output_root, args.strong)
    cheap = _load_predictions(cheap_paths)
    strong = _load_predictions(strong_paths)
    paired_keys = sorted(set(cheap) & set(strong))

    proxy_keys = [
        key for key in paired_keys
        if cheap[key].get("quality", {}).get("table_count_f1_proxy") is not None
        and strong[key].get("quality", {}).get("table_count_f1_proxy") is not None
    ]
    cheap_proxy = [float(cheap[key]["quality"]["table_count_f1_proxy"]) for key in proxy_keys]
    strong_proxy = [float(strong[key]["quality"]["table_count_f1_proxy"]) for key in proxy_keys]
    cheap_latencies = [float(cheap[key]["latency_ms"]) for key in paired_keys]
    strong_latencies = [float(strong[key]["latency_ms"]) for key in paired_keys]
    strong_better = sum(s > c for c, s in zip(cheap_proxy, strong_proxy))
    cheap_better = sum(c > s for c, s in zip(cheap_proxy, strong_proxy))
    ties = len(proxy_keys) - strong_better - cheap_better

    cheap_summary = read_json(output_root / "cheap_300_aggregate.json")
    strong_summary = read_json(output_root / "strong_300_aggregate.json")
    p50_ratio = strong_summary["latency_ms_p50"] / cheap_summary["latency_ms_p50"]
    p95_ratio = strong_summary["latency_ms_p95"] / cheap_summary["latency_ms_p95"]
    result = {
        "expected_items": args.expected,
        "paired_items": len(paired_keys),
        "complete": len(paired_keys) == args.expected,
        "quality_metric": "table_count_f1_proxy",
        "quality_evaluable_items": len(proxy_keys),
        "quality_warning": "Diagnostic count proxy only; this is not official GriTS and cannot certify P0 quality.",
        "cheap": {
            "parser": args.cheap,
            "quality_mean_on_paired_items": _mean(cheap_proxy),
            "latency_ms_p50": cheap_summary["latency_ms_p50"],
            "latency_ms_p95": cheap_summary["latency_ms_p95"],
        },
        "strong": {
            "parser": args.strong,
            "quality_mean_on_paired_items": _mean(strong_proxy),
            "latency_ms_p50": strong_summary["latency_ms_p50"],
            "latency_ms_p95": strong_summary["latency_ms_p95"],
        },
        "paired_quality_outcomes": {
            "strong_better": strong_better,
            "cheap_better": cheap_better,
            "tie": ties,
        },
        "latency_ratio_strong_over_cheap": {"p50": p50_ratio, "p95": p95_ratio},
        "p0_gate": "HOLD",
        "p0_gate_reason": "Cost separation is measured, but official structure quality evaluation is not implemented.",
        "prediction_files": {
            "cheap": [str(path) for path in cheap_paths],
            "strong": [str(path) for path in strong_paths],
        },
    }
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
