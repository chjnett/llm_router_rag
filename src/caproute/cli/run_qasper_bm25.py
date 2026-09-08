from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive, normalize_evidence, sha256_file
from caproute.evaluation.retrieval import bm25_rank, mean_metrics, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen QASPER oracle and BM25 retrieval baselines")
    parser.add_argument("--config", default="configs/r1_qasper_bm25.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    audit = json.loads(Path(config["dataset"]["audit"]).read_text(encoding="utf-8"))
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    cutoffs = tuple(int(value) for value in config["retrieval"]["cutoffs"])

    details = []
    for frozen in audit["questions"]:
        paper = dataset[frozen["paper_id"]]
        paragraphs = canonical_paragraphs(paper)
        normalized = [normalize_evidence(text) for text in paragraphs]
        qa = next(row for row in paper["qas"] if row["question_id"] == frozen["question_id"])
        evidence = {
            normalize_evidence(item)
            for annotation in qa["answers"] if not annotation["answer"].get("unanswerable", False)
            for item in annotation["answer"].get("evidence", [])
            if normalize_evidence(item) and normalize_evidence(item) != "float selected"
        }
        relevant = {index for index, paragraph in enumerate(normalized) if paragraph in evidence}
        if not relevant:
            continue
        oracle_rank = sorted(relevant) + [index for index in range(len(paragraphs)) if index not in relevant]
        bm25 = bm25_rank(qa["question"], paragraphs, float(config["retrieval"]["bm25_k1"]), float(config["retrieval"]["bm25_b"]))
        details.append({
            "paper_id": frozen["paper_id"], "question_id": frozen["question_id"],
            "paragraph_count": len(paragraphs), "relevant_count": len(relevant),
            "oracle": retrieval_metrics(oracle_rank, relevant, cutoffs),
            "bm25": retrieval_metrics(bm25, relevant, cutoffs),
            "bm25_top_indices": bm25[:max(cutoffs)], "relevant_indices": sorted(relevant),
        })

    summary = {
        "evaluated_questions": len(details),
        "skipped_without_mapped_evidence": len(audit["questions"]) - len(details),
        "oracle": mean_metrics([row["oracle"] for row in details]),
        "bm25": mean_metrics([row["bm25"] for row in details]),
    }
    output = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config, "config_sha256": config_hash(config),
        "archive_sha256": sha256_file(config["dataset"]["archive"]),
        "audit_config_sha256": audit["config_sha256"], "summary": summary, "questions": details,
    }
    output_root = Path(config["outputs"]["root"])
    output_root.mkdir(parents=True, exist_ok=True)
    target = output_root / "results.json"
    target.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))


if __name__ == "__main__":
    main()
