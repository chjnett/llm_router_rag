from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

from caproute.cli.run_qasper_dense import encode
from caproute.cli.run_qasper_reranker import score_pairs
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import contextual_paragraphs, load_split_from_archive, sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def expand_adjacent(indices: list[int], document_length: int, radius: int) -> list[int]:
    expanded: list[int] = []
    seen: set[int] = set()
    for index in indices:
        for candidate in range(max(0, index - radius), min(document_length, index + radius + 1)):
            if candidate not in seen:
                seen.add(candidate)
                expanded.append(candidate)
    return expanded


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen final QASPER adjacent-window rescue preflight")
    parser.add_argument("--config", default="configs/r1_qasper_adjacent_rescue.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    bm25 = json.loads(Path(config["dataset"]["bm25_results"]).read_text(encoding="utf-8"))
    dense = json.loads(Path(config["dataset"]["dense_results"]).read_text(encoding="utf-8"))
    bm25_by_id = {row["question_id"]: row for row in bm25["questions"]}
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dense_config = config["dense_model"]
    dense_tokenizer = AutoTokenizer.from_pretrained(dense_config["local_path"], local_files_only=True)
    dense_model = AutoModel.from_pretrained(dense_config["local_path"], local_files_only=True).to(device).eval()
    rerank_config = config["reranker"]
    rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_config["local_path"], local_files_only=True)
    rerank_model = AutoModelForSequenceClassification.from_pretrained(rerank_config["local_path"], local_files_only=True).to(device).eval()

    cutoffs = tuple(int(value) for value in config["evaluation"]["cutoffs"])
    pool_config = config["candidate_pool"]
    encoded_papers: dict[str, tuple[list[str], np.ndarray]] = {}
    details = []
    started = time.perf_counter()
    for result in dense["questions"]:
        paper_id = result["paper_id"]
        paper = dataset[paper_id]
        if paper_id not in encoded_papers:
            passages = contextual_paragraphs(paper)
            embeddings = encode(passages, dense_tokenizer, dense_model, device, int(dense_config["batch_size"]), int(dense_config["max_length"]))
            encoded_papers[paper_id] = passages, embeddings
        passages, passage_embeddings = encoded_papers[paper_id]
        question = next(row["question"] for row in paper["qas"] if row["question_id"] == result["question_id"])
        query_embedding = encode([dense_config["query_prefix"] + question], dense_tokenizer, dense_model, device, 1, int(dense_config["max_length"]))[0]
        section_dense = np.argsort(-(passage_embeddings @ query_embedding), kind="stable").tolist()
        lexical = bm25_by_id[result["question_id"]]["bm25_top_indices"]
        seeds = list(dict.fromkeys(
            section_dense[:int(pool_config["section_dense_top_k"])]
            + lexical[:int(pool_config["bm25_top_k"])]
        ))
        candidates = expand_adjacent(seeds, len(passages), int(pool_config["adjacent_radius"]))
        scores = score_pairs(question, [passages[index] for index in candidates], rerank_tokenizer, rerank_model, device,
                             int(rerank_config["batch_size"]), int(rerank_config["max_length"]))
        ranking = [index for _, index in sorted(zip(scores, candidates), key=lambda row: (-row[0], row[1]))]
        relevant = set(result["relevant_indices"])
        details.append({
            "paper_id": paper_id, "question_id": result["question_id"],
            "seed_count": len(seeds), "candidate_count": len(candidates),
            "candidate_recall": len(set(candidates) & relevant) / len(relevant),
            "rescue": retrieval_metrics(ranking, relevant, cutoffs),
            "top_indices": ranking[:max(cutoffs)], "relevant_indices": sorted(relevant),
        })

    metrics = mean_metrics([row["rescue"] for row in details])
    summary = {
        "evaluated_questions": len(details), "device": str(device), "wall_seconds": time.perf_counter() - started,
        "mean_seed_count": sum(row["seed_count"] for row in details) / len(details),
        "mean_candidate_count": sum(row["candidate_count"] for row in details) / len(details),
        "candidate_recall": sum(row["candidate_recall"] for row in details) / len(details),
        "rescue": metrics,
        "gate_passed": metrics["recall_at_5"] >= float(config["gate"]["min_recall_at_5"])
        and metrics["ndcg_at_5"] >= float(config["gate"]["min_ndcg_at_5"]),
    }
    output = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "config": config,
              "config_sha256": config_hash(config), "archive_sha256": sha256_file(config["dataset"]["archive"]),
              "summary": summary, "questions": details}
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
