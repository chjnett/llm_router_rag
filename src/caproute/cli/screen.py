from __future__ import annotations

import argparse
import datetime as dt
import gc
from pathlib import Path

from caproute.benchmark.harness import run_parser
from caproute.cache import PredictionCache
from caproute.core.config import config_hash, load_config
from caproute.core.io import write_json, write_jsonl
from caproute.core.repro import environment_metadata, git_metadata, set_seed
from caproute.datasets.pubtables import load_pubtables_subset
from caproute.parsers.strong import build_parser


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/p0_screening.yaml")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--refresh-cache", action="store_true")
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    cfg = load_config(config_path)
    root = config_path.parent.parent
    dataset = cfg["dataset"]
    resolve = lambda value: (root / value).resolve()
    annotation_path = resolve(dataset["annotations"])
    split_path = resolve(dataset["split_file"])
    if not annotation_path.exists() or not split_path.exists():
        raise FileNotFoundError(
            f"PubTables VOC annotations/split not found: {annotation_path}, {split_path}"
        )
    configured_size = int(dataset["sample_size"])
    window_size = args.limit or configured_size
    load_limit = min(configured_size, args.offset + window_size)
    samples = load_pubtables_subset(
        annotation_path, split_path, resolve(dataset["image_root"]), resolve(dataset["pdf_root"]),
        load_limit, int(cfg["seed"]), bool(dataset.get("document_level_sampling", True)),
        set(dataset.get("exclude_document_ids", [])),
    )
    samples = samples[args.offset : args.offset + window_size]
    missing = [str(sample.item.source_path) for sample in samples if not sample.item.source_path.exists()]
    if missing:
        raise FileNotFoundError(f"{len(missing)} selected sources are missing; first: {missing[0]}")
    if dataset.get("require_source_pdf", True):
        non_pdf = [str(sample.item.source_path) for sample in samples if sample.item.source_path.suffix.lower() != ".pdf"]
        if non_pdf:
            raise FileNotFoundError(
                f"{len(non_pdf)} samples have no source PubMed PDF; first fallback image: {non_pdf[0]}"
            )
    if args.validate_only:
        parsers = [build_parser(row["name"], row.get("options")) for row in cfg["parsers"]]
        print(f"validated config, {len(samples)} samples, parsers={[p.name for p in parsers]}")
        return
    set_seed(int(cfg["seed"]))
    run_id = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    output = resolve(cfg["outputs"]["root"]) / run_id
    cache = PredictionCache(resolve(cfg["cache"]["root"]))
    manifest = {
        "run_id": run_id, "config_path": str(config_path), "config_hash": config_hash(cfg),
        "config_snapshot": cfg,
        "git": git_metadata(root), "environment": environment_metadata(),
        "dataset": {
            **dataset,
            "selected_count": len(samples),
            "sample_offset": args.offset,
            "sample_window": window_size,
        },
    }
    write_json(output / "run_manifest.json", manifest)
    for parser_config in cfg["parsers"]:
        implementation = build_parser(parser_config["name"], parser_config.get("options"))
        predictions, failures, metrics = run_parser(
            implementation, samples, cache, args.refresh_cache,
            float(cfg["benchmark"]["power_interval_seconds"]),
            int(cfg["benchmark"].get("warmup", 0)),
        )
        write_jsonl(output / "predictions" / f"{implementation.name}.jsonl", predictions)
        write_jsonl(output / "failures" / f"{implementation.name}.jsonl", failures)
        write_json(output / "metrics" / f"{implementation.name}.json", metrics)
        print(f"{implementation.name}: {metrics}")
        del implementation
        gc.collect()
    print(output)


if __name__ == "__main__":
    main()
