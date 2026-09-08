from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from caproute.benchmark.harness import percentile
from caproute.benchmark.power import PowerSampler
from caproute.cache import PredictionCache
from caproute.core.config import config_hash, load_config
from caproute.core.repro import environment_metadata, git_metadata
from caproute.parsers.base import DocumentInput
from caproute.parsers.strong import build_parser


def adjacent_pages(pages: list[int], page_count: int) -> set[int]:
    result = set(pages)
    for page in pages:
        result.update(index for index in (page - 1, page + 1) if 0 <= index < page_count)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure Always Strong versus cached query-time page rescue cost")
    parser.add_argument("--config", default="configs/r2_page_rescue_cost.yaml")
    parser.add_argument("--refresh-cache", action="store_true")
    parser.add_argument("--resume", action="store_true", help="Process only pages missing from the latency checkpoint")
    parser.add_argument("--limit", type=int, help="Bound one native Docling process to a small page batch")
    args = parser.parse_args()
    config = load_config(args.config)
    root = Path.cwd()
    mapping = json.loads(Path(config["dataset"]["page_mapping_results"]).read_text(encoding="utf-8"))
    paper_pages = {paper["paper_id"]: paper["pages"] for paper in mapping["papers"] if paper.get("success")}
    all_pages = {(paper_id, page) for paper_id, count in paper_pages.items() for page in range(count)}
    top_pages: set[tuple[str, int]] = set()
    adjacent: set[tuple[str, int]] = set()
    top_query_page_sets: list[set[tuple[str, int]]] = []
    adjacent_query_page_sets: list[set[tuple[str, int]]] = []
    uncached_top_calls = uncached_adjacent_calls = 0
    for row in mapping["questions"]:
        current = set(row["retrieved_pages"])
        expanded = adjacent_pages(row["retrieved_pages"], paper_pages[row["paper_id"]])
        top_pages.update((row["paper_id"], page) for page in current)
        adjacent.update((row["paper_id"], page) for page in expanded)
        top_query_page_sets.append({(row["paper_id"], page) for page in current})
        adjacent_query_page_sets.append({(row["paper_id"], page) for page in expanded})
        uncached_top_calls += len(current)
        uncached_adjacent_calls += len(expanded)

    implementation = build_parser(config["strong_parser"]["name"], config["strong_parser"]["options"])
    cache = PredictionCache(config["cache"]["root"])
    ordered_pages = sorted(all_pages)
    output_root = Path(config["outputs"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_root / "page_measurements.checkpoint.json"
    latencies: dict[tuple[str, int], float] = {}
    if args.resume and checkpoint_path.exists():
        saved = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        latencies = {(row["paper_id"], int(row["page"])): float(row["latency_seconds"]) for row in saved}
    pages_to_process = [page for page in ordered_pages if page not in latencies] if args.resume else ordered_pages
    if args.limit is not None:
        pages_to_process = pages_to_process[:args.limit]
    if int(config["benchmark"]["warmup_pages"]):
        paper_id, page = ordered_pages[0]
        implementation.parse(DocumentInput(paper_id, Path(config["dataset"]["pdf_root"]) / f"{paper_id}.pdf", page))

    torch = sys.modules.get("torch")
    if torch is not None and torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    power = PowerSampler(float(config["benchmark"]["power_interval_seconds"]))
    power.start()
    run_started = time.perf_counter()
    cache_hits = 0
    failures = []
    for number, (paper_id, page) in enumerate(pages_to_process, 1):
        item = DocumentInput(paper_id, Path(config["dataset"]["pdf_root"]) / f"{paper_id}.pdf", page)
        key = cache.key(implementation, item)
        document = None if args.refresh_cache else cache.get(key)
        if document is not None:
            cache_hits += 1
            continue
        try:
            if torch is not None and torch.cuda.is_available():
                torch.cuda.synchronize()
            started = time.perf_counter()
            document = implementation.parse(item)
            if torch is not None and torch.cuda.is_available():
                torch.cuda.synchronize()
            latencies[(paper_id, page)] = time.perf_counter() - started
            cache.put(key, document)
            checkpoint_path.write_text(json.dumps([
                {"paper_id": key[0], "page": key[1], "latency_seconds": value}
                for key, value in sorted(latencies.items())
            ], indent=2), encoding="utf-8")
        except Exception as error:
            failures.append({"paper_id": paper_id, "page": page, "error": repr(error)})
        if number % 10 == 0 or number == len(pages_to_process):
            print(f"batch_progress {number}/{len(pages_to_process)} total_checkpoint={len(latencies)}/{len(ordered_pages)} failures={len(failures)}", flush=True)
    elapsed = time.perf_counter() - run_started
    energy = power.stop(elapsed)
    peak_vram = torch.cuda.max_memory_allocated() if torch is not None and torch.cuda.is_available() else None
    previous_result_path = output_root / "results.json"
    if args.resume and previous_result_path.exists():
        previous_peak = json.loads(previous_result_path.read_text(encoding="utf-8")).get("summary", {}).get("peak_vram_allocated_bytes")
        if previous_peak is not None:
            peak_vram = max(peak_vram or 0, previous_peak)

    if len(latencies) < len(all_pages):
        print(json.dumps({"status": "partial", "checkpoint_pages": len(latencies), "all_pages": len(all_pages),
                          "batch_failures": failures, "batch_elapsed_seconds": elapsed}, indent=2))
        return

    # A fresh measurement is required for the comparison. A fully cached rerun is
    # useful operationally but cannot silently replace measured page latency.
    if cache_hits:
        previous = output_root / "results.json"
        if previous.exists():
            old = json.loads(previous.read_text(encoding="utf-8"))
            latencies = {(row["paper_id"], row["page"]): row["latency_seconds"] for row in old["page_measurements"]}
    always_cost = sum(latencies.get(page, 0.0) for page in all_pages)

    def strategy(name: str, pages: set[tuple[str, int]], per_query_pages: list[set[tuple[str, int]]],
                 recall: float, hit: float, uncached_calls: int) -> dict:
        cost = sum(latencies.get(page, 0.0) for page in pages)
        uncached_cost = sum(latencies.get(page, 0.0) for query_pages in per_query_pages for page in query_pages)
        page_reduction = 1 - len(pages) / len(all_pages)
        saving = 1 - cost / always_cost if always_cost else 0.0
        gate = config["gate"]
        return {
            "name": name, "quality_page_recall": recall, "quality_page_hit": hit,
            "unique_strong_pages": len(pages), "uncached_per_query_page_calls": uncached_calls,
            "unique_strong_page_reduction": page_reduction, "measured_strong_seconds": cost,
            "measured_strong_latency_saving": saving,
            "uncached_per_query_strong_seconds": uncached_cost,
            "uncached_per_query_saving_vs_one_always_strong_index": 1 - uncached_cost / always_cost if always_cost else 0.0,
            "gate_passed": recall >= float(gate["min_page_recall"])
            and page_reduction >= float(gate["min_unique_strong_page_reduction"])
            and saving >= float(gate["min_strong_latency_saving"]),
        }

    page_metrics = mapping["summary"]["page_metrics"]
    strategies = [
        strategy("top5_pages", top_pages, top_query_page_sets, page_metrics["page_recall_at_5"], page_metrics["page_hit_at_5"], uncached_top_calls),
        strategy("top5_plus_adjacent", adjacent, adjacent_query_page_sets, page_metrics["adjacent_rescue_recall"], page_metrics["adjacent_rescue_hit"], uncached_adjacent_calls),
    ]
    output = {
        "config": config, "config_sha256": config_hash(config), "git": git_metadata(root),
        "environment": environment_metadata(), "summary": {
            "all_pages": len(all_pages), "questions": len(mapping["questions"]),
            "completed_pages": len(latencies), "cache_hits": cache_hits, "failures": len(failures),
            "always_strong_seconds": always_cost,
            "latency_ms_p50": 1000 * percentile(list(latencies.values()), 0.5) if latencies else None,
            "latency_ms_p95": 1000 * percentile(list(latencies.values()), 0.95) if latencies else None,
            "peak_vram_allocated_bytes": peak_vram, **energy,
            "energy_measurement_scope": "current process batch only; not aggregated across recovered native-process batches",
            "any_strategy_passed": any(row["gate_passed"] for row in strategies),
        }, "strategies": strategies, "failures": failures,
        "page_measurements": [{"paper_id": paper_id, "page": page, "latency_seconds": latency}
                              for (paper_id, page), latency in sorted(latencies.items())],
    }
    target = output_root / "results.json"
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), "summary": output["summary"], "strategies": strategies}, indent=2))
    raise SystemExit(0 if output["summary"]["any_strategy_passed"] else 2)


if __name__ == "__main__":
    main()
