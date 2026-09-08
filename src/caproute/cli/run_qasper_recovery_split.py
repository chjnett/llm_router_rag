from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

from caproute.cli.run_qasper_adjacent_rescue import expand_adjacent
from caproute.cli.run_qasper_dense import encode
from caproute.cli.run_qasper_reranker import score_pairs
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import canonical_paragraphs, contextual_paragraphs, load_split_from_archive, normalize_evidence, sha256_file
from caproute.evaluation.retrieval import bm25_rank, mean_metrics, retrieval_metrics


def mapped_relevant_indices(paper: dict, qa: dict) -> set[int]:
    evidence = {
        normalize_evidence(item)
        for annotation in qa["answers"] if not annotation["answer"].get("unanswerable", False)
        for item in annotation["answer"].get("evidence", [])
        if normalize_evidence(item) and normalize_evidence(item) != "float selected"
    }
    return {
        index for index, paragraph in enumerate(canonical_paragraphs(paper))
        if normalize_evidence(paragraph) in evidence
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a frozen retrieval method on one QASPER paper-disjoint split")
    parser.add_argument("--config", default="configs/r1_calibration_baseline.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    manifest = json.loads(Path(config["dataset"]["manifest"]).read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    dense_config = config["dense_model"]
    dense_tokenizer = AutoTokenizer.from_pretrained(dense_config["local_path"], local_files_only=True)
    dense_model = AutoModel.from_pretrained(dense_config["local_path"], local_files_only=True).to(device).eval()
    rerank_config = config["reranker"]
    rerank_tokenizer = AutoTokenizer.from_pretrained(rerank_config["local_path"], local_files_only=True)
    rerank_model = AutoModelForSequenceClassification.from_pretrained(rerank_config["local_path"], local_files_only=True).to(device).eval()

    cutoffs = tuple(int(value) for value in config["evaluation"]["cutoffs"])
    pool_config = config["candidate_pool"]
    paper_cache: dict[str, tuple[list[str], list[str], np.ndarray]] = {}
    details = []
    skipped = []
    started = time.perf_counter()
    for item in manifest:
        paper_id, question_id = item["paper_id"], item["question_id"]
        paper = dataset[paper_id]
        qa = next(row for row in paper["qas"] if row["question_id"] == question_id)
        relevant = mapped_relevant_indices(paper, qa)
        if not relevant:
            skipped.append({"paper_id": paper_id, "question_id": question_id, "reason": "no_exact_mapped_text_evidence"})
            continue
        if paper_id not in paper_cache:
            plain = canonical_paragraphs(paper)
            contextual = contextual_paragraphs(paper)
            embeddings = encode(contextual, dense_tokenizer, dense_model, device, int(dense_config["batch_size"]), int(dense_config["max_length"]))
            paper_cache[paper_id] = plain, contextual, embeddings
        plain, contextual, passage_embeddings = paper_cache[paper_id]
        bm25_ranking = bm25_rank(qa["question"], plain, float(config["retrieval"]["bm25_k1"]), float(config["retrieval"]["bm25_b"]))
        query_embedding = encode([dense_config["query_prefix"] + qa["question"]], dense_tokenizer, dense_model, device, 1, int(dense_config["max_length"]))[0]
        dense_ranking = np.argsort(-(passage_embeddings @ query_embedding), kind="stable").tolist()
        seeds = list(dict.fromkeys(
            dense_ranking[:int(pool_config["section_dense_top_k"])]
            + bm25_ranking[:int(pool_config["bm25_top_k"])]
        ))
        candidates = expand_adjacent(seeds, len(plain), int(pool_config["adjacent_radius"]))
        scores = score_pairs(qa["question"], [contextual[index] for index in candidates], rerank_tokenizer, rerank_model,
                             device, int(rerank_config["batch_size"]), int(rerank_config["max_length"]))
        rescue_ranking = [index for _, index in sorted(zip(scores, candidates), key=lambda row: (-row[0], row[1]))]
        details.append({
            "paper_id": paper_id, "question_id": question_id, "relevant_indices": sorted(relevant),
            "bm25": retrieval_metrics(bm25_ranking, relevant, cutoffs),
            "section_dense": retrieval_metrics(dense_ranking, relevant, cutoffs),
            "rescue": retrieval_metrics(rescue_ranking, relevant, cutoffs),
            "bm25_top_indices": bm25_ranking[:max(cutoffs)], "section_dense_top_indices": dense_ranking[:max(cutoffs)],
            "candidate_indices": candidates, "candidate_scores": scores,
            "candidate_recall": len(set(candidates) & relevant) / len(relevant),
        })

    method_metrics = {
        method: mean_metrics([row[method] for row in details])
        for method in ("bm25", "section_dense", "rescue")
    }
    rescue = method_metrics["rescue"]
    summary = {
        "manifest_questions": len(manifest), "evaluated_questions": len(details), "skipped_questions": len(skipped),
        "unique_papers": len(paper_cache), "device": str(device), "wall_seconds": time.perf_counter() - started,
        "candidate_recall": sum(row["candidate_recall"] for row in details) / len(details),
        "methods": method_metrics,
        "gate_passed": rescue["recall_at_5"] >= float(config["gate"]["min_recall_at_5"])
        and rescue["ndcg_at_5"] >= float(config["gate"]["min_ndcg_at_5"]),
    }
    output = {"schema_version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "config": config,
              "config_sha256": config_hash(config), "archive_sha256": sha256_file(config["dataset"]["archive"]),
              "summary": summary, "skipped": skipped, "questions": details}
    target = Path(config["outputs"]["root"]) / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(target), **summary}, indent=2))
    raise SystemExit(0 if summary["gate_passed"] else 2)


if __name__ == "__main__":
    main()
