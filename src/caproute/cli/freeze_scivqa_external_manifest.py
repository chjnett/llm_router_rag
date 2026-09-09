from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file


def normalize_paper_id(value: str) -> str:
    normalized = str(value).removesuffix(".pdf")
    return re.sub(r"v\d+$", "", normalized)


def build_manifest(rows: list[dict], archive_names: set[str], image_prefix: str,
                   excluded_papers: set[str], excluded_types: set[str]) -> tuple[list[dict], list[dict]]:
    corpus_by_image: dict[str, dict] = {}
    queries = []
    prefix = image_prefix.rstrip("/")
    for row in rows:
        paper_id = normalize_paper_id(row["paper_id"])
        if paper_id in excluded_papers or row["qa_pair_type"] in excluded_types:
            continue
        image_file = row["image_file"]
        archive_path = f"{prefix}/{image_file}"
        if archive_path not in archive_names:
            continue
        corpus_by_image.setdefault(image_file, {
            "image_file": image_file,
            "archive_path": archive_path,
            "caption": row["caption"],
            "paper_id": paper_id,
            "figure_id": row["figure_id"],
        })
        queries.append({
            "query_id": row["instance_id"],
            "question": row["question"],
            "reference_image_file": image_file,
            "paper_id": paper_id,
            "qa_pair_type": row["qa_pair_type"],
        })
    corpus = sorted(corpus_by_image.values(), key=lambda row: row["image_file"])
    corpus_index = {row["image_file"]: index for index, row in enumerate(corpus)}
    for query in queries:
        query["relevant_index"] = corpus_index[query["reference_image_file"]]
    queries.sort(key=lambda row: row["query_id"])
    return corpus, queries


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the SciVQA external retrieval contract")
    parser.add_argument("--config", default="configs/r3_scivqa_external_manifest.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset_path = Path(config["dataset"]["json"])
    images_path = Path(config["dataset"]["images_zip"])
    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    spiqa = json.loads(Path(config["dataset"]["spiqa_json"]).read_text(encoding="utf-8"))
    excluded_papers = {normalize_paper_id(paper_id) for paper_id in spiqa}
    with zipfile.ZipFile(images_path) as archive:
        archive_names = set(archive.namelist())
    corpus, queries = build_manifest(
        rows, archive_names, config["dataset"]["image_archive_prefix"], excluded_papers,
        set(config["selection"]["excluded_qa_pair_types"]),
    )
    selected_papers = {row["paper_id"] for row in corpus}
    output = {
        "config": config,
        "config_sha256": config_hash(config),
        "dataset_sha256": sha256_file(dataset_path),
        "images_zip_sha256": sha256_file(images_path),
        "spiqa_sha256": sha256_file(config["dataset"]["spiqa_json"]),
        "contract": {
            "external_dataset": config["dataset"].get("name", "katebor/SciVQA validation"),
            "usage": config["dataset"].get("usage", "one-shot external retrieval evaluation"),
            "excluded_qa_pair_types": config["selection"]["excluded_qa_pair_types"],
            "spiqa_paper_overlap": len(selected_papers & excluded_papers),
            "papers": len(selected_papers),
            "corpus_images": len(corpus),
            "queries": len(queries),
        },
        "corpus": corpus,
        "queries": queries,
    }
    minimum = config["gate"]
    passed = (
        len(queries) >= int(minimum["min_queries"])
        and len(corpus) >= int(minimum["min_images"])
        and output["contract"]["spiqa_paper_overlap"] == 0
    )
    output["gate_passed"] = passed
    target = Path(config["outputs"]["manifest"])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **output["contract"], "gate_passed": passed}, indent=2))
    raise SystemExit(0 if passed else 2)


if __name__ == "__main__":
    main()
