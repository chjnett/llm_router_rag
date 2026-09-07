from __future__ import annotations

import argparse
from pathlib import Path

from caproute.benchmark.harness import percentile
from caproute.core.io import read_json, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", default="outputs/p0")
    parser.add_argument("--parser", default="docling")
    parser.add_argument("--expected", type=int, default=300)
    parser.add_argument("--output", default="outputs/p0/strong_300_aggregate.json")
    args = parser.parse_args()

    candidates: dict[int, tuple[Path, dict]] = {}
    for manifest_path in Path(args.output_root).glob("*/run_manifest.json"):
        manifest = read_json(manifest_path)
        offset = int(manifest.get("dataset", {}).get("sample_offset", -1))
        prediction_path = manifest_path.parent / "predictions" / f"{args.parser}.jsonl"
        if offset >= 0 and prediction_path.exists():
            previous = candidates.get(offset)
            if previous is None or manifest_path.parent.name > previous[0].parent.name:
                candidates[offset] = (manifest_path, manifest)

    items: dict[tuple[str, int | None], dict] = {}
    runs = []
    for offset, (manifest_path, manifest) in sorted(candidates.items()):
        prediction_path = manifest_path.parent / "predictions" / f"{args.parser}.jsonl"
        for line in prediction_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            import json
            row = json.loads(line)
            document = row["document"]
            key = (document["document_id"], document.get("metadata", {}).get("requested_page"))
            items[key] = row
        runs.append({"offset": offset, "run": manifest_path.parent.name, "config_hash": manifest["config_hash"]})

    rows = list(items.values())
    latencies = [float(row["latency_ms"]) for row in rows if row.get("latency_ms") is not None]
    table_f1 = [
        float(row["quality"]["table_count_f1_proxy"])
        for row in rows
        if row.get("quality", {}).get("table_count_f1_proxy") is not None
    ]
    result = {
        "parser": args.parser,
        "unique_items": len(rows),
        "expected_items": args.expected,
        "complete": len(rows) == args.expected and len(latencies) == args.expected,
        "latency_ms_p50": percentile(latencies, 0.5),
        "latency_ms_p95": percentile(latencies, 0.95),
        "table_count_f1_proxy_mean": sum(table_f1) / len(table_f1) if table_f1 else None,
        "runs": runs,
    }
    write_json(args.output, result)
    print(result)
    if not result["complete"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
