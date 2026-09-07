from __future__ import annotations

import time
import sys
from pathlib import Path
from statistics import median
from typing import Any

from caproute.benchmark.power import PowerSampler
from caproute.cache import PredictionCache
from caproute.datasets.pubtables import PubTablesSample
from caproute.evaluation.parsing import aggregate_quality, evaluate_document
from caproute.parsers.base import DocumentParser


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[round((len(ordered) - 1) * fraction)]


def run_parser(
    parser: DocumentParser, samples: list[PubTablesSample], cache: PredictionCache,
    refresh_cache: bool = False, power_interval_seconds: float = 0.5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    predictions, failures, latencies, quality_rows = [], [], [], []
    peak_before = peak_after = 0
    torch = sys.modules.get("torch")
    if torch is not None and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        peak_before = torch.cuda.max_memory_allocated()
    power = PowerSampler(power_interval_seconds)
    power.start()
    started_all = time.perf_counter()
    for sample in samples:
        try:
            key = cache.key(parser, sample.item)
            document = None if refresh_cache else cache.get(key)
            cached = document is not None
            started = time.perf_counter()
            if document is None:
                if torch is not None and torch.cuda.is_available():
                    torch.cuda.synchronize()
                document = parser.parse(sample.item)
                if torch is not None and torch.cuda.is_available():
                    torch.cuda.synchronize()
                latencies.append(1000 * (time.perf_counter() - started))
                cache.put(key, document)
            quality = evaluate_document(document, sample.ground_truth)
            quality_rows.append(quality)
            predictions.append({"document": document.to_dict(), "cache_key": key, "cache_hit": cached, "quality": quality})
        except Exception as error:
            failures.append({"document_id": sample.item.document_id, "source_path": str(sample.item.source_path), "error": repr(error)})
    elapsed = time.perf_counter() - started_all
    energy = power.stop(elapsed)
    if torch is not None and torch.cuda.is_available():
        peak_after = torch.cuda.max_memory_allocated()
    metrics = {
        **aggregate_quality(quality_rows),
        "attempted": len(samples),
        "completed": len(predictions),
        "failed": len(failures),
        "cache_hits": sum(bool(row["cache_hit"]) for row in predictions),
        "measured_uncached_items": len(latencies),
        "latency_ms_p50": percentile(latencies, 0.5),
        "latency_ms_p95": percentile(latencies, 0.95),
        "elapsed_seconds": elapsed,
        "gpu_seconds_per_page": elapsed / len(latencies) if latencies else None,
        "peak_vram_allocated_bytes": max(0, peak_after - peak_before),
        **energy,
    }
    return predictions, failures, metrics
