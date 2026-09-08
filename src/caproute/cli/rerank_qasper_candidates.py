from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from caproute.cli.run_qasper_reranker import score_pairs
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import contextual_paragraphs, load_split_from_archive, sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Rerank a frozen QASPER candidate pool with another fixed model")
    parser.add_argument("--config", default="configs/r1_calibration_reranker_l12.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    source = json.loads(Path(config["dataset"]["candidate_results"]).read_text(encoding="utf-8"))
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_config = config["reranker"]
    tokenizer = AutoTokenizer.from_pretrained(model_config["local_path"], local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_config["local_path"], local_files_only=True).to(device).eval()
    cutoffs = tuple(int(value) for value in config["evaluation"]["cutoffs"])
    details = []
    passage_cache = {}
    started = time.perf_counter()
    for row in source["questions"]:
        paper_id = row["paper_id"]
        paper = dataset[paper_id]
        if paper_id not in passage_cache:
            passage_cache[paper_id] = contextual_paragraphs(paper)
        passages = passage_cache[paper_id]
        question = next(item["question"] for item in paper["qas"] if item["question_id"] == row["question_id"])
        candidates = row["candidate_indices"]
        scores = score_pairs(question, [passages[index] for index in candidates], tokenizer, model, device,
                             int(model_config["batch_size"]), int(model_config["max_length"]))
        ranking = [index for _, index in sorted(zip(scores, candidates), key=lambda item: (-item[0], item[1]))]
        relevant = set(row["relevant_indices"])
        details.append({
            "paper_id": paper_id, "question_id": row["question_id"], "relevant_indices": sorted(relevant),
            "candidate_indices": candidates, "candidate_scores": scores,
            "reranker": retrieval_metrics(ranking, relevant, cutoffs),
        })
    metrics = mean_metrics([row["reranker"] for row in details])
    summary = {
        "evaluated_questions": len(details), "device": str(device), "wall_seconds": time.perf_counter() - started,
        "reranker": metrics,
        "gate_passed": metrics["recall_at_5"] >= float(config["gate"]["min_recall_at_5"])
        and metrics["ndcg_at_5"] >= float(config["gate"]["min_ndcg_at_5"]),
    }
    output = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "config": config,
              "config_sha256": config_hash(config), "archive_sha256": sha256_file(config["dataset"]["archive"]),
              "source_config_sha256": source["config_sha256"], "summary": summary, "questions": details}
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
