from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as functional
from transformers import AutoModel, AutoTokenizer

from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import canonical_paragraphs, load_split_from_archive, normalize_evidence, sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def encode(texts: list[str], tokenizer, model, device: torch.device, batch_size: int, max_length: int) -> np.ndarray:
    rows = []
    for start in range(0, len(texts), batch_size):
        inputs = tokenizer(texts[start:start + batch_size], padding=True, truncation=True, max_length=max_length, return_tensors="pt")
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.inference_mode():
            output = model(**inputs).last_hidden_state[:, 0]
            output = functional.normalize(output, p=2, dim=1)
        rows.append(output.cpu().numpy())
    return np.concatenate(rows) if rows else np.empty((0, model.config.hidden_size), dtype=np.float32)


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = 60) -> list[int]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, index in enumerate(ranking, 1):
            scores[index] = scores.get(index, 0.0) + 1.0 / (k + rank)
    return sorted(scores, key=lambda index: (-scores[index], index))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run frozen BGE dense and BM25+dense hybrid baselines")
    parser.add_argument("--config", default="configs/r1_qasper_dense.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    audit = json.loads(Path(config["dataset"]["audit"]).read_text(encoding="utf-8"))
    bm25 = json.loads(Path(config["dataset"]["bm25_results"]).read_text(encoding="utf-8"))
    bm25_by_id = {row["question_id"]: row for row in bm25["questions"]}
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    model_config = config["model"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_config["local_path"], local_files_only=True)
    model = AutoModel.from_pretrained(model_config["local_path"], local_files_only=True).to(device).eval()
    cutoffs = tuple(int(value) for value in config["retrieval"]["cutoffs"])
    question_prefix = model_config["query_prefix"]
    details = []
    encoded_papers: dict[str, tuple[list[str], np.ndarray]] = {}
    started = time.perf_counter()

    for frozen in audit["questions"]:
        baseline = bm25_by_id.get(frozen["question_id"])
        if baseline is None:
            continue
        paper_id = frozen["paper_id"]
        paper = dataset[paper_id]
        if paper_id not in encoded_papers:
            paragraphs = canonical_paragraphs(paper)
            embeddings = encode(paragraphs, tokenizer, model, device, int(model_config["batch_size"]), int(model_config["max_length"]))
            encoded_papers[paper_id] = paragraphs, embeddings
        paragraphs, passage_embeddings = encoded_papers[paper_id]
        qa = next(row for row in paper["qas"] if row["question_id"] == frozen["question_id"])
        query_embedding = encode([question_prefix + qa["question"]], tokenizer, model, device, 1, int(model_config["max_length"]))[0]
        dense_ranking = np.argsort(-(passage_embeddings @ query_embedding), kind="stable").tolist()
        relevant = set(baseline["relevant_indices"])
        hybrid_ranking = reciprocal_rank_fusion([baseline["bm25_top_indices"] + [i for i in range(len(paragraphs)) if i not in baseline["bm25_top_indices"]], dense_ranking], int(config["retrieval"]["rrf_k"]))
        details.append({
            "paper_id": paper_id, "question_id": frozen["question_id"],
            "dense": retrieval_metrics(dense_ranking, relevant, cutoffs),
            "hybrid": retrieval_metrics(hybrid_ranking, relevant, cutoffs),
            "dense_top_indices": dense_ranking[:max(cutoffs)],
            "hybrid_top_indices": hybrid_ranking[:max(cutoffs)],
            "relevant_indices": sorted(relevant),
        })

    elapsed = time.perf_counter() - started
    summary = {
        "evaluated_questions": len(details), "device": str(device),
        "unique_papers": len(encoded_papers), "wall_seconds": elapsed,
        "dense": mean_metrics([row["dense"] for row in details]),
        "hybrid": mean_metrics([row["hybrid"] for row in details]),
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
