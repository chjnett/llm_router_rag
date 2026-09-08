from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import load_split_from_archive, sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the R1-P ten-paper QASPER page-mapping sample")
    parser.add_argument("--config", default="configs/r1_page_mapping.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    source = json.loads(Path(config["dataset"]["calibration_results"]).read_text(encoding="utf-8"))
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    by_paper = defaultdict(list)
    for row in source["questions"]:
        by_paper[row["paper_id"]].append(row["question_id"])
    minimum = int(config["selection"]["min_evaluable_questions_per_paper"])
    eligible = [paper_id for paper_id in sorted(by_paper) if len(by_paper[paper_id]) >= minimum]
    selected = eligible[:int(config["selection"]["paper_count"])]
    manifest = {
        "config_sha256": config_hash(config), "archive_sha256": sha256_file(config["dataset"]["archive"]),
        "papers": [{
            "paper_id": paper_id, "title": dataset[paper_id]["title"],
            "pdf_url": f"https://arxiv.org/pdf/{paper_id}",
            "question_ids": sorted(by_paper[paper_id]),
        } for paper_id in selected],
    }
    target = Path(config["outputs"]["root"]) / "sample_manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), "papers": len(selected),
                      "questions": sum(len(by_paper[paper_id]) for paper_id in selected),
                      "paper_ids": selected}, indent=2))
    if len(selected) != int(config["selection"]["paper_count"]):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
