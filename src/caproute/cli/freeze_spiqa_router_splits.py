from __future__ import annotations

import argparse
import json
import random
import zipfile
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import sha256_file


def eligible_by_paper(dataset: dict, archive_names: set[str], excluded: set[str]) -> dict[str, list[dict]]:
    result = {}
    for paper_id in sorted(dataset):
        if paper_id in excluded:
            continue
        rows = []
        paper = dataset[paper_id]
        for qa_index, qa in enumerate(paper["qa"]):
            reference = qa.get("reference")
            metadata = paper["all_figures"].get(reference)
            if not metadata or metadata.get("content_type") not in {"table", "figure"}:
                continue
            if f"SPIQA_testA_Images_224px/{paper_id}/{reference}" not in archive_names:
                continue
            rows.append({"paper_id": paper_id, "qa_index": qa_index, "question": qa["question"],
                         "reference": reference, "content_type": metadata["content_type"]})
        if rows:
            result[paper_id] = rows
    return result


def allocate(papers: list[str], rows_by_paper: dict[str, list[dict]], target: int) -> tuple[list[str], list[str]]:
    selected = []
    count = 0
    for index, paper_id in enumerate(papers):
        if count >= target:
            return selected, papers[index:]
        selected.append(paper_id)
        count += len(rows_by_paper[paper_id])
    return selected, []


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze paper-disjoint SPIQA router splits")
    parser.add_argument("--config", default="configs/p1v_spiqa_router_splits.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset = json.loads(Path(config["dataset"]["json"]).read_text(encoding="utf-8"))
    excluded = set()
    for manifest in config["excluded_manifests"]:
        excluded.update(row["paper_id"] for row in json.loads(Path(manifest).read_text(encoding="utf-8")))
    with zipfile.ZipFile(config["dataset"]["images_zip"]) as archive:
        rows_by_paper = eligible_by_paper(dataset, set(archive.namelist()), excluded)
    papers = sorted(rows_by_paper)
    random.Random(int(config["seed"])).shuffle(papers)
    train_papers, remaining = allocate(papers, rows_by_paper, int(config["targets"]["train_questions"]))
    calibration_papers, certification_papers = allocate(
        remaining, rows_by_paper, int(config["targets"]["calibration_questions"])
    )
    splits = {"train": train_papers, "calibration": calibration_papers, "certification": certification_papers}
    output_root = Path(config["outputs"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    summary = {"excluded_papers": len(excluded), "eligible_papers": len(rows_by_paper), "splits": {}}
    for name, paper_ids in splits.items():
        rows = [row for paper_id in paper_ids for row in rows_by_paper[paper_id]]
        (output_root / f"{name}_manifest.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        summary["splits"][name] = {
            "papers": len(paper_ids), "questions": len(rows),
            "tables": sum(row["content_type"] == "table" for row in rows),
            "figures": sum(row["content_type"] == "figure" for row in rows),
        }
    paper_sets = [set(ids) for ids in splits.values()]
    summary["paper_disjoint"] = all(not paper_sets[i] & paper_sets[j] for i in range(3) for j in range(i + 1, 3))
    output = {"config": config, "config_sha256": config_hash(config),
              "dataset_sha256": sha256_file(config["dataset"]["json"]), "summary": summary}
    (output_root / "summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
