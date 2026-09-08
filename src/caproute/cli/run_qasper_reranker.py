from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive, sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def score_pairs(query: str, passages: list[str], tokenizer, model, device: torch.device, batch_size: int, max_length: int) -> list[float]:
    scores: list[float] = []
    for start in range(0, len(passages), batch_size):
        batch = passages[start:start + batch_size]
        inputs = tokenizer([query] * len(batch), batch, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.inference_mode():
            logits = model(**inputs).logits.squeeze(-1)
        scores.extend(float(value) for value in logits.cpu())
    return scores


def main() -> None:
    parser = argparse.ArgumentParser(description="Rerank frozen BM25+dense QASPER candidates")
    parser.add_argument("--config", default="configs/r1_qasper_reranker.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    bm25 = json.loads(Path(config["dataset"]["bm25_results"]).read_text(encoding="utf-8"))
    dense = json.loads(Path(config["dataset"]["dense_results"]).read_text(encoding="utf-8"))
    bm25_by_id = {row["question_id"]: row for row in bm25["questions"]}
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_config = config["model"]
    tokenizer = AutoTokenizer.from_pretrained(model_config["local_path"], local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(model_config["local_path"], local_files_only=True).to(device).eval()
    cutoffs = tuple(int(value) for value in config["evaluation"]["cutoffs"])
    details = []
    started = time.perf_counter()

    for result in dense["questions"]:
        lexical = bm25_by_id[result["question_id"]]
        paper = dataset[result["paper_id"]]
        paragraphs = canonical_paragraphs(paper)
        question = next(row["question"] for row in paper["qas"] if row["question_id"] == result["question_id"])
        candidates = list(dict.fromkeys(
            lexical["bm25_top_indices"][:int(config["candidate_pool"]["bm25_top_k"])]
            + result["dense_top_indices"][:int(config["candidate_pool"]["dense_top_k"])]
        ))
        scores = score_pairs(question, [paragraphs[index] for index in candidates], tokenizer, model, device, int(model_config["batch_size"]), int(model_config["max_length"]))
        ranking = [index for _, index in sorted(zip(scores, candidates), key=lambda row: (-row[0], row[1]))]
        relevant = set(result["relevant_indices"])
        details.append({
            "paper_id": result["paper_id"], "question_id": result["question_id"],
            "candidate_count": len(candidates), "candidate_recall": len(set(candidates) & relevant) / len(relevant),
            "reranker": retrieval_metrics(ranking, relevant, cutoffs),
            "top_indices": ranking[:max(cutoffs)], "relevant_indices": sorted(relevant),
        })

    metrics = mean_metrics([row["reranker"] for row in details])
    summary = {
        "evaluated_questions": len(details), "device": str(device),
        "wall_seconds": time.perf_counter() - started,
        "mean_candidate_count": sum(row["candidate_count"] for row in details) / len(details),
        "candidate_recall": sum(row["candidate_recall"] for row in details) / len(details),
        "reranker": metrics,
        "gate_passed": metrics["recall_at_5"] >= float(config["gate"]["min_recall_at_5"])
        and metrics["ndcg_at_5"] >= float(config["gate"]["min_ndcg_at_5"]),
    }
    output = {
        "schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config, "config_sha256": config_hash(config),
        "archive_sha256": sha256_file(config["dataset"]["archive"]),
        "summary": summary, "questions": details,
    }
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
