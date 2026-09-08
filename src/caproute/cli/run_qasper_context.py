from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

from caproute.cli.run_qasper_dense import encode
from caproute.core.config import config_hash, load_config
from caproute.datasets.qasper import contextual_paragraphs, load_split_from_archive, sha256_file
from caproute.evaluation.retrieval import mean_metrics, retrieval_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate section/title context in frozen QASPER dense retrieval")
    parser.add_argument("--config", default="configs/r1_qasper_context.yaml")
    args = parser.parse_args()
    config = load_config(args.config)
    baseline = json.loads(Path(config["dataset"]["dense_results"]).read_text(encoding="utf-8"))
    dataset = load_split_from_archive(config["dataset"]["archive"], config["dataset"]["split"])
    model_config = config["model"]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_config["local_path"], local_files_only=True)
    model = AutoModel.from_pretrained(model_config["local_path"], local_files_only=True).to(device).eval()
    cutoffs = tuple(int(value) for value in config["evaluation"]["cutoffs"])
    paper_embeddings = {}
    details = []
    started = time.perf_counter()

    for result in baseline["questions"]:
        paper_id = result["paper_id"]
        paper = dataset[paper_id]
        if paper_id not in paper_embeddings:
            passages = contextual_paragraphs(paper)
            paper_embeddings[paper_id] = encode(passages, tokenizer, model, device, int(model_config["batch_size"]), int(model_config["max_length"]))
        passage_embeddings = paper_embeddings[paper_id]
        qa = next(row for row in paper["qas"] if row["question_id"] == result["question_id"])
        queries = {
            "section_passage": model_config["query_prefix"] + qa["question"],
            "title_query_and_section_passage": model_config["query_prefix"] + f"Paper: {paper['title']} Question: {qa['question']}",
        }
        relevant = set(result["relevant_indices"])
        row = {"paper_id": paper_id, "question_id": result["question_id"]}
        for variant in config["variants"]:
            query = encode([queries[variant]], tokenizer, model, device, 1, int(model_config["max_length"]))[0]
            ranking = np.argsort(-(passage_embeddings @ query), kind="stable").tolist()
            row[variant] = retrieval_metrics(ranking, relevant, cutoffs)
        details.append(row)

    metrics = {variant: mean_metrics([row[variant] for row in details]) for variant in config["variants"]}
    best = max(metrics, key=lambda variant: (metrics[variant]["recall_at_5"], metrics[variant]["ndcg_at_5"]))
    gate = config["gate"]
    summary = {
        "evaluated_questions": len(details), "device": str(device),
        "wall_seconds": time.perf_counter() - started, "variants": metrics, "best_variant": best,
        "gate_passed": metrics[best]["recall_at_5"] >= float(gate["min_recall_at_5"])
        and metrics[best]["ndcg_at_5"] >= float(gate["min_ndcg_at_5"]),
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
